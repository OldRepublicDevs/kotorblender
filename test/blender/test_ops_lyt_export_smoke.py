"""
test_ops_lyt_export_smoke.py – bpy.ops.kb.lytexport (ExportHelper path)

Run with:
    blender --background --python test/blender/test_ops_lyt_export_smoke.py
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
from io_scene_kotor.ops.lyt import export as _kb_lyt_export_module  # noqa: F401, E402


def _clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def _make_mdl_root(name: str) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    obj.kb.dummytype = DummyType.MDLROOT
    bpy.context.collection.objects.link(obj)
    return obj


def _parse_roomcount(content: str) -> int:
    for line in content.splitlines():
        tokens = line.split()
        if tokens and tokens[0].startswith("roomcount"):
            return int(tokens[1])
    return -1


def test_ops_lytexport_writes_expected_roomcount() -> bool:
    _clear_scene()
    _make_mdl_root("room_a")
    _make_mdl_root("room_b")
    with tempfile.NamedTemporaryFile(suffix=".lyt", delete=False) as f:
        path = f.name
    try:
        try:
            bpy.ops.kb.lytexport(filepath=path, check_existing=False)
        except Exception as e:
            print(f"  FAIL test_ops_lytexport_writes_expected_roomcount: {e}")
            return False
        with open(path, encoding="utf-8", errors="replace") as rf:
            content = rf.read()
        rc = _parse_roomcount(content)
        ok = rc == 2 and "beginlayout" in content and "donelayout" in content
        if ok:
            print("  PASS test_ops_lytexport_writes_expected_roomcount")
        else:
            print(f"  FAIL roomcount={rc}, content head:\n{content[:400]}")
        return ok
    finally:
        _clear_scene()
        if os.path.isfile(path):
            os.unlink(path)


def run_tests() -> bool:
    print("\n=== test_ops_lyt_export_smoke.py ===")
    ok = test_ops_lytexport_writes_expected_roomcount()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_ops_lyt_export_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
