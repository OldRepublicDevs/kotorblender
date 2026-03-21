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

from ...constants import PropertyName
from ...utils import is_mdl_root


class KB_PT_model(bpy.types.Panel):
    bl_label = "KotOR Model"
    bl_description = "Root MDL object settings: classification, supermodel, fog, and export-related options"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return is_mdl_root(context.object)

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

        row = layout.row()
        row.prop(kb, PropertyName.CLASSIFICATION)
        row = layout.row()
        row.prop(kb, PropertyName.SUPERMODEL)
        row = layout.row()
        row.prop(kb, PropertyName.ANIMSCALE)
        row = layout.row()
        row.prop_search(kb, PropertyName.ANIMROOT, context.collection, "objects")
        row = layout.row()
        row.prop(kb, PropertyName.AFFECTED_BY_FOG)

        row = layout.row()
        row.operator("kb.rebuild_all_materials")
