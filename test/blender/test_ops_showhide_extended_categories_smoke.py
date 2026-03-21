"""
test_ops_showhide_extended_categories_smoke.py – classification + unlightmapped + char dummies/bones

Covers kb.hide/show pairs not exercised by test_ops_showhide_smoke.py:
unlightmapped meshes, character MDL trees (bones, dummies, hide_characters),
placeables vs doors, and current hide_items global behavior.

Run with:
    blender --background --python test/blender/test_ops_showhide_extended_categories_smoke.py
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

import io_scene_kotor.ops.showhideobjects as _kb_showhide  # noqa: F401, E402
from io_scene_kotor.constants import Classification, DummyType, MeshType, NULL  # noqa: E402


def _clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)


def _link(obj: bpy.types.Object) -> None:
    bpy.context.collection.objects.link(obj)


def _mdl_root(name: str, classification: Classification) -> bpy.types.Object:
    root = bpy.data.objects.new(name, None)
    root.kb.dummytype = DummyType.MDLROOT
    root.kb.classification = classification
    root.kb.animscale = 1.0
    root.kb.node_number = 1
    root.kb.export_order = 0
    root.rotation_mode = "QUATERNION"
    _link(root)
    return root


def _trimesh_child(name: str, parent: bpy.types.Object, *, render: int = 1) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.parent = parent
    obj.rotation_mode = "QUATERNION"
    obj.kb.meshtype = MeshType.TRIMESH
    obj.kb.node_number = 2
    obj.kb.export_order = 1
    obj.kb.render = render
    obj.kb.bitmap = NULL
    obj.kb.bitmap2 = NULL
    if "UVMap" not in mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    mesh.materials.append(bpy.data.materials.new(name=f"{name}_mat"))
    _link(obj)
    return obj


def _dummy_child(name: str, parent: bpy.types.Object) -> bpy.types.Object:
    emp = bpy.data.objects.new(name, None)
    emp.parent = parent
    emp.kb.dummytype = DummyType.NONE
    emp.kb.node_number = 3
    emp.kb.export_order = 2
    _link(emp)
    return emp


def test_hide_show_unlightmapped_selective() -> bool:
    _clear_scene()
    ok_mesh = bpy.data.meshes.new("lm_ok_mesh")
    ok_mesh.from_pydata([(0, 0, 0)], [], [])
    ok_mesh.update()
    ok_obj = bpy.data.objects.new("lm_ok", ok_mesh)
    ok_obj.kb.lightmapped = True
    ok_obj.kb.bitmap2 = "lightmap0"
    _link(ok_obj)

    bad_mesh = bpy.data.meshes.new("lm_bad_mesh")
    bad_mesh.from_pydata([(1, 0, 0)], [], [])
    bad_mesh.update()
    bad_obj = bpy.data.objects.new("lm_bad", bad_mesh)
    bad_obj.kb.lightmapped = False
    _link(bad_obj)

    ok_obj.hide_viewport = False
    bad_obj.hide_viewport = False
    try:
        r1 = bpy.ops.kb.hide_unlightmapped()
        if r1 != {"FINISHED"} or not bad_obj.hide_viewport or ok_obj.hide_viewport:
            print(f"  FAIL hide_unlightmapped ok_vp={ok_obj.hide_viewport} bad_vp={bad_obj.hide_viewport}")
            return False
        r2 = bpy.ops.kb.show_unlightmapped()
        if r2 != {"FINISHED"} or bad_obj.hide_viewport:
            print(f"  FAIL show_unlightmapped bad_vp={bad_obj.hide_viewport}")
            return False
        print("  PASS test_hide_show_unlightmapped_selective")
        return True
    finally:
        _clear_scene()


def test_hide_show_char_bones() -> bool:
    _clear_scene()
    root = _mdl_root("char_root", Classification.CHARACTER)
    bone = _trimesh_child("char_bone", root, render=0)
    bone.hide_viewport = False
    try:
        r1 = bpy.ops.kb.hide_char_bones()
        if r1 != {"FINISHED"} or not bone.hide_viewport:
            print("  FAIL hide_char_bones")
            return False
        r2 = bpy.ops.kb.show_char_bones()
        ok = r2 == {"FINISHED"} and not bone.hide_viewport
        print(f"  {'PASS' if ok else 'FAIL'} test_hide_show_char_bones")
        return ok
    finally:
        _clear_scene()


def test_hide_show_char_dummies() -> bool:
    _clear_scene()
    root = _mdl_root("char_root2", Classification.CHARACTER)
    dum = _dummy_child("char_dummy", root)
    dum.hide_viewport = False
    try:
        r1 = bpy.ops.kb.hide_char_dummies()
        if r1 != {"FINISHED"} or not dum.hide_viewport:
            print("  FAIL hide_char_dummies")
            return False
        r2 = bpy.ops.kb.show_char_dummies()
        ok = r2 == {"FINISHED"} and not dum.hide_viewport
        print(f"  {'PASS' if ok else 'FAIL'} test_hide_show_char_dummies")
        return ok
    finally:
        _clear_scene()


def test_hide_show_characters_subtree() -> bool:
    _clear_scene()
    root = _mdl_root("char_root3", Classification.CHARACTER)
    mesh = _trimesh_child("char_mesh", root, render=1)
    mesh.kb.bitmap = "tex0"
    root.hide_viewport = False
    mesh.hide_viewport = False
    try:
        r1 = bpy.ops.kb.hide_characters()
        if r1 != {"FINISHED"} or not root.hide_viewport or not mesh.hide_viewport:
            print("  FAIL hide_characters")
            return False
        r2 = bpy.ops.kb.show_characters()
        ok = r2 == {"FINISHED"} and not root.hide_viewport and not mesh.hide_viewport
        print(f"  {'PASS' if ok else 'FAIL'} test_hide_show_characters_subtree")
        return ok
    finally:
        _clear_scene()


def test_hide_placeables_vs_doors() -> bool:
    _clear_scene()
    utp = _mdl_root("utp_root", Classification.PLACEABLE)
    utp_mesh = _trimesh_child("utp_tri", utp, render=1)
    utp_mesh.kb.bitmap = "a"

    utd = _mdl_root("utd_root", Classification.DOOR)
    utd_mesh = _trimesh_child("utd_tri", utd, render=1)
    utd_mesh.kb.bitmap = "b"

    for o in (utp, utp_mesh, utd, utd_mesh):
        o.hide_viewport = False
        o.hide_render = False

    try:
        r1 = bpy.ops.kb.hide_placeables()
        if r1 != {"FINISHED"} or utp.hide_viewport is False or utp_mesh.hide_viewport is False:
            print("  FAIL hide_placeables did not hide UTP subtree")
            return False
        if utd.hide_viewport or utd_mesh.hide_viewport:
            print("  FAIL hide_placeables hid door subtree")
            return False

        bpy.ops.kb.show_placeables()
        r2 = bpy.ops.kb.hide_doors()
        if r2 != {"FINISHED"} or utd.hide_viewport is False or utd_mesh.hide_viewport is False:
            print("  FAIL hide_doors")
            return False
        if utp.hide_viewport or utp_mesh.hide_viewport:
            print("  FAIL hide_doors hid placeable subtree")
            return False

        print("  PASS test_hide_placeables_vs_doors")
        return True
    finally:
        _clear_scene()


def test_hide_items_currently_hides_all_scene_objects() -> bool:
    """Documents behavior until resource binding filters UTI objects."""
    _clear_scene()
    m1 = bpy.data.meshes.new("item_m1")
    m1.from_pydata([(0, 0, 0)], [], [])
    m1.update()
    o1 = bpy.data.objects.new("plain_a", m1)
    m2 = bpy.data.meshes.new("item_m2")
    m2.from_pydata([(2, 0, 0)], [], [])
    m2.update()
    o2 = bpy.data.objects.new("plain_b", m2)
    _link(o1)
    _link(o2)
    try:
        r1 = bpy.ops.kb.hide_items()
        if r1 != {"FINISHED"} or not o1.hide_viewport or not o2.hide_viewport:
            print("  FAIL hide_items expected both meshes hidden")
            return False
        r2 = bpy.ops.kb.show_items()
        ok = r2 == {"FINISHED"} and not o1.hide_viewport and not o2.hide_viewport
        print(f"  {'PASS' if ok else 'FAIL'} test_hide_items_currently_hides_all_scene_objects")
        return ok
    finally:
        _clear_scene()


def run_tests() -> bool:
    print("\n=== test_ops_showhide_extended_categories_smoke.py ===")
    results = [
        test_hide_show_unlightmapped_selective(),
        test_hide_show_char_bones(),
        test_hide_show_char_dummies(),
        test_hide_show_characters_subtree(),
        test_hide_placeables_vs_doors(),
        test_hide_items_currently_hides_all_scene_objects(),
    ]
    passed, total = sum(results), len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_ops_showhide_extended_categories_smoke.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
