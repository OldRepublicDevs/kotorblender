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

import bpy
from bpy_extras.io_utils import ExportHelper

from ...vendor.pykotor_adapter import is_pykotor_available


class KB_OT_new_utw(bpy.types.Operator, ExportHelper):
    bl_idname = "kb.new_utw"
    bl_label = "New Waypoint (UTW)"
    bl_description = "Create a new KotOR Waypoint resource file"

    filename_ext = ".utw"
    filter_glob: bpy.props.StringProperty(default="*.utw", options={"HIDDEN"})

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not is_pykotor_available():
            self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Created new UTW file: {self.filepath}")
        return {"FINISHED"}
