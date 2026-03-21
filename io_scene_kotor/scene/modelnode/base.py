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

from collections.abc import Callable

import bpy
from mathutils import Matrix, Quaternion, Vector

from ...constants import ExportOptions, ImportOptions, NodeType, RootType


class BaseNode:
    def __init__(self, name: str = "UNNAMED") -> None:
        self.nodetype: NodeType = NodeType.UNDEFINED
        self.roottype: RootType = RootType.MODEL

        self.node_number: int = -1
        self.export_order: int = 0
        self.name: str = name
        self.position: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.orientation: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)
        self.scale: float = 1.0

        self.parent: BaseNode | None = None
        self.children: list[BaseNode] = []
        self.from_root: Matrix = Matrix()

    def add_to_collection(
        self,
        collection: bpy.types.Collection,
        options: ImportOptions,
    ) -> bpy.types.Object:
        obj = bpy.data.objects.new(self.name, None)
        self.set_object_data(obj, options)
        collection.objects.link(obj)
        return obj

    def set_object_data(self, obj: bpy.types.Object, options: ImportOptions) -> None:
        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError(f"Object [{obj.name}] has no kb attribute")
        kb.node_number = self.node_number
        kb.export_order = self.export_order
        obj.location = Vector(self.position)
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = Quaternion((self.orientation[1], self.orientation[2], self.orientation[3], self.orientation[0]))
        obj.scale = (self.scale, self.scale, self.scale)

    def load_object_data(
        self,
        obj: bpy.types.Object,
        eval_obj: bpy.types.Object,
        options: ImportOptions | ExportOptions,
    ) -> None:
        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError(f"Object [{obj.name}] has no kb attribute")
        if kb.node_number == -1:
            raise RuntimeError(f"Object '{obj.name}' node number is undefined")
        self.node_number = kb.node_number
        self.export_order = kb.export_order
        self.position = (eval_obj.location.x, eval_obj.location.y, eval_obj.location.z)
        if eval_obj.rotation_mode != "QUATERNION":
            raise RuntimeError(f"Object '{eval_obj.name}' must have Quaternion rotation mode")
        self.orientation = (eval_obj.rotation_quaternion.x, eval_obj.rotation_quaternion.y, eval_obj.rotation_quaternion.z, eval_obj.rotation_quaternion.w)
        self.scale = eval_obj.scale[0]

        self.from_root = eval_obj.matrix_local
        if self.parent is not None:
            self.from_root = self.parent.from_root @ self.from_root

    def find_node(self, test: Callable[[BaseNode], bool]) -> BaseNode | None:
        if test(self):
            return self
        for child in self.children:
            result = child.find_node(test)
            if result is not None:
                return result
        return None
