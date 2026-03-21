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

from ....constants import Direction, PropertyName


class KB_PT_light(bpy.types.Panel):
    bl_label = "Light"
    bl_parent_id = "KB_PT_modelnode"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj: bpy.types.Object | None = context.object
        return obj is not None and obj.type == "LIGHT"

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
        row.prop(kb, PropertyName.LIGHTPRIORITY)
        row = layout.row()
        row.prop(kb, PropertyName.RADIUS)
        row = layout.row()
        row.prop(kb, PropertyName.MULTIPLIER)
        row = layout.row()
        row.prop(kb, PropertyName.DYNAMICTYPE)
        row = layout.row()
        col = row.column(align=True)
        col.prop(kb, PropertyName.AMBIENTONLY)
        col.prop(kb, PropertyName.AFFECTDYNAMIC)
        col.prop(kb, PropertyName.SHADOW)
        col.prop(kb, PropertyName.FADINGLIGHT)
        col.prop(kb, PropertyName.LENSFLARES)
        col.prop(kb, PropertyName.NEGATIVELIGHT)


class KB_PT_light_lens_flares(bpy.types.Panel):
    bl_label = "Lens Flares"
    bl_parent_id = "KB_PT_light"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj: bpy.types.Object | None = context.object
        if obj is None:
            return False
        kb = getattr(obj, "kb", None)
        if kb is None:
            return False
        return obj.type == "LIGHT" and kb.lensflares

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
        row.prop(kb, PropertyName.FLARERADIUS, text="Radius")
        row = layout.row()
        row.template_list(
            "KB_UL_lens_flares",
            "lens_flares",
            kb,
            "flare_list",
            kb,
            "flare_list_idx",
        )
        col = row.column(align=True)
        col.operator("kb.add_lens_flare", icon="ADD", text="")
        col.operator("kb.delete_lens_flare", icon="REMOVE", text="")
        col.separator()
        col.operator("kb.move_lens_flare", icon="TRIA_UP", text="").direction = Direction.UP
        col.operator("kb.move_lens_flare", icon="TRIA_DOWN", text="").direction = Direction.DOWN

        if kb.flare_list_idx >= 0 and kb.flare_list_idx < len(kb.flare_list):
            flare = kb.flare_list[kb.flare_list_idx]
            row = layout.row()
            row.prop(flare, "texture")
            row = layout.row()
            row.prop(flare, "colorshift")
            row = layout.row()
            row.prop(flare, "size")
            row = layout.row()
            row.prop(flare, "position")
