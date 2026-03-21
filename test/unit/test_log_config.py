"""
Unit tests for io_scene_kotor.log_config (no bpy in exercised paths).

Run: pytest test/unit/test_log_config.py -v
"""

from __future__ import annotations

import logging


def test_verbosity_string_to_level_known() -> None:
    from io_scene_kotor.log_config import verbosity_string_to_level

    assert verbosity_string_to_level("DISABLED") == 100
    assert verbosity_string_to_level("ERROR") == logging.ERROR
    assert verbosity_string_to_level("WARNING") == logging.WARNING
    assert verbosity_string_to_level("INFO") == logging.INFO
    assert verbosity_string_to_level("DEBUG") == logging.DEBUG


def test_verbosity_string_to_level_case_insensitive() -> None:
    from io_scene_kotor.log_config import verbosity_string_to_level

    assert verbosity_string_to_level("debug") == logging.DEBUG


def test_verbosity_string_to_level_unknown_defaults_info() -> None:
    from io_scene_kotor.log_config import verbosity_string_to_level

    assert verbosity_string_to_level("nosuch") == logging.INFO
    assert verbosity_string_to_level("") == logging.INFO


def test_get_kb_logger_names() -> None:
    from io_scene_kotor.log_config import PACKAGE_ROOT_LOGGER, get_kb_logger

    assert get_kb_logger("").name == PACKAGE_ROOT_LOGGER
    assert get_kb_logger("mdl").name == f"{PACKAGE_ROOT_LOGGER}.mdl"


def test_configure_package_logging_sets_level() -> None:
    from io_scene_kotor import log_config as lc

    lc.configure_package_logging(logging.WARNING)
    root = logging.getLogger(lc.PACKAGE_ROOT_LOGGER)
    assert root.level == logging.WARNING
