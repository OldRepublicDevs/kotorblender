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

from ...constants import DummyType, ExportOptions, ImportOptions, NodeType

from .base import BaseNode


class DummyNode(BaseNode):
    def __init__(self, name: str = "UNNAMED") -> None:
        BaseNode.__init__(self, name)

        self.nodetype: str = NodeType.DUMMY
        self.dummytype: str = DummyType.NONE

    def set_object_data(self, obj: bpy.types.Object, options: ImportOptions) -> None:
        BaseNode.set_object_data(self, obj, options)

        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError(f"Object [{obj.name}] has no kb attribute")
        kb.dummytype = self.dummytype

    def load_object_data(
        self, obj: bpy.types.Object, eval_obj: bpy.types.Object, options: ExportOptions
    ) -> None:
        BaseNode.load_object_data(self, obj, eval_obj, options)

        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError(f"Object [{obj.name}] has no kb attribute")
        self.dummytype = kb.dummytype
