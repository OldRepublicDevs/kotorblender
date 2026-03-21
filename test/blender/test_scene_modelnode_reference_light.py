"""
test_scene_modelnode_reference_light.py – ReferenceNode / LightNode / FlareList

Run with:
    blender --background --python test/blender/test_scene_modelnode_reference_light.py
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
if MODULE not in bpy.context.preferences.addons:  # pyright: ignore[reportOptionalMemberAccess]
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.constants import DummyType, ImportOptions, NodeType, NULL  # noqa: E402
from io_scene_kotor.scene.modelnode.light import FlareList, LightNode  # noqa: E402
from io_scene_kotor.scene.modelnode.reference import ReferenceNode  # noqa: E402


def test_reference_node_defaults() -> bool:
    n = ReferenceNode("ref1")
    if n.refmodel != NULL or n.reattachable != 0:
        print("  FAIL test_reference_node_defaults")
        return False
    if n.nodetype != NodeType.REFERENCE or n.dummytype != DummyType.REFERENCE:
        print("  FAIL test_reference_node_defaults: types")
        return False
    print("  PASS test_reference_node_defaults")
    return True


def test_reference_set_object_data() -> bool:
    obj = bpy.data.objects.new("ref_obj", None)
    bpy.context.collection.objects.link(obj)
    try:
        n = ReferenceNode("ref1")
        n.refmodel = "mymodel"
        n.reattachable = 1
        opts = ImportOptions()
        n.set_object_data(obj, opts)
        kb = getattr(obj, "kb", None)
        if kb is None:
            print("  FAIL test_reference_set_object_data: kb")
            return False
        if kb.dummytype != DummyType.REFERENCE or kb.refmodel != "mymodel" or not kb.reattachable:
            print("  FAIL test_reference_set_object_data: kb fields")
            return False
    finally:
        bpy.data.objects.remove(obj, do_unlink=True)
    print("  PASS test_reference_set_object_data")
    return True


def test_light_node_defaults() -> bool:
    ln = LightNode("lgt")
    if ln.nodetype != NodeType.LIGHT:
        print("  FAIL test_light_node_defaults: nodetype")
        return False
    if ln.radius != 5.0 or not ln.shadow:
        print("  FAIL test_light_node_defaults: light fields")
        return False
    if not isinstance(ln.flare_list, FlareList):
        print("  FAIL test_light_node_defaults: flare_list")
        return False
    print("  PASS test_light_node_defaults")
    return True


def test_flare_list_lists() -> bool:
    fl = FlareList()
    fl.textures.append("tex0")
    fl.sizes.append(1.5)
    fl.positions.append(0.25)
    fl.colorshifts.append((0.1, 0.2, 0.3))
    ok = len(fl.textures) == 1 and len(fl.sizes) == len(fl.positions) == len(fl.colorshifts)
    print(f"  {'PASS' if ok else 'FAIL'} test_flare_list_lists")
    return ok


def run_tests() -> bool:
    print("\n=== test_scene_modelnode_reference_light.py ===")
    results = [
        test_reference_node_defaults(),
        test_reference_set_object_data(),
        test_light_node_defaults(),
        test_flare_list_lists(),
    ]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
