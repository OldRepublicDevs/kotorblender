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

from __future__ import annotations

import os

import bpy
from bpy_extras.io_utils import ImportHelper


def _find_text_editor_area(context: bpy.types.Context) -> bpy.types.SpaceTextEditor | None:
    """Return the first TEXT_EDITOR space found in any window, or None.

    Args:
        context: Blender context

    Returns:
        First TEXT_EDITOR space found, or None if no text editor area exists
    """
    for win in context.window_manager.windows:
        for area in win.screen.areas:
            if area.type != "TEXT_EDITOR":
                continue
            for space in area.spaces:
                if space.type == "TEXT_EDITOR":
                    return space
    return None


class KB_OT_edit_nss(bpy.types.Operator, ImportHelper):
    bl_idname = "kb.edit_nss"
    bl_label = "Edit Script"
    bl_description = "Open a KotOR Script (NSS) file in the Blender Text Editor"

    filename_ext = ".nss"
    filter_glob: bpy.props.StringProperty(default="*.nss", options={"HIDDEN"})

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not self.filepath or not os.path.isfile(self.filepath):
            self.report({"ERROR"}, "No valid NSS file path")
            return {"CANCELLED"}
        try:
            text_block = bpy.data.texts.load(self.filepath, internal=False)
        except Exception as ex:
            self.report({"ERROR"}, f"Failed to load NSS file: {ex}")
            return {"CANCELLED"}
        space = _find_text_editor_area(context)
        if space is not None:
            space.text = text_block
        self.report({"INFO"}, f"Opened NSS in Text Editor: {os.path.basename(self.filepath)}")
        return {"FINISHED"}
