"""
Unit tests for io_scene_kotor.game_install_detect (no Blender).

Run: pytest test/unit/test_game_install_detect.py -v
"""

from __future__ import annotations

import logging
import os
import tempfile


def test_is_probable_kotor1_empty_path() -> None:
    from io_scene_kotor.game_install_detect import is_probable_kotor1_install

    assert is_probable_kotor1_install("") is False
    assert is_probable_kotor1_install("   ") is False


def test_is_probable_kotor1_requires_chitin() -> None:
    from io_scene_kotor.game_install_detect import is_probable_kotor1_install

    with tempfile.TemporaryDirectory() as d:
        assert is_probable_kotor1_install(d) is False


def test_is_probable_kotor1_rejects_swkotor2_exe() -> None:
    from io_scene_kotor.game_install_detect import is_probable_kotor1_install

    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "chitin.key"), "wb").close()
        open(os.path.join(d, "swkotor2.exe"), "wb").close()
        assert is_probable_kotor1_install(d) is False


def test_is_probable_kotor1_accepts_chitin_only() -> None:
    from io_scene_kotor.game_install_detect import is_probable_kotor1_install

    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "chitin.key"), "wb").close()
        assert is_probable_kotor1_install(d) is True


def test_is_probable_kotor1_rejects_kotor2_folder_name() -> None:
    from io_scene_kotor.game_install_detect import is_probable_kotor1_install

    with tempfile.TemporaryDirectory() as parent:
        d = os.path.join(parent, "My KOTOR2")
        os.makedirs(d)
        open(os.path.join(d, "chitin.key"), "wb").close()
        assert is_probable_kotor1_install(d) is False


def test_is_probable_kotor2_requires_chitin() -> None:
    from io_scene_kotor.game_install_detect import is_probable_kotor2_install

    with tempfile.TemporaryDirectory() as d:
        assert is_probable_kotor2_install(d) is False


def test_is_probable_kotor2_chitin_plus_exe() -> None:
    from io_scene_kotor.game_install_detect import is_probable_kotor2_install

    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "chitin.key"), "wb").close()
        open(os.path.join(d, "swkotor2.exe"), "wb").close()
        assert is_probable_kotor2_install(d) is True


def test_is_probable_kotor2_name_tslp() -> None:
    from io_scene_kotor.game_install_detect import is_probable_kotor2_install

    with tempfile.TemporaryDirectory() as parent:
        d = os.path.join(parent, "Game tsl")
        os.makedirs(d)
        open(os.path.join(d, "chitin.key"), "wb").close()
        assert is_probable_kotor2_install(d) is True


def test_parse_steam_library_folders_reads_path() -> None:
    from io_scene_kotor.game_install_detect import _parse_steam_library_folders

    log = logging.getLogger("test_kotor_detect")
    with tempfile.TemporaryDirectory() as lib_root:
        steamapps = os.path.join(lib_root, "steamapps")
        os.makedirs(steamapps)
        vdf = os.path.join(tempfile.gettempdir(), f"kb_test_lib_{os.getpid()}.vdf")
        try:
            escaped = lib_root.replace("\\", "\\\\")
            with open(vdf, "w", encoding="utf-8") as f:
                f.write(f'"libraryfolders"\n{{\n"0"\n{{\n"path"\t\t"{escaped}"\n}}\n}}\n')
            dirs = _parse_steam_library_folders(vdf, log)
            assert steamapps in dirs or os.path.normpath(steamapps) in [os.path.normpath(x) for x in dirs]
        finally:
            if os.path.isfile(vdf):
                os.unlink(vdf)
