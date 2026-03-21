"""
test_scene_walkmesh.py – Walkmesh class behavior

Run with:
    blender --background --python test/blender/test_scene_walkmesh.py
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

from io_scene_kotor.constants import DummyType, ExportOptions, WalkmeshType  # noqa: E402
from io_scene_kotor.scene.modelnode.aabb import AabbNode  # noqa: E402
from io_scene_kotor.scene.walkmesh import Walkmesh  # noqa: E402


def test_from_aabb_node_is_wok() -> bool:
    aabb = AabbNode("geom")
    wm = Walkmesh.from_aabb_node(aabb)
    if wm.walkmesh_type != WalkmeshType.WOK:
        print("  FAIL test_from_aabb_node_is_wok: type")
        return False
    found = wm.root_node.find_node(lambda n: isinstance(n, AabbNode)) if wm.root_node else None
    if found is not aabb:
        print("  FAIL test_from_aabb_node_is_wok: aabb not found")
        return False
    print("  PASS test_from_aabb_node_is_wok")
    return True


def test_from_root_object_rejects_mdl_root() -> bool:
    root = bpy.data.objects.new("mdlroot", None)
    root.kb.dummytype = DummyType.MDLROOT
    bpy.context.collection.objects.link(root)
    try:
        try:
            Walkmesh.from_root_object(root, ExportOptions())
        except ValueError:
            print("  PASS test_from_root_object_rejects_mdl_root")
            return True
        print("  FAIL test_from_root_object_rejects_mdl_root: expected ValueError")
        return False
    finally:
        bpy.data.objects.remove(root, do_unlink=True)


def run_tests() -> bool:
    print("\n=== test_scene_walkmesh.py ===")
    results = [test_from_aabb_node_is_wok(), test_from_root_object_rejects_mdl_root()]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
