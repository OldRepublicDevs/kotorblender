"""
test_bin_io.py – Blender background-mode test

Tests BinaryReader and BinaryWriter in isolation: write known bytes to temp
files, read back, assert exact values. Covers byte order, numerics, strings,
seek/skip/tell. No mocks; real file I/O.

Run with:
    blender --background --python test/blender/test_bin_io.py
"""

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

MODULE = "bl_ext.user_default.io_scene_kotor"
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.format.binreader import BinaryReader, SeekOrigin
from io_scene_kotor.format.binwriter import BinaryWriter


def _float_eq(a, b, tol=1e-5):
    return abs(a - b) < tol


def _write_then_read(write_fn, read_fn, path):
    """Run write_fn(BinaryWriter), close, then read_fn(BinaryReader); return read result."""
    w = BinaryWriter(path, "little")
    try:
        write_fn(w)
    finally:
        w.file.close()
    r = BinaryReader(path, "little")
    try:
        return read_fn(r)
    finally:
        r.file.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_little_endian_roundtrip():
    """uint32 and float round-trip with little-endian."""
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        path = f.name
    try:
        w = BinaryWriter(path, "little")
        w.write_uint32(0x12345678)
        w.write_float(3.25)
        w.file.close()
        r = BinaryReader(path, "little")
        u = r.read_uint32()
        fl = r.read_float()
        r.file.close()
        ok = u == 0x12345678 and _float_eq(fl, 3.25)
        if ok:
            print("  PASS test_little_endian_roundtrip")
        else:
            print(f"  FAIL test_little_endian_roundtrip: u={u}, fl={fl}")
        return ok
    finally:
        os.unlink(path)


def test_big_endian_roundtrip():
    """uint32 and int16 round-trip with big-endian."""
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        path = f.name
    try:
        w = BinaryWriter(path, "big")
        w.write_uint32(0x12345678)
        w.write_int16(-100)
        w.file.close()
        r = BinaryReader(path, "big")
        u = r.read_uint32()
        i = r.read_int16()
        r.file.close()
        ok = u == 0x12345678 and i == -100
        if ok:
            print("  PASS test_big_endian_roundtrip")
        else:
            print(f"  FAIL test_big_endian_roundtrip: u={u}, i={i}")
        return ok
    finally:
        os.unlink(path)


def test_all_numeric_types():
    """int8/16/32 signed and unsigned, float; boundary values."""
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        path = f.name
    try:
        w = BinaryWriter(path, "little")
        w.write_int8(-128)
        w.write_int8(127)
        w.write_uint8(0)
        w.write_uint8(255)
        w.write_int16(-32768)
        w.write_int16(32767)
        w.write_uint16(0)
        w.write_uint16(65535)
        w.write_int32(-0x80000000)
        w.write_int32(0x7FFFFFFF)
        w.write_uint32(0)
        w.write_uint32(0xFFFFFFFF)
        w.write_float(0.0)
        w.write_float(-1.5)
        w.file.close()
        r = BinaryReader(path, "little")
        vals = (
            r.read_int8() == -128
            and r.read_int8() == 127
            and r.read_uint8() == 0
            and r.read_uint8() == 255
            and r.read_int16() == -32768
            and r.read_int16() == 32767
            and r.read_uint16() == 0
            and r.read_uint16() == 65535
            and r.read_int32() == -0x80000000
            and r.read_int32() == 0x7FFFFFFF
            and r.read_uint32() == 0
            and r.read_uint32() == 0xFFFFFFFF
            and _float_eq(r.read_float(), 0.0)
            and _float_eq(r.read_float(), -1.5)
        )
        r.file.close()
        if vals:
            print("  PASS test_all_numeric_types")
        else:
            print("  FAIL test_all_numeric_types")
        return bool(vals)
    finally:
        os.unlink(path)


def test_read_string():
    """read_string(length) returns decoded bytes for given length."""
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        path = f.name
    try:
        w = BinaryWriter(path, "little")
        w.write_string("ABC")
        w.file.close()
        r = BinaryReader(path, "little")
        s = r.read_string(3)
        r.file.close()
        ok = s == "ABC"
        if ok:
            print("  PASS test_read_string")
        else:
            print(f"  FAIL test_read_string: got {s!r}")
        return ok
    finally:
        os.unlink(path)


def test_read_c_string():
    """read_c_string() reads until null or EOF."""
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        path = f.name
    try:
        w = BinaryWriter(path, "little")
        w.write_c_string("hello")
        w.file.close()
        r = BinaryReader(path, "little")
        s = r.read_c_string()
        r.file.close()
        ok = s == "hello"
        if ok:
            print("  PASS test_read_c_string")
        else:
            print(f"  FAIL test_read_c_string: got {s!r}")
        return ok
    finally:
        os.unlink(path)


def test_read_c_string_up_to_short():
    """read_c_string_up_to(max_len) with string shorter than max_len consumes padding."""
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        path = f.name
    try:
        w = BinaryWriter(path, "little")
        w.write_bytes(b"ab\x00\x00\x00\x00\x00\x00")
        w.write_uint32(0xDEADBEEF)
        w.file.close()
        r = BinaryReader(path, "little")
        s = r.read_c_string_up_to(8)
        u = r.read_uint32()
        r.file.close()
        ok = s == "ab" and u == 0xDEADBEEF
        if ok:
            print("  PASS test_read_c_string_up_to_short")
        else:
            print(f"  FAIL test_read_c_string_up_to_short: s={s!r}, u={u}")
        return ok
    finally:
        os.unlink(path)


def test_seek_skip_tell():
    """seek, skip, tell produce expected positions."""
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        path = f.name
    try:
        w = BinaryWriter(path, "little")
        w.write_uint32(1)
        w.write_uint32(2)
        w.write_uint32(3)
        w.write_uint32(4)
        w.file.close()
        r = BinaryReader(path, "little")
        ok = r.tell() == 0
        r.seek(4, SeekOrigin.BEGIN)
        ok = ok and r.tell() == 4 and r.read_uint32() == 2
        r.skip(4)
        ok = ok and r.tell() == 12 and r.read_uint32() == 4
        r.file.close()
        if ok:
            print("  PASS test_seek_skip_tell")
        else:
            print("  FAIL test_seek_skip_tell")
        return ok
    finally:
        os.unlink(path)


def test_binary_writer_roundtrip():
    """Write sequence with BinaryWriter, read same sequence with BinaryReader, assert equality."""
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        path = f.name
    try:
        w = BinaryWriter(path, "little")
        w.write_uint32(100)
        w.write_float(2.5)
        w.write_int16(-42)
        w.write_c_string("x")
        w.file.close()
        r = BinaryReader(path, "little")
        a, b, c = r.read_uint32(), r.read_float(), r.read_int16()
        s = r.read_c_string()
        r.file.close()
        ok = a == 100 and _float_eq(b, 2.5) and c == -42 and s == "x"
        if ok:
            print("  PASS test_binary_writer_roundtrip")
        else:
            print(f"  FAIL test_binary_writer_roundtrip: a={a}, b={b}, c={c}, s={s!r}")
        return ok
    finally:
        os.unlink(path)


def run_tests():
    print("\n=== test_bin_io.py ===")
    tests = [
        test_little_endian_roundtrip,
        test_big_endian_roundtrip,
        test_all_numeric_types,
        test_read_string,
        test_read_c_string,
        test_read_c_string_up_to_short,
        test_seek_skip_tell,
        test_binary_writer_roundtrip,
    ]
    results = [t() for t in tests]
    passed = sum(results)
    total = len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_bin_io.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
