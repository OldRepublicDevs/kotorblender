"""
Unit tests for constants and options (no Blender).

Tests enumerations, walkmesh material table, and option defaults.
Does not test utils (is_mdl_root, is_path_point, is_dummy_type) which
require real bpy objects; those remain in test/blender/test_constants.py.

Run with: pytest test/unit/test_constants.py -v
"""

from __future__ import annotations

import pytest

from io_scene_kotor.constants import (
    ANIM_FPS,
    ANIM_PADDING,
    ANIM_REST_POSE_OFFSET,
    NAME_TO_WALKMESH_MATERIAL,
    NON_WALKABLE,
    USE_PYKOTOR_READERS,
    UV_MAP_LIGHTMAP,
    UV_MAP_MAIN,
    WALKMESH_MATERIALS,
    Classification,
    DummyType,
    ExportOptions,
    ImportOptions,
    LogReasonCode,
    MeshType,
    NodeType,
)
from io_scene_kotor.vendor.pykotor_adapter import get_use_pykotor_readers


def test_animation_constants():
    """Animation constants have expected values."""
    assert ANIM_FPS == 30 and ANIM_REST_POSE_OFFSET == 5 and ANIM_PADDING == 60


def test_uv_map_names():
    """UV map name constants are correct strings."""
    assert UV_MAP_MAIN == "UVMap" and UV_MAP_LIGHTMAP == "UVMap_lm"


def test_walkmesh_materials_count():
    """WALKMESH_MATERIALS has exactly 23 entries."""
    assert len(WALKMESH_MATERIALS) == 23


def test_walkmesh_materials_structure():
    """Each walkmesh material entry has (name: str, color: tuple, walkable: bool)."""
    for m in WALKMESH_MATERIALS:
        assert isinstance(m[0], str)
        assert len(m[1]) == 3 and all(isinstance(c, float) for c in m[1])
        assert isinstance(m[2], bool)


def test_walkmesh_name_lookup():
    """NAME_TO_WALKMESH_MATERIAL maps every material name back to its entry."""
    for m in WALKMESH_MATERIALS:
        assert NAME_TO_WALKMESH_MATERIAL[m[0]] is m


def test_non_walkable_list():
    """NON_WALKABLE contains only indices where walkable==False."""
    expected = [i for i, m in enumerate(WALKMESH_MATERIALS) if not m[2]]
    assert set(NON_WALKABLE) == set(expected)


def test_classification_values():
    """Classification enum has the expected string constants."""
    expected = {
        "OTHER",
        "TILE",
        "CHARACTER",
        "DOOR",
        "EFFECT",
        "GUI",
        "LIGHTSABER",
        "PLACEABLE",
        "FLYER",
    }
    actual = {e.value for e in Classification}
    assert expected == actual


def test_dummy_type_values():
    """DummyType enum has all expected string constants."""
    expected = {
        "NONE",
        "MDLROOT",
        "PWKROOT",
        "DWKROOT",
        "PTHROOT",
        "REFERENCE",
        "PATHPOINT",
        "USE1",
        "USE2",
    }
    actual = {e.value for e in DummyType}
    assert expected == actual


def test_mesh_type_values():
    """MeshType enum has all expected string constants."""
    expected = {"TRIMESH", "DANGLYMESH", "LIGHTSABER", "SKIN", "AABB", "EMITTER"}
    actual = {e.value for e in MeshType}
    assert expected == actual


def test_node_type_values():
    """NodeType enum has all expected string constants."""
    expected = {
        "UNDEFINED",
        "DUMMY",
        "REFERENCE",
        "TRIMESH",
        "DANGLYMESH",
        "SKIN",
        "EMITTER",
        "LIGHT",
        "AABB",
        "LIGHTSABER",
    }
    actual = {e.value for e in NodeType}
    assert expected == actual


def test_log_reason_code_values():
    """LogReasonCode lists stable diagnostic strings."""
    expected = {"OK", "INTERNAL_ERROR", "MISSING_FILE", "PARSE_ERROR", "IO_ERROR", "CONFIG_ERROR"}
    assert {e.value for e in LogReasonCode} == expected


def test_export_options_defaults():
    """ExportOptions default values are as documented."""
    opts = ExportOptions()
    assert opts.export_for_tsl is False
    assert opts.export_for_xbox is False
    assert opts.export_animations is True
    assert opts.export_walkmeshes is True
    assert opts.compress_quaternions is False


def test_import_options_defaults():
    """ImportOptions default values are as documented."""
    opts = ImportOptions()
    assert opts.import_geometry is True
    assert opts.import_animations is True
    assert opts.import_walkmeshes is True
    assert opts.build_materials is True
    assert opts.build_armature is False


def test_use_pykotor_readers_default():
    """USE_PYKOTOR_READERS defaults to False for safe migration."""
    assert USE_PYKOTOR_READERS is False


def test_get_use_pykotor_readers_fallback():
    """get_use_pykotor_readers() is False when flag is False (or PyKotor unavailable)."""
    # With default USE_PYKOTOR_READERS=False, getter must always be False
    assert get_use_pykotor_readers() is False
