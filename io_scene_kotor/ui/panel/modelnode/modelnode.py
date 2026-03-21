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

from ....constants import PropertyName
from ....utils import is_exported_to_mdl


class KB_PT_modelnode(bpy.types.Panel):
    bl_label = "KotOR Model Node"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj: bpy.types.Object | None = context.object
        return obj is not None and obj.type in ["EMPTY", "MESH", "LIGHT"]

    def draw(self, context: bpy.types.Context) -> None:
        obj: bpy.types.Object | None = context.object
        if obj is None:
            raise ValueError("Object is None")
        layout = self.layout
        if layout is None:
            raise ValueError("Layout is None")
        layout.use_property_split = True

        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError("Object.kb is None")

        if obj.type == "EMPTY":
            row = layout.row()
            row.prop(kb, PropertyName.DUMMYTYPE)
        elif obj.type == "MESH":
            row = layout.row()
            row.prop(kb, PropertyName.MESHTYPE)

        if is_exported_to_mdl(obj):
            row = layout.row()
            row.prop(kb, PropertyName.NODE_NUMBER)
