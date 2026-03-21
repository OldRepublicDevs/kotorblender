"""
test_addonprefs_paths.py – Addon preferences path strings resolve like import pipeline

Mirrors KB_OT_import_mdl.execute() preference handling (str coercion for Blender 5.x).

Run with:
    blender --background --python test/blender/test_addonprefs_paths.py
"""

from __future__ import annotations

import os
import sys
import tempfile

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from test_helpers import get_addon_module_name  # noqa: E402

MODULE = get_addon_module_name()
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.utils import semicolon_separated_to_absolute_paths  # noqa: E402
from io_scene_kotor.vendor.pykotor_adapter import is_pykotor_available  # noqa: E402


def test_addonprefs_paths_roundtrip_str() -> bool:
    addons = bpy.context.preferences.addons
    prefs = None
    for key in (get_addon_module_name(), "bl_ext.user_default.io_scene_kotor", "io_scene_kotor"):
        if key in addons:
            prefs = addons[key].preferences
            break
    if prefs is None:
        print("  FAIL test_addonprefs_paths_roundtrip_str: no preferences")
        return False
    old_tex = str(prefs.texture_search_paths)
    old_lm = str(prefs.lightmap_search_paths)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            prefs.texture_search_paths = tmp
            s = str(prefs.texture_search_paths)
            out = semicolon_separated_to_absolute_paths(s, tmp)
            if not out or not any(os.path.isdir(p) for p in out):
                print(f"  FAIL test_addonprefs_paths_roundtrip_str: {out!r}")
                return False
    finally:
        prefs.texture_search_paths = old_tex
        prefs.lightmap_search_paths = old_lm
    print("  PASS test_addonprefs_paths_roundtrip_str")
    return True


def test_pykotor_available_returns_bool() -> bool:
    """Addon prefs runtime status uses is_pykotor_available(); RNA blocks calling draw() without a real layout."""
    v = is_pykotor_available()
    if not isinstance(v, bool):
        print(f"  FAIL test_pykotor_available_returns_bool: expected bool, got {type(v)!r}")
        return False
    print("  PASS test_pykotor_available_returns_bool")
    return True


def run_tests() -> bool:
    print("\n=== test_addonprefs_paths.py ===")
    results = [test_addonprefs_paths_roundtrip_str(), test_pykotor_available_returns_bool()]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] test_addonprefs_paths.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
