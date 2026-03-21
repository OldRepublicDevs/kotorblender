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

"""Drag-and-drop file handlers for KotOR formats.

When users drag .mdl, .lyt, .pth, .wok, .pwk, .dwk, or .mdl.ascii files onto the 3D View (or
Outliner in ViewLayer mode), Blender invokes the corresponding import
operator with the dropped file path. Requires Blender 3.2+ (FileHandler API).
"""

from __future__ import annotations

import bpy
from bpy_extras.io_utils import poll_file_object_drop


class KB_FH_import_mdl(bpy.types.FileHandler):
    """FileHandler for KotOR binary model (.mdl). Drag-and-drop onto 3D View or Outliner."""

    bl_idname = "KB_FH_import_mdl"
    bl_label = "KotOR Model (.mdl) drag-and-drop"
    bl_import_operator = "kb.mdlimport"
    bl_file_extensions = ".mdl"

    @classmethod
    def poll_drop(cls, context: bpy.types.Context) -> bool:
        return poll_file_object_drop(context)


class KB_FH_import_ascii_mdl(bpy.types.FileHandler):
    """FileHandler for KotOR ASCII model (.mdl.ascii). Drag-and-drop onto 3D View or Outliner."""

    bl_idname = "KB_FH_import_ascii_mdl"
    bl_label = "KotOR ASCII Model (.mdl.ascii) drag-and-drop"
    bl_import_operator = "kb.asciimdlimport"
    bl_file_extensions = ".mdl.ascii;.ascii"

    @classmethod
    def poll_drop(cls, context: bpy.types.Context) -> bool:
        return poll_file_object_drop(context)


class KB_FH_import_lyt(bpy.types.FileHandler):
    """FileHandler for KotOR layout (.lyt). Drag-and-drop onto 3D View or Outliner."""

    bl_idname = "KB_FH_import_lyt"
    bl_label = "KotOR Layout (.lyt) drag-and-drop"
    bl_import_operator = "kb.lytimport"
    bl_file_extensions = ".lyt"

    @classmethod
    def poll_drop(cls, context: bpy.types.Context) -> bool:
        return poll_file_object_drop(context)


class KB_FH_import_pth(bpy.types.FileHandler):
    """FileHandler for KotOR path (.pth). Drag-and-drop onto 3D View or Outliner."""

    bl_idname = "KB_FH_import_pth"
    bl_label = "KotOR Path (.pth) drag-and-drop"
    bl_import_operator = "kb.pthimport"
    bl_file_extensions = ".pth"

    @classmethod
    def poll_drop(cls, context: bpy.types.Context) -> bool:
        return poll_file_object_drop(context)


class KB_FH_import_bwm(bpy.types.FileHandler):
    """FileHandler for KotOR walkmesh (.wok, .pwk, .dwk). Drag-and-drop onto 3D View or Outliner."""

    bl_idname = "KB_FH_import_bwm"
    bl_label = "KotOR Walkmesh (.wok/.pwk/.dwk) drag-and-drop"
    bl_import_operator = "kb.bwmimport"
    bl_file_extensions = ".wok;.pwk;.dwk"

    @classmethod
    def poll_drop(cls, context: bpy.types.Context) -> bool:
        return poll_file_object_drop(context)


# Tuple of all file handlers for registration
FILE_HANDLER_CLASSES = (
    KB_FH_import_mdl,
    KB_FH_import_ascii_mdl,
    KB_FH_import_lyt,
    KB_FH_import_pth,
    KB_FH_import_bwm,
)
