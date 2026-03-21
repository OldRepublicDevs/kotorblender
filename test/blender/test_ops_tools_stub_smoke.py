"""
test_ops_tools_stub_smoke.py – tools operators: PyKotor gate, clone_module errors, TSLPatch stub

Ensures kb.module_designer, kb.indoor_map_builder, kb.clone_module, kb.tslpatchdata_editor
do not throw uncaught exceptions in background mode.

Run with:
    blender --background --python test/blender/test_ops_tools_stub_smoke.py
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

MODULE = "bl_ext.user_default.io_scene_kotor"
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

import io_scene_kotor.ops.tools.clone_module as _kb_clone  # noqa: F401, E402
import io_scene_kotor.ops.tools.indoor_map_builder as _kb_indoor  # noqa: F401, E402
import io_scene_kotor.ops.tools.module_designer as _kb_md  # noqa: F401, E402
import io_scene_kotor.ops.tools.tslpatchdata_editor as _kb_tslp  # noqa: F401, E402

from io_scene_kotor.vendor.pykotor_adapter import is_pykotor_available  # noqa: E402


def _pykotor_error_ok(exc: RuntimeError) -> bool:
    return "PyKotor" in str(exc)


def test_module_designer_gate() -> bool:
    try:
        result = bpy.ops.kb.module_designer()
    except RuntimeError as e:
        if not is_pykotor_available() and _pykotor_error_ok(e):
            print("  PASS test_module_designer_gate (RuntimeError, no PyKotor)")
            return True
        print(f"  FAIL module_designer unexpected RuntimeError: {e}")
        return False
    if is_pykotor_available():
        ok = result == {"FINISHED"}
        print(f"  {'PASS' if ok else 'FAIL'} test_module_designer_gate FINISHED with PyKotor")
        return ok
    print(f"  FAIL module_designer expected error without PyKotor, got {result!r}")
    return False


def test_indoor_map_builder_gate() -> bool:
    try:
        result = bpy.ops.kb.indoor_map_builder()
    except RuntimeError as e:
        if not is_pykotor_available() and _pykotor_error_ok(e):
            print("  PASS test_indoor_map_builder_gate (RuntimeError, no PyKotor)")
            return True
        print(f"  FAIL indoor_map_builder unexpected RuntimeError: {e}")
        return False
    if is_pykotor_available():
        ok = result == {"FINISHED"}
        print(f"  {'PASS' if ok else 'FAIL'} test_indoor_map_builder_gate FINISHED with PyKotor")
        return ok
    print(f"  FAIL indoor_map_builder expected error without PyKotor, got {result!r}")
    return False


def test_clone_module_no_selection() -> bool:
    scene = bpy.context.scene
    kb = scene.kb
    kb.module_list.clear()
    kb.module_list_idx = 0
    try:
        result = bpy.ops.kb.clone_module(new_module_name="clone_test")
    except RuntimeError as e:
        msg = str(e)
        if "No module selected" in msg:
            print("  PASS test_clone_module_no_selection (RuntimeError: no module)")
            return True
        if not is_pykotor_available() and _pykotor_error_ok(e):
            print("  PASS test_clone_module_no_selection (RuntimeError: no PyKotor)")
            return True
        print(f"  FAIL clone_module unexpected RuntimeError: {e}")
        return False
    if result == {"CANCELLED"}:
        print("  PASS test_clone_module_no_selection (CANCELLED)")
        return True
    print(f"  FAIL clone_module expected CANCELLED, got {result!r}")
    return False


def test_tslpatchdata_editor_gate() -> bool:
    fd, path = tempfile.mkstemp(suffix=".ini")
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("[Settings]\n")
        try:
            result = bpy.ops.kb.tslpatchdata_editor(filepath=path)
        except RuntimeError as e:
            if not is_pykotor_available() and _pykotor_error_ok(e):
                print("  PASS test_tslpatchdata_editor_gate (RuntimeError, no PyKotor)")
                return True
            print(f"  FAIL tslpatchdata_editor unexpected RuntimeError: {e}")
            return False
        if is_pykotor_available():
            ok = result == {"FINISHED"}
            print(f"  {'PASS' if ok else 'FAIL'} test_tslpatchdata_editor_gate FINISHED with PyKotor")
            return ok
        print(f"  FAIL tslpatchdata_editor expected error without PyKotor, got {result!r}")
        return False
    finally:
        if os.path.isfile(path):
            os.unlink(path)


def run_tests() -> bool:
    print("\n=== test_ops_tools_stub_smoke.py ===")
    results = [
        test_module_designer_gate(),
        test_indoor_map_builder_gate(),
        test_clone_module_no_selection(),
        test_tslpatchdata_editor_gate(),
    ]
    passed, total = sum(results), len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_ops_tools_stub_smoke.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
