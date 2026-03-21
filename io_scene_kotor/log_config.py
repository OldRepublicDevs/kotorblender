# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""Central logging for KotorBlender.

* One package root logger: ``io_scene_kotor`` (non-propagating) with a single
  :class:`logging.StreamHandler` on ``stderr`` (Blender system console).
* Child loggers via :func:`get_kb_logger` — no per-module handlers.
* Level is driven by **Add-on Preferences → Logging verbosity**.
* Third-party ``pykotor.*`` loggers follow the same preference (DEBUG/INFO vs WARNING;
  disabled when logging is off) without attaching extra handlers—see Python logging
  HOWTO (hierarchy, propagation, avoid duplicate handlers on reload).

Blender background mode and GUI both show stderr in the system console / terminal
when launched from one.
"""

from __future__ import annotations

import logging
import sys
from typing import Final

PACKAGE_ROOT_LOGGER: Final[str] = "io_scene_kotor"

# Above CRITICAL (50) so nothing is emitted when user chooses Off.
_LEVEL_DISABLED: Final[int] = 100

_LEVEL_BY_VERBOSITY: dict[str, int] = {
    "DISABLED": _LEVEL_DISABLED,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}

_stderr_handler: logging.StreamHandler | None = None


def _sync_pykotor_library_loggers(level: int) -> None:
    """Align bundled PyKotor loggers with add-on verbosity (no extra handlers)."""
    names = ("pykotor", "pykotor.extract", "pykotor.extract.installation")
    if level >= _LEVEL_DISABLED:
        for name in names:
            logging.getLogger(name).disabled = True
        return
    for name in names:
        lg = logging.getLogger(name)
        lg.disabled = False
        if level <= logging.DEBUG:
            lg.setLevel(logging.DEBUG)
        elif level <= logging.INFO:
            lg.setLevel(logging.INFO)
        else:
            lg.setLevel(logging.WARNING)


def _ensure_stderr_handler(root: logging.Logger) -> None:
    global _stderr_handler
    if _stderr_handler is None:
        _stderr_handler = logging.StreamHandler(sys.stderr)
        _stderr_handler.setFormatter(
            logging.Formatter(
                fmt="[%(levelname)s] %(name)s | %(message)s",
            )
        )
    if _stderr_handler not in root.handlers:
        root.addHandler(_stderr_handler)


def configure_package_logging(level: int) -> None:
    """Configure the ``io_scene_kotor`` root logger level and stderr handler."""
    root = logging.getLogger(PACKAGE_ROOT_LOGGER)
    root.setLevel(level)
    root.propagate = False
    if level <= logging.CRITICAL:
        _ensure_stderr_handler(root)
    _sync_pykotor_library_loggers(level)


def get_kb_logger(submodule: str = "") -> logging.Logger:
    """Return ``io_scene_kotor`` or ``io_scene_kotor.<submodule>`` logger."""
    name = PACKAGE_ROOT_LOGGER if not submodule else f"{PACKAGE_ROOT_LOGGER}.{submodule}"
    return logging.getLogger(name)


def verbosity_string_to_level(verbosity: str) -> int:
    return _LEVEL_BY_VERBOSITY.get(str(verbosity).upper(), logging.INFO)


def apply_preferences_log_level_safe() -> None:
    """Set log level from add-on preferences; default INFO if prefs missing."""
    try:
        import bpy

        from .constants import ADDON_PREFERENCE_MODULE_KEYS
    except Exception:
        configure_package_logging(logging.INFO)
        return

    prefs = None
    try:
        for key in ADDON_PREFERENCE_MODULE_KEYS:
            addon = bpy.context.preferences.addons.get(key)
            if addon is not None and getattr(addon, "preferences", None) is not None:
                prefs = addon.preferences
                break
    except Exception:
        prefs = None

    raw = getattr(prefs, "log_verbosity", None) if prefs is not None else None
    if isinstance(raw, str):
        configure_package_logging(verbosity_string_to_level(raw))
    else:
        configure_package_logging(logging.INFO)


def on_log_verbosity_updated(_prefs: object, _context: object) -> None:
    """``EnumProperty(update=...)`` hook for add-on preferences."""
    apply_preferences_log_level_safe()
