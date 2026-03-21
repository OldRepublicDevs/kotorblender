"""
test_ops_pykotor_stub_texture_save_smoke.py – batch_convert_textures & extract_save execute paths

Both operators gate on PyKotor; when available they FINISHED with a stub INFO (not yet implemented).

Run with:
    blender --background --python test/blender/test_ops_pykotor_stub_texture_save_smoke.py
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

from io_scene_kotor.vendor.pykotor_adapter import is_pykotor_available  # noqa: E402

import io_scene_kotor.ops.texture.batch_convert_textures as _kb_batch  # noqa: F401, E402
import io_scene_kotor.ops.save.extract as _kb_extract  # noqa: F401, E402


def test_batch_convert_textures_execute_path() -> bool:
    fd, path = tempfile.mkstemp(suffix=".tga")
    os.close(fd)
    try:
        try:
            result = bpy.ops.kb.batch_convert_textures(filepath=path)
        except RuntimeError as e:
            if not is_pykotor_available() and "PyKotor" in str(e):
                print("  PASS test_batch_convert_textures_execute_path")
                return True
            print(f"  FAIL batch_convert_textures RuntimeError: {e}")
            return False
        except Exception as e:
            print(f"  FAIL batch_convert_textures raised: {e}")
            return False
        ok = result == {"FINISHED"} if is_pykotor_available() else result == {"CANCELLED"}
        if ok:
            print("  PASS test_batch_convert_textures_execute_path")
        else:
            print(f"  FAIL unexpected {result!r} (pykotor={is_pykotor_available()})")
        return ok
    finally:
        if os.path.isfile(path):
            os.unlink(path)


def test_extract_save_execute_path() -> bool:
    fd, path = tempfile.mkstemp(suffix=".sav")
    os.close(fd)
    try:
        try:
            result = bpy.ops.kb.extract_save(filepath=path)
        except RuntimeError as e:
            if not is_pykotor_available() and "PyKotor" in str(e):
                print("  PASS test_extract_save_execute_path")
                return True
            print(f"  FAIL extract_save RuntimeError: {e}")
            return False
        except Exception as e:
            print(f"  FAIL extract_save raised: {e}")
            return False
        ok = result == {"FINISHED"} if is_pykotor_available() else result == {"CANCELLED"}
        if ok:
            print("  PASS test_extract_save_execute_path")
        else:
            print(f"  FAIL unexpected {result!r} (pykotor={is_pykotor_available()})")
        return ok
    finally:
        if os.path.isfile(path):
            os.unlink(path)


def run_tests() -> bool:
    print("\n=== test_ops_pykotor_stub_texture_save_smoke.py ===")
    results = [test_batch_convert_textures_execute_path(), test_extract_save_execute_path()]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
