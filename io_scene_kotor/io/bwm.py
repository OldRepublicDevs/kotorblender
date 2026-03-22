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

"""Standalone binary walkmesh (BWM) import: .wok, .pwk, .dwk."""

from __future__ import annotations

import os

import bpy

from ..constants import ImportOptions
from ..diagnostic_log import begin_io_file_span, end_io_file_span
from ..log_config import get_kb_logger
from ..format.bwm.reader import BwmReader
from ..utils import kotor_addon_preferences, semicolon_separated_to_absolute_paths


def load_bwm(
    operator: bpy.types.Operator,
    filepath: str,
    options: ImportOptions,
) -> None:
    span = begin_io_file_span(get_kb_logger("io.bwm"), "load_bwm", filepath)
    err = False
    try:
        _load_bwm_body(operator, filepath, options)
    except BaseException:
        err = True
        raise
    finally:
        end_io_file_span(span, error=err)


def _load_bwm_body(
    operator: bpy.types.Operator,
    filepath: str,
    options: ImportOptions,
) -> None:
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Walkmesh file not found: {filepath}")

    stem = os.path.splitext(os.path.basename(filepath))[0]
    operator.report({"INFO"}, f"Loading walkmesh from '{filepath}'")

    if not options.texture_search_paths or not options.lightmap_search_paths:
        try:
            addon_preferences = kotor_addon_preferences()
            if addon_preferences is not None:
                working_dir = os.path.dirname(filepath)
                if not options.texture_search_paths:
                    options.texture_search_paths = semicolon_separated_to_absolute_paths(
                        addon_preferences.texture_search_paths,
                        working_dir,
                    )
                if not options.lightmap_search_paths:
                    options.lightmap_search_paths = semicolon_separated_to_absolute_paths(
                        addon_preferences.lightmap_search_paths,
                        working_dir,
                    )
        except Exception:
            if not options.texture_search_paths:
                options.texture_search_paths = []
            if not options.lightmap_search_paths:
                options.lightmap_search_paths = []

    if not options.import_geometry:
        operator.report({"WARNING"}, "Import geometry is disabled; nothing to load")
        return

    reader = BwmReader(filepath, stem)
    walkmesh = reader.load()

    collection = bpy.context.collection
    if collection is None:
        raise ValueError("No active collection")

    walkmesh.attach_to_collection(None, collection, options)
    operator.report({"INFO"}, f"Imported walkmesh '{stem}'")
