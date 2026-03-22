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

import re
from collections.abc import Callable
from typing import TYPE_CHECKING

import bpy
from mathutils import Matrix

from ..constants import NULL, Classification, DummyType, ExportOptions, ImportOptions, MeshType, NodeType
from ..diagnostic_log import begin_scene_work_span, end_scene_work_span, sanitize_scene_context
from ..log_config import get_kb_logger
from ..utils import is_dwk_root, is_mdl_root, is_pwk_root, logger

from . import armature
from .animation import Animation
from .modelnode.aabb import AabbNode
from .modelnode.danglymesh import DanglymeshNode
from .modelnode.dummy import DummyNode
from .modelnode.emitter import EmitterNode
from .modelnode.light import LightNode
from .modelnode.lightsaber import LightsaberNode
from .modelnode.reference import ReferenceNode
from .modelnode.skinmesh import SkinmeshNode
from .modelnode.trimesh import TrimeshNode

if TYPE_CHECKING:
    from .modelnode.base import BaseNode


class Model:
    def __init__(self) -> None:
        self.name = "UNNAMED"
        self.supermodel = NULL
        self.classification = Classification.OTHER
        self.subclassification = 0
        self.classification_unk1 = 0
        self.affected_by_fog = True
        self.animroot = NULL
        self.animscale = 1.0
        self.bounding_box_min = (0.0, 0.0, 0.0)
        self.bounding_box_max = (0.0, 0.0, 0.0)
        self.model_radius = 0.0
        self.lytposition: tuple[float, float, float] | None = None

        self.root_node: BaseNode | DummyNode | None = None
        self.animations: list[Animation] = []

    def add_to_collection(
        self,
        collection: bpy.types.Collection,
        options: ImportOptions,
        position: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> bpy.types.Object | None:
        log = get_kb_logger("scene.model")
        span = begin_scene_work_span(log, "scene.model.Model.add_to_collection", self.name)
        err = False
        try:
            if self.root_node is None or not isinstance(self.root_node, DummyNode) or self.root_node.parent:
                raise RuntimeError("Root node has to be a dummy without a parent")

            logger().info(f"Adding model [{self.name}] to collection")

            if options.import_geometry:
                root_obj = self.root_node.add_to_collection(collection, options)
                root_obj.location = position
                kb = getattr(root_obj, "kb", None)
                if kb is None:
                    raise ValueError("root_obj.kb is None")
                kb.dummytype = DummyType.MDLROOT
                kb.supermodel = self.supermodel
                kb.classification = self.classification
                kb.subclassification = self.subclassification
                kb.classification_unk1 = self.classification_unk1
                kb.affected_by_fog = self.affected_by_fog
                kb.animroot = self.animroot
                kb.animscale = self.animscale
                kb.bounding_box_min = self.bounding_box_min
                kb.bounding_box_max = self.bounding_box_max
                kb.model_radius = self.model_radius

                for child in self.root_node.children:
                    self.import_nodes_to_collection(child, root_obj, collection, options)

                animscale = 1.0  # animation scale must only be applied to supermodel animations
            else:
                root_obj = next(
                    iter(obj for obj in bpy.context.selected_objects if is_mdl_root(obj)),
                    None,
                )
                if not root_obj:
                    root_obj = next(
                        iter(obj for obj in bpy.context.collection.objects if is_mdl_root(obj)),
                        None,
                    )
                if root_obj is None:
                    return None

                kb = getattr(root_obj, "kb", None)
                animscale = float(kb.animscale) if kb is not None else 1.0

            if options.import_animations:
                self.create_animations(root_obj, animscale)

            if options.build_armature:
                armature_obj = armature.rebuild_armature(root_obj)
                if armature_obj:
                    armature.apply_object_keyframes(root_obj, armature_obj)

            return root_obj
        except BaseException:
            err = True
            raise
        finally:
            end_scene_work_span(span, error=err)

    def import_nodes_to_collection(
        self,
        node: BaseNode,
        parent_obj: bpy.types.Object | None,
        collection: bpy.types.Collection,
        options: ImportOptions,
    ) -> None:
        logger().debug("Importing node [%s] to collection", sanitize_scene_context(node.name))
        get_kb_logger("scene.model").debug(
            "event=scene_model fn=import_nodes_to_collection node=%s parent=%s children=%s",
            sanitize_scene_context(node.name),
            sanitize_scene_context(parent_obj.name) if parent_obj is not None else "",
            len(node.children),
        )

        obj = node.add_to_collection(collection, options)
        if parent_obj is not None:
            obj.parent = parent_obj

        for child in node.children:
            self.import_nodes_to_collection(child, obj, collection, options)

    def create_animations(
        self,
        mdl_root: bpy.types.Object,
        animscale: float,
    ) -> None:
        log = get_kb_logger("scene.model")
        span = begin_scene_work_span(log, "scene.model.Model.create_animations", mdl_root.name)
        err = False
        try:
            log.debug(
                "event=scene_model fn=Model.create_animations_begin count=%s animscale=%s mdl_root=%s",
                len(self.animations),
                animscale,
                sanitize_scene_context(mdl_root.name),
            )
            for anim in self.animations:
                anim.add_to_objects(mdl_root, animscale)
        except BaseException:
            err = True
            raise
        finally:
            end_scene_work_span(span, error=err)

    def find_node(self, test: Callable[[BaseNode], bool]) -> BaseNode | None:
        log = get_kb_logger("scene.model")
        if self.root_node is None:
            log.debug("event=scene_model fn=Model.find_node outcome=no_root")
            return None
        result = self.root_node.find_node(test)
        if result is not None:
            log.debug(
                "event=scene_model fn=Model.find_node outcome=hit node=%s nodetype=%s",
                sanitize_scene_context(result.name),
                getattr(result.nodetype, "name", str(result.nodetype)),
            )
        else:
            log.debug("event=scene_model fn=Model.find_node outcome=miss")
        return result

    @classmethod
    def from_mdl_root(cls, root_obj: bpy.types.Object, options: ExportOptions) -> Model:
        log = get_kb_logger("scene.model")
        span = begin_scene_work_span(log, "scene.model.Model.from_mdl_root", root_obj.name)
        err = False
        try:
            logger().info(f"Loading model from object [{root_obj.name}]")

            cls.sanitize_model(root_obj)

            model = Model()
            model.name = root_obj.name
            kb: ObjectPropertyGroup | None = getattr(root_obj, "kb", None)  # noqa: F821  # pyright: ignore[reportUndefinedVariable]
            if kb is None:
                raise ValueError("root_obj.kb is None")
            model.supermodel = kb.supermodel
            model.classification = kb.classification
            model.subclassification = kb.subclassification
            model.classification_unk1 = kb.classification_unk1
            model.affected_by_fog = kb.affected_by_fog
            model.animroot = kb.animroot
            model.animscale = kb.animscale
            model.bounding_box_min = kb.bounding_box_min
            model.bounding_box_max = kb.bounding_box_max
            model.model_radius = kb.model_radius
            model.root_node = cls.model_node_from_object(root_obj, options)

            if options.export_animations:
                model.animations = [
                    Animation.from_list_anim(anim, root_obj) for anim in kb.anim_list
                ]

            return model
        except BaseException:
            err = True
            raise
        finally:
            end_scene_work_span(span, error=err)

    @classmethod
    def sanitize_model(cls, root_obj: bpy.types.Object):
        log = get_kb_logger("scene.model")
        log.debug(
            "event=scene_model fn=sanitize_model_begin root=%s",
            sanitize_scene_context(root_obj.name),
        )
        # Make a set of unique node numbers
        node_numbers = set()
        obj_stack = []
        obj_stack.append(root_obj)
        while obj_stack:
            obj = obj_stack.pop()
            if obj.kb.node_number in node_numbers:
                logger().warning(
                    f"Duplicate node number [{obj.kb.node_number}] in object [{obj.name}]",
                )
            if obj.kb.node_number != -1:
                node_numbers.add(obj.kb.node_number)
            for child in obj.children:
                obj_stack.append(child)
        sorted_node_numbers = sorted(node_numbers)
        if sorted_node_numbers:
            next_node_number = sorted_node_numbers[-1] + 1
        else:
            next_node_number = 0

        # Generate node numbers when undefined
        obj_stack.append(root_obj)
        while obj_stack:
            obj = obj_stack.pop()
            if obj.kb.node_number == -1:
                obj.kb.node_number = next_node_number
                next_node_number += 1
            for child in obj.children:
                obj_stack.append(child)

        log.debug(
            "event=scene_model fn=sanitize_model_done root=%s unique_assigned_node_numbers=%s next_node_number=%s",
            sanitize_scene_context(root_obj.name),
            len(node_numbers),
            next_node_number,
        )

    @classmethod
    def model_node_from_object(
        cls,
        obj: bpy.types.Object,
        options: ExportOptions,
        parent: BaseNode | None = None,
        exclude_xwk: bool = True,
    ) -> BaseNode | None:
        if exclude_xwk and (is_pwk_root(obj) or is_dwk_root(obj)):
            return None

        logger().debug(f"Loading model node from object [{obj.name}]")

        if obj.type == "EMPTY":
            if obj.kb.dummytype == DummyType.REFERENCE:
                node_type = NodeType.REFERENCE
            else:
                node_type = NodeType.DUMMY
        elif obj.type == "MESH":
            if obj.kb.meshtype == MeshType.EMITTER:
                node_type = NodeType.EMITTER
            elif obj.kb.meshtype == MeshType.AABB:
                node_type = NodeType.AABB
            elif obj.kb.meshtype == MeshType.SKIN:
                node_type = NodeType.SKIN
            elif obj.kb.meshtype == MeshType.LIGHTSABER:
                node_type = NodeType.LIGHTSABER
            elif obj.kb.meshtype == MeshType.DANGLYMESH:
                node_type = NodeType.DANGLYMESH
            else:
                node_type = NodeType.TRIMESH
        elif obj.type == "LIGHT":
            node_type = NodeType.LIGHT

        nt = getattr(node_type, "name", str(node_type))
        get_kb_logger("scene.model").debug(
            "event=scene_model fn=model_node_from_object obj=%s node_type=%s exclude_xwk=%s obj_type=%s",
            sanitize_scene_context(obj.name),
            nt,
            exclude_xwk,
            obj.type,
        )

        switch = {
            NodeType.DUMMY: DummyNode,
            NodeType.REFERENCE: ReferenceNode,
            NodeType.TRIMESH: TrimeshNode,
            NodeType.DANGLYMESH: DanglymeshNode,
            NodeType.SKIN: SkinmeshNode,
            NodeType.EMITTER: EmitterNode,
            NodeType.LIGHT: LightNode,
            NodeType.AABB: AabbNode,
            NodeType.LIGHTSABER: LightsaberNode,
        }

        name = obj.name
        if re.match(r".+\.\d{3}$", name):
            name = name[:-4]

        node = switch[node_type](name)
        node.parent = parent

        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        node.load_object_data(obj, eval_obj, options)

        # Ignore transformations up to MDL root
        if not parent:
            node.position = (0.0, 0.0, 0.0)
            node.orientation = (1.0, 0.0, 0.0, 0.0)
            node.from_root = Matrix()

        for child_obj in sorted(obj.children, key=lambda o: o.kb.export_order):
            child = cls.model_node_from_object(child_obj, options, node, exclude_xwk)
            if child:
                node.children.append(child)

        return node
