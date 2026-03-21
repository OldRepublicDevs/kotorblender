"""
test_ops_convert_tpc_to_tga_smoke.py – bpy.ops.kb.convert_tpc_to_tga

Run with:
    blender --background --python test/blender/test_ops_convert_tpc_to_tga_smoke.py
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

import io_scene_kotor.ops.texture.convert_tpc_to_tga as _kb_tpc_tga  # noqa: F401, E402


def _write_min_grayscale_tpc(path: str, w: int = 2, h: int = 2) -> None:
    hdr = bytearray()
    hdr += struct.pack("<I", 0)
    hdr += struct.pack("<I", 0)
    hdr += struct.pack("<HH", w, h)
    hdr += struct.pack("<BB", 1, 1)
    hdr += b"\x00" * (128 - len(hdr))
    with open(path, "wb") as f:
        f.write(hdr)
        f.write(b"\x00" * (w * h))


def test_ops_convert_tpc_to_tga_writes_tga() -> bool:
    d = tempfile.mkdtemp()
    tpc = os.path.join(d, "tiny.tpc")
    tga = os.path.join(d, "tiny.tga")
    try:
        _write_min_grayscale_tpc(tpc)
        try:
            bpy.ops.kb.convert_tpc_to_tga(filepath=tpc)
        except Exception as e:
            print(f"  FAIL convert_tpc_to_tga: {e}")
            return False
        ok = os.path.isfile(tga) and os.path.getsize(tga) > 0
        if ok:
            print("  PASS test_ops_convert_tpc_to_tga_writes_tga")
        else:
            print(f"  FAIL missing or empty TGA: {tga!r}")
        return ok
    finally:
        for p in (tpc, tga):
            if os.path.isfile(p):
                os.unlink(p)
        try:
            os.rmdir(d)
        except OSError:
            pass


def run_tests() -> bool:
    print("\n=== test_ops_convert_tpc_to_tga_smoke.py ===")
    ok = test_ops_convert_tpc_to_tga_writes_tga()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_ops_convert_tpc_to_tga_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
