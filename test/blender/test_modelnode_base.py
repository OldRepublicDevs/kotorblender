"""
test_modelnode_base.py – Blender background-mode test

Tests BaseNode: find_node (tree traversal), set_object_data, and load_object_data
using real bpy objects and addon kb. No mocks or monkey patching.

Run with:
    blender --background --python test/blender/test_modelnode_base.py
"""

import os
import sys

import bpy

from mathutils import Quaternion

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

MODULE = "bl_ext.user_default.io_scene_kotor"
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.constants import ImportOptions
from io_scene_kotor.scene.modelnode.base import BaseNode


def _clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def test_find_node():
    """find_node returns matching node in tree; None when no match."""
    root = BaseNode("root")
    root.node_number = 1
    c1 = BaseNode("c1")
    c1.node_number = 2
    c2 = BaseNode("c2")
    c2.node_number = 3
    root.children = [c1, c2]
    c1.parent = root
    c2.parent = root
    c1a = BaseNode("c1a")
    c1a.node_number = 4
    c1.children = [c1a]
    c1a.parent = c1

    by_name = root.find_node(lambda n: n.name == "c1a")
    ok = by_name is c1a
    by_num = root.find_node(lambda n: n.node_number == 3)
    ok = ok and by_num is c2
    none = root.find_node(lambda n: n.node_number == 99)
    ok = ok and none is None
    self_match = root.find_node(lambda n: n.name == "root")
    ok = ok and self_match is root
    if ok:
        print("  PASS test_find_node")
    else:
        print("  FAIL test_find_node")
    return ok


def test_set_object_data():
    """set_object_data writes node position, quaternion, scale, node_number, export_order to obj."""
    _clear_scene()
    col = bpy.context.scene.collection
    obj = bpy.data.objects.new("T", None)
    col.objects.link(obj)

    node = BaseNode("T")
    node.position = (1.0, 2.0, 3.0)
    node.orientation = (0.0, 0.0, 0.0, 1.0)
    node.scale = 2.0
    node.node_number = 5
    node.export_order = 4

    opts = ImportOptions()
    node.set_object_data(obj, opts)

    ok = (
        list(obj.location) == [1.0, 2.0, 3.0]
        and obj.rotation_mode == "QUATERNION"
        and abs(obj.scale[0] - 2.0) < 1e-6
        and obj.kb.node_number == 5
        and obj.kb.export_order == 4
    )
    if ok:
        print("  PASS test_set_object_data")
    else:
        print(
            f"  FAIL test_set_object_data: loc={list(obj.location)}, scale={list(obj.scale)}, kb.node_number={obj.kb.node_number}"
        )
    return ok


def test_load_object_data():
    """load_object_data reads from obj and eval_obj into node; from_root updated."""
    _clear_scene()
    col = bpy.context.scene.collection
    obj = bpy.data.objects.new("O", None)
    col.objects.link(obj)
    obj.kb.node_number = 10
    obj.kb.export_order = 9

    eval_obj = bpy.data.objects.new("E", None)
    col.objects.link(eval_obj)
    eval_obj.location = (5.0, 6.0, 7.0)
    eval_obj.rotation_mode = "QUATERNION"
    eval_obj.rotation_quaternion = Quaternion((0.0, 1.0, 0.0, 0.0))
    eval_obj.scale = (3.0, 3.0, 3.0)

    node = BaseNode("O")
    opts = ImportOptions()
    node.load_object_data(obj, eval_obj, opts)

    ok = (
        list(node.position) == [5.0, 6.0, 7.0]
        and node.scale == 3.0
        and node.node_number == 10
        and node.export_order == 9
    )
    if ok:
        print("  PASS test_load_object_data")
    else:
        print(f"  FAIL test_load_object_data: position={node.position}, scale={node.scale}")
    return ok


def test_load_object_data_raises_when_not_quaternion():
    """load_object_data raises RuntimeError when eval_obj rotation_mode is not QUATERNION."""
    _clear_scene()
    col = bpy.context.scene.collection
    obj = bpy.data.objects.new("O2", None)
    col.objects.link(obj)
    obj.kb.node_number = 1
    obj.kb.export_order = 0
    eval_obj = bpy.data.objects.new("E2", None)
    col.objects.link(eval_obj)
    eval_obj.rotation_mode = "XYZ"

    node = BaseNode("O2")
    opts = ImportOptions()
    try:
        node.load_object_data(obj, eval_obj, opts)
        ok = False
    except RuntimeError as e:
        ok = "Quaternion" in str(e)
    if ok:
        print("  PASS test_load_object_data_raises_when_not_quaternion")
    else:
        print("  FAIL test_load_object_data_raises_when_not_quaternion")
    return ok


def run_tests():
    print("\n=== test_modelnode_base.py ===")
    tests = [
        test_find_node,
        test_set_object_data,
        test_load_object_data,
        test_load_object_data_raises_when_not_quaternion,
    ]
    results = [t() for t in tests]
    passed = sum(results)
    total = len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_modelnode_base.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
