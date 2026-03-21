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


class KB_OT_select_game_installation(bpy.types.Operator, ImportHelper):
    bl_idname = "kb.select_game_installation"
    bl_label = "Select Game Installation"
    bl_description = "Select the KotOR game installation directory"

    filename_ext = ""
    filter_glob: bpy.props.StringProperty(default="", options={"HIDDEN"})

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not self.filepath:
            self.report({"ERROR"}, "No path selected")
            return {"CANCELLED"}

        # ImportHelper gives us a file path, but we need a directory
        directory = (
            os.path.dirname(self.filepath) if os.path.isfile(self.filepath) else self.filepath
        )

        scene: bpy.types.Scene = context.scene
        kb = getattr(scene, "kb", None)
        if kb is None:
            self.report({"ERROR"}, "Scene.kb is None")
            return {"CANCELLED"}
        kb.game_installation_path = directory
        self.report({"INFO"}, f"Game installation path set to: {directory}")

        return {"FINISHED"}
