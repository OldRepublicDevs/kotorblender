"""
test_ops_convert_tga_to_tpc_smoke.py – bpy.ops.kb.convert_tga_to_tpc

Operator currently stubs conversion when PyKotor is present; without PyKotor it cancels.

Run with:
    blender --background --python test/blender/test_ops_convert_tga_to_tpc_smoke.py
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

import io_scene_kotor.ops.texture.convert_tga_to_tpc as _kb_tga_tpc  # noqa: F401, E402
from io_scene_kotor.vendor.pykotor_adapter import is_pykotor_available  # noqa: E402


def test_convert_tga_to_tpc_defined_outcome() -> bool:
    d = tempfile.mkdtemp()
    path = os.path.join(d, "x.tga")
    try:
        with open(path, "wb") as f:
            f.write(b"\x00\x01\x02")
        if is_pykotor_available():
            r = bpy.ops.kb.convert_tga_to_tpc(filepath=path)
            ok = r == {"FINISHED"}
        else:
            try:
                r = bpy.ops.kb.convert_tga_to_tpc(filepath=path)
                ok = r == {"CANCELLED"}
            except RuntimeError as e:
                ok = "pykotor" in str(e).lower() or "not available" in str(e).lower()
        if ok:
            print("  PASS test_convert_tga_to_tpc_defined_outcome")
        else:
            print("  FAIL unexpected operator outcome")
        return ok
    finally:
        if os.path.isfile(path):
            os.unlink(path)
        try:
            os.rmdir(d)
        except OSError:
            pass


def run_tests() -> bool:
    print("\n=== test_ops_convert_tga_to_tpc_smoke.py ===")
    ok = test_convert_tga_to_tpc_defined_outcome()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_ops_convert_tga_to_tpc_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
