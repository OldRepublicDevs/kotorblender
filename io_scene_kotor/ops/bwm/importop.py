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
from bpy_extras.io_utils import ImportHelper

from ...constants import ImportOptions
from ...io import bwm
from ...utils import logger


class KB_OT_import_bwm(bpy.types.Operator, ImportHelper):
    bl_idname = "kb.bwmimport"
    bl_label = "Import KotOR Walkmesh"
    bl_description = (
        "Import a KotOR binary walkmesh (.wok area, .pwk placeable, .dwk door). "
        "Root objects are not parented to an MDL; parent them under a model root before "
        "export if you need walkmeshes in the same MDL file. "
        "Full door walkmesh sets (0/1/2 .dwk) are still loaded together via KotOR Model import."
    )
    bl_options = {"UNDO"}

    filename_ext = ".wok"

    filter_glob: bpy.props.StringProperty(default="*.wok;*.pwk;*.dwk", options={"HIDDEN"})

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        if self.filepath:
            return self.execute(context)
        return ImportHelper.invoke(self, context, event)

    def execute(self, context: bpy.types.Context) -> set[str]:
        options = ImportOptions()
        options.import_geometry = True
        options.import_animations = False
        options.import_walkmeshes = True
        options.build_armature = False
        try:
            bwm.load_bwm(self, self.filepath, options)
        except Exception as e:
            logger().exception(f"Error loading walkmesh [{self.filepath}]")
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}
        return {"FINISHED"}
