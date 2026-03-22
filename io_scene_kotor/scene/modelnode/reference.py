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

from ...constants import DummyType, ExportOptions, ImportOptions, NULL, NodeType

from .base import BaseNode, _log_modelnode


class ReferenceNode(BaseNode):
    def __init__(self, name: str = "UNNAMED") -> None:
        BaseNode.__init__(self, name)
        self.nodetype: str = NodeType.REFERENCE
        self.dummytype: str = DummyType.REFERENCE
        self.refmodel: str = NULL
        self.reattachable: int = 0

    def set_object_data(self, obj: bpy.types.Object, options: ImportOptions) -> None:
        BaseNode.set_object_data(self, obj, options)

        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError(f"Object [{obj.name}] has no kb attribute")
        kb.dummytype = DummyType.REFERENCE
        kb.refmodel = self.refmodel
        kb.reattachable = self.reattachable == 1
        _log_modelnode("ReferenceNode.set_object_data", self)

    def load_object_data(
        self, obj: bpy.types.Object, eval_obj: bpy.types.Object, options: ExportOptions
    ) -> None:
        BaseNode.load_object_data(self, obj, eval_obj, options)

        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError(f"Object [{obj.name}] has no kb attribute")
        self.refmodel = kb.refmodel
        self.reattachable = 1 if kb.reattachable else 0
        _log_modelnode("ReferenceNode.load_object_data", self)
