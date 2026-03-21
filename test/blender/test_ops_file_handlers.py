"""
test_ops_file_handlers.py – KotOR FileHandler classes registered with correct targets

Run with:
    blender --background --python test/blender/test_ops_file_handlers.py
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

from io_scene_kotor.ops.file_handler_drop import FILE_HANDLER_CLASSES  # noqa: E402


def test_file_handlers_registered_and_target_ops() -> bool:
    if not hasattr(bpy.types, "FileHandler"):
        print("  SKIP test_file_handlers_registered_and_target_ops (no FileHandler API)")
        return True
    expected_ops = {
        "KB_FH_import_mdl": "kb.mdlimport",
        "KB_FH_import_ascii_mdl": "kb.asciimdlimport",
        "KB_FH_import_lyt": "kb.lytimport",
        "KB_FH_import_pth": "kb.pthimport",
        "KB_FH_import_bwm": "kb.bwmimport",
    }
    for cls in FILE_HANDLER_CLASSES:
        bid = cls.bl_idname
        op = cls.bl_import_operator
        if bid not in expected_ops or expected_ops[bid] != op:
            print(f"  FAIL unexpected mapping {bid!r} -> {op!r}")
            return False
        reg = getattr(bpy.types, bid, None)
        if reg is None:
            print(f"  FAIL FileHandler {bid!r} not registered on bpy.types")
            return False
    print("  PASS test_file_handlers_registered_and_target_ops")
    return True


def run_tests() -> bool:
    print("\n=== test_ops_file_handlers.py ===")
    ok = test_file_handlers_registered_and_target_ops()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_ops_file_handlers.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
