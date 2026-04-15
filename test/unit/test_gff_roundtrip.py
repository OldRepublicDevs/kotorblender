"""
Unit tests for GFF binary format reader/writer roundtrip.

No Blender (bpy) required. Uses real temp files and io_scene_kotor.format.gff.
Run with: pytest test/unit/test_gff_roundtrip.py -v
"""

from __future__ import annotations

import os
import tempfile

import pytest

from io_scene_kotor.format.gff.reader import GffReader
from io_scene_kotor.format.gff.types import (
    FIELD_TYPE_DWORD,
    FIELD_TYPE_FLOAT,
    FIELD_TYPE_LIST,
)
from io_scene_kotor.format.gff.writer import GffWriter


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


def test_dword_roundtrip():
    """A single DWORD field survives write->read unchanged."""
    tree = {
        "_type": 0xFFFFFFFF,
        "_fields": {"MyDword": FIELD_TYPE_DWORD},
        "MyDword": 42,
    }
    result = _write_read(tree)
    assert result["MyDword"] == 42


def test_float_roundtrip():
    """A FLOAT field survives write->read within single-precision tolerance."""
    value = 3.14159
    tree = {
        "_type": 0xFFFFFFFF,
        "_fields": {"MyFloat": FIELD_TYPE_FLOAT},
        "MyFloat": value,
    }
    result = _write_read(tree)
    assert _float_eq(result["MyFloat"], value, tol=1e-4)


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
    assert result["Alpha"] == 100
    assert _float_eq(result["Beta"], -1.5)
    assert result["Gamma"] == 0


def test_empty_list_roundtrip():
    """An empty LIST field round-trips as an empty Python list."""
    tree = {
        "_type": 0xFFFFFFFF,
        "_fields": {"Items": FIELD_TYPE_LIST},
        "Items": [],
    }
    result = _write_read(tree)
    assert result["Items"] == []


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
    assert len(pts) == 2
    assert _float_eq(pts[0]["X"], 10.0) and _float_eq(pts[0]["Y"], 20.0)
    assert pts[0]["Conections"] == 0
    assert _float_eq(pts[1]["X"], -5.5) and pts[1]["Conections"] == 1


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
    conections = [{"_type": 3, "_fields": {"Destination": FIELD_TYPE_DWORD}, "Destination": 1}]
    tree = {
        "_type": 0xFFFFFFFF,
        "_fields": {"Path_Points": FIELD_TYPE_LIST, "Path_Conections": FIELD_TYPE_LIST},
        "Path_Points": points,
        "Path_Conections": conections,
    }
    result = _write_read(tree, file_type="PTH")
    assert len(result["Path_Points"]) == 2 and len(result["Path_Conections"]) == 1
    assert _float_eq(result["Path_Points"][0]["X"], 1.0)
    assert _float_eq(result["Path_Points"][1]["Y"], 4.0)
    assert result["Path_Conections"][0]["Destination"] == 1


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
        with pytest.raises(RuntimeError):
            GffReader(path, "WRONG").load()
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
    assert result["Zero"] == 0 and result["Large"] == 0x7FFFFFFF


def test_negative_float():
    """Negative floats survive write->read."""
    value = -999.75
    tree = {
        "_type": 0xFFFFFFFF,
        "_fields": {"NegF": FIELD_TYPE_FLOAT},
        "NegF": value,
    }
    result = _write_read(tree)
    assert _float_eq(result["NegF"], value, tol=1e-3)


def test_large_list():
    """A list of 50 structs all survives the roundtrip."""
    items = [
        {
            "_type": 1,
            "_fields": {"Idx": FIELD_TYPE_DWORD, "Val": FIELD_TYPE_FLOAT},
            "Idx": i,
            "Val": float(i) * 0.5,
        }
        for i in range(50)
    ]
    tree = {
        "_type": 0xFFFFFFFF,
        "_fields": {"Items": FIELD_TYPE_LIST},
        "Items": items,
    }
    result = _write_read(tree)
    result_items = result["Items"]
    assert len(result_items) == 50
    for i in range(50):
        assert result_items[i]["Idx"] == i and _float_eq(result_items[i]["Val"], i * 0.5)
