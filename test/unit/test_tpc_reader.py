"""
Unit tests for the TPC texture format reader.

No Blender (bpy) required. Uses real temp files and io_scene_kotor.format.tpc.
Run with: pytest test/unit/test_tpc_reader.py -v
"""

from __future__ import annotations

import os
import struct
import tempfile


def _make_minimal_tpc(path: str, width: int = 2, height: int = 2) -> None:
    """Write a minimal valid KotOR TPC: uncompressed grayscale."""
    with open(path, "wb") as f:
        f.write(struct.pack("<I", 0))  # compressed_size = 0
        f.write(struct.pack("<I", 0))  # reserved
        f.write(struct.pack("<HH", width, height))
        f.write(struct.pack("<BB", 1, 1))  # TpcEncoding.GRAYSCALE=1, num_mips=1
        f.write(b"\x00" * (128 - 14))  # pad so pixel data starts at offset 128
        f.write(b"\x00" * (width * height))  # pixel data


def test_tpc_reader_minimal_uncompressed_grayscale():
    """TpcReader loads a minimal uncompressed grayscale TPC and returns correct dimensions."""
    from io_scene_kotor.format.tpc.reader import TpcEncoding, TpcReader

    fd, path = tempfile.mkstemp(suffix=".tpc")
    try:
        os.close(fd)
        _make_minimal_tpc(path, width=4, height=4)
        reader = TpcReader(path)
        image = reader.load()
        reader.reader.file.close()  # release handle so Windows can unlink
        assert image.w == 4 and image.h == 4
        assert reader.encoding == TpcEncoding.GRAYSCALE
        assert len(image.pixels) == 4 * 4 * 4  # RGBA floats
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_tpc_reader_dimensions_1x1():
    """TpcReader reports correct dimensions and pixel count for 1x1 grayscale."""
    from io_scene_kotor.format.tpc.reader import TpcEncoding, TpcReader

    fd, path = tempfile.mkstemp(suffix=".tpc")
    try:
        os.close(fd)
        _make_minimal_tpc(path, width=1, height=1)
        reader = TpcReader(path)
        image = reader.load()
        reader.reader.file.close()  # release handle so Windows can unlink
        assert image.w == 1 and image.h == 1
        assert reader.encoding == TpcEncoding.GRAYSCALE
        assert len(image.pixels) == 1 * 1 * 4
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_tpc_reader_dimensions_8x8():
    """TpcReader reports correct dimensions and pixel count for 8x8 grayscale."""
    from io_scene_kotor.format.tpc.reader import TpcEncoding, TpcReader

    fd, path = tempfile.mkstemp(suffix=".tpc")
    try:
        os.close(fd)
        _make_minimal_tpc(path, width=8, height=8)
        reader = TpcReader(path)
        image = reader.load()
        reader.reader.file.close()  # release handle so Windows can unlink
        assert image.w == 8 and image.h == 8
        assert reader.encoding == TpcEncoding.GRAYSCALE
        assert len(image.pixels) == 8 * 8 * 4
    finally:
        if os.path.exists(path):
            os.unlink(path)
