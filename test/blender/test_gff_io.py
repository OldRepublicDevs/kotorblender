"""
test_gff_io.py – Blender background-mode test

Tests the GFF binary format reader and writer in isolation (no game assets
required).  Creates synthetic GFF trees, writes them to temp files, reads
them back, and asserts round-trip fidelity.

Run with:
    blender --background --python test/blender/test_gff_io.py
"""

import os
import sys
import tempfile

import bpy

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

MODULE = "bl_ext.user_default.io_scene_kotor"
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.format.gff.reader import GffReader
from io_scene_kotor.format.gff.writer import GffWriter
from io_scene_kotor.format.gff.types import (
    FIELD_TYPE_DWORD,
    FIELD_TYPE_FLOAT,
    FIELD_TYPE_LIST,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_read(tree, file_type="TST"):
    """Write *tree* to a temp file, read it back, return the parsed dict."""
    with tempfile.NamedTemporaryFile(suffix=".gff", delete=False) as f:
        path = f.name
    try:
        GffWriter(tree, path, file_type).save()
        return GffReader(path, file_type).load()
    finally:
        os.unlink(path)


def _float_eq(a, b, tol=1e-5):
    return abs(a - b) < tol


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_dword_roundtrip():
    """A single DWORD field survives write→read unchanged."""
    tree = {
        "_type": 0xFFFFFFFF,
        "_fields": {"MyDword": FIELD_TYPE_DWORD},
        "MyDword": 42,
    }
    result = _write_read(tree)
    ok = result["MyDword"] == 42
    if ok:
        print("  PASS test_dword_roundtrip")
    else:
        print(f"  FAIL test_dword_roundtrip: got {result['MyDword']!r}")
    return ok


def test_float_roundtrip():
    """A FLOAT field survives write→read within single-precision tolerance."""
    value = 3.14159
    tree = {
        "_type": 0xFFFFFFFF,
        "_fields": {"MyFloat": FIELD_TYPE_FLOAT},
        "MyFloat": value,
    }
    result = _write_read(tree)
    ok = _float_eq(result["MyFloat"], value, tol=1e-4)
    if ok:
        print("  PASS test_float_roundtrip")
    else:
        print(f"  FAIL test_float_roundtrip: got {result['MyFloat']!r}, expected {value}")
    return ok


def test_multiple_fields_roundtrip():
    """A struct with both DWORD and FLOAT fields round-trips correctly."""
    tree = {
        "_type": 0xFFFFFFFF,
        "_fields": {
            "Alpha": FIELD_TYPE_DWORD,
            "Beta": FIELD_TYPE_FLOAT,
            "Gamma": FIELD_TYPE_DWORD,
        },
        "Alpha": 100,
        "Beta": -1.5,
        "Gamma": 0,
    }
    result = _write_read(tree)
    ok = (
        result["Alpha"] == 100
        and _float_eq(result["Beta"], -1.5)
        and result["Gamma"] == 0
    )
    if ok:
        print("  PASS test_multiple_fields_roundtrip")
    else:
        print(f"  FAIL test_multiple_fields_roundtrip: {result}")
    return ok


def test_empty_list_roundtrip():
    """An empty LIST field round-trips as an empty Python list."""
    tree = {
        "_type": 0xFFFFFFFF,
        "_fields": {"Items": FIELD_TYPE_LIST},
        "Items": [],
    }
    result = _write_read(tree)
    ok = result["Items"] == []
    if ok:
        print("  PASS test_empty_list_roundtrip")
    else:
        print(f"  FAIL test_empty_list_roundtrip: got {result['Items']!r}")
    return ok


def test_list_with_structs_roundtrip():
    """A LIST of structs (path-point style) round-trips correctly."""
    tree = {
        "_type": 0xFFFFFFFF,
        "_fields": {"Points": FIELD_TYPE_LIST},
        "Points": [
            {
                "_type": 2,
                "_fields": {
                    "X": FIELD_TYPE_FLOAT,
                    "Y": FIELD_TYPE_FLOAT,
                    "Conections": FIELD_TYPE_DWORD,
                    "First_Conection": FIELD_TYPE_DWORD,
                },
                "X": 10.0,
                "Y": 20.0,
                "Conections": 0,
                "First_Conection": 0,
            },
            {
                "_type": 2,
                "_fields": {
                    "X": FIELD_TYPE_FLOAT,
                    "Y": FIELD_TYPE_FLOAT,
                    "Conections": FIELD_TYPE_DWORD,
                    "First_Conection": FIELD_TYPE_DWORD,
                },
                "X": -5.5,
                "Y": 0.0,
                "Conections": 1,
                "First_Conection": 0,
            },
        ],
    }
    result = _write_read(tree)
    pts = result["Points"]
    ok = (
        len(pts) == 2
        and _float_eq(pts[0]["X"], 10.0)
        and _float_eq(pts[0]["Y"], 20.0)
        and pts[0]["Conections"] == 0
        and _float_eq(pts[1]["X"], -5.5)
        and pts[1]["Conections"] == 1
        and pts[1]["First_Conection"] == 0
    )
    if ok:
        print("  PASS test_list_with_structs_roundtrip")
    else:
        print(f"  FAIL test_list_with_structs_roundtrip: {result}")
    return ok


def test_pth_shaped_tree_roundtrip():
    """A tree matching the exact PTH schema used by save_pth round-trips."""
    points = [
        {
            "_type": 2,
            "_fields": {
                "Conections": FIELD_TYPE_DWORD,
                "First_Conection": FIELD_TYPE_DWORD,
                "X": FIELD_TYPE_FLOAT,
                "Y": FIELD_TYPE_FLOAT,
            },
            "Conections": 1,
            "First_Conection": 0,
            "X": 1.0,
            "Y": 2.0,
        },
        {
            "_type": 2,
            "_fields": {
                "Conections": FIELD_TYPE_DWORD,
                "First_Conection": FIELD_TYPE_DWORD,
                "X": FIELD_TYPE_FLOAT,
                "Y": FIELD_TYPE_FLOAT,
            },
            "Conections": 0,
            "First_Conection": 1,
            "X": 3.0,
            "Y": 4.0,
        },
    ]
    conections = [
        {
            "_type": 3,
            "_fields": {"Destination": FIELD_TYPE_DWORD},
            "Destination": 1,
        }
    ]
    tree = {
        "_type": 0xFFFFFFFF,
        "_fields": {"Path_Points": FIELD_TYPE_LIST, "Path_Conections": FIELD_TYPE_LIST},
        "Path_Points": points,
        "Path_Conections": conections,
    }
    result = _write_read(tree, file_type="PTH")
    ok = (
        len(result["Path_Points"]) == 2
        and len(result["Path_Conections"]) == 1
        and _float_eq(result["Path_Points"][0]["X"], 1.0)
        and _float_eq(result["Path_Points"][1]["Y"], 4.0)
        and result["Path_Conections"][0]["Destination"] == 1
    )
    if ok:
        print("  PASS test_pth_shaped_tree_roundtrip")
    else:
        print(f"  FAIL test_pth_shaped_tree_roundtrip: {result}")
    return ok


def test_file_type_validation():
    """GffReader raises RuntimeError when file_type mismatches."""
    tree = {
        "_type": 0xFFFFFFFF,
        "_fields": {"Val": FIELD_TYPE_DWORD},
        "Val": 1,
    }
    with tempfile.NamedTemporaryFile(suffix=".gff", delete=False) as f:
        path = f.name
    try:
        GffWriter(tree, path, "PTH").save()
        try:
            GffReader(path, "WRONG").load()
            print("  FAIL test_file_type_validation: expected RuntimeError, got none")
            return False
        except RuntimeError:
            print("  PASS test_file_type_validation")
            return True
    finally:
        os.unlink(path)


def test_zero_and_max_dword():
    """Boundary DWORD values (0 and 0x7FFFFFFF) survive the roundtrip."""
    tree = {
        "_type": 0xFFFFFFFF,
        "_fields": {"Zero": FIELD_TYPE_DWORD, "Large": FIELD_TYPE_DWORD},
        "Zero": 0,
        "Large": 0x7FFFFFFF,
    }
    result = _write_read(tree)
    ok = result["Zero"] == 0 and result["Large"] == 0x7FFFFFFF
    if ok:
        print("  PASS test_zero_and_max_dword")
    else:
        print(f"  FAIL test_zero_and_max_dword: {result}")
    return ok


def test_negative_float():
    """Negative floats survive write→read."""
    value = -999.75
    tree = {
        "_type": 0xFFFFFFFF,
        "_fields": {"NegF": FIELD_TYPE_FLOAT},
        "NegF": value,
    }
    result = _write_read(tree)
    ok = _float_eq(result["NegF"], value, tol=1e-3)
    if ok:
        print("  PASS test_negative_float")
    else:
        print(f"  FAIL test_negative_float: got {result['NegF']}")
    return ok


def test_large_list():
    """A list of 50 structs all survives the roundtrip."""
    items = []
    for i in range(50):
        items.append(
            {
                "_type": 1,
                "_fields": {"Idx": FIELD_TYPE_DWORD, "Val": FIELD_TYPE_FLOAT},
                "Idx": i,
                "Val": float(i) * 0.5,
            }
        )
    tree = {
        "_type": 0xFFFFFFFF,
        "_fields": {"Items": FIELD_TYPE_LIST},
        "Items": items,
    }
    result = _write_read(tree)
    result_items = result["Items"]
    ok = len(result_items) == 50 and all(
        result_items[i]["Idx"] == i and _float_eq(result_items[i]["Val"], i * 0.5)
        for i in range(50)
    )
    if ok:
        print("  PASS test_large_list (50 items)")
    else:
        bad = next((i for i in range(len(result_items)) if result_items[i].get("Idx") != i), -1)
        print(f"  FAIL test_large_list: count={len(result_items)}, first bad index={bad}")
    return ok


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_tests():
    print("\n=== test_gff_io.py ===")
    tests = [
        test_dword_roundtrip,
        test_float_roundtrip,
        test_multiple_fields_roundtrip,
        test_empty_list_roundtrip,
        test_list_with_structs_roundtrip,
        test_pth_shaped_tree_roundtrip,
        test_file_type_validation,
        test_zero_and_max_dword,
        test_negative_float,
        test_large_list,
    ]
    results = [t() for t in tests]
    passed = sum(results)
    total = len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_gff_io.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
