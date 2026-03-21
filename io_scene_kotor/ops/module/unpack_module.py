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

from ...vendor.pykotor_adapter import is_pykotor_available, list_erf_mod_resources
from .resource_helpers import write_bytes_to_filepath


class KB_OT_unpack_module(bpy.types.Operator, ImportHelper):
    bl_idname = "kb.unpack_module"
    bl_label = "Unpack Module"
    bl_description = "Extract all resources from a .mod / .erf / .rim into a folder next to the archive"

    filename_ext = ".mod"
    filter_glob: bpy.props.StringProperty(default="*.mod;*.erf;*.rim", options={"HIDDEN"})

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not is_pykotor_available():
            self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
            return {"CANCELLED"}

        fp = self.filepath
        if not fp or not os.path.isfile(fp):
            self.report({"ERROR"}, "No valid archive selected.")
            return {"CANCELLED"}

        base = os.path.splitext(os.path.basename(fp))[0]
        out_dir = os.path.join(os.path.dirname(os.path.abspath(fp)), f"{base}_unpacked")
        n = 0
        try:
            for resref, ext, data in list_erf_mod_resources(fp):
                name = f"{resref}.{ext}"
                write_bytes_to_filepath(data, os.path.join(out_dir, name))
                n += 1
        except Exception as e:
            self.report({"ERROR"}, f"Unpack failed: {e}")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Unpacked {n} file(s) to {out_dir}")
        return {"FINISHED"}
