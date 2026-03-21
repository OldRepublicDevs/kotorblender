"""
test_ops_rebuild_armature_smoke.py – kb.rebuild_armature operator success path

Run with:
    blender --background --python test/blender/test_ops_rebuild_armature_smoke.py
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
import io_scene_kotor.ops.rebuildarmature as _kb_rebuildarmature  # noqa: F401, E402


def _clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)


def test_ops_rebuild_armature_character_with_skin() -> bool:
    _clear_scene()
    root = bpy.data.objects.new("char_root", None)
    root.kb.dummytype = DummyType.MDLROOT
    root.kb.classification = Classification.CHARACTER
    bpy.context.collection.objects.link(root)

    mesh_data = bpy.data.meshes.new("skin_mesh")
    mesh_data.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    mesh_data.update()
    skin = bpy.data.objects.new("skin", mesh_data)
    skin.kb.meshtype = MeshType.SKIN
    skin.parent = root
    bpy.context.collection.objects.link(skin)

    bpy.context.view_layer.objects.active = root
    root.select_set(True)
    skin.select_set(False)

    try:
        bpy.ops.object.mode_set(mode="OBJECT")
    except Exception:
        pass

    if not bpy.ops.kb.rebuild_armature.poll():
        print("  FAIL test_ops_rebuild_armature_character_with_skin: poll() is False")
        _clear_scene()
        return False

    result = bpy.ops.kb.rebuild_armature()
    arm_name = "Armature_" + root.name
    arm_obj = bpy.data.objects.get(arm_name)
    ok = result == {"FINISHED"} and arm_obj is not None and arm_obj.type == "ARMATURE"
    _clear_scene()
    if ok:
        print("  PASS test_ops_rebuild_armature_character_with_skin")
    else:
        print(f"  FAIL result={result!r} arm={arm_obj!r}")
    return ok


def run_tests() -> bool:
    print("\n=== test_ops_rebuild_armature_smoke.py ===")
    ok = test_ops_rebuild_armature_character_with_skin()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_ops_rebuild_armature_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
