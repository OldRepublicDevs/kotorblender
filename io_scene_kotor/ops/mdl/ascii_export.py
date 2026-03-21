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

from ...constants import ExportOptions
from ...io import mdl
from ...utils import logger


class KB_OT_export_ascii_mdl(bpy.types.Operator, ExportHelper):
    bl_idname = "kb.asciimdlexport"
    bl_label = "Export KotOR ASCII MDL"
    bl_description = "Export the selected KotOR model to ASCII MDL format (.mdl.ascii)"

    filename_ext = ".mdl.ascii"

    filter_glob: bpy.props.StringProperty(default="*.mdl.ascii;*.ascii", options={"HIDDEN"})

    export_animations: bpy.props.BoolProperty(name="Export Animations", default=True)

    export_walkmeshes: bpy.props.BoolProperty(
        name="Export Walkmeshes",
        description="Export area, door and placeable walkmeshes",
        default=True,
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        options = ExportOptions()
        options.export_for_tsl = False  # ASCII format doesn't support TSL/Xbox variants
        options.export_for_xbox = False
        options.export_animations = self.export_animations
        options.export_walkmeshes = self.export_walkmeshes
        options.compress_quaternions = False  # ASCII format doesn't use quaternion compression

        try:
            mdl.save_mdl(self, self.filepath, options)
        except Exception as ex:
            logger().exception(f"Error saving ASCII MDL file [{self.filepath}]")
            self.report({"ERROR"}, str(ex))

        return {"FINISHED"}
