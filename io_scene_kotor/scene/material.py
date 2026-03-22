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

import os

import bpy
from bpy_extras import image_utils

from ..constants import UV_MAP_LIGHTMAP, WALKMESH_MATERIALS, NodeName, WalkmeshNodeName
from ..diagnostic_log import begin_scene_work_span, end_scene_work_span, sanitize_scene_context
from ..format.tpc.reader import TpcReader
from ..log_config import get_kb_logger
from ..ui.props.object import ObjectPropertyGroup
from ..utils import color_to_hex, float_to_byte, int_to_hex, is_aabb_mesh, is_not_null, logger
from ..vendor.pykotor_adapter import convert_pykotor_tpc_to_tpcimage, get_use_pykotor_readers, load_tpc_via_pykotor


def rebuild_object_materials(
    obj: bpy.types.Object,
    texture_search_paths: list[str] | None = None,
    lightmap_search_paths: list[str] | None = None,
) -> None:
    if obj.data is None or not isinstance(obj.data, bpy.types.Mesh):
        logger().warning(f"Object [{obj.name}] is not a mesh, skipping material rebuild")
        return
    diag = get_kb_logger("scene.material")
    ctx = sanitize_scene_context(obj.name)
    span = begin_scene_work_span(diag, "scene.material.rebuild_object_materials", ctx)
    err = False
    try:
        rebuild_object_materials0(obj, texture_search_paths, lightmap_search_paths)
    except Exception:
        err = True
        logger().exception(f"Error building object [{obj.name}] materials")
        obj.data.materials.clear()
    finally:
        end_scene_work_span(span, error=err)


def rebuild_object_materials0(
    obj: bpy.types.Object,
    texture_search_paths: list[str] | None = None,
    lightmap_search_paths: list[str] | None = None,
) -> None:
    texture_search_paths = [] if texture_search_paths is None else texture_search_paths
    lightmap_search_paths = [] if lightmap_search_paths is None else lightmap_search_paths
    diag = get_kb_logger("scene.material")
    diag.debug(
        "event=scene_material fn=rebuild_object_materials0 obj=%s tex_paths=%s lm_paths=%s",
        sanitize_scene_context(obj.name),
        len(texture_search_paths),
        len(lightmap_search_paths),
    )

    mesh: bpy.types.Armature | bpy.types.Camera | bpy.types.Curve | bpy.types.Curves | bpy.types.GreasePencil | bpy.types.Lattice | bpy.types.Light | bpy.types.LightProbe | bpy.types.Mesh | bpy.types.MetaBall | bpy.types.PointCloud | bpy.types.Speaker | bpy.types.SurfaceCurve | bpy.types.TextCurve | bpy.types.Volume | None = obj.data
    if mesh is None or not isinstance(mesh, bpy.types.Mesh):
        logger().warning(f"Object [{obj.name}] is not a mesh, skipping material rebuild")
        return
    polygon_materials: list[int] = [polygon.material_index for polygon in mesh.polygons]
    mesh.materials.clear()

    if is_aabb_mesh(obj):
        diag.debug(
            "event=scene_material fn=rebuild_object_materials0_branch branch=walkmesh polys=%s",
            len(polygon_materials),
        )
        rebuild_walkmesh_materials(obj)
        mesh.polygons.foreach_set("material_index", polygon_materials)
        return

    kb = getattr(obj, "kb", None)
    if kb is None or not hasattr(kb, "bitmap"):
        logger().warning(f"Object [{obj.name}] has no kb property group. Cannot rebuild material.")
        return
    if is_not_null(kb.bitmap):
        diag.debug("event=scene_material fn=rebuild_object_materials0_branch branch=textured")
        material = get_or_create_material(obj.name)
        mesh.materials.append(material)
        rebuild_material_textured(material, obj, texture_search_paths, lightmap_search_paths)
    else:
        diag.debug("event=scene_material fn=rebuild_object_materials0_branch branch=solid")
        diffuse = color_to_hex(kb.diffuse)
        alpha = int_to_hex(float_to_byte(kb.alpha))
        material = get_or_create_material(f"D{diffuse}__A{alpha}")
        mesh.materials.append(material)
        rebuild_material_solid(material, obj)


def rebuild_walkmesh_materials(obj: bpy.types.Object) -> None:
    if not isinstance(obj.data, bpy.types.Mesh):
        logger().warning(f"Object [{obj.name}] is not a mesh, skipping walkmesh material rebuild")
        return
    mesh: bpy.types.Mesh = obj.data
    get_kb_logger("scene.material").debug(
        "event=scene_material fn=rebuild_walkmesh_materials obj=%s materials=%s",
        sanitize_scene_context(obj.name),
        len(WALKMESH_MATERIALS),
    )

    for name, color, _ in WALKMESH_MATERIALS:
        material: bpy.types.Material = get_or_create_material(name)
        material.use_nodes = True
        material.blend_method = "BLEND"
        if bpy.app.version < (4, 3):
            material.shadow_method = "NONE"

        node_tree: bpy.types.NodeTree | None = material.node_tree
        if node_tree is None:
            logger().warning(f"Object [{obj.name}] has no node tree. Cannot rebuild material.")
            return
        nodes: bpy.types.Nodes = node_tree.nodes
        nodes.clear()
        links: bpy.types.NodeLinks = node_tree.links
        links.clear()

        x = 0

        color_node_raw: bpy.types.Node = nodes.new("ShaderNodeRGB")
        if not isinstance(color_node_raw, bpy.types.ShaderNodeRGB):
            raise TypeError(f"Expected ShaderNodeRGB, got {type(color_node_raw)}")
        color_node: bpy.types.ShaderNodeRGB = color_node_raw
        color_node.name = WalkmeshNodeName.COLOR
        color_node.location = (x, 300)
        color_node_outputs0: bpy.types.NodeSocket = color_node.outputs[0]
        if not isinstance(color_node_outputs0, bpy.types.NodeSocketColor):
            raise TypeError(f"Expected NodeSocketColor, got {type(color_node_outputs0)}")
        color_node_outputs0.default_value = [*color, 1.0]

        x += 300

        opacity_raw: bpy.types.Node = nodes.new("ShaderNodeValue")
        if not isinstance(opacity_raw, bpy.types.ShaderNodeValue):
            raise TypeError(f"Expected ShaderNodeValue, got {type(opacity_raw)}")
        opacity: bpy.types.ShaderNodeValue = opacity_raw
        opacity.name = WalkmeshNodeName.OPACITY
        opacity.location = (x, 300)
        opacity_outputs0: bpy.types.NodeSocket = opacity.outputs[0]
        assert isinstance(opacity_outputs0, bpy.types.NodeSocketFloat), "Outputs[0] is not a NodeSocketFloat"
        opacity_outputs0.default_value = 1.0

        transparent_bsdf_raw: bpy.types.Node = nodes.new("ShaderNodeBsdfTransparent")
        if not isinstance(transparent_bsdf_raw, bpy.types.ShaderNodeBsdfTransparent):
            raise TypeError(f"Expected ShaderNodeBsdfTransparent, got {type(transparent_bsdf_raw)}")
        transparent_bsdf: bpy.types.ShaderNodeBsdfTransparent = transparent_bsdf_raw
        transparent_bsdf.location = (x, 150)
        links.new(transparent_bsdf.inputs["Color"], color_node.outputs[0])

        emission_raw: bpy.types.Node = nodes.new("ShaderNodeEmission")
        if not isinstance(emission_raw, bpy.types.ShaderNodeEmission):
            raise TypeError(f"Expected ShaderNodeEmission, got {type(emission_raw)}")
        emission: bpy.types.ShaderNodeEmission = emission_raw
        emission.location = (x, 0)
        links.new(emission.inputs["Color"], color_node.outputs[0])

        x += 300

        mix_shader_raw: bpy.types.Node = nodes.new("ShaderNodeMixShader")
        if not isinstance(mix_shader_raw, bpy.types.ShaderNodeMixShader):
            raise TypeError(f"Expected ShaderNodeMixShader, got {type(mix_shader_raw)}")
        mix_shader: bpy.types.ShaderNodeMixShader = mix_shader_raw
        mix_shader.location = (x, 0)
        links.new(mix_shader.inputs[0], opacity.outputs[0])
        links.new(mix_shader.inputs[1], transparent_bsdf.outputs[0])
        links.new(mix_shader.inputs[2], emission.outputs[0])

        x += 300

        output_raw: bpy.types.Node = nodes.new("ShaderNodeOutputMaterial")
        if not isinstance(output_raw, bpy.types.ShaderNodeOutputMaterial):
            raise TypeError(f"Expected ShaderNodeOutputMaterial, got {type(output_raw)}")
        output: bpy.types.ShaderNodeOutputMaterial = output_raw
        output.location = (x, 0)
        links.new(output.inputs[0], mix_shader.outputs[0])

        mesh.materials.append(material)


def get_or_create_material(name: str) -> bpy.types.Material:
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    return bpy.data.materials.new(name)


def rebuild_material_solid(material: bpy.types.Material, obj: bpy.types.Object) -> None:
    material.use_nodes = False
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        logger().warning(f"Object [{obj.name}] has no kb property group. Cannot rebuild material.")
        return
    material.diffuse_color = [*kb.diffuse, 1.0]


def rebuild_material_textured(
    material: bpy.types.Material,
    obj: bpy.types.Object,
    texture_search_paths: list[str],
    lightmap_search_paths: list[str],
) -> None:
    material.use_nodes = True

    node_tree: bpy.types.NodeTree | None = material.node_tree
    if node_tree is None:
        logger().warning(f"Material [{material.name}] has no node tree. Cannot rebuild material.")
        return
    links: bpy.types.NodeLinks = node_tree.links
    links.clear()

    nodes: bpy.types.Nodes = node_tree.nodes
    nodes.clear()

    x: int = 0
    envmapped: bool = False
    bumpmapped: bool = False
    additive: bool = False
    decal: bool = False

    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        logger().warning(f"Object [{obj.name}] has no kb property group. Cannot rebuild material.")
        return

    # Diffuse texture
    diffuse_tex: bpy.types.ShaderNodeTexImage | None = None
    normal_map: bpy.types.ShaderNodeNormalMap | None = None
    if is_not_null(kb.bitmap):
        node = nodes.new("ShaderNodeTexImage")
        if not isinstance(node, bpy.types.ShaderNodeTexImage):
            raise TypeError(f"Expected ShaderNodeTexImage, got {node.__class__.__name__}")
        diffuse_tex = node
        diffuse_tex.name = NodeName.DIFFUSE_TEX
        diffuse_tex.location = (x, 0)
        texture = get_or_create_texture(kb.bitmap, texture_search_paths)
        if not isinstance(texture, bpy.types.Texture):
            raise TypeError(f"Expected Texture, got {texture.__class__.__name__}")
        tex_image: bpy.types.Image | None = _texture_get_image(texture)
        if tex_image is None:
            raise ValueError(f"Texture [{texture.name}] has no image")
        diffuse_tex.image = tex_image
        if diffuse_tex.image is None:
            raise ValueError("Diffuse texture image is None")
        image_kb = getattr(diffuse_tex.image, "kb", None)
        if image_kb is None:
            raise ValueError(f"Image [{diffuse_tex.image.name}] has no kb property group")
        envmapped = image_kb.envmap
        if image_kb.bumpmap:
            bumpmapped = True
            bumpmap_node = nodes.new("ShaderNodeTexImage")
            if not isinstance(bumpmap_node, bpy.types.ShaderNodeTexImage):
                raise TypeError(f"Expected ShaderNodeTexImage, got {bumpmap_node.__class__.__name__}")
            bumpmap_tex = bumpmap_node
            bumpmap_tex.name = NodeName.BUMPMAP_TEX
            bumpmap_tex.location = (x, 300)
            bumpmap_texture = get_or_create_texture(
                image_kb.bumpmap,
                texture_search_paths,
            )
            if not isinstance(bumpmap_texture, bpy.types.Texture):
                raise TypeError(f"Expected Texture, got {bumpmap_texture.__class__.__name__}")
            bump_img = _texture_get_image(bumpmap_texture)
            if bump_img is None:
                raise ValueError(f"Texture [{bumpmap_texture.name}] has no image")
            bumpmap_tex.image = bump_img
            normal_map_node = nodes.new("ShaderNodeNormalMap")
            if not isinstance(normal_map_node, bpy.types.ShaderNodeNormalMap):
                raise TypeError(f"Expected ShaderNodeNormalMap, got {normal_map_node.__class__.__name__}")
            normal_map = normal_map_node
            normal_map.name = NodeName.NORMAL_MAP
            normal_map.location = (x + 300, 300)
            links.new(normal_map.inputs[1], bumpmap_tex.outputs[0])
        if diffuse_tex is not None and diffuse_tex.image is not None:
            image_kb_final = getattr(diffuse_tex.image, "kb", None)
            if image_kb_final is not None:
                additive = image_kb_final.additive
                decal = image_kb_final.decal

    # Lightmap texture
    lightmap_tex: bpy.types.ShaderNodeTexImage | None = None
    lightmap_uv: bpy.types.ShaderNodeUVMap | None = None
    if is_not_null(kb.bitmap2):
        uv_node = nodes.new("ShaderNodeUVMap")
        if not isinstance(uv_node, bpy.types.ShaderNodeUVMap):
            raise TypeError(f"Expected ShaderNodeUVMap, got {uv_node.__class__.__name__}")
        lightmap_uv = uv_node
        lightmap_uv.location = (x - 300, -300)
        lightmap_uv.uv_map = UV_MAP_LIGHTMAP

        lightmap_node = nodes.new("ShaderNodeTexImage")
        if not isinstance(lightmap_node, bpy.types.ShaderNodeTexImage):
            raise TypeError(f"Expected ShaderNodeTexImage, got {lightmap_node.__class__.__name__}")
        lightmap_tex = lightmap_node
        lightmap_tex.name = NodeName.LIGHTMAP_TEX
        lightmap_tex.location = (x, -300)
        lightmap_texture = get_or_create_texture(kb.bitmap2, lightmap_search_paths)
        if not isinstance(lightmap_texture, bpy.types.Texture):
            raise TypeError(f"Expected Texture, got {lightmap_texture.__class__.__name__}")
        lm_img = _texture_get_image(lightmap_texture)
        if lm_img is None:
            raise ValueError(f"Texture [{lightmap_texture.name}] has no image")
        lightmap_tex.image = lm_img
        if lightmap_uv is not None:
            links.new(lightmap_tex.inputs[0], lightmap_uv.outputs[0])

    x += 300

    # White color
    white_node: bpy.types.Node = nodes.new("ShaderNodeRGB")
    if not isinstance(white_node, bpy.types.ShaderNodeRGB):
        raise TypeError(f"Expected ShaderNodeRGB, got {white_node.__class__.__name__}")
    white: bpy.types.ShaderNodeRGB = white_node
    white.name = NodeName.WHITE
    white.location = (x, 0)
    white_outputs0: bpy.types.NodeSocket = white.outputs[0]
    if not isinstance(white_outputs0, bpy.types.NodeSocketColor):
        raise TypeError(f"Expected NodeSocketColor, got {type(white_outputs0)}")
    white_outputs0.default_value = [1.0] * 4

    # Multiply diffuse color by lightmap color
    mul_diffuse_lightmap_node: bpy.types.Node = nodes.new("ShaderNodeVectorMath")
    if not isinstance(mul_diffuse_lightmap_node, bpy.types.ShaderNodeVectorMath):
        raise TypeError(f"Expected ShaderNodeVectorMath, got {mul_diffuse_lightmap_node.__class__.__name__}")
    mul_diffuse_lightmap: bpy.types.ShaderNodeVectorMath = mul_diffuse_lightmap_node
    mul_diffuse_lightmap.name = NodeName.MUL_DIFFUSE_LIGHTMAP
    mul_diffuse_lightmap.location = (x, -300)
    mul_diffuse_lightmap.operation = "MULTIPLY"
    inputs1: bpy.types.NodeSocket = mul_diffuse_lightmap.inputs[1]
    if not isinstance(inputs1, bpy.types.NodeSocketVector):
        raise TypeError(f"Expected NodeSocketVector, got {type(inputs1)}")
    inputs1.default_value = [1.0, 1.0, 1.0]
    if diffuse_tex is not None:
        links.new(mul_diffuse_lightmap.inputs[0], diffuse_tex.outputs[0])
    if is_not_null(kb.bitmap2) and lightmap_tex is not None:
        links.new(mul_diffuse_lightmap.inputs[1], lightmap_tex.outputs[0])

    # Multiply diffuse color by self-illumination color
    mul_diffuse_selfillum_node: bpy.types.Node = nodes.new("ShaderNodeVectorMath")
    if not isinstance(mul_diffuse_selfillum_node, bpy.types.ShaderNodeVectorMath):
        raise TypeError(f"Expected ShaderNodeVectorMath, got {mul_diffuse_selfillum_node.__class__.__name__}")
    mul_diffuse_selfillum: bpy.types.ShaderNodeVectorMath = mul_diffuse_selfillum_node
    mul_diffuse_selfillum.name = NodeName.MUL_DIFFUSE_SELFILLUM
    mul_diffuse_selfillum.location = (x, -600)
    mul_diffuse_selfillum.operation = "MULTIPLY"
    selfillum_vec_in: bpy.types.NodeSocket = mul_diffuse_selfillum.inputs[1]
    if not isinstance(selfillum_vec_in, bpy.types.NodeSocketVector):
        raise TypeError(f"Expected NodeSocketVector, got {selfillum_vec_in.__class__.__name__}")
    sic = kb.selfillumcolor
    selfillum_vec_in.default_value = (float(sic[0]), float(sic[1]), float(sic[2]))
    if diffuse_tex is not None:
        links.new(mul_diffuse_selfillum.inputs[0], diffuse_tex.outputs[0])

    x += 300

    # Diffuse BSDF
    diffuse_bsdf_node: bpy.types.Node = nodes.new("ShaderNodeBsdfDiffuse")
    if not isinstance(diffuse_bsdf_node, bpy.types.ShaderNodeBsdfDiffuse):
        raise TypeError(f"Expected ShaderNodeBsdfDiffuse, got {diffuse_bsdf_node.__class__.__name__}")
    diffuse_bsdf: bpy.types.ShaderNodeBsdfDiffuse = diffuse_bsdf_node
    diffuse_bsdf.name = NodeName.DIFFUSE_BSDF
    diffuse_bsdf.location = (x, 0)
    if diffuse_tex is not None:
        links.new(diffuse_bsdf.inputs["Color"], diffuse_tex.outputs[0])
    if bumpmapped and normal_map is not None:
        links.new(diffuse_bsdf.inputs["Normal"], normal_map.outputs[0])

    # Emission from diffuse * lightmap
    diff_lm_emission_node: bpy.types.Node = nodes.new("ShaderNodeEmission")
    if not isinstance(diff_lm_emission_node, bpy.types.ShaderNodeEmission):
        raise TypeError(f"Expected ShaderNodeEmission, got {diff_lm_emission_node.__class__.__name__}")
    diff_lm_emission: bpy.types.ShaderNodeEmission = diff_lm_emission_node
    diff_lm_emission.name = NodeName.DIFF_LM_EMISSION
    diff_lm_emission.location = (x, -300)
    links.new(diff_lm_emission.inputs["Color"], mul_diffuse_lightmap.outputs[0])

    # Emission from self-illumination
    selfillum_emission_node: bpy.types.Node = nodes.new("ShaderNodeEmission")
    if not isinstance(selfillum_emission_node, bpy.types.ShaderNodeEmission):
        raise TypeError(f"Expected ShaderNodeEmission, got {selfillum_emission_node.__class__.__name__}")
    selfillum_emission: bpy.types.ShaderNodeEmission = selfillum_emission_node
    selfillum_emission.name = NodeName.SELFILLUM_EMISSION
    selfillum_emission.location = (x, -600)
    links.new(selfillum_emission.inputs["Color"], mul_diffuse_selfillum.outputs[0])

    x += 300

    # Object alpha
    object_alpha_node: bpy.types.Node = nodes.new("ShaderNodeValue")
    if not isinstance(object_alpha_node, bpy.types.ShaderNodeValue):
        raise TypeError(f"Expected ShaderNodeValue, got {object_alpha_node.__class__.__name__}")
    object_alpha: bpy.types.ShaderNodeValue = object_alpha_node
    object_alpha.name = NodeName.OBJECT_ALPHA
    object_alpha.location = (x, 300)
    object_alpha_outputs0: bpy.types.NodeSocket = object_alpha.outputs[0]
    assert isinstance(object_alpha_outputs0, bpy.types.NodeSocketFloat), "Outputs[0] is not a NodeSocketFloat"
    object_alpha_outputs0.default_value = float(kb.alpha)

    # Glossy BSDF (ShaderNodeBsdfGlossy not in fake-bpy-module stubs; use ShaderNode)
    glossy_bsdf_node: bpy.types.Node = nodes.new("ShaderNodeBsdfGlossy")
    if not isinstance(glossy_bsdf_node, bpy.types.ShaderNode):
        raise TypeError(f"Expected ShaderNode, got {glossy_bsdf_node.__class__.__name__}")
    glossy_bsdf: bpy.types.ShaderNode = glossy_bsdf_node
    glossy_bsdf.name = NodeName.GLOSSY_BSDF
    glossy_bsdf.location = (x, 0)
    roughness_input: bpy.types.NodeSocket = glossy_bsdf.inputs["Roughness"]
    roughness_input.default_value = 0.2  # pyright: ignore[reportAttributeAccessIssue]
    if bumpmapped and normal_map is not None:
        links.new(glossy_bsdf.inputs["Normal"], normal_map.outputs[0])

    # Combine diffuse or diffuse * lightmap, and self-illumination emission
    add_diffuse_emission_node: bpy.types.Node = nodes.new("ShaderNodeAddShader")
    if not isinstance(add_diffuse_emission_node, bpy.types.ShaderNodeAddShader):
        raise TypeError(f"Expected ShaderNodeAddShader, got {add_diffuse_emission_node.__class__.__name__}")
    add_diffuse_emission: bpy.types.ShaderNodeAddShader = add_diffuse_emission_node
    add_diffuse_emission.name = NodeName.ADD_DIFFUSE_EMISSION
    add_diffuse_emission.location = (x, -300)
    if kb.lightmapped:
        links.new(add_diffuse_emission.inputs[0], diff_lm_emission.outputs[0])
    else:
        links.new(add_diffuse_emission.inputs[0], diffuse_bsdf.outputs[0])
    links.new(add_diffuse_emission.inputs[1], selfillum_emission.outputs[0])

    x += 300

    # Multiply diffuse texture alpha by object alpha
    mul_diff_obj_alpha_node: bpy.types.Node = nodes.new("ShaderNodeMath")
    if not isinstance(mul_diff_obj_alpha_node, bpy.types.ShaderNodeMath):
        raise TypeError(f"Expected ShaderNodeMath, got {mul_diff_obj_alpha_node.__class__.__name__}")
    mul_diff_obj_alpha: bpy.types.ShaderNodeMath = mul_diff_obj_alpha_node
    mul_diff_obj_alpha.name = NodeName.MUL_DIFFUSE_OBJECT_ALPHA
    mul_diff_obj_alpha.operation = "MULTIPLY"
    mul_diff_obj_alpha.location = (x, 300)
    obj_alpha_inputs1 = mul_diff_obj_alpha.inputs[1]
    assert isinstance(obj_alpha_inputs1, bpy.types.NodeSocketFloat), "Inputs[1] is not a NodeSocketFloat"
    obj_alpha_inputs1.default_value = 1.0
    links.new(mul_diff_obj_alpha.inputs[0], object_alpha.outputs[0])
    if not envmapped and not bumpmapped and diffuse_tex is not None:
        links.new(mul_diff_obj_alpha.inputs[1], diffuse_tex.outputs[1])

    # Transparent BSDF
    transparent_bsdf_node: bpy.types.Node = nodes.new("ShaderNodeBsdfTransparent")
    if not isinstance(transparent_bsdf_node, bpy.types.ShaderNodeBsdfTransparent):
        raise TypeError(f"Expected ShaderNodeBsdfTransparent, got {transparent_bsdf_node.__class__.__name__}")
    transparent_bsdf: bpy.types.ShaderNodeBsdfTransparent = transparent_bsdf_node
    transparent_bsdf.name = NodeName.TRANSPARENT_BSDF
    transparent_bsdf.location = (x, 0)

    # Mix matte and glossy
    mix_matte_glossy_node: bpy.types.Node = nodes.new("ShaderNodeMixShader")
    if not isinstance(mix_matte_glossy_node, bpy.types.ShaderNodeMixShader):
        raise TypeError(f"Expected ShaderNodeMixShader, got {mix_matte_glossy_node.__class__.__name__}")
    mix_matte_glossy: bpy.types.ShaderNodeMixShader = mix_matte_glossy_node
    mix_matte_glossy.name = NodeName.MIX_MATTE_GLOSSY
    mix_matte_glossy.location = (x, -300)
    inputs0 = mix_matte_glossy.inputs[0]
    inputs0.default_value = 1.0  # pyright: ignore[reportAttributeAccessIssue]
    if envmapped and diffuse_tex is not None:
        links.new(mix_matte_glossy.inputs[0], diffuse_tex.outputs[1])
    links.new(mix_matte_glossy.inputs[1], glossy_bsdf.outputs[0])
    links.new(mix_matte_glossy.inputs[2], add_diffuse_emission.outputs[0])

    x += 300

    # Add opaque and transparent
    add_opaque_transparent_node: bpy.types.Node = nodes.new("ShaderNodeAddShader")
    if not isinstance(add_opaque_transparent_node, bpy.types.ShaderNodeAddShader):
        raise TypeError(f"Expected ShaderNodeAddShader, got {add_opaque_transparent_node.__class__.__name__}")
    add_opaque_transparent: bpy.types.ShaderNodeAddShader = add_opaque_transparent_node
    add_opaque_transparent.name = NodeName.ADD_OPAQUE_TRANSPARENT
    add_opaque_transparent.location = (x, 0)
    links.new(add_opaque_transparent.inputs[0], transparent_bsdf.outputs[0])
    links.new(add_opaque_transparent.inputs[1], mix_matte_glossy.outputs[0])

    # Mix opaque and transparent
    mix_opaque_transparent_node: bpy.types.Node = nodes.new("ShaderNodeMixShader")
    if not isinstance(mix_opaque_transparent_node, bpy.types.ShaderNodeMixShader):
        raise TypeError(f"Expected ShaderNodeMixShader, got {mix_opaque_transparent_node.__class__.__name__}")
    mix_opaque_transparent: bpy.types.ShaderNodeMixShader = mix_opaque_transparent_node
    mix_opaque_transparent.name = NodeName.MIX_OPAQUE_TRANSPARENT
    mix_opaque_transparent.location = (x, -300)
    links.new(mix_opaque_transparent.inputs[0], mul_diff_obj_alpha.outputs[0])
    links.new(mix_opaque_transparent.inputs[1], transparent_bsdf.outputs[0])
    links.new(mix_opaque_transparent.inputs[2], mix_matte_glossy.outputs[0])

    x += 300

    # Material output node
    material_output_node: bpy.types.Node = nodes.new("ShaderNodeOutputMaterial")
    if not isinstance(material_output_node, bpy.types.ShaderNodeOutputMaterial):
        raise TypeError(f"Expected ShaderNodeOutputMaterial, got {material_output_node.__class__.__name__}")
    material_output: bpy.types.ShaderNodeOutputMaterial = material_output_node
    material_output.location = (x, 0)
    if additive:
        links.new(material_output.inputs[0], add_opaque_transparent.outputs[0])
    else:
        links.new(material_output.inputs[0], mix_opaque_transparent.outputs[0])

    material.use_backface_culling = not decal
    material.blend_method = "BLEND" if additive else "HASHED"


def _texture_get_image(texture: bpy.types.Texture) -> bpy.types.Image | None:
    """Return linked image for IMAGE textures (RNA field omitted from Texture stubs)."""
    if texture.type != "IMAGE":
        return None
    img = getattr(texture, "image", None)
    if img is None:
        return None
    if not isinstance(img, bpy.types.Image):
        raise TypeError(f"Texture [{texture.name}].image is not an Image, got {img.__class__.__name__}")
    return img


def _texture_set_image(texture: bpy.types.Texture, image: bpy.types.Image) -> None:
    """Assign image on IMAGE textures (RNA field omitted from Texture stubs)."""
    if texture.type != "IMAGE":
        raise ValueError(f"Texture [{texture.name}] is not IMAGE type, cannot set .image")
    setattr(texture, "image", image)


def get_or_create_texture(name: str, search_paths: list[str]) -> bpy.types.Texture:
    if name in bpy.data.textures:
        return bpy.data.textures[name]

    if name in bpy.data.images:
        image = bpy.data.images[name]
    else:
        image = create_image(name, search_paths)

    texture = bpy.data.textures.new(name, type="IMAGE")
    _texture_set_image(texture, image)
    texture.use_fake_user = True

    return texture


def create_image(name: str, search_paths: list[str]) -> bpy.types.Image:
    tga_filename = (name + ".tga").lower()
    txi_filename = (name + ".txi").lower()
    tpc_filename = (name + ".tpc").lower()
    for search_path in search_paths:
        if not os.path.isdir(search_path):
            continue
        tga_path = None
        txi_path = None
        tpc_path = None
        try:
            filenames = os.listdir(search_path)
        except OSError:
            continue
        for filename in filenames:
            lower_filename = filename.lower()
            if lower_filename == tga_filename:
                tga_path = os.path.join(search_path, filename)
            elif lower_filename == txi_filename:
                txi_path = os.path.join(search_path, filename)
            elif lower_filename == tpc_filename:
                tpc_path = os.path.join(search_path, filename)
        if tga_path:
            logger().debug(f"Loading TGA image [{tga_path}]")
            image = image_utils.load_image(tga_path)
            image.name = name
            if txi_path:
                logger().debug(f"Loading TXI file [{txi_path}]")
                with open(txi_path) as txi:
                    txi_lines = txi.readlines()
                    apply_txi_to_image(txi_lines, image)
            return image
        if tpc_path:
            logger().debug(f"Loading TPC image [{tpc_path}]")
            tpc_image = None
            if get_use_pykotor_readers():
                pykotor_tpc = load_tpc_via_pykotor(tpc_path)
                if pykotor_tpc:
                    tpc_image = convert_pykotor_tpc_to_tpcimage(pykotor_tpc)
                if not tpc_image:
                    # Fallback to current reader
                    logger().debug("PyKotor TPC conversion failed, falling back to current reader")
                    tpc_image = TpcReader(tpc_path).load()
            else:
                tpc_image = TpcReader(tpc_path).load()
            image = bpy.data.images.new(name, tpc_image.w, tpc_image.h)
            image.pixels = tpc_image.pixels
            image.update()
            image.pack()
            apply_txi_to_image(tpc_image.txi_lines, image)
            return image

    return bpy.data.images.new(name, 512, 512)


def apply_txi_to_image(txi: list[str], image: bpy.types.Image) -> None:
    for line in txi:
        tokens = line.split()
        if not tokens:
            continue
        lower_token = tokens[0]
        kb = getattr(image, "kb", None)
        if kb is None:
            raise ValueError(f"Image [{image.name}] has no kb property group")
        if lower_token in ["envmaptexture", "bumpyshinytexture"]:
            kb.envmap = tokens[1]
        elif lower_token == "bumpmaptexture":
            kb.bumpmap = tokens[1]
        elif lower_token == "blending":
            kb.additive = tokens[1].lower() == "additive"
        elif lower_token == "decal":
            kb.decal = bool(int(tokens[1]))
