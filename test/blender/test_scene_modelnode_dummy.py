"""
test_scene_modelnode_dummy.py – DummyNode tree helpers

Run with:
    blender --background --python test/blender/test_scene_modelnode_dummy.py
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

from io_scene_kotor.scene.modelnode.dummy import DummyNode  # noqa: E402


def test_dummy_find_node_nested() -> bool:
    root = DummyNode("root")
    child = DummyNode("child")
    leaf = DummyNode("leaf")
    root.children.append(child)
    child.parent = root
    child.children.append(leaf)
    leaf.parent = child
    got = root.find_node(lambda n: n.name == "leaf")
    if got is not leaf:
        print("  FAIL test_dummy_find_node_nested")
        return False
    print("  PASS test_dummy_find_node_nested")
    return True


def run_tests() -> bool:
    print("\n=== test_scene_modelnode_dummy.py ===")
    ok = test_dummy_find_node_nested()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_scene_modelnode_dummy.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
