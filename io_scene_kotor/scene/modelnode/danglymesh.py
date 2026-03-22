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

from ...constants import ExportOptions, ImportOptions, MeshType, NodeType

from .base import _log_modelnode
from .trimesh import TrimeshNode

CONSTRAINTS = "constraints"


class DanglymeshNode(TrimeshNode):
    def __init__(self, name: str = "UNNAMED") -> None:
        TrimeshNode.__init__(self, name)
        self.nodetype: str = NodeType.DANGLYMESH
        self.meshtype: str = MeshType.DANGLYMESH
        self.period: float = 1.0
        self.tightness: float = 1.0
        self.displacement: float = 1.0

    def apply_edge_loop_mesh(
        self, mesh: object, obj: bpy.types.Object
    ) -> None:  # type: ignore[override]
        TrimeshNode.apply_edge_loop_mesh(self, mesh, obj)
        self.apply_vertex_constraints(mesh, obj)

    def apply_vertex_constraints(self, mesh: object, obj: bpy.types.Object) -> None:
        group = obj.vertex_groups.new(name=CONSTRAINTS)
        for vert_idx, constraint in enumerate(mesh.constraints):  # type: ignore[attr-defined]
            weight = constraint / 255
            group.add([vert_idx], weight, "REPLACE")
        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError(f"Object [{obj.name}] has no kb attribute")
        kb.constraints = group.name
        _log_modelnode("DanglymeshNode.apply_vertex_constraints", self)

    def set_object_data(self, obj: bpy.types.Object, options: ImportOptions) -> None:
        TrimeshNode.set_object_data(self, obj, options)
        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError(f"Object [{obj.name}] has no kb attribute")
        kb.period = self.period
        kb.tightness = self.tightness
        kb.displacement = self.displacement
        _log_modelnode("DanglymeshNode.set_object_data", self)

    def load_object_data(
        self, obj: bpy.types.Object, eval_obj: bpy.types.Object, options: ExportOptions
    ) -> None:
        TrimeshNode.load_object_data(self, obj, eval_obj, options)
        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError(f"Object [{obj.name}] has no kb attribute")
        self.period = kb.period
        self.tightness = kb.tightness
        self.displacement = kb.displacement
        _log_modelnode("DanglymeshNode.load_object_data", self)

    def unapply_edge_loop_mesh(
        self, obj: bpy.types.Object
    ) -> object:  # type: ignore[override]
        mesh = TrimeshNode.unapply_edge_loop_mesh(self, obj)
        self.unapply_vertex_constraints(obj, mesh)
        return mesh

    def unapply_vertex_constraints(self, obj: bpy.types.Object, mesh: object) -> None:
        if CONSTRAINTS not in obj.vertex_groups:
            mesh.constraints = [0] * len(mesh.verts)
        else:
            group = obj.vertex_groups[CONSTRAINTS]
            mesh.constraints = [255.0 * group.weight(i) for i in range(len(mesh.verts))]
        _log_modelnode("DanglymeshNode.unapply_vertex_constraints", self)
