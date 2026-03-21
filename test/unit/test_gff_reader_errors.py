"""
Error paths for GffReader (no Blender).

Run: pytest test/unit/test_gff_reader_errors.py -v
"""

from __future__ import annotations

import os
import tempfile


def test_gff_reader_wrong_file_type() -> None:
    from io_scene_kotor.format.gff.reader import GffReader

    fd, path = tempfile.mkstemp(suffix=".gff")
    os.close(fd)
    try:
        with open(path, "wb") as f:
            f.write(b"WRNG")
            f.write(b"V3.2")
            f.write(b"\x00" * 40)
        reader = GffReader(path, "TST ")
        try:
            reader.load()
        except RuntimeError as e:
            reader.reader.file.close()
            assert "invalid" in str(e).lower() or "expected" in str(e).lower()
            return
        reader.reader.file.close()
        raise AssertionError("expected RuntimeError")
    finally:
        if os.path.isfile(path):
            os.unlink(path)


def test_gff_reader_wrong_version() -> None:
    from io_scene_kotor.format.gff.reader import GffReader

    fd, path = tempfile.mkstemp(suffix=".gff")
    os.close(fd)
    try:
        with open(path, "wb") as f:
            f.write(b"TST ")
            f.write(b"BAD!")
            f.write(b"\x00" * 40)
        reader = GffReader(path, "TST")
        try:
            reader.load()
        except RuntimeError as e:
            reader.reader.file.close()
            assert "version" in str(e).lower()
            return
        reader.reader.file.close()
        raise AssertionError("expected RuntimeError")
    finally:
        if os.path.isfile(path):
            os.unlink(path)


def test_gff_reader_truncated() -> None:
    from io_scene_kotor.format.gff.reader import GffReader

    fd, path = tempfile.mkstemp(suffix=".gff")
    os.close(fd)
    try:
        with open(path, "wb") as f:
            f.write(b"TST ")
            f.write(b"V3.2")
            f.write(b"\x00" * 8)
        reader = GffReader(path, "TST")
        try:
            reader.load()
        except Exception:
            reader.reader.file.close()
            return
        reader.reader.file.close()
        raise AssertionError("expected error on truncated GFF")
    finally:
        if os.path.isfile(path):
            os.unlink(path)
