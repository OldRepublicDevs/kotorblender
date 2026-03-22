"""
test_ops_clone_module.py – kb.clone_module validation paths (PyKotor + scene.kb)

Run with:
    blender --background --python test/blender/test_ops_clone_module.py
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

from io_scene_kotor.constants import GameType  # noqa: E402
from io_scene_kotor.vendor.pykotor_adapter import is_pykotor_available  # noqa: E402


def test_clone_no_selection() -> bool:
    scene = bpy.context.scene
    kb = scene.kb
    kb.module_list_idx = -1
    try:
        r = bpy.ops.kb.clone_module(new_module_name="x")
    except RuntimeError as e:
        if "No module selected" in str(e):
            print("  PASS test_clone_no_selection (RuntimeError)")
            return True
        print(f"  FAIL unexpected RuntimeError: {e}")
        return False
    ok = r == {"CANCELLED"}
    print(f"  {'PASS' if ok else 'FAIL'} test_clone_no_selection CANCELLED={ok}")
    return ok


def test_clone_invalid_name() -> bool:
    if not is_pykotor_available():
        print("  SKIP test_clone_invalid_name (no PyKotor)")
        return True
    scene = bpy.context.scene
    kb = scene.kb
    kb.module_list.clear()
    m = kb.module_list.add()
    m.name = "dummy"
    kb.module_list_idx = 0
    try:
        r = bpy.ops.kb.clone_module(new_module_name="")
    except RuntimeError as e:
        if "Invalid new module name" in str(e):
            print("  PASS test_clone_invalid_name (RuntimeError)")
            return True
        print(f"  FAIL unexpected RuntimeError: {e}")
        return False
    ok = r == {"CANCELLED"}
    print(f"  {'PASS' if ok else 'FAIL'} test_clone_invalid_name")
    return ok


def test_clone_no_install_path() -> bool:
    if not is_pykotor_available():
        print("  SKIP test_clone_no_install_path (no PyKotor)")
        return True
    scene = bpy.context.scene
    kb = scene.kb
    kb.module_list.clear()
    m = kb.module_list.add()
    m.name = "dummy"
    kb.module_list_idx = 0
    kb.game_type = GameType.CUSTOM.value
    kb.game_installation_path = ""
    try:
        r = bpy.ops.kb.clone_module(new_module_name="newmod")
    except RuntimeError as e:
        msg = str(e)
        if "installation" in msg.lower() or "not set" in msg.lower() or "not found" in msg.lower():
            print("  PASS test_clone_no_install_path (RuntimeError)")
            return True
        print(f"  FAIL unexpected RuntimeError: {e}")
        return False
    ok = r == {"CANCELLED"}
    print(f"  {'PASS' if ok else 'FAIL'} test_clone_no_install_path")
    return ok


def run_tests() -> bool:
    print("\n=== test_ops_clone_module.py ===")
    results = [
        test_clone_no_selection(),
        test_clone_invalid_name(),
        test_clone_no_install_path(),
    ]
    passed, total = sum(results), len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_ops_clone_module.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
