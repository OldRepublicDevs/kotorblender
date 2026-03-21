"""
test_io_scene_kotor_package.py – Package bl_info aligns with extension manifest

Run with:
    blender --background --python test/blender/test_io_scene_kotor_package.py
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

import io_scene_kotor  # noqa: E402


def test_bl_info_name_and_version() -> bool:
    bi = getattr(io_scene_kotor, "bl_info", None)
    if not isinstance(bi, dict):
        print("  FAIL test_bl_info_name_and_version: bl_info missing")
        return False
    if bi.get("name") != "KotorBlender":
        print(f"  FAIL test_bl_info_name_and_version: name={bi.get('name')!r}")
        return False
    if bi.get("version") != (5, 0, 0):
        print(f"  FAIL test_bl_info_name_and_version: version={bi.get('version')!r}")
        return False
    print("  PASS test_bl_info_name_and_version")
    return True


def run_tests() -> bool:
    print("\n=== test_io_scene_kotor_package.py ===")
    ok = test_bl_info_name_and_version()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_io_scene_kotor_package.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
