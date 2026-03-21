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
from ..utils import find_objects, is_mdl_root


class KB_OT_rebuild_all_materials(bpy.types.Operator):
    bl_idname: ClassVar[str] = "kb.rebuild_all_materials"
    bl_label: ClassVar[str] = "Rebuild All Materials"
    bl_description: ClassVar[str] = "Rebuild materials for all meshes in the selected KotOR model"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj: bpy.types.Object | None = context.object
        if obj is None or not is_mdl_root(obj):
            cls.poll_message_set(context, "Select a KotOR model object")
            return False
        return True

    def execute(self, context: bpy.types.Context) -> set[str]:
        root: bpy.types.Object | None = context.object
        if root is None:
            self.report({"ERROR"}, "No object selected")
            return {"CANCELLED"}

        def is_rebuild_target(o: bpy.types.Object) -> bool:
            if o.type != "MESH":
                return False
            kb = getattr(o, "kb", None)
            if kb is None:
                return False
            return kb.meshtype not in (MeshType.EMITTER,)

        objects = find_objects(root, is_rebuild_target)
        for obj in objects:
            material.rebuild_object_materials(obj)
        return {"FINISHED"}
