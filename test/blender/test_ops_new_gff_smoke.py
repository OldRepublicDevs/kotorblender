"""
test_ops_new_gff_smoke.py – bpy.ops.kb.new_gff writes minimal GFF (GffWriter path)

Run with:
    blender --background --python test/blender/test_ops_new_gff_smoke.py
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

from io_scene_kotor.ops.resource import new_gff as _kb_new_gff  # noqa: F401, E402


def test_ops_new_gff_writes_file() -> bool:
    fd, path = tempfile.mkstemp(suffix=".gff")
    os.close(fd)
    try:
        if os.path.isfile(path):
            os.unlink(path)
        try:
            result = bpy.ops.kb.new_gff(filepath=path)
        except Exception as e:
            print(f"  FAIL new_gff raised: {e}")
            return False
        if result != {"FINISHED"}:
            print(f"  FAIL new_gff returned {result!r}")
            return False
        if not os.path.isfile(path) or os.path.getsize(path) < 32:
            print("  FAIL new_gff output missing or too small")
            return False
    finally:
        if os.path.isfile(path):
            os.unlink(path)
    print("  PASS test_ops_new_gff_writes_file")
    return True


def run_tests() -> bool:
    print("\n=== test_ops_new_gff_smoke.py ===")
    ok = test_ops_new_gff_writes_file()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_ops_new_gff_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
