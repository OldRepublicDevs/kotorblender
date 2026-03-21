"""
test_format_mdl_reader_errors.py – MdlReader rejects invalid / tiny MDL files

Run with:
    blender --background --python test/blender/test_format_mdl_reader_errors.py
"""

from __future__ import annotations

import os
import struct
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

from io_scene_kotor.format.mdl.reader import MdlReader  # noqa: E402


def test_mdl_reader_invalid_signature() -> bool:
    fd, path = tempfile.mkstemp(suffix=".mdl")
    os.close(fd)
    try:
        with open(path, "wb") as f:
            f.write(struct.pack("<I", 0xFFFFFFFF))
        reader = MdlReader(path)
        try:
            reader.load()
        except RuntimeError as e:
            if "signature" in str(e).lower() or "invalid" in str(e).lower():
                print("  PASS test_mdl_reader_invalid_signature")
                return True
            print(f"  FAIL test_mdl_reader_invalid_signature: {e!r}")
            return False
        except Exception as e:
            print(f"  FAIL test_mdl_reader_invalid_signature: {type(e).__name__}: {e}")
            return False
        else:
            print("  FAIL test_mdl_reader_invalid_signature: load() succeeded")
            return False
        finally:
            reader.mdl.file.close()
    finally:
        if os.path.isfile(path):
            os.unlink(path)


def test_mdl_reader_truncated_after_header_start() -> bool:
    fd, path = tempfile.mkstemp(suffix=".mdl")
    os.close(fd)
    try:
        with open(path, "wb") as f:
            f.write(struct.pack("<III", 0, 100, 0))
        reader = MdlReader(path)
        try:
            reader.load()
        except Exception as e:
            print(f"  PASS test_mdl_reader_truncated_after_header_start ({type(e).__name__})")
            return True
        else:
            print("  FAIL test_mdl_reader_truncated_after_header_start: load() succeeded")
            return False
        finally:
            reader.mdl.file.close()
    finally:
        if os.path.isfile(path):
            os.unlink(path)


def run_tests() -> bool:
    print("\n=== test_format_mdl_reader_errors.py ===")
    results = [test_mdl_reader_invalid_signature(), test_mdl_reader_truncated_after_header_start()]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
