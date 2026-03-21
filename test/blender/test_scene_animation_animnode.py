"""
test_scene_animation_animnode.py – Animation / AnimationNode invariants

Run with:
    blender --background --python test/blender/test_scene_animation_animnode.py
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

from io_scene_kotor.constants import Classification, DummyType, NULL, NodeType  # noqa: E402
from io_scene_kotor.scene.animation import Animation  # noqa: E402
from io_scene_kotor.scene.animnode import (  # noqa: E402
    AnimationNode,
    convert_bl_location_to_mdl_position,
    convert_mdl_position_to_bl_location,
)


def _make_mdl_root(name: str = "mdlroot") -> bpy.types.Object:
    root = bpy.data.objects.new(name, None)
    root.kb.dummytype = DummyType.MDLROOT
    root.kb.classification = Classification.OTHER
    root.kb.animscale = 1.0
    root.kb.node_number = 1
    root.kb.export_order = 0
    root.rotation_mode = "QUATERNION"
    bpy.context.collection.objects.link(root)
    return root


def test_animation_default_fields() -> bool:
    a = Animation("testanim")
    if a.name != "testanim" or a.root_node is not None:
        print("  FAIL test_animation_default_fields")
        return False
    if a.animroot != NULL or a.length != 1.0:
        print("  FAIL test_animation_default_fields: defaults")
        return False
    print("  PASS test_animation_default_fields")
    return True


def test_animation_append_to_object() -> bool:
    """get_next_frame() uses max(anim_list.frame_end); seed one row so first append works."""
    root = _make_mdl_root("anim_root")
    try:
        kb = getattr(root, "kb", None)
        if kb is None:
            print("  FAIL test_animation_append_to_object: no kb")
            return False
        seed = kb.anim_list.add()
        seed.name = "__seed"
        seed.frame_start = 0
        seed.frame_end = 0
        before = len(kb.anim_list)
        anim = Animation.append_to_object(root, "walk", 2.0, 0.5, root.name)
        after = len(kb.anim_list)
        if after != before + 1:
            print("  FAIL test_animation_append_to_object: list length")
            return False
        if anim.name != "walk" or abs(anim.transtime - 0.5) > 1e-6:
            print("  FAIL test_animation_append_to_object: props")
            return False
    finally:
        bpy.data.objects.remove(root, do_unlink=True)
    print("  PASS test_animation_append_to_object")
    return True


def test_animation_node_defaults_and_children() -> bool:
    root = AnimationNode("root")
    child = AnimationNode("child")
    child.parent = root
    root.children.append(child)
    if root.nodetype != NodeType.DUMMY or root.node_number != -1:
        print("  FAIL test_animation_node_defaults_and_children: root defaults")
        return False
    if child.parent is not root or len(root.children) != 1:
        print("  FAIL test_animation_node_defaults_and_children: links")
        return False
    print("  PASS test_animation_node_defaults_and_children")
    return True


def test_convert_mdl_position_respects_animscale() -> bool:
    rest = (0.0, 0.0, 0.0)
    mdl = [1.0, 0.0, 0.0]
    bl = convert_mdl_position_to_bl_location(mdl, rest, animscale=3.0)
    if len(bl) != 3 or any(abs(bl[i] - [3.0, 0.0, 0.0][i]) > 1e-5 for i in range(3)):
        print(f"  FAIL test_convert_mdl_position_respects_animscale: {bl}")
        return False
    print("  PASS test_convert_mdl_position_respects_animscale")
    return True


def test_convert_mdl_position_roundtrip_linear() -> bool:
    """bl→mdl path does not apply animscale; roundtrip only holds for animscale=1."""
    rest = (1.0, 2.0, 3.0)
    mdl = [0.5, -0.25, 1.0]
    bl = convert_mdl_position_to_bl_location(mdl, rest, animscale=1.0)
    if len(bl) != 3:
        print("  FAIL test_convert_mdl_position_roundtrip_linear: len")
        return False
    back = convert_bl_location_to_mdl_position(bl, rest)
    if any(abs(back[i] - mdl[i]) > 1e-5 for i in range(3)):
        print(f"  FAIL test_convert_mdl_position_roundtrip_linear: {back} != {mdl}")
        return False
    print("  PASS test_convert_mdl_position_roundtrip_linear")
    return True


def run_tests() -> bool:
    print("\n=== test_scene_animation_animnode.py ===")
    results = [
        test_animation_default_fields(),
        test_animation_append_to_object(),
        test_animation_node_defaults_and_children(),
        test_convert_mdl_position_respects_animscale(),
        test_convert_mdl_position_roundtrip_linear(),
    ]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
