"""
test_format_bwm_reader_errors.py – BwmReader rejects invalid / truncated files

Run with:
    blender --background --python test/blender/test_format_bwm_reader_errors.py
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

from io_scene_kotor.format.bwm.reader import BwmReader  # noqa: E402


def test_bwm_reader_invalid_magic() -> bool:
    fd, path = tempfile.mkstemp(suffix=".wok")
    os.close(fd)
    try:
        with open(path, "wb") as f:
            f.write(b"XXXX")
        reader = BwmReader(path, "root")
        try:
            reader.load()
        except RuntimeError as e:
            if "BWM " in str(e) or "invalid" in str(e).lower():
                print("  PASS test_bwm_reader_invalid_magic")
                return True
        finally:
            reader.bwm.file.close()
        print("  FAIL test_bwm_reader_invalid_magic: expected RuntimeError")
        return False
    finally:
        if os.path.isfile(path):
            os.unlink(path)


def test_bwm_reader_truncated_header() -> bool:
    fd, path = tempfile.mkstemp(suffix=".wok")
    os.close(fd)
    try:
        with open(path, "wb") as f:
            f.write(b"BWM \x00\x00\x00\x00")  # magic + incomplete rest
        reader = BwmReader(path, "root")
        try:
            reader.load()
        except Exception as e:
            print(f"  PASS test_bwm_reader_truncated_header ({type(e).__name__})")
            return True
        finally:
            reader.bwm.file.close()
        print("  FAIL test_bwm_reader_truncated_header: expected error")
        return False
    finally:
        if os.path.isfile(path):
            os.unlink(path)


def run_tests() -> bool:
    print("\n=== test_format_bwm_reader_errors.py ===")
    results = [test_bwm_reader_invalid_magic(), test_bwm_reader_truncated_header()]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
