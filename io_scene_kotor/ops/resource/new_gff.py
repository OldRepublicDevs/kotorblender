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

from ...format.gff.writer import GffWriter
from ...vendor.pykotor_adapter import convert_tree_to_pykotor_gff, get_use_pykotor_readers, is_pykotor_available, save_gff_via_pykotor


class KB_OT_new_gff(bpy.types.Operator, ExportHelper):
    bl_idname = "kb.new_gff"
    bl_label = "New GFF File"
    bl_description = "Create a new KotOR GFF file with empty root struct"

    filename_ext = ".gff"
    filter_glob: bpy.props.StringProperty(default="*.gff", options={"HIDDEN"})

    def execute(self, context: bpy.types.Context) -> set[str]:
        if os.path.exists(self.filepath):
            self.report({"WARNING"}, f"File already exists: {self.filepath}")

        # Create empty GFF tree
        tree = {
            "_type": 0xFFFFFFFF,
            "_fields": {},
        }

        # Infer file type from filename
        file_type = os.path.splitext(os.path.basename(self.filepath))[0].upper()[:4]
        if len(file_type) < 4:
            file_type = "GFF "

        # Save using PyKotor or current writer
        if get_use_pykotor_readers() and is_pykotor_available():
            pykotor_gff = convert_tree_to_pykotor_gff(tree, file_type)
            if pykotor_gff:
                if save_gff_via_pykotor(pykotor_gff, self.filepath):
                    self.report({"INFO"}, f"Created new GFF file: {self.filepath}")
                    return {"FINISHED"}
            # Fallback to current writer
            try:
                saver = GffWriter(tree, self.filepath, file_type)
                saver.save()
                self.report({"INFO"}, f"Created new GFF file: {self.filepath}")
                return {"FINISHED"}
            except Exception as e:
                self.report({"ERROR"}, f"Failed to create GFF (PyKotor and fallback failed): {e}")
                return {"CANCELLED"}
        else:
            # Use current writer
            try:
                saver = GffWriter(tree, self.filepath, file_type)
                saver.save()
                self.report({"INFO"}, f"Created new GFF file: {self.filepath}")
                return {"FINISHED"}
            except Exception as e:
                self.report({"ERROR"}, f"Failed to create GFF: {e}")
                return {"CANCELLED"}
