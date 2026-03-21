"""
test_ops_path_connection_smoke.py – kb.add_path_connection / kb.remove_path_connection

Run with:
    blender --background --python test/blender/test_ops_path_connection_smoke.py
"""

from __future__ import annotations

import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

MODULE = "bl_ext.user_default.io_scene_kotor"
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.constants import DummyType  # noqa: E402
import io_scene_kotor.ops.pth.addconnection as _kb_pth_add  # noqa: F401, E402
import io_scene_kotor.ops.pth.removeconnection as _kb_pth_remove  # noqa: F401, E402


def _clear() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def test_add_then_remove_path_connection() -> bool:
    _clear()
    pt = bpy.data.objects.new("pp", None)
    pt.kb.dummytype = DummyType.PATHPOINT
    bpy.context.collection.objects.link(pt)
    bpy.context.view_layer.objects.active = pt
    pt.select_set(True)

    if not bpy.ops.kb.add_path_connection.poll():
        print("  FAIL add_path_connection poll() False")
        _clear()
        return False
    r1 = bpy.ops.kb.add_path_connection()
    if r1 != {"FINISHED"} or len(pt.kb.path_connection_list) != 1:
        print(f"  FAIL add: result={r1!r} len={len(pt.kb.path_connection_list)}")
        _clear()
        return False

    pt.kb.path_connection_idx = 0
    if not bpy.ops.kb.remove_path_connection.poll():
        print("  FAIL remove_path_connection poll() False")
        _clear()
        return False
    r2 = bpy.ops.kb.remove_path_connection()
    ok = r2 == {"FINISHED"} and len(pt.kb.path_connection_list) == 0
    _clear()
    if ok:
        print("  PASS test_add_then_remove_path_connection")
    else:
        print(f"  FAIL remove: result={r2!r} len={len(pt.kb.path_connection_list)}")
    return ok


def run_tests() -> bool:
    print("\n=== test_ops_path_connection_smoke.py ===")
    ok = test_add_then_remove_path_connection()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_ops_path_connection_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
