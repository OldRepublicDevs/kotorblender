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

from ..constants import MeshType
from ..diagnostic_log import run_simple_operator_logged
from ..log_config import get_kb_logger
from ..scene.material import NodeName
from ..scene.modelnode.trimesh import UV_MAP_LIGHTMAP
from ..utils import is_mesh_type, is_null


class _BakeLightmapsCommon:
    """Shared bake logic; not a bpy.types.Operator subclass (Blender 5.x breaks nested Operator __init__)."""

    def _execute_bake_lightmaps_body(self, context: bpy.types.Context) -> set[str]:
        hide_nm = bool(getattr(self, "hide_non_lightmapped", True))
        # Find bake targets
        objects: list[bpy.types.Object] = (
            list(context.selected_objects)
            if context.selected_objects
            else list(context.scene.objects)
        )
        targets = [obj for obj in objects if self.is_bake_target(obj)]
        if not targets:
            return {"CANCELLED"}

        # Optionally, hide everything except lightmapped objects and lights
        if hide_nm:
            target_names = set([obj.name for obj in targets])
            for obj in context.scene.objects:
                obj.hide_render = obj.type != "LIGHT" and obj.name not in target_names

        for obj in targets:
            self.preprocess_target(obj)

        # Select only bake targets
        bpy.ops.object.select_all(action="DESELECT")
        for obj in targets:
            obj.select_set(True)
        view_layer: bpy.types.ViewLayer | None = context.view_layer
        if view_layer is None:
            self.report({"ERROR"}, "View layer is None")
            return {"CANCELLED"}
        view_layer.objects.active = targets[0]

        scene: bpy.types.Scene = context.scene
        scene.render.engine = "CYCLES"
        # context.scene.cycles.device = "GPU"
        if scene.cycles.samples > 512:
            scene.cycles.samples = 4
        bpy.ops.object.bake(margin=2, uv_layer=UV_MAP_LIGHTMAP)

        for obj in targets:
            self.postprocess_target(obj)

        return {"FINISHED"}

    def is_bake_target(self, obj: bpy.types.Object) -> bool:
        # AABB (grass) meshes skipped; support planned.
        if not is_mesh_type(obj, MeshType.TRIMESH):
            return False
        kb = getattr(obj, "kb", None)
        if kb is None:
            return False
        if not kb.render:
            return False
        if not kb.lightmapped:
            return False
        if is_null(kb.bitmap):
            return False
        if is_null(kb.bitmap2):
            return False
        if not isinstance(obj.data, bpy.types.Mesh):
            return False
        if UV_MAP_LIGHTMAP not in obj.data.uv_layers:
            return False
        material: bpy.types.Material | None = obj.active_material
        if material is None or not material.use_nodes:
            return False
        node_tree: bpy.types.ShaderNodeTree | None = material.node_tree
        if node_tree is None:
            return False
        nodes = node_tree.nodes
        if NodeName.DIFFUSE_TEX not in nodes:
            return False
        if NodeName.LIGHTMAP_TEX not in nodes:
            return False
        if NodeName.WHITE not in nodes:
            return False
        if NodeName.DIFFUSE_BSDF not in nodes:
            return False
        if NodeName.DIFF_LM_EMISSION not in nodes:
            return False
        if NodeName.ADD_DIFFUSE_EMISSION not in nodes:
            return False
        return True

    def preprocess_target(self, obj: bpy.types.Object) -> None:
        material: bpy.types.Material | None = obj.active_material
        if material is None:
            raise ValueError("Object has no active material")
        node_tree: bpy.types.ShaderNodeTree | None = material.node_tree
        if node_tree is None:
            raise ValueError("Material has no node tree")
        nodes = node_tree.nodes
        links = node_tree.links

        # Replace diffuse * lightmap shader by diffuse
        add_diffuse_emission = nodes[NodeName.ADD_DIFFUSE_EMISSION]
        if add_diffuse_emission.inputs[0].is_linked:
            links.remove(add_diffuse_emission.inputs[0].links[0])
        diffuse_bsdf = nodes[NodeName.DIFFUSE_BSDF]
        links.new(add_diffuse_emission.inputs[0], diffuse_bsdf.outputs[0])

        # Replace diffuse color by white
        if diffuse_bsdf.inputs[0].is_linked:
            links.remove(diffuse_bsdf.inputs[0].links[0])
        white = nodes[NodeName.WHITE]
        links.new(diffuse_bsdf.inputs[0], white.outputs[0])

        # Select only lightmap texture node and make it active
        for node in nodes:
            node.select = False
        lightmap_tex = nodes[NodeName.LIGHTMAP_TEX]
        lightmap_tex.select = True
        nodes.active = lightmap_tex

    def postprocess_target(self, obj: bpy.types.Object) -> None:
        material: bpy.types.Material | None = obj.active_material
        if material is None:
            raise ValueError("Object has no active material")
        node_tree: bpy.types.ShaderNodeTree | None = material.node_tree
        if node_tree is None:
            raise ValueError("Material has no node tree")
        nodes = node_tree.nodes
        links = node_tree.links

        # Replace diffuse shader by diffuse * lightmap
        add_diffuse_emission = nodes[NodeName.ADD_DIFFUSE_EMISSION]
        diff_lm_emission = nodes[NodeName.DIFF_LM_EMISSION]
        if add_diffuse_emission.inputs[0].is_linked:
            links.remove(add_diffuse_emission.inputs[0].links[0])
        links.new(add_diffuse_emission.inputs[0], diff_lm_emission.outputs[0])

        # Replace white by diffuse color
        diffuse_bsdf = nodes[NodeName.DIFFUSE_BSDF]
        if diffuse_bsdf.inputs[0].is_linked:
            links.remove(diffuse_bsdf.inputs[0].links[0])
        diffuse_tex = nodes[NodeName.DIFFUSE_TEX]
        links.new(diffuse_bsdf.inputs[0], diffuse_tex.outputs[0])


class KB_OT_bake_lightmaps_auto(_BakeLightmapsCommon, bpy.types.Operator):
    bl_idname = "kb.bake_lightmaps_auto"
    bl_label = "Bake Lightmaps (auto)"
    bl_description = "Bake lighting and shadows into lightmap textures, hiding non-lightmapped objects from render"

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        self.hide_non_lightmapped = True
        return self.execute(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.bakelightmaps")

        def _body() -> set[str]:
            return self._execute_bake_lightmaps_body(context)

        return run_simple_operator_logged(log, "kb.bake_lightmaps_auto", _body)


class KB_OT_bake_lightmaps_manual(_BakeLightmapsCommon, bpy.types.Operator):
    bl_idname = "kb.bake_lightmaps_manual"
    bl_label = "Bake Lightmaps (manual)"
    bl_description = "Bake lighting and shadows into lightmap textures, user is responsible for setting object visibility"

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        self.hide_non_lightmapped = False
        return self.execute(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.bakelightmaps")

        def _body() -> set[str]:
            return self._execute_bake_lightmaps_body(context)

        return run_simple_operator_logged(log, "kb.bake_lightmaps_manual", _body)
