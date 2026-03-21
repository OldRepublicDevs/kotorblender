"""
test_scene_armature.py – rebuild_armature guard paths

Run with:
    blender --background --python test/blender/test_scene_armature.py
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

from io_scene_kotor.constants import Classification, DummyType  # noqa: E402
from io_scene_kotor.scene.armature import rebuild_armature  # noqa: E402


def _clear_objects() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)


def test_rebuild_armature_skips_non_character() -> bool:
    _clear_objects()
    root = bpy.data.objects.new("mdlroot", None)
    root.kb.dummytype = DummyType.MDLROOT
    root.kb.classification = Classification.OTHER
    bpy.context.collection.objects.link(root)
    result = rebuild_armature(root)
    _clear_objects()
    if result is not None:
        print("  FAIL test_rebuild_armature_skips_non_character: expected None")
        return False
    print("  PASS test_rebuild_armature_skips_non_character")
    return True


def test_rebuild_armature_skips_character_without_skin() -> bool:
    _clear_objects()
    root = bpy.data.objects.new("charroot", None)
    root.kb.dummytype = DummyType.MDLROOT
    root.kb.classification = Classification.CHARACTER
    bpy.context.collection.objects.link(root)
    result = rebuild_armature(root)
    _clear_objects()
    if result is not None:
        print("  FAIL test_rebuild_armature_skips_character_without_skin: expected None")
        return False
    print("  PASS test_rebuild_armature_skips_character_without_skin")
    return True


def run_tests() -> bool:
    print("\n=== test_scene_armature.py ===")
    results = [test_rebuild_armature_skips_non_character(), test_rebuild_armature_skips_character_without_skin()]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
