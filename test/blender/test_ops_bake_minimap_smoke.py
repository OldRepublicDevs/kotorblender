"""
test_ops_bake_minimap_smoke.py – bake lightmaps / render minimap execute (no-op paths)

Background scenes without bake targets or walkmeshes should return CANCELLED without raising.

Run with:
    blender --background --python test/blender/test_ops_bake_minimap_smoke.py
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

import io_scene_kotor.ops.bakelightmaps as _kb_bake  # noqa: F401, E402
import io_scene_kotor.ops.renderminimap as _kb_minimap  # noqa: F401, E402


def test_bake_lightmaps_auto_cancelled_no_targets() -> bool:
    try:
        r = bpy.ops.kb.bake_lightmaps_auto()
    except Exception as e:
        print(f"  FAIL bake_lightmaps_auto raised: {e}")
        return False
    ok = r == {"CANCELLED"}
    if ok:
        print("  PASS test_bake_lightmaps_auto_cancelled_no_targets")
    else:
        print(f"  FAIL bake_lightmaps_auto returned {r!r}, expected CANCELLED")
    return ok


def test_render_minimap_manual_cancelled_no_aabb() -> bool:
    try:
        r = bpy.ops.kb.render_minimap_manual()
    except Exception as e:
        print(f"  FAIL render_minimap_manual raised: {e}")
        return False
    ok = r == {"CANCELLED"}
    if ok:
        print("  PASS test_render_minimap_manual_cancelled_no_aabb")
    else:
        print(f"  FAIL render_minimap_manual returned {r!r}, expected CANCELLED")
    return ok


def run_tests() -> bool:
    print("\n=== test_ops_bake_minimap_smoke.py ===")
    results = [
        test_bake_lightmaps_auto_cancelled_no_targets(),
        test_render_minimap_manual_cancelled_no_aabb(),
    ]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed test_ops_bake_minimap_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
