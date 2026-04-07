"""
test_utils.py – Blender background-mode test

Tests utils.py: pure functions (is_null, is_close*, time_to_frame, color_to_hex,
semicolon_separated_to_absolute_paths) and Blender-dependent helpers
(find_mdl_root_of, is_exported_to_mdl, find_object, find_objects) using real
bpy objects. No mocks or monkey patching.

Run with:
    blender --background --python test/blender/test_utils.py
"""

import os
import sys

import bpy

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

from io_scene_kotor.constants import DummyType
from io_scene_kotor.utils import (
    color_to_hex,
    find_mdl_root_of,
    find_object,
    find_objects,
    float_to_byte,
    frame_to_time,
    int_to_hex,
    is_close,
    is_close_2,
    is_close_3,
    is_exported_to_mdl,
    is_not_null,
    is_null,
    semicolon_separated_to_absolute_paths,
    time_to_frame,
)

# ---------------------------------------------------------------------------
# Pure function tests (no bpy)
# ---------------------------------------------------------------------------


def test_is_null():
    """is_null: empty, NULL, null, non-null, None."""
    ok = is_null("") and is_null("NULL") and is_null("null") and not is_null("x") and is_null(None)
    if ok:
        print("  PASS test_is_null")
    else:
        print("  FAIL test_is_null")
    return ok


def test_is_not_null():
    """is_not_null is inverse of is_null."""
    ok = is_not_null("x") and not is_not_null("") and not is_not_null("NULL")
    if ok:
        print("  PASS test_is_not_null")
    else:
        print("  FAIL test_is_not_null")
    return ok


def test_is_close():
    """is_close: equal, within epsilon, just outside epsilon; negative and zero."""
    ok = (
        is_close(1.0, 1.0)
        and is_close(1.0, 1.0 + 1e-5, 1e-4)
        and not is_close(1.0, 1.0 + 1e-3, 1e-4)
        and is_close(-2.0, -2.0)
        and is_close(0.0, 0.0)
    )
    if ok:
        print("  PASS test_is_close")
    else:
        print("  FAIL test_is_close")
    return ok


def test_is_close_2():
    """is_close_2 for 2-tuples."""
    ok = is_close_2((1.0, 2.0), (1.0, 2.0)) and not is_close_2((1.0, 2.0), (1.0, 3.0))
    if ok:
        print("  PASS test_is_close_2")
    else:
        print("  FAIL test_is_close_2")
    return ok


def test_is_close_3():
    """is_close_3 for 3-tuples."""
    ok = is_close_3((0, 0, 0), (0, 0, 0)) and not is_close_3((1, 1, 1), (1, 1, 2))
    if ok:
        print("  PASS test_is_close_3")
    else:
        print("  FAIL test_is_close_3")
    return ok


def test_time_to_frame():
    """time_to_frame uses ANIM_FPS (30); 0 and positive."""
    ok = time_to_frame(0) == 0 and time_to_frame(1.0) == 30 and time_to_frame(0.5) == 15
    if ok:
        print("  PASS test_time_to_frame")
    else:
        print("  FAIL test_time_to_frame")
    return ok


def test_frame_to_time():
    """frame_to_time and inverse of time_to_frame."""
    t = 1.5
    f = time_to_frame(t)
    back = frame_to_time(f)
    ok = abs(back - t) < 1e-6 and frame_to_time(0) == 0.0
    if ok:
        print("  PASS test_frame_to_time")
    else:
        print(f"  FAIL test_frame_to_time: t={t}, f={f}, back={back}")
    return ok


def test_float_to_byte_int_to_hex():
    """float_to_byte and int_to_hex edge values."""
    ok = (
        float_to_byte(0.0) == 0
        and float_to_byte(1.0) == 255
        and int_to_hex(0) == "00"
        and int_to_hex(255) == "FF"
    )
    if ok:
        print("  PASS test_float_to_byte_int_to_hex")
    else:
        print("  FAIL test_float_to_byte_int_to_hex")
    return ok


def test_color_to_hex():
    """color_to_hex (1,0,0) -> FF0000."""
    ok = color_to_hex((1.0, 0.0, 0.0)) == "FF0000" and color_to_hex((0, 0, 0)) == "000000"
    if ok:
        print("  PASS test_color_to_hex")
    else:
        print("  FAIL test_color_to_hex")
    return ok


def test_semicolon_separated_to_absolute_paths():
    """semicolon_separated_to_absolute_paths: empty yields working_dir only (normpath); one relative yields [wd, wd/a]."""
    wd = os.path.abspath(os.path.normpath(os.path.join("some", "dir")))
    empty = semicolon_separated_to_absolute_paths("", wd)
    wd_n = os.path.normpath(wd)
    # On Windows join(wd,'') can add trailing sep, so result may be [wd] or [wd, wd+sep]; normpath collapses
    empty_n = [os.path.normpath(p) for p in empty]
    ok = set(empty_n) == {wd_n} and len(empty_n) >= 1
    rel = semicolon_separated_to_absolute_paths("a", wd)
    expected_rel_n = os.path.normpath(os.path.join(wd, "a"))
    rel_n = [os.path.normpath(p) for p in rel]
    ok = ok and len(rel_n) >= 2 and wd_n in rel_n and expected_rel_n in rel_n
    if ok:
        print("  PASS test_semicolon_separated_to_absolute_paths")
    else:
        print("  FAIL test_semicolon_separated_to_absolute_paths")
    return ok


# ---------------------------------------------------------------------------
# Blender-dependent tests (real bpy objects)
# ---------------------------------------------------------------------------


def _clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def test_find_mdl_root_of():
    """find_mdl_root_of: root returns self, child/grandchild return root, no parent returns None."""
    _clear_scene()
    root = bpy.data.objects.new("Root", None)
    root.kb.dummytype = DummyType.MDLROOT
    bpy.context.scene.collection.objects.link(root)
    child = bpy.data.objects.new("Child", None)
    child.kb.dummytype = DummyType.NONE
    child.parent = root
    bpy.context.scene.collection.objects.link(child)
    grandchild = bpy.data.objects.new("Grandchild", None)
    grandchild.parent = child
    bpy.context.scene.collection.objects.link(grandchild)
    orphan = bpy.data.objects.new("Orphan", None)
    bpy.context.scene.collection.objects.link(orphan)

    ok = (
        find_mdl_root_of(root) is root
        and find_mdl_root_of(child) is root
        and find_mdl_root_of(grandchild) is root
        and find_mdl_root_of(orphan) is None
    )
    if ok:
        print("  PASS test_find_mdl_root_of")
    else:
        print("  FAIL test_find_mdl_root_of")
    return ok


def test_is_exported_to_mdl():
    """is_exported_to_mdl: MESH/LIGHT True; EMPTY NONE/MDLROOT/REFERENCE True, others False."""
    _clear_scene()
    mesh = bpy.data.meshes.new("M")
    mesh_obj = bpy.data.objects.new("MeshObj", mesh)
    bpy.context.scene.collection.objects.link(mesh_obj)
    light_data = bpy.data.lights.new("L", "POINT")
    light_obj = bpy.data.objects.new("LightObj", light_data)
    bpy.context.scene.collection.objects.link(light_obj)
    root = bpy.data.objects.new("Root", None)
    root.kb.dummytype = DummyType.MDLROOT
    bpy.context.scene.collection.objects.link(root)
    ref = bpy.data.objects.new("Ref", None)
    ref.kb.dummytype = DummyType.REFERENCE
    bpy.context.scene.collection.objects.link(ref)
    pt = bpy.data.objects.new("Pt", None)
    pt.kb.dummytype = DummyType.PATHPOINT
    bpy.context.scene.collection.objects.link(pt)

    ok = (
        is_exported_to_mdl(mesh_obj)
        and is_exported_to_mdl(light_obj)
        and is_exported_to_mdl(root)
        and is_exported_to_mdl(ref)
        and not is_exported_to_mdl(pt)
        and not is_exported_to_mdl(None)
    )
    if ok:
        print("  PASS test_is_exported_to_mdl")
    else:
        print("  FAIL test_is_exported_to_mdl")
    return ok


def test_find_object_find_objects():
    """find_object and find_objects with predicate."""
    _clear_scene()
    root = bpy.data.objects.new("R", None)
    bpy.context.scene.collection.objects.link(root)
    a = bpy.data.objects.new("A", None)
    a.parent = root
    bpy.context.scene.collection.objects.link(a)
    b = bpy.data.objects.new("B", None)
    b.parent = root
    bpy.context.scene.collection.objects.link(b)

    single = find_object(root, lambda o: o.name == "A")
    ok = single is a
    multi = find_objects(root, lambda o: o.name in ("A", "B"))
    ok = ok and len(multi) == 2 and set(o.name for o in multi) == {"A", "B"}
    none = find_object(root, lambda o: o.name == "Z")
    ok = ok and none is None
    if ok:
        print("  PASS test_find_object_find_objects")
    else:
        print("  FAIL test_find_object_find_objects")
    return ok


def run_tests():
    print("\n=== test_utils.py ===")
    tests = [
        test_is_null,
        test_is_not_null,
        test_is_close,
        test_is_close_2,
        test_is_close_3,
        test_time_to_frame,
        test_frame_to_time,
        test_float_to_byte_int_to_hex,
        test_color_to_hex,
        test_semicolon_separated_to_absolute_paths,
        test_find_mdl_root_of,
        test_is_exported_to_mdl,
        test_find_object_find_objects,
    ]
    results = [t() for t in tests]
    passed = sum(results)
    total = len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_utils.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
