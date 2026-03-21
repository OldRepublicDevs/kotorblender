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
from bpy_extras.io_utils import ExportHelper

from ...vendor.pykotor_adapter import get_use_pykotor_readers, is_pykotor_available


class KB_OT_extract_tpc(bpy.types.Operator, ExportHelper):
    bl_idname = "kb.extract_tpc"
    bl_label = "Extract TPC"
    bl_description = "Extract TPC texture files from module (requires module browser functionality)"

    filename_ext = ""
    filter_glob: bpy.props.StringProperty(default="", options={"HIDDEN"})

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not os.path.isdir(self.filepath):
            self.report({"ERROR"}, f"Directory not found: {self.filepath}")
            return {"CANCELLED"}

        # This operator requires module extraction functionality which is not yet implemented.
        # It will use PyKotor's module extraction when available.
        if not is_pykotor_available():
            self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
            return {"CANCELLED"}

        if not get_use_pykotor_readers():
            self.report(
                {"INFO"},
                "PyKotor readers not enabled. Enable USE_PYKOTOR_READERS to use module extraction.",
            )
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            f"Module TPC extraction not yet implemented. Target directory: {self.filepath}",
        )
        return {"FINISHED"}
