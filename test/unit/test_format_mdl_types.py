"""Unit tests for io_scene_kotor.format.mdl.types (no Blender)."""

from __future__ import annotations

from io_scene_kotor.constants import Classification
from io_scene_kotor.format.mdl.types import (
    CLASS_BY_VALUE,
    CLASS_CHARACTER,
    CLASS_DOOR,
    EMITTER_FLAG_DEPTH_TEXTURE,
    EMITTER_FLAG_KNOWN_MASK,
    MODEL_ANIM,
    MODEL_MODEL,
    NODE_AABB,
    NODE_MESH,
)


def test_model_type_constants() -> None:
    assert MODEL_MODEL == 2
    assert MODEL_ANIM == 5


def test_class_by_value_matches_constants_enum() -> None:
    assert CLASS_BY_VALUE[CLASS_CHARACTER] is Classification.CHARACTER
    assert CLASS_BY_VALUE[CLASS_DOOR] is Classification.DOOR
    assert len(CLASS_BY_VALUE) == 8


def test_node_type_flags_are_powers_of_two() -> None:
    assert NODE_MESH & NODE_AABB == 0
    assert NODE_MESH != 0 and NODE_AABB != 0


def test_emitter_known_mask_includes_depth_texture() -> None:
    assert (EMITTER_FLAG_KNOWN_MASK & EMITTER_FLAG_DEPTH_TEXTURE) == EMITTER_FLAG_DEPTH_TEXTURE
