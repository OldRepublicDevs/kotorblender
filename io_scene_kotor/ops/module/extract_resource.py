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
import shutil

import bpy
from bpy_extras.io_utils import ExportHelper

from ...constants import ResourceStorage
from ...vendor.pykotor_adapter import is_pykotor_available
from .resource_helpers import resource_entry_bytes, write_bytes_to_filepath


class KB_OT_extract_resource(bpy.types.Operator, ExportHelper):
    bl_idname = "kb.extract_resource"
    bl_label = "Extract Selected Resource"
    bl_description = "Extract the selected resource to disk (choose output folder + filename)"

    filename_ext = ""
    filter_glob: bpy.props.StringProperty(default="*.*", options={"HIDDEN"})

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        scene = context.scene
        kb = scene.kb
        if kb.resource_list_idx < 0 or kb.resource_list_idx >= len(kb.resource_list):
            self.report({"ERROR"}, "No resource selected")
            return {"CANCELLED"}
        entry = kb.resource_list[kb.resource_list_idx]
        ext = entry.restype_ext or "dat"
        self.filename_ext = "." + ext.lstrip(".")
        base = entry.resref or "resource"
        self.filepath = base + self.filename_ext
        return ExportHelper.invoke(self, context, event)

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene = context.scene
        kb = scene.kb

        if kb.resource_list_idx < 0 or kb.resource_list_idx >= len(kb.resource_list):
            self.report({"ERROR"}, "No resource selected")
            return {"CANCELLED"}

        if not is_pykotor_available():
            self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
            return {"CANCELLED"}

        entry = kb.resource_list[kb.resource_list_idx]

        if (
            entry.storage == ResourceStorage.LOOSE
            and entry.loose_path
            and os.path.isfile(entry.loose_path)
        ):
            try:
                shutil.copy2(entry.loose_path, self.filepath)
            except OSError as e:
                self.report({"ERROR"}, f"Copy failed: {e}")
                return {"CANCELLED"}
            self.report({"INFO"}, f"Copied to {self.filepath}")
            return {"FINISHED"}

        data = resource_entry_bytes(entry)
        if not data:
            self.report({"ERROR"}, "Could not read resource data.")
            return {"CANCELLED"}
        try:
            write_bytes_to_filepath(data, self.filepath)
        except OSError as e:
            self.report({"ERROR"}, f"Write failed: {e}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Wrote {self.filepath}")
        return {"FINISHED"}
