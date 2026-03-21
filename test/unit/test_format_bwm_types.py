"""Unit tests for io_scene_kotor.format.bwm.types (no Blender)."""

from __future__ import annotations

from io_scene_kotor.format.bwm.types import AABB, BWM_TYPE_PWK_DWK, BWM_TYPE_WOK


def test_bwm_type_constants() -> None:
    assert BWM_TYPE_PWK_DWK == 0
    assert BWM_TYPE_WOK == 1


def test_aabb_fields() -> None:
    bbox = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    a = AABB(bbox, face_idx=7, most_significant_plane=2, child_idx1=10, child_idx2=11)
    assert a.bounding_box == bbox
    assert a.face_idx == 7
    assert a.most_significant_plane == 2
    assert a.child_idx1 == 10
    assert a.child_idx2 == 11
