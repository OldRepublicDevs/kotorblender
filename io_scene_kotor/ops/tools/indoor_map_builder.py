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

from ...vendor.pykotor_adapter import is_pykotor_available


class KB_OT_indoor_map_builder(bpy.types.Operator):
    bl_idname = "kb.indoor_map_builder"
    bl_label = "Indoor Map Builder"
    bl_description = (
        "Full indoor map tools are not in Blender yet — import LYT, edit walkmeshes, and use "
        "Scene → KotOR Game Installation → Area edit flag for upcoming gizmos. "
        "Use HolocronToolset for full area GIT/VIS editing if needed"
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not is_pykotor_available():
            self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            "Indoor Map Builder: import LYT here; Scene props → Area edit flag for future use. "
            "See operator tooltip for details.",
        )
        return {"FINISHED"}
