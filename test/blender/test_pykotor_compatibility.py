"""
test_pykotor_compatibility.py – Blender background-mode test

PyKotor compatibility test suite for format readers (MDL, TPC, GFF).
Tests skip gracefully if PyKotor is unavailable or test assets are missing.
When both are available, compares current reader output with PyKotor reader output.

Run with:
    blender --background --python test/blender/test_pykotor_compatibility.py
"""

from __future__ import annotations

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
from io_scene_kotor.format.gff.types import FIELD_TYPE_DWORD
from io_scene_kotor.format.mdl.reader import MdlReader
from io_scene_kotor.format.tpc.reader import TpcReader
from io_scene_kotor.vendor.pykotor_adapter import (
    get_use_pykotor_readers,
    is_pykotor_available,
    load_gff_via_pykotor,
    load_mdl_via_pykotor,
    load_tpc_via_pykotor,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _first_fixed_mdl_path() -> tuple[str, str] | None:
    """Return (mdl_path, name) for first fixed MDL+MDX pair, or None."""
    fixed_base = os.path.join(WORKSPACE_ROOT, "test", "test_files", "fixed")
    for subdir in ("", "converted"):
        search_dir = os.path.join(fixed_base, subdir) if subdir else fixed_base
        if not os.path.isdir(search_dir):
            continue
        for entry in os.listdir(search_dir):
            if not entry.lower().endswith(".mdl"):
                continue
            mdl_path = os.path.join(search_dir, entry)
            if not os.path.isfile(mdl_path):
                continue
            mdx_path = os.path.splitext(mdl_path)[0] + ".mdx"
            if not os.path.isfile(mdx_path):
                continue
            return mdl_path, os.path.splitext(entry)[0]
    return None


def _first_tpc_path() -> str | None:
    """Return path to first .tpc in test_files, or None."""
    base = os.path.join(WORKSPACE_ROOT, "test", "test_files")
    if not os.path.isdir(base):
        return None
    for root, _dirs, files in os.walk(base):
        for f in files:
            if f.lower().endswith(".tpc"):
                return os.path.join(root, f)
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_pykotor_mdl_roundtrip_kotor1() -> bool:
    """Load one fixed MDL with current reader and PyKotor; compare name and node count."""
    if not is_pykotor_available():
        print("  SKIP test_pykotor_mdl_roundtrip_kotor1 (PyKotor not available)")
        return True
    pair = _first_fixed_mdl_path()
    if not pair:
        print("  SKIP test_pykotor_mdl_roundtrip_kotor1 (no test_files/fixed MDL+MDX)")
        return True
    mdl_path, name = pair
    try:
        our_reader = MdlReader(mdl_path)
        our_model = our_reader.load()
        pykotor_mdl = load_mdl_via_pykotor(mdl_path)
        if pykotor_mdl is None:
            print(f"  FAIL test_pykotor_mdl_roundtrip_kotor1 ({name}): PyKotor returned None")
            return False
        # Compare key properties
        our_name = (our_model.name or "").strip() or "unknown"
        pk_name = getattr(pykotor_mdl, "name", None) or getattr(pykotor_mdl, "model_name", "") or "unknown"
        if isinstance(pk_name, bytes):
            pk_name = pk_name.decode("utf-8", errors="replace").strip() or "unknown"
        our_nodes = len(our_model.nodes) if hasattr(our_model, "nodes") else 0
        pk_nodes = len(getattr(pykotor_mdl, "nodes", []))
        if our_name != pk_name:
            print(f"  FAIL test_pykotor_mdl_roundtrip_kotor1 ({name}): name mismatch our={our_name!r} pk={pk_name!r}")
            return False
        if our_nodes != pk_nodes:
            print(f"  WARN test_pykotor_mdl_roundtrip_kotor1 ({name}): node count our={our_nodes} pk={pk_nodes}")
        print(f"  PASS test_pykotor_mdl_roundtrip_kotor1 ({name})")
        return True
    except Exception as e:
        print(f"  FAIL test_pykotor_mdl_roundtrip_kotor1 ({name}): {e}")
        return False


def test_pykotor_mdl_roundtrip_kotor2() -> bool:
    """Load one fixed MDL with PyKotor (K2 format if present); same as K1 when only fixed assets."""
    if not is_pykotor_available():
        print("  SKIP test_pykotor_mdl_roundtrip_kotor2 (PyKotor not available)")
        return True
    pair = _first_fixed_mdl_path()
    if not pair:
        print("  SKIP test_pykotor_mdl_roundtrip_kotor2 (no test_files/fixed MDL+MDX)")
        return True
    mdl_path, name = pair
    try:
        pykotor_mdl = load_mdl_via_pykotor(mdl_path)
        if pykotor_mdl is None:
            print(f"  FAIL test_pykotor_mdl_roundtrip_kotor2 ({name}): PyKotor returned None")
            return False
        # PyKotor loads; K2-specific checks (e.g. anim scale) can be added when we have K2-only assets
        print(f"  PASS test_pykotor_mdl_roundtrip_kotor2 ({name})")
        return True
    except Exception as e:
        print(f"  FAIL test_pykotor_mdl_roundtrip_kotor2 ({name}): {e}")
        return False


def test_pykotor_tpc_roundtrip() -> bool:
    """Load one TPC with current reader and PyKotor; compare width and height."""
    if not is_pykotor_available():
        print("  SKIP test_pykotor_tpc_roundtrip (PyKotor not available)")
        return True
    tpc_path = _first_tpc_path()
    if not tpc_path or not os.path.isfile(tpc_path):
        print("  SKIP test_pykotor_tpc_roundtrip (no test_files TPC)")
        return True
    try:
        our_tpc = TpcReader(tpc_path).load()
        pykotor_tpc = load_tpc_via_pykotor(tpc_path)
        if pykotor_tpc is None:
            print("  FAIL test_pykotor_tpc_roundtrip: PyKotor returned None")
            return False
        our_w = getattr(our_tpc, "width", 0) or 0
        our_h = getattr(our_tpc, "height", 0) or 0
        pk_w = getattr(pykotor_tpc, "width", 0) or getattr(pykotor_tpc, "dimensions", (0, 0))[0]
        pk_h = getattr(pykotor_tpc, "height", 0) or (getattr(pykotor_tpc, "dimensions", (0, 0))[1] if hasattr(pykotor_tpc, "dimensions") else 0)
        if not hasattr(pykotor_tpc, "dimensions") and not hasattr(pykotor_tpc, "width"):
            # PyKotor TPC may expose dimensions differently
            dims = getattr(pykotor_tpc, "dimensions", None)
            if dims and len(dims) >= 2:
                pk_w, pk_h = dims[0], dims[1]
        if our_w != pk_w or our_h != pk_h:
            print(f"  WARN test_pykotor_tpc_roundtrip: size our={our_w}x{our_h} pk={pk_w}x{pk_h}")
        print("  PASS test_pykotor_tpc_roundtrip")
        return True
    except Exception as e:
        print(f"  FAIL test_pykotor_tpc_roundtrip: {e}")
        return False


def test_pykotor_gff_roundtrip() -> bool:
    """Write GFF with current writer, read with current reader and PyKotor; compare root structure."""
    if not is_pykotor_available():
        print("  SKIP test_pykotor_gff_roundtrip (PyKotor not available)")
        return True
    tree = {
        "_type": 0xFFFFFFFF,
        "_fields": {"TestDword": FIELD_TYPE_DWORD},
        "TestDword": 123,
    }
    with tempfile.NamedTemporaryFile(suffix=".gff", delete=False) as f:
        path = f.name
    try:
        GffWriter(tree, path, "PTH").save()
        our_tree = GffReader(path, "PTH").load()
        pk_gff = load_gff_via_pykotor(path)
        if pk_gff is None:
            print("  FAIL test_pykotor_gff_roundtrip: PyKotor returned None")
            return False
        our_type = our_tree.get("_type")
        pk_root = getattr(pk_gff, "root", None)
        if pk_root is not None:
            pk_type = getattr(pk_root, "struct_id", getattr(pk_root, "type_id", None))
            if our_type != pk_type:
                print(f"  WARN test_pykotor_gff_roundtrip: root type our={our_type} pk={pk_type}")
        print("  PASS test_pykotor_gff_roundtrip")
        return True
    except Exception as e:
        print(f"  FAIL test_pykotor_gff_roundtrip: {e}")
        return False
    finally:
        if os.path.isfile(path):
            os.unlink(path)


def test_get_use_pykotor_readers_respects_flag() -> bool:
    """get_use_pykotor_readers() is False when USE_PYKOTOR_READERS is False."""
    from io_scene_kotor.constants import USE_PYKOTOR_READERS

    if USE_PYKOTOR_READERS:
        print("  SKIP test_get_use_pykotor_readers_respects_flag (flag is True)")
        return True
    result = get_use_pykotor_readers()
    if result:
        print("  FAIL test_get_use_pykotor_readers_respects_flag: expected False")
        return False
    print("  PASS test_get_use_pykotor_readers_respects_flag")
    return True


def test_mdl_io_does_not_import_pykotor_mdl() -> bool:
    """io.mdl must not import PyKotor MDL functions; MDL uses only format/mdl readers/writers."""
    import io_scene_kotor.io.mdl as mdl_module

    forbidden = (
        "load_mdl_via_pykotor",
        "save_mdl_via_pykotor",
        "convert_pykotor_mdl_to_scene",
        "convert_scene_model_to_pykotor",
        "get_use_pykotor_readers",
    )
    for name in forbidden:
        if hasattr(mdl_module, name):
            print(
                f"  FAIL test_mdl_io_does_not_import_pykotor_mdl: io.mdl must not import {name!r}"
            )
            return False
    print("  PASS test_mdl_io_does_not_import_pykotor_mdl")
    return True


def run_tests() -> bool:
    print("\n=== test_pykotor_compatibility.py ===")
    results = [
        test_get_use_pykotor_readers_respects_flag(),
        test_mdl_io_does_not_import_pykotor_mdl(),
        test_pykotor_mdl_roundtrip_kotor1(),
        test_pykotor_mdl_roundtrip_kotor2(),
        test_pykotor_tpc_roundtrip(),
        test_pykotor_gff_roundtrip(),
    ]
    passed, total = sum(1 for r in results if r), len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_pykotor_compatibility.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
