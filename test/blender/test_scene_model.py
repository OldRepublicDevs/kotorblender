"""
test_scene_model.py – Model defaults and invariants

Run with:
    blender --background --python test/blender/test_scene_model.py
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

from io_scene_kotor.constants import Classification  # noqa: E402
from io_scene_kotor.scene.model import Model  # noqa: E402


def test_model_default_state() -> bool:
    m = Model()
    if m.name != "UNNAMED":
        print("  FAIL test_model_default_state: name")
        return False
    if m.classification is not Classification.OTHER:
        print("  FAIL test_model_default_state: classification")
        return False
    if m.root_node is not None:
        print("  FAIL test_model_default_state: root_node")
        return False
    if m.animations:
        print("  FAIL test_model_default_state: animations")
        return False
    print("  PASS test_model_default_state")
    return True


def run_tests() -> bool:
    print("\n=== test_scene_model.py ===")
    ok = test_model_default_state()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_scene_model.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
