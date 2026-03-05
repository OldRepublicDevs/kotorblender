"""
test_constants.py – Blender background-mode test

Tests the constants module: enumerations, walkmesh material table,
and utility functions from utils.py.  No game assets required.

Run with:
    blender --background --python test/blender/test_constants.py
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

from io_scene_kotor.constants import (
    ANIM_FPS,
    ANIM_PADDING,
    ANIM_REST_POSE_OFFSET,
    UV_MAP_MAIN,
    UV_MAP_LIGHTMAP,
    WALKMESH_MATERIALS,
    NAME_TO_WALKMESH_MATERIAL,
    NON_WALKABLE,
    Classification,
    DummyType,
    ExportOptions,
    ImportOptions,
    MeshType,
    NodeType,
)
from io_scene_kotor.utils import (
    is_dummy_type,
    is_mdl_root,
    is_path_point,
)

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_animation_constants():
    """Animation constants have expected values."""
    ok = ANIM_FPS == 30 and ANIM_REST_POSE_OFFSET == 5 and ANIM_PADDING == 60
    if ok:
        print(f"  PASS test_animation_constants (FPS={ANIM_FPS}, padding={ANIM_PADDING})")
    else:
        print(f"  FAIL test_animation_constants: FPS={ANIM_FPS}, rest={ANIM_REST_POSE_OFFSET}, pad={ANIM_PADDING}")
    return ok


def test_uv_map_names():
    """UV map name constants are correct strings."""
    ok = UV_MAP_MAIN == "UVMap" and UV_MAP_LIGHTMAP == "UVMap_lm"
    if ok:
        print("  PASS test_uv_map_names")
    else:
        print(f"  FAIL test_uv_map_names: main={UV_MAP_MAIN!r}, lm={UV_MAP_LIGHTMAP!r}")
    return ok


def test_walkmesh_materials_count():
    """WALKMESH_MATERIALS has exactly 23 entries."""
    ok = len(WALKMESH_MATERIALS) == 23
    if ok:
        print(f"  PASS test_walkmesh_materials_count ({len(WALKMESH_MATERIALS)} materials)")
    else:
        print(f"  FAIL test_walkmesh_materials_count: got {len(WALKMESH_MATERIALS)}")
    return ok


def test_walkmesh_materials_structure():
    """Each walkmesh material entry has (name: str, color: tuple, walkable: bool)."""
    ok = all(
        isinstance(m[0], str)
        and len(m[1]) == 3
        and all(isinstance(c, float) for c in m[1])
        and isinstance(m[2], bool)
        for m in WALKMESH_MATERIALS
    )
    if ok:
        print("  PASS test_walkmesh_materials_structure")
    else:
        bad = [m for m in WALKMESH_MATERIALS if not (isinstance(m[0], str) and len(m[1]) == 3)]
        print(f"  FAIL test_walkmesh_materials_structure: bad entries {bad}")
    return ok


def test_walkmesh_name_lookup():
    """NAME_TO_WALKMESH_MATERIAL maps every material name back to its entry."""
    ok = all(
        NAME_TO_WALKMESH_MATERIAL[m[0]] is m for m in WALKMESH_MATERIALS
    )
    if ok:
        print("  PASS test_walkmesh_name_lookup")
    else:
        print("  FAIL test_walkmesh_name_lookup")
    return ok


def test_non_walkable_list():
    """NON_WALKABLE contains only indices where walkable==False."""
    expected = [i for i, m in enumerate(WALKMESH_MATERIALS) if not m[2]]
    ok = set(NON_WALKABLE) == set(expected)
    if ok:
        print(f"  PASS test_non_walkable_list ({len(NON_WALKABLE)} non-walkable types)")
    else:
        print(f"  FAIL test_non_walkable_list: expected={expected}, got={NON_WALKABLE}")
    return ok


def test_classification_values():
    """Classification enum has the expected string constants."""
    expected = {"OTHER", "TILE", "CHARACTER", "DOOR", "EFFECT", "GUI", "LIGHTSABER", "PLACEABLE", "FLYER"}
    actual = {getattr(Classification, k) for k in dir(Classification) if not k.startswith("_")}
    ok = expected == actual
    if ok:
        print(f"  PASS test_classification_values ({len(actual)} values)")
    else:
        print(f"  FAIL test_classification_values: missing={expected-actual}, extra={actual-expected}")
    return ok


def test_dummy_type_values():
    """DummyType enum has all expected string constants."""
    expected = {"NONE", "MDLROOT", "PWKROOT", "DWKROOT", "PTHROOT", "REFERENCE", "PATHPOINT", "USE1", "USE2"}
    actual = {getattr(DummyType, k) for k in dir(DummyType) if not k.startswith("_")}
    ok = expected == actual
    if ok:
        print(f"  PASS test_dummy_type_values ({len(actual)} values)")
    else:
        print(f"  FAIL test_dummy_type_values: missing={expected-actual}, extra={actual-expected}")
    return ok


def test_mesh_type_values():
    """MeshType enum has all expected string constants."""
    expected = {"TRIMESH", "DANGLYMESH", "LIGHTSABER", "SKIN", "AABB", "EMITTER"}
    actual = {getattr(MeshType, k) for k in dir(MeshType) if not k.startswith("_")}
    ok = expected == actual
    if ok:
        print(f"  PASS test_mesh_type_values ({len(actual)} values)")
    else:
        print(f"  FAIL test_mesh_type_values: missing={expected-actual}, extra={actual-expected}")
    return ok


def test_node_type_values():
    """NodeType enum has all expected string constants."""
    expected = {"DUMMY", "REFERENCE", "TRIMESH", "DANGLYMESH", "SKIN", "EMITTER", "LIGHT", "AABB", "LIGHTSABER"}
    actual = {getattr(NodeType, k) for k in dir(NodeType) if not k.startswith("_")}
    ok = expected == actual
    if ok:
        print(f"  PASS test_node_type_values ({len(actual)} values)")
    else:
        print(f"  FAIL test_node_type_values: missing={expected-actual}, extra={actual-expected}")
    return ok


def test_export_options_defaults():
    """ExportOptions default values are as documented."""
    opts = ExportOptions()
    ok = (
        opts.export_for_tsl is False
        and opts.export_for_xbox is False
        and opts.export_animations is True
        and opts.export_walkmeshes is True
        and opts.compress_quaternions is False
    )
    if ok:
        print("  PASS test_export_options_defaults")
    else:
        print(
            f"  FAIL test_export_options_defaults: "
            f"tsl={opts.export_for_tsl}, xbox={opts.export_for_xbox}, "
            f"anim={opts.export_animations}, wm={opts.export_walkmeshes}, "
            f"cq={opts.compress_quaternions}"
        )
    return ok


def test_import_options_defaults():
    """ImportOptions default values are as documented."""
    opts = ImportOptions()
    ok = (
        opts.import_geometry is True
        and opts.import_animations is True
        and opts.import_walkmeshes is True
        and opts.build_materials is True
        and opts.build_armature is False
    )
    if ok:
        print("  PASS test_import_options_defaults")
    else:
        print("  FAIL test_import_options_defaults")
    return ok


def test_utility_is_mdl_root():
    """is_mdl_root() correctly identifies MDLROOT empty objects."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    root = bpy.data.objects.new("TestRoot", None)
    root.kb.dummytype = DummyType.MDLROOT
    bpy.context.scene.collection.objects.link(root)

    other = bpy.data.objects.new("TestOther", None)
    other.kb.dummytype = DummyType.PATHPOINT
    bpy.context.scene.collection.objects.link(other)

    ok = is_mdl_root(root) and not is_mdl_root(other)
    if ok:
        print("  PASS test_utility_is_mdl_root")
    else:
        print(f"  FAIL test_utility_is_mdl_root: root={is_mdl_root(root)}, other={is_mdl_root(other)}")
    return ok


def test_utility_is_path_point():
    """is_path_point() correctly identifies PATHPOINT empty objects."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    pt = bpy.data.objects.new("TestPt", None)
    pt.kb.dummytype = DummyType.PATHPOINT
    bpy.context.scene.collection.objects.link(pt)

    root = bpy.data.objects.new("TestRoot2", None)
    root.kb.dummytype = DummyType.MDLROOT
    bpy.context.scene.collection.objects.link(root)

    ok = is_path_point(pt) and not is_path_point(root)
    if ok:
        print("  PASS test_utility_is_path_point")
    else:
        print(f"  FAIL test_utility_is_path_point: pt={is_path_point(pt)}, root={is_path_point(root)}")
    return ok


def test_utility_is_dummy_type():
    """is_dummy_type() returns False for None and mesh objects."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    ok = not is_dummy_type(None, DummyType.MDLROOT)
    if ok:
        print("  PASS test_utility_is_dummy_type")
    else:
        print("  FAIL test_utility_is_dummy_type: is_dummy_type(None) should be False")
    return ok


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_tests():
    print("\n=== test_constants.py ===")
    tests = [
        test_animation_constants,
        test_uv_map_names,
        test_walkmesh_materials_count,
        test_walkmesh_materials_structure,
        test_walkmesh_name_lookup,
        test_non_walkable_list,
        test_classification_values,
        test_dummy_type_values,
        test_mesh_type_values,
        test_node_type_values,
        test_export_options_defaults,
        test_import_options_defaults,
        test_utility_is_mdl_root,
        test_utility_is_path_point,
        test_utility_is_dummy_type,
    ]
    results = [t() for t in tests]
    passed = sum(results)
    total = len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_constants.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
