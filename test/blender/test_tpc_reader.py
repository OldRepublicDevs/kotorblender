"""
test_tpc_reader.py – Blender background-mode test (TPC format)

Ports equivalent behaviour of PyKotor test_texture_loader_core: verifies TPC
reader can load a minimal uncompressed texture and produce expected dimensions.

Run with:
    blender --background --python test/blender/test_tpc_reader.py
"""

from __future__ import annotations

import os
import struct
import sys
import tempfile

# Path setup before io_scene_kotor (no bpy for TpcReader - it only uses BinaryReader)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)


def _make_minimal_tpc(path: str, width: int = 2, height: int = 2) -> None:
    """Write a minimal valid KotOR TPC: uncompressed grayscale."""
    # Reader uses: uint32(4) + skip(4) + uint16(2) + uint16(2) + uint8(1) + uint8(1) = 14, then seek(128)
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
        ok = (
            image.w == 4
            and image.h == 4
            and reader.encoding == TpcEncoding.GRAYSCALE
            and len(image.pixels) == 4 * 4 * 4  # RGBA floats
        )
        if ok:
            print("  PASS test_tpc_reader_minimal_uncompressed_grayscale")
        else:
            print(
                f"  FAIL test_tpc_reader_minimal_uncompressed_grayscale: w={image.w} h={image.h} encoding={reader.encoding}"
            )
        return ok
    except Exception as e:
        print(f"  FAIL test_tpc_reader_minimal_uncompressed_grayscale: {e.__class__.__name__}: {e}")
        return False
    finally:
        try:
            if os.path.exists(path):
                os.unlink(path)
        except OSError:
            pass


def test_tpc_reader_dimensions_1x1():
    """TpcReader reports correct dimensions and pixel count for 1x1 grayscale."""
    from io_scene_kotor.format.tpc.reader import TpcEncoding, TpcReader

    fd, path = tempfile.mkstemp(suffix=".tpc")
    try:
        os.close(fd)
        _make_minimal_tpc(path, width=1, height=1)
        reader = TpcReader(path)
        image = reader.load()
        ok = (
            image.w == 1
            and image.h == 1
            and reader.encoding == TpcEncoding.GRAYSCALE
            and len(image.pixels) == 1 * 1 * 4
        )
        if ok:
            print("  PASS test_tpc_reader_dimensions_1x1")
        else:
            print(
                f"  FAIL test_tpc_reader_dimensions_1x1: w={image.w} h={image.h} pixels={len(image.pixels)}"
            )
        return ok
    except Exception as e:
        print(f"  FAIL test_tpc_reader_dimensions_1x1: {e.__class__.__name__}: {e}")
        return False
    finally:
        try:
            if os.path.exists(path):
                os.unlink(path)
        except OSError:
            pass


def test_tpc_reader_dimensions_8x8():
    """TpcReader reports correct dimensions and pixel count for 8x8 grayscale."""
    from io_scene_kotor.format.tpc.reader import TpcEncoding, TpcReader

    fd, path = tempfile.mkstemp(suffix=".tpc")
    try:
        os.close(fd)
        _make_minimal_tpc(path, width=8, height=8)
        reader = TpcReader(path)
        image = reader.load()
        ok = (
            image.w == 8
            and image.h == 8
            and reader.encoding == TpcEncoding.GRAYSCALE
            and len(image.pixels) == 8 * 8 * 4
        )
        if ok:
            print("  PASS test_tpc_reader_dimensions_8x8")
        else:
            print(
                f"  FAIL test_tpc_reader_dimensions_8x8: w={image.w} h={image.h} pixels={len(image.pixels)}"
            )
        return ok
    except Exception as e:
        print(f"  FAIL test_tpc_reader_dimensions_8x8: {e.__class__.__name__}: {e}")
        return False
    finally:
        try:
            if os.path.exists(path):
                os.unlink(path)
        except OSError:
            pass


def run_tests():
    print("\n=== test_tpc_reader.py ===")
    results = [
        test_tpc_reader_minimal_uncompressed_grayscale(),
        test_tpc_reader_dimensions_1x1(),
        test_tpc_reader_dimensions_8x8(),
    ]
    passed = sum(results)
    total = len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_tpc_reader.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
