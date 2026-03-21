"""
test_mdl_import_op.py – Blender background-mode test

Tests the exact MDL import pipeline used by the GUI: operator execute()
reads addon_preferences.texture_search_paths / lightmap_search_paths and
passes them to semicolon_separated_to_absolute_paths before load_mdl.
These tests would fail if addon prefs were _PropertyDeferred (e.g. Blender 5.x)
and the code did not coerce to str.

  - test_import_prefs_paths_resolve: same code path as execute() up to load_mdl
    (addon prefs → semicolon_separated_to_absolute_paths). No MDL file.
  - test_mdlimport_operator_full_pipeline: bpy.ops.kb.mdlimport(filepath=...)
    with a minimal exported MDL. Full operator execute() with real addon prefs.

Run with:
    blender --background --python test/blender/test_mdl_import_op.py
"""
from __future__ import annotations

import os
import sys
import tempfile

import bpy

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from test_helpers import get_addon_module_name

MODULE = get_addon_module_name()
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.constants import DummyType, Classification, ExportOptions
from io_scene_kotor.io.mdl import save_mdl
from io_scene_kotor.utils import semicolon_separated_to_absolute_paths

# ---------------------------------------------------------------------------
# Helpers (minimal copy for self-contained operator-path test)
# ---------------------------------------------------------------------------


class _Op:
    def report(self, level, message):
        tag = next(iter(level)) if level else "INFO"
        print(f"    [{tag}] {message}")


def _clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)


def _make_mdl_root(name="testmodel"):
    root = bpy.data.objects.new(name, None)
    root.kb.dummytype = DummyType.MDLROOT
    root.kb.classification = Classification.OTHER
    root.kb.animscale = 1.0
    root.kb.node_number = 1
    root.kb.export_order = 0
    root.rotation_mode = "QUATERNION"
    bpy.context.collection.objects.link(root)
    return root


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_import_prefs_paths_resolve():
    """
    Same pipeline as KB_OT_import_mdl.execute(): get addon prefs, pass
    texture_search_paths and lightmap_search_paths to semicolon_separated_to_absolute_paths.
    Would raise AttributeError if prefs were _PropertyDeferred and .split() were called.
    """
    try:
        context = bpy.context
        addons = context.preferences.addons
        addon_preferences = None
        for key in (get_addon_module_name(), "bl_ext.user_default.io_scene_kotor", "io_scene_kotor"):
            if key in addons:
                addon_preferences = addons[key].preferences
                break
        if addon_preferences is None:
            print("  FAIL test_import_prefs_paths_resolve: addon preferences not found")
            return False
        working_dir = os.path.dirname(os.path.abspath(__file__))

        texture_paths = semicolon_separated_to_absolute_paths(
            addon_preferences.texture_search_paths, working_dir
        )
        lightmap_paths = semicolon_separated_to_absolute_paths(
            addon_preferences.lightmap_search_paths, working_dir
        )

        ok = isinstance(texture_paths, list) and isinstance(lightmap_paths, list)
        ok = ok and all(isinstance(p, str) for p in texture_paths)
        ok = ok and all(isinstance(p, str) for p in lightmap_paths)
        ok = ok and len(texture_paths) >= 1 and len(lightmap_paths) >= 1

        if ok:
            print("  PASS test_import_prefs_paths_resolve (same path as operator execute)")
        else:
            print("  FAIL test_import_prefs_paths_resolve: invalid path lists")
        return ok
    except AttributeError as e:
        print(f"  FAIL test_import_prefs_paths_resolve: {e} (e.g. _PropertyDeferred)")
        return False
    except Exception as e:
        print(f"  FAIL test_import_prefs_paths_resolve: {e.__class__.__name__}: {e}")
        return False


def test_mdlimport_operator_full_pipeline():
    """
    Full GUI path: export minimal MDL, then bpy.ops.kb.mdlimport(filepath=...).
    Exercises execute() with real addon preferences and semicolon_separated_to_absolute_paths.
    """
    _clear_scene()
    _make_mdl_root("op_import_test")
    _op = _Op()

    with tempfile.NamedTemporaryFile(suffix=".mdl", delete=False) as f:
        path = f.name
    mdx_path = path[:-4] + ".mdx"
    try:
        opts = ExportOptions()
        opts.export_animations = False
        opts.export_walkmeshes = False
        save_mdl(_op, path, opts)

        _clear_scene()
        result = bpy.ops.kb.mdlimport(filepath=path)

        ok = result == {"FINISHED"}
        if ok:
            roots = [
                o
                for o in bpy.data.objects
                if getattr(o.kb, "dummytype", None) == DummyType.MDLROOT
            ]
            ok = len(roots) >= 1
        if ok:
            print("  PASS test_mdlimport_operator_full_pipeline (full execute path)")
        else:
            print(f"  FAIL test_mdlimport_operator_full_pipeline: result={result}")
        return ok
    except Exception as e:
        print(f"  FAIL test_mdlimport_operator_full_pipeline: {e.__class__.__name__}: {e}")
        return False
    finally:
        for p in (path, mdx_path):
            if os.path.exists(p):
                try:
                    os.unlink(p)
                except OSError:
                    pass


def run_tests():
    print("\n=== test_mdl_import_op.py ===")
    tests = [
        test_import_prefs_paths_resolve,
        test_mdlimport_operator_full_pipeline,
    ]
    results = [t() for t in tests]
    passed = sum(results)
    total = len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_mdl_import_op.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
