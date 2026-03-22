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

from ...constants import ResourceStorage
from ...diagnostic_log import run_simple_operator_logged
from ...log_config import get_kb_logger
from ...vendor.pykotor_adapter import is_pykotor_available
from .resource_helpers import resource_entry_bytes, temp_file_with_suffix


class KB_OT_open_resource(bpy.types.Operator):
    bl_idname = "kb.open_resource"
    bl_label = "Open Selected Resource"
    bl_description = "Open the selected resource in Blender (MDL, LYT, PTH, ASCII MDL) or the image editor (TGA/TPC as temp)"

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.module.open_resource")

        def _body() -> set[str]:
            scene = context.scene
            kb = scene.kb

            if kb.resource_list_idx < 0 or kb.resource_list_idx >= len(kb.resource_list):
                self.report({"ERROR"}, "No resource selected")
                return {"CANCELLED"}

            if not is_pykotor_available():
                self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
                return {"CANCELLED"}

            entry = kb.resource_list[kb.resource_list_idx]
            ext = (entry.restype_ext or "").lower().lstrip(".")

            # Loose path shortcut (no temp file)
            if entry.storage == ResourceStorage.LOOSE and entry.loose_path and os.path.isfile(entry.loose_path):
                path = entry.loose_path
                return self._open_path(context, path, ext)

            data = resource_entry_bytes(entry)
            if not data:
                self.report({"ERROR"}, "Could not read resource data.")
                return {"CANCELLED"}

            suffix = "." + ext if ext else ".dat"
            tmp = temp_file_with_suffix(suffix, data)
            try:
                return self._open_path(context, tmp, ext)
            finally:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

        return run_simple_operator_logged(log, "kb.open_resource", _body)

    def _open_path(self, context: bpy.types.Context, path: str, ext: str) -> set[str]:
        ext = ext.lower().lstrip(".")
        try:
            if ext == "mdl":
                bpy.ops.kb.mdlimport(filepath=path)
            elif ext in {"mdl.ascii", "ascii"}:
                bpy.ops.kb.asciimdlimport(filepath=path)
            elif ext == "lyt":
                bpy.ops.kb.lytimport(filepath=path)
            elif ext == "pth":
                bpy.ops.kb.pthimport(filepath=path)
            elif ext == "tga":
                bpy.ops.image.open(filepath=path, relative_path=False)
            elif ext == "tpc":
                self.report(
                    {"INFO"},
                    "TPC: use Texture → Convert TPC to TGA, or extract to disk first.",
                )
                return {"FINISHED"}
            else:
                self.report(
                    {"INFO"},
                    f"No direct open handler for .{ext}. Use Extract Resource or a format-specific importer.",
                )
                return {"FINISHED"}
        except RuntimeError as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}
        self.report({"INFO"}, f"Opened {os.path.basename(path)}")
        return {"FINISHED"}
