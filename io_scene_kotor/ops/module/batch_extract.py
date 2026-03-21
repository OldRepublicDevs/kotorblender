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

from ...constants import ResourceStorage
from ...vendor.pykotor_adapter import is_pykotor_available
from .resource_helpers import resource_entry_bytes, write_bytes_to_filepath


class KB_OT_batch_extract_resources(bpy.types.Operator):
    bl_idname = "kb.batch_extract_resources"
    bl_label = "Batch Extract Resources"
    bl_description = "Extract all resources marked for batch in the list to a folder"

    dest_directory: bpy.props.StringProperty(
        name="Output Folder",
        subtype="DIR_PATH",
        description="Directory to write files into",
        default="",
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: bpy.types.Context) -> None:
        self.layout.prop(self, "dest_directory")

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not is_pykotor_available():
            self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
            return {"CANCELLED"}

        dest = (self.dest_directory or "").strip()
        if not dest or not os.path.isdir(dest):
            self.report({"ERROR"}, "Choose a valid output folder.")
            return {"CANCELLED"}

        scene = context.scene
        kb = scene.kb
        n_ok = 0
        n_fail = 0
        for entry in kb.resource_list:
            if not entry.bulk_select:
                continue
            fname = f"{entry.resref}.{entry.restype_ext}".strip(".")
            out_path = os.path.join(dest, fname)
            try:
                if (
                    entry.storage == ResourceStorage.LOOSE
                    and entry.loose_path
                    and os.path.isfile(entry.loose_path)
                ):
                    shutil.copy2(entry.loose_path, out_path)
                else:
                    data = resource_entry_bytes(entry)
                    if not data:
                        n_fail += 1
                        continue
                    write_bytes_to_filepath(data, out_path)
                n_ok += 1
            except OSError:
                n_fail += 1

        self.report({"INFO"}, f"Batch extract: {n_ok} ok, {n_fail} failed.")
        return {"FINISHED"}
