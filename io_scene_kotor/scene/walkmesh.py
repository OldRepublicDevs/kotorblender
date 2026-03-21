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

from ..constants import ExportOptions, ImportOptions, WalkmeshType
from ..utils import is_dwk_root, is_pwk_root

from .model import Model
from .modelnode.aabb import AabbNode
from .modelnode.dummy import DummyNode


class Walkmesh(Model):
    def __init__(self, walkmesh_type: str) -> None:
        Model.__init__(self)
        self.walkmesh_type: str = walkmesh_type

    def attach_to_collection(
        self,
        parent_obj: bpy.types.Object | None,
        collection: bpy.types.Collection,
        options: ImportOptions,
    ) -> None:
        """Link walkmesh objects into ``collection`` (distinct from ``Model.add_to_collection``).

        ``parent_obj`` is the Blender parent for the walkmesh root dummy (typically the MDL
        root when loaded with a model). Pass ``None`` for standalone BWM import so the root
        sits at world origin with no parent; child dummies and meshes still parent correctly.
        """
        if not isinstance(self.root_node, DummyNode) or self.root_node.parent is not None:
            raise RuntimeError("Root node has to be a dummy without a parent")
        if self.root_node is None:
            raise RuntimeError("Root node is None")
        self.import_nodes_to_collection(self.root_node, parent_obj, collection, options)

    @classmethod
    def from_aabb_node(cls, aabb: AabbNode) -> Walkmesh:
        root_node = DummyNode("wok")
        root_node.children.append(aabb)

        walkmesh = Walkmesh(WalkmeshType.WOK)
        walkmesh.root_node = root_node

        return walkmesh

    @classmethod
    def from_root_object(cls, obj: bpy.types.Object, options: ExportOptions) -> Walkmesh:
        if is_pwk_root(obj):
            walkmesh_type = WalkmeshType.PWK
        elif is_dwk_root(obj):
            walkmesh_type = WalkmeshType.DWK
        else:
            raise ValueError(f"Cannot create walkmesh from root object '{obj.name}'")

        walkmesh = Walkmesh(walkmesh_type)
        walkmesh.root_node = cls.model_node_from_object(obj, options, exclude_xwk=False)

        return walkmesh
