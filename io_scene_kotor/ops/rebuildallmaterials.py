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
        if not context.object or not is_mdl_root(context.object):
            cls.poll_message_set(context, "Select a KotOR model object")
            return False
        return True

    def execute(self, context: bpy.types.Context) -> set[str]:
        objects = find_objects(
            context.object,
            lambda obj: obj.type == "MESH" and obj.kb.meshtype not in [MeshType.EMITTER],
        )
        for obj in objects:
            material.rebuild_object_materials(obj)
        return {"FINISHED"}
