"""
test_ops_open_preferences_smoke.py – kb.open_addon_preferences must not crash

In background mode, preferences.addon_show may not apply; operator should return
FINISHED or CANCELLED without raising.

Run with:
    blender --background --python test/blender/test_ops_open_preferences_smoke.py
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

from io_scene_kotor.ops.misc import open_addon_preferences as _kb_open_prefs  # noqa: F401, E402


def test_open_addon_preferences_no_crash() -> bool:
    try:
        result = bpy.ops.kb.open_addon_preferences()
    except Exception as e:
        print(f"  FAIL open_addon_preferences raised: {e}")
        return False
    if result not in ({"FINISHED"}, {"CANCELLED"}):
        print(f"  FAIL unexpected return {result!r}")
        return False
    print("  PASS test_open_addon_preferences_no_crash")
    return True


def run_tests() -> bool:
    print("\n=== test_ops_open_preferences_smoke.py ===")
    ok = test_open_addon_preferences_no_crash()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_ops_open_preferences_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
