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

from typing import ClassVar

import bpy

from ..constants import MeshType
from ..scene import material


class KB_OT_rebuild_material(bpy.types.Operator):
    bl_idname: ClassVar[str] = "kb.rebuild_material"
    bl_label: ClassVar[str] = "Rebuild Material"
    bl_description: ClassVar[str] = (
        "Rebuild the material for the selected mesh (textures, lightmap, shader graph)"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj: bpy.types.Object | None = context.object
        if obj is None:
            cls.poll_message_set(context, "Select an object")
            return False
        if obj.type != "MESH":
            cls.poll_message_set(context, "Select a mesh object")
            return False
        kb = getattr(obj, "kb", None)
        if kb is None:
            return False
        if kb.meshtype == MeshType.EMITTER:
            cls.poll_message_set(context, "Cannot rebuild material on emitter mesh")
            return False
        return True

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj: bpy.types.Object | None = context.object
        if obj is None:
            self.report({"ERROR"}, "No object selected")
            return {"CANCELLED"}
        material.rebuild_object_materials(obj)
        return {"FINISHED"}
