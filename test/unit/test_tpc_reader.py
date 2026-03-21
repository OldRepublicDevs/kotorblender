"""
Unit tests for the TPC texture format reader.

No Blender (bpy) required. Uses real temp files and io_scene_kotor.format.tpc.
Run with: pytest test/unit/test_tpc_reader.py -v
"""

from __future__ import annotations

import os
import struct
import tempfile


def _tpc_header(compressed: int, width: int, height: int, encoding: int, num_mips: int) -> bytes:
    hdr = bytearray()
    hdr += struct.pack("<I", compressed)
    hdr += struct.pack("<I", 0)
    hdr += struct.pack("<HH", width, height)
    hdr += struct.pack("<BB", encoding, num_mips)
    hdr += b"\x00" * (128 - len(hdr))
    return bytes(hdr)


def _make_minimal_tpc(path: str, width: int = 2, height: int = 2) -> None:
    """Write a minimal valid KotOR TPC: uncompressed grayscale."""
    with open(path, "wb") as f:
        f.write(_tpc_header(0, width, height, 1, 1))
        f.write(b"\x00" * (width * height))  # pixel data


def test_tpc_reader_minimal_uncompressed_grayscale():
    """TpcReader loads a minimal uncompressed grayscale TPC and returns correct dimensions."""
    from io_scene_kotor.format.tpc.reader import TpcReader, TpcEncoding

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
    from io_scene_kotor.format.tpc.reader import TpcReader, TpcEncoding

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
    from io_scene_kotor.format.tpc.reader import TpcReader, TpcEncoding

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


def test_tpc_reader_uncompressed_rgb():
    """Uncompressed RGB: 2x2 single mip."""
    from io_scene_kotor.format.tpc.reader import TpcEncoding, TpcReader

    fd, path = tempfile.mkstemp(suffix=".tpc")
    try:
        os.close(fd)
        pix = bytes(range(12))  # 3 * 2 * 2
        with open(path, "wb") as f:
            f.write(_tpc_header(0, 2, 2, 2, 1))
            f.write(pix)
        reader = TpcReader(path)
        image = reader.load()
        reader.reader.file.close()
        assert reader.encoding == TpcEncoding.RGB
        assert image.w == 2 and image.h == 2
        assert len(image.pixels) == 16
        assert image.pixels[0] == 0 / 255 and image.pixels[1] == 1 / 255
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_tpc_reader_uncompressed_rgba():
    """Uncompressed RGBA 1x1."""
    from io_scene_kotor.format.tpc.reader import TpcEncoding, TpcReader

    fd, path = tempfile.mkstemp(suffix=".tpc")
    try:
        os.close(fd)
        with open(path, "wb") as f:
            f.write(_tpc_header(0, 1, 1, 4, 1))
            f.write(bytes([10, 20, 30, 200]))
        reader = TpcReader(path)
        image = reader.load()
        reader.reader.file.close()
        assert reader.encoding == TpcEncoding.RGBA
        assert image.w == 1 and image.h == 1
        assert len(image.pixels) == 4
        assert abs(image.pixels[3] - 200 / 255) < 1e-5
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_tpc_reader_two_mips_rgb():
    """RGB 2x2 with mip1 1x1 (uncompressed)."""
    from io_scene_kotor.format.tpc.reader import TpcReader

    fd, path = tempfile.mkstemp(suffix=".tpc")
    try:
        os.close(fd)
        mip0 = bytes(range(12))
        mip1 = bytes([7, 8, 9])
        with open(path, "wb") as f:
            f.write(_tpc_header(0, 2, 2, 2, 2))
            f.write(mip0 + mip1)
        reader = TpcReader(path)
        image = reader.load()
        reader.reader.file.close()
        assert image.w == 2 and image.h == 2
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_tpc_reader_cubemap_rgb_uncompressed():
    """Cubemap when h // w == 6: six faces w×w RGB."""
    from io_scene_kotor.format.tpc.reader import TpcReader

    w, h = 2, 12
    fd, path = tempfile.mkstemp(suffix=".tpc")
    try:
        os.close(fd)
        face = bytes(range(12))  # 2x2 RGB
        with open(path, "wb") as f:
            f.write(_tpc_header(0, w, h, 2, 1))
            for _ in range(6):
                f.write(face)
        reader = TpcReader(path)
        image = reader.load()
        reader.reader.file.close()
        assert image.w == w and image.h == h
        assert len(image.pixels) == w * h * 4
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_tpc_reader_trailing_txi():
    """Bytes after image payload are parsed as UTF-8 TXI lines."""
    from io_scene_kotor.format.tpc.reader import TpcReader

    fd, path = tempfile.mkstemp(suffix=".tpc")
    try:
        os.close(fd)
        txi = b"bumpmap 1\n# comment\n"
        with open(path, "wb") as f:
            f.write(_tpc_header(0, 1, 1, 1, 1))
            f.write(b"\xff")
            f.write(txi)
        reader = TpcReader(path)
        image = reader.load()
        reader.reader.file.close()
        assert image.txi_lines == ["bumpmap 1", "# comment"]
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_tpc_reader_truncated_file():
    """Shorter than 128-byte header causes load() to fail."""
    from io_scene_kotor.format.tpc.reader import TpcReader

    fd, path = tempfile.mkstemp(suffix=".tpc")
    try:
        os.close(fd)
        with open(path, "wb") as f:
            f.write(b"\x00" * 20)
        reader = TpcReader(path)
        try:
            reader.load()
        except Exception:
            reader.reader.file.close()
            return
        reader.reader.file.close()
        raise AssertionError("expected error for truncated TPC")
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_tpc_reader_compressed_dxt1_rgb_4x4():
    """Single 4×4 DXT1 (BC1) block: RGB compressed path in TpcReader."""
    import struct

    from io_scene_kotor.format.tpc.reader import TpcEncoding, TpcReader

    # One 4×4 block = 8 bytes (two RGB565 colors + 32-bit index table).
    dxt1_block = struct.pack("<HHI", 0xF800, 0x001F, 0x00000000)
    compressed_size = len(dxt1_block)
    fd, path = tempfile.mkstemp(suffix=".tpc")
    try:
        os.close(fd)
        with open(path, "wb") as f:
            f.write(_tpc_header(compressed_size, 4, 4, 2, 1))
            f.write(dxt1_block)
        reader = TpcReader(path)
        image = reader.load()
        reader.reader.file.close()
        assert reader.compressed is True
        assert reader.encoding == TpcEncoding.RGB
        assert image.w == 4 and image.h == 4
        assert len(image.pixels) == 4 * 4 * 4
    finally:
        if os.path.exists(path):
            os.unlink(path)
