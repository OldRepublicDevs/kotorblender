"""
test_ops_armature_keyframes_smoke.py – kb.armature_apply_keyframes / unapply execute paths

Run with:
    blender --background --python test/blender/test_ops_armature_keyframes_smoke.py
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

from io_scene_kotor.constants import Classification, DummyType, MeshType  # noqa: E402

import io_scene_kotor.ops.armatureapplykeyframes as _kb_apply  # noqa: F401, E402
import io_scene_kotor.ops.armatureunapplykeyframes as _kb_unapply  # noqa: F401, E402


def _clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)


def _armature_with_bone(arm_name: str, bone_name: str) -> bpy.types.Object:
    data = bpy.data.armatures.new(arm_name)
    obj = bpy.data.objects.new(arm_name, data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    eb = data.edit_bones.new(bone_name)
    eb.head = (0.0, 0.0, 0.0)
    eb.tail = (0.0, 0.0, 0.05)
    bpy.ops.object.mode_set(mode="OBJECT")
    return obj


def _character_with_skin_and_bone_anim(bone_name: str = "b1") -> None:
    arm_obj = _armature_with_bone("ArmatureKeyframes", bone_name)

    root = bpy.data.objects.new("char_kf", None)
    root.kb.dummytype = DummyType.MDLROOT
    root.kb.classification = Classification.CHARACTER
    root.kb.animscale = 1.0
    root.kb.node_number = 1
    root.kb.export_order = 0
    root.rotation_mode = "QUATERNION"
    bpy.context.collection.objects.link(root)

    bone_obj = bpy.data.objects.new(bone_name, None)
    bone_obj.parent = root
    bone_obj.rotation_mode = "QUATERNION"
    bone_obj.kb.dummytype = DummyType.NONE
    bone_obj.kb.node_number = 2
    bone_obj.kb.export_order = 1
    bpy.context.collection.objects.link(bone_obj)

    bone_obj.animation_data_create()
    bone_obj.animation_data.action = bpy.data.actions.new("bone_obj_action")
    bone_obj.location = (0.0, 0.0, 0.0)
    bone_obj.keyframe_insert(data_path="location", frame=1)
    bone_obj.location = (0.1, 0.0, 0.0)
    bone_obj.keyframe_insert(data_path="location", frame=5)

    mesh_data = bpy.data.meshes.new("skin_kf")
    mesh_data.from_pydata([(0, 0, 0), (0.1, 0, 0), (0, 0.1, 0)], [], [(0, 1, 2)])
    mesh_data.update()
    skin = bpy.data.objects.new("skin_kf", mesh_data)
    skin.parent = root
    skin.rotation_mode = "QUATERNION"
    skin.kb.meshtype = MeshType.SKIN
    skin.kb.node_number = 3
    skin.kb.export_order = 2
    if "UVMap" not in mesh_data.uv_layers:
        mesh_data.uv_layers.new(name="UVMap")
    vg = skin.vertex_groups.new(name=bone_name)
    vg.add([0, 1, 2], 1.0, "REPLACE")
    mod = skin.modifiers.new(name="Armature", type="ARMATURE")
    mod.object = arm_obj
    bpy.context.collection.objects.link(skin)


def test_armature_apply_and_unapply_keyframes() -> bool:
    _clear_scene()
    _character_with_skin_and_bone_anim("b1")
    root = bpy.data.objects["char_kf"]
    arm = bpy.data.objects["ArmatureKeyframes"]

    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = root
    root.select_set(True)
    bpy.context.scene.frame_set(0)
    try:
        bpy.ops.object.mode_set(mode="OBJECT")
    except Exception:
        pass

    if not bpy.ops.kb.armature_apply_keyframes.poll():
        print("  FAIL armature_apply_keyframes poll() is False")
        _clear_scene()
        return False
    r1 = bpy.ops.kb.armature_apply_keyframes()
    if r1 != {"FINISHED"}:
        print(f"  FAIL armature_apply_keyframes returned {r1!r}")
        _clear_scene()
        return False
    if arm.animation_data is None or arm.animation_data.action is None:
        print("  FAIL armature has no action after apply")
        _clear_scene()
        return False

    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.objects.active = root
    root.select_set(True)
    if not bpy.ops.kb.armature_unapply_keyframes.poll():
        print("  FAIL armature_unapply_keyframes poll() is False")
        _clear_scene()
        return False
    r2 = bpy.ops.kb.armature_unapply_keyframes()
    ok = r2 == {"FINISHED"}
    _clear_scene()
    if ok:
        print("  PASS test_armature_apply_and_unapply_keyframes")
    else:
        print(f"  FAIL armature_unapply_keyframes returned {r2!r}")
    return ok


def run_tests() -> bool:
    print("\n=== test_ops_armature_keyframes_smoke.py ===")
    ok = test_armature_apply_and_unapply_keyframes()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_ops_armature_keyframes_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
