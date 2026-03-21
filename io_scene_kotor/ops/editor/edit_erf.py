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

from typing import TYPE_CHECKING

import bpy
from bpy_extras.io_utils import ImportHelper

from ...vendor.pykotor_adapter import is_pykotor_available

if TYPE_CHECKING:
    from bpy.stub_internal.rna_enums import OperatorReturnItems


class KB_OT_edit_erf(bpy.types.Operator, ImportHelper):  # pyright: ignore[reportIncompatibleMethodOverride]
    bl_idname = "kb.edit_erf"
    bl_label = "Edit ERF Archive"
    bl_description = "Edit a KotOR ERF archive file"

    filename_ext = ".erf"
    filter_glob: bpy.props.StringProperty(default="*.erf", options={"HIDDEN"})  # pyright: ignore[reportInvalidTypeForm]

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        if not is_pykotor_available():
            self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Editing ERF file: {self.filepath}")  # pyright: ignore[reportUnknownMemberType]
        return {"FINISHED"}
