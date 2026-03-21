"""
test_ops_autodetect_smoke.py – kb.autodetect_game_installation (no crash)

Autodetect uses native registry/Steam/GOG when PyKotor is missing; operator must not crash.

Run with:
    blender --background --python test/blender/test_ops_autodetect_smoke.py
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

from io_scene_kotor.constants import GameType  # noqa: E402
import io_scene_kotor.ops.game.autodetect_installation as _kb_autodetect  # noqa: F401, E402


def test_autodetect_runs_without_crash() -> bool:
    scene = bpy.context.scene
    prev = scene.kb.game_type
    try:
        scene.kb.game_type = GameType.KOTOR1
        try:
            r = bpy.ops.kb.autodetect_game_installation()
            ok = r in ({"FINISHED"}, {"CANCELLED"})
        except RuntimeError as e:
            # Blender surfaces operator ERROR reports as RuntimeError in some builds.
            msg = str(e).lower()
            ok = "pykotor" in msg or "cancelled" in msg or "not available" in msg
            r = {"RUNTIME_ERROR"}
        if ok:
            print(f"  PASS test_autodetect_runs_without_crash ({r!r})")
        else:
            print(f"  FAIL unexpected return/outcome {r!r}")
        return ok
    except Exception as e:
        print(f"  FAIL exception: {e}")
        return False
    finally:
        scene.kb.game_type = prev


def run_tests() -> bool:
    print("\n=== test_ops_autodetect_smoke.py ===")
    ok = test_autodetect_runs_without_crash()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_ops_autodetect_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
