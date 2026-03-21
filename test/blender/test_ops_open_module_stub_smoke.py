"""
test_ops_open_module_stub_smoke.py – kb.open_module with no module selected

Run with:
    blender --background --python test/blender/test_ops_open_module_stub_smoke.py
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

import io_scene_kotor.ops.game.open_module as _kb_open_module  # noqa: F401, E402


def test_open_module_cancelled_when_no_module_selected() -> bool:
    scene = bpy.context.scene
    kb = scene.kb
    kb.module_list.clear()
    kb.module_list_idx = 0
    try:
        result = bpy.ops.kb.open_module()
    except RuntimeError as e:
        # Blender reports operator ERROR to console and raises (background-safe path).
        if "No module selected" in str(e):
            print("  PASS test_open_module_cancelled_when_no_module_selected")
            return True
        print(f"  FAIL open_module unexpected RuntimeError: {e}")
        return False
    if result != {"CANCELLED"}:
        print(f"  FAIL expected CANCELLED, got {result!r}")
        return False
    print("  PASS test_open_module_cancelled_when_no_module_selected")
    return True


def run_tests() -> bool:
    print("\n=== test_ops_open_module_stub_smoke.py ===")
    ok = test_open_module_cancelled_when_no_module_selected()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_ops_open_module_stub_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
