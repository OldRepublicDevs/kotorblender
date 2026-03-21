"""
test_ops_pth_export_import_smoke.py – bpy.ops.kb.pthexport / kb.pthimport vs io.pth

Run with:
    blender --background --python test/blender/test_ops_pth_export_import_smoke.py
"""

from __future__ import annotations

import os
import sys
import tempfile

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

MODULE = "bl_ext.user_default.io_scene_kotor"
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.constants import DummyType  # noqa: E402


def _clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def _make_single_point() -> None:
    root = bpy.data.objects.new("PTH_Root", None)
    root.kb.dummytype = DummyType.PTHROOT
    bpy.context.collection.objects.link(root)
    pt = bpy.data.objects.new("PathPoint000", None)
    pt.kb.dummytype = DummyType.PATHPOINT
    pt.parent = root
    pt.location = (2.0, -3.0, 0.0)
    bpy.context.collection.objects.link(pt)


def _count_path_points() -> int:
    return sum(1 for o in bpy.data.objects if o.kb.dummytype == DummyType.PATHPOINT)


def test_ops_pthexport_then_pthimport() -> bool:
    _clear_scene()
    _make_single_point()
    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        path = f.name
    try:
        try:
            bpy.ops.kb.pthexport(filepath=path)
        except Exception as e:
            print(f"  FAIL test_ops_pthexport_then_pthimport export: {e}")
            return False
        if not os.path.isfile(path) or os.path.getsize(path) <= 0:
            print("  FAIL test_ops_pthexport_then_pthimport: empty file")
            return False
        _clear_scene()
        try:
            bpy.ops.kb.pthimport(filepath=path)
        except Exception as e:
            print(f"  FAIL test_ops_pthexport_then_pthimport import: {e}")
            return False
        n = _count_path_points()
        if n != 1:
            print(f"  FAIL test_ops_pthexport_then_pthimport: expected 1 point, got {n}")
            return False
    finally:
        if os.path.isfile(path):
            os.unlink(path)
        _clear_scene()
    print("  PASS test_ops_pthexport_then_pthimport")
    return True


def run_tests() -> bool:
    print("\n=== test_ops_pth_export_import_smoke.py ===")
    ok = test_ops_pthexport_then_pthimport()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_ops_pth_export_import_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
