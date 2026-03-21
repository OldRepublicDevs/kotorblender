"""
Edge cases for BinaryReader / BinaryWriter (SeekOrigin, read_bytes, c-string).

No Blender. Run: pytest test/unit/test_binreader_edges.py -v
"""

from __future__ import annotations

import os
import struct
import tempfile

from io_scene_kotor.format.binreader import BinaryReader, SeekOrigin
from io_scene_kotor.format.binwriter import BinaryWriter


def test_seek_from_end_and_current() -> None:
    fd, path = tempfile.mkstemp(suffix=".bin")
    os.close(fd)
    try:
        with open(path, "wb") as f:
            f.write(b"ABCDxxxx")
        r = BinaryReader(path, "little")
        r.seek(-4, SeekOrigin.END)
        assert r.tell() == 4
        assert r.read_bytes(4) == b"xxxx"
        r.seek(-6, SeekOrigin.CURRENT)
        assert r.tell() == 2
        assert r.read_uint16() == ord("C") | (ord("D") << 8)
        r.file.close()
    finally:
        if os.path.isfile(path):
            os.unlink(path)


def test_read_write_bytes_roundtrip() -> None:
    fd, path = tempfile.mkstemp(suffix=".bin")
    os.close(fd)
    try:
        w = BinaryWriter(path, "little")
        w.write_bytes(b"\x00\xff\x7f")
        w.file.close()
        r = BinaryReader(path, "little")
        assert r.read_bytes(3) == b"\x00\xff\x7f"
        assert r.read_bytes(0) == b""
        r.file.close()
    finally:
        if os.path.isfile(path):
            os.unlink(path)


def test_read_c_string_eof_no_null() -> None:
    fd, path = tempfile.mkstemp(suffix=".bin")
    os.close(fd)
    try:
        with open(path, "wb") as f:
            f.write(b"nul")
        r = BinaryReader(path, "little")
        assert r.read_c_string() == "nul"
        r.file.close()
    finally:
        if os.path.isfile(path):
            os.unlink(path)


def test_read_c_string_empty_file() -> None:
    fd, path = tempfile.mkstemp(suffix=".bin")
    os.close(fd)
    try:
        r = BinaryReader(path, "little")
        assert r.read_c_string() == ""
        r.file.close()
    finally:
        if os.path.isfile(path):
            os.unlink(path)


def test_read_c_string_up_to_full_without_null() -> None:
    fd, path = tempfile.mkstemp(suffix=".bin")
    os.close(fd)
    try:
        with open(path, "wb") as f:
            f.write(b"12345678")
            f.write(struct.pack("<I", 0x11223344))
        r = BinaryReader(path, "little")
        assert r.read_c_string_up_to(8) == "12345678"
        assert r.read_uint32() == 0x11223344
        r.file.close()
    finally:
        if os.path.isfile(path):
            os.unlink(path)
