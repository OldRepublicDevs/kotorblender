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

from ....constants import MeshType, PropertyName
from ....utils import is_mesh_type


class KB_PT_mesh(bpy.types.Panel):
    bl_label = "Mesh"
    bl_parent_id = "KB_PT_modelnode"
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
        return obj.type == "MESH" and kb.meshtype != MeshType.EMITTER

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
        row.prop(kb, PropertyName.BITMAP)
        row = layout.row()
        row.prop(kb, PropertyName.BITMAP2)
        row = layout.row()
        row.prop(kb, PropertyName.DIFFUSE)
        row = layout.row()
        row.prop(kb, PropertyName.AMBIENT)
        row = layout.row()
        row.prop(kb, PropertyName.SELFILLUMCOLOR)
        row = layout.row()
        row.prop(kb, PropertyName.ALPHA)
        row = layout.row()
        row.prop(kb, PropertyName.TRANSPARENCYHINT)
        row = layout.row()
        col = row.column(align=True)
        col.prop(kb, PropertyName.RENDER)
        col.prop(kb, PropertyName.SHADOW)
        col.prop(kb, PropertyName.LIGHTMAPPED)
        col.prop(kb, PropertyName.TANGENTSPACE)
        col.prop(kb, PropertyName.BACKGROUND_GEOMETRY)
        col.prop(kb, PropertyName.BEAMING)
        col.prop(kb, PropertyName.ROTATETEXTURE)
        col.prop(kb, PropertyName.ANIMATEUV)

        row = layout.row()
        col = row.column(align=True, heading="TSL only")
        col.prop(kb, PropertyName.HOLOGRAM_DONOTDRAW)
        col.prop(kb, PropertyName.DIRT_ENABLED)

        row = layout.row()
        row.operator("kb.rebuild_material")


class KB_PT_mesh_uv_anim(bpy.types.Panel):
    bl_label = "UV animation"
    bl_parent_id = "KB_PT_mesh"
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
        return obj.type == "MESH" and kb.meshtype != MeshType.EMITTER and kb.animateuv

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
        col = row.column(align=True)
        col.prop(kb, "uvdirectionx", text="Direction X")
        col.prop(kb, "uvdirectiony", text="Y")
        row = layout.row()
        col = row.column(align=True)
        col.prop(kb, "uvjitter", text="Jitter Amount")
        col.prop(kb, "uvjitterspeed", text="Speed")


class KB_PT_mesh_dirt(bpy.types.Panel):
    bl_label = "Dirt"
    bl_parent_id = "KB_PT_mesh"
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
        return obj.type == "MESH" and kb.meshtype != MeshType.EMITTER and kb.dirt_enabled

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
        row.prop(kb, PropertyName.DIRT_TEXTURE)
        row = layout.row()
        row.prop(kb, PropertyName.DIRT_WORLDSPACE)


class KB_PT_mesh_dangly(bpy.types.Panel):
    bl_label = "Danglymesh"
    bl_parent_id = "KB_PT_mesh"
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
        return is_mesh_type(obj, MeshType.DANGLYMESH)

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
        row.prop_search(kb, PropertyName.CONSTRAINTS, obj, "vertex_groups", text="Constraints")
        row = layout.row()
        row.prop(kb, PropertyName.PERIOD)
        row = layout.row()
        row.prop(kb, PropertyName.TIGHTNESS)
        row = layout.row()
        row.prop(kb, PropertyName.DISPLACEMENT)


class KB_PT_mesh_aabb(bpy.types.Panel):
    bl_label = "AABB"
    bl_parent_id = "KB_PT_mesh"
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
        obj = context.object
        return is_mesh_type(obj, MeshType.AABB)

    def draw(self, context: bpy.types.Context) -> None:
        obj: bpy.types.Object | None = context.object
        if obj is None:
            raise ValueError("Object is None")
        layout = self.layout
        if layout is None:
            raise ValueError("Layout is None")
        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError("Object.kb is None")
        layout.use_property_split = True

        row = layout.row()
        row.prop(kb, PropertyName.LYTPOSITION)
