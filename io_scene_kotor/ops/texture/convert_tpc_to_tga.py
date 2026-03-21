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

from ...format.tpc.reader import TpcReader
from ...vendor.pykotor_adapter import convert_pykotor_tpc_to_tpcimage, get_use_pykotor_readers, is_pykotor_available, load_tpc_via_pykotor


class KB_OT_convert_tpc_to_tga(bpy.types.Operator, ImportHelper):
    bl_idname = "kb.convert_tpc_to_tga"
    bl_label = "Convert TPC to TGA"
    bl_description = "Convert KotOR TPC texture to TGA format"

    filename_ext = ".tpc"
    filter_glob: bpy.props.StringProperty(default="*.tpc", options={"HIDDEN"})

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not os.path.isfile(self.filepath):
            self.report({"ERROR"}, f"File not found: {self.filepath}")
            return {"CANCELLED"}

        # Load TPC using PyKotor or current reader
        tpc_image = None
        if get_use_pykotor_readers() and is_pykotor_available():
            pykotor_tpc = load_tpc_via_pykotor(self.filepath)
            if pykotor_tpc:
                tpc_image = convert_pykotor_tpc_to_tpcimage(pykotor_tpc)
            if not tpc_image:
                # Fallback to current reader
                try:
                    tpc_image = TpcReader(self.filepath).load()
                except Exception as e:
                    self.report({"ERROR"}, f"Failed to load TPC (PyKotor and fallback failed): {e}")
                    return {"CANCELLED"}
        else:
            # Use current reader
            try:
                tpc_image = TpcReader(self.filepath).load()
            except Exception as e:
                self.report({"ERROR"}, f"Failed to load TPC: {e}")
                return {"CANCELLED"}

        if not tpc_image:
            self.report({"ERROR"}, "Failed to load TPC file")
            return {"CANCELLED"}

        # Create Blender image from TpcImage
        temp_name = os.path.basename(self.filepath)[:-4]  # Remove .tpc extension
        image = bpy.data.images.new(temp_name, tpc_image.w, tpc_image.h)
        image.pixels = tpc_image.pixels
        image.update()

        # Save as TGA
        tga_path = self.filepath[:-4] + ".tga"
        image.filepath = tga_path
        image.file_format = "TARGA"
        image.save()

        # Clean up temporary image
        bpy.data.images.remove(image)

        self.report({"INFO"}, f"Converted TPC to TGA: {tga_path}")
        return {"FINISHED"}
