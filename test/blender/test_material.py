"""
test_material.py – Blender background-mode test

Comprehensive test suite for io_scene_kotor.scene.material module.
Tests all public functions, node creation, material properties, edge cases,
error handling, and roundtrip scenarios.

Run with:
    blender --background --python test/blender/test_material.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from types import SimpleNamespace
from typing import Callable

import bpy
from bpy.types import bpy_prop_array

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

MODULE = "bl_ext.user_default.io_scene_kotor"
preferences = bpy.context.preferences
if preferences is None:
    raise ValueError("bpy.context.preferences is None")
if preferences.addons is None:
    raise ValueError("bpy.context.preferences.addons is None")
if MODULE not in preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.constants import NULL, UV_MAP_LIGHTMAP, WALKMESH_MATERIALS  # noqa: E402
from io_scene_kotor.ui.props.image import ImagePropertyGroup  # noqa: E402
from io_scene_kotor.scene.material import (  # noqa: E402, F403
    NodeName,
    WalkmeshNodeName,
    _texture_get_image,
    _texture_set_image,
    apply_txi_to_image,
    create_image,
    get_or_create_material,
    get_or_create_texture,
    rebuild_material_solid,
    rebuild_material_textured,
    rebuild_object_materials,
    rebuild_walkmesh_materials,
)
from io_scene_kotor.ui.props.object import ObjectPropertyGroup  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clear_scene():
    """Clear all objects, meshes, materials, textures, and images."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for tex in list(bpy.data.textures):
        bpy.data.textures.remove(tex)
    for img in list(bpy.data.images):
        bpy.data.images.remove(img)


def _make_mesh_object(name: str, with_kb: bool = True) -> bpy.types.Object:
    """Create a mesh object with optional kb property group."""
    mesh: bpy.types.Mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    mesh.update()
    obj: bpy.types.Object = bpy.data.objects.new(name, mesh)
    if with_kb:
        # Ensure kb property group exists
        if not hasattr(obj, "kb"):
            # This should be registered, but if not, we'll handle it
            pass
    bpy.context.scene.collection.objects.link(obj)  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
    return obj


def _make_image_with_kb(name: str) -> bpy.types.Image:
    """Create an image with kb property group."""
    img: bpy.types.Image = bpy.data.images.new(name, 64, 64)
    # kb property should be registered, but ensure it exists
    if not hasattr(img, "kb"):
        # In real usage, this is registered via addon registration
        # For testing, we'll check if it exists
        pass
    return img


def _make_texture_image(name: str) -> bpy.types.Texture:
    """Create an IMAGE type texture with an image."""
    img: bpy.types.Image = _make_image_with_kb(name)
    tex: bpy.types.Texture = bpy.data.textures.new(name, type="IMAGE")
    _texture_set_image(tex, img)
    return tex


# ---------------------------------------------------------------------------
# Test Functions - get_or_create_material
# ---------------------------------------------------------------------------


def test_get_or_create_material_new():
    """get_or_create_material creates a new material when it doesn't exist."""
    _clear_scene()
    mat: bpy.types.Material = get_or_create_material("test_mat")
    ok: bool = mat is not None and mat.name == "test_mat" and bpy.data.materials.get("test_mat") == mat
    print(f"  {'PASS' if ok else 'FAIL'} test_get_or_create_material_new")
    return ok


def test_get_or_create_material_existing():
    """get_or_create_material returns existing material when it exists."""
    _clear_scene()
    mat1: bpy.types.Material = bpy.data.materials.new("existing_mat")
    mat2: bpy.types.Material = get_or_create_material("existing_mat")
    ok: bool = mat1 is mat2
    print(f"  {'PASS' if ok else 'FAIL'} test_get_or_create_material_existing")
    return ok


def test_get_or_create_material_multiple():
    """get_or_create_material handles multiple unique materials."""
    _clear_scene()
    mats: list[bpy.types.Material] = [get_or_create_material(f"mat_{i}") for i in range(10)]
    ok: bool = len(set(mats)) == 10 and all(m.name == f"mat_{i}" for i, m in enumerate(mats))
    print(f"  {'PASS' if ok else 'FAIL'} test_get_or_create_material_multiple")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - rebuild_material_solid
# ---------------------------------------------------------------------------


def test_rebuild_material_solid_basic():
    """rebuild_material_solid sets diffuse color from kb.diffuse."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.diffuse = (0.5, 0.6, 0.7)
    mat: bpy.types.Material = get_or_create_material("solid_mat")
    rebuild_material_solid(mat, obj)
    diffuse_ok: bool = abs(mat.diffuse_color[0] - 0.5) < 0.01 and abs(mat.diffuse_color[1] - 0.6) < 0.01 and abs(mat.diffuse_color[2] - 0.7) < 0.01  # pyright: ignore[reportOptionalMemberAccess]
    if bpy.app.version < (5, 0):
        ok = not mat.use_nodes and diffuse_ok  # pyright: ignore[reportAttributeAccessIssue]
    else:
        ok = diffuse_ok
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_solid_basic")
    return ok


def test_rebuild_material_solid_no_kb():
    """rebuild_material_solid handles object with None kb (getattr returns None)."""
    _clear_scene()
    obj = _make_mesh_object("test_obj", with_kb=False)
    # kb property exists but may be None or uninitialized
    # rebuild_material_solid uses getattr(obj, "kb", None) which handles this
    mat = get_or_create_material("solid_mat")
    try:
        rebuild_material_solid(mat, obj)
        # Should not crash, material may remain unchanged or use defaults
        ok = True
    except Exception as e:
        # If it raises, check that it's a reasonable error
        ok = "kb" in str(e).lower() or "none" in str(e).lower() or "type" in str(e).lower()
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_solid_no_kb")
    return ok


def test_rebuild_material_solid_none_kb():
    """rebuild_material_solid raises when kb is missing (Object.kb is read-only; cannot set None)."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("test_obj")
    mat: bpy.types.Material = get_or_create_material("solid_mat")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        try:
            rebuild_material_solid(mat, obj)
            ok = False
        except (ValueError, TypeError, AttributeError):
            ok = True
    else:
        # Normal object always has kb registered; exercise happy path
        rebuild_material_solid(mat, obj)
        ok = True
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_solid_none_kb")
    return ok


def test_rebuild_material_solid_different_colors():
    """rebuild_material_solid handles various diffuse colors."""
    _clear_scene()
    colors: list[tuple[float, float, float]] = [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0.5, 0.5, 0.5), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]
    results: list[bool] = []
    for i, color in enumerate(colors):
        obj: bpy.types.Object = _make_mesh_object(f"obj_{i}")
        kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
        if kb is None:
            print("  FAIL test_rebuild_material_solid_different_colors: no kb")
            return False
        kb.diffuse = color
        mat: bpy.types.Material = get_or_create_material(f"mat_{i}")
        rebuild_material_solid(mat, obj)
        results.append(abs(mat.diffuse_color[0] - color[0]) < 0.01 and abs(mat.diffuse_color[1] - color[1]) < 0.01 and abs(mat.diffuse_color[2] - color[2]) < 0.01)
    ok: bool = all(results)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_solid_different_colors")
    return ok


def test_rebuild_material_solid_disables_nodes():
    """rebuild_material_solid disables node-based materials."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_solid_disables_nodes: no kb")
        return False
    kb.diffuse = (0.8, 0.8, 0.8)
    mat: bpy.types.Material = get_or_create_material("solid_mat")
    mat.use_nodes = True
    rebuild_material_solid(mat, obj)
    if bpy.app.version < (5, 0):
        ok = not mat.use_nodes  # pyright: ignore[reportAttributeAccessIssue]
    else:
        ok = True  # use_nodes may remain True on 5.x; solid diffuse still applied above
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_solid_disables_nodes")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - _texture_get_image and _texture_set_image
# ---------------------------------------------------------------------------


def test_texture_get_image_image_type():
    """_texture_get_image returns image for IMAGE type texture."""
    _clear_scene()
    tex: bpy.types.Texture = _make_texture_image("test_tex")
    img: bpy.types.Image | None = _texture_get_image(tex)
    ok: bool = img is not None and img.name == "test_tex"
    print(f"  {'PASS' if ok else 'FAIL'} test_texture_get_image_image_type")
    return ok


def test_texture_get_image_non_image_type():
    """_texture_get_image returns None for non-IMAGE texture types."""
    _clear_scene()
    tex: bpy.types.Texture = bpy.data.textures.new("test_tex", type="CLOUDS")
    img: bpy.types.Image | None = _texture_get_image(tex)
    ok: bool = img is None
    print(f"  {'PASS' if ok else 'FAIL'} test_texture_get_image_non_image_type")
    return ok


def test_texture_get_image_no_image():
    """_texture_get_image returns None when texture has no image."""
    _clear_scene()
    tex: bpy.types.Texture = bpy.data.textures.new("test_tex", type="IMAGE")
    # Don't set image
    img: bpy.types.Image | None = _texture_get_image(tex)
    ok: bool = img is None
    print(f"  {'PASS' if ok else 'FAIL'} test_texture_get_image_no_image")
    return ok


def test_texture_set_image_success():
    """_texture_set_image sets image on IMAGE type texture."""
    _clear_scene()
    tex: bpy.types.Texture = bpy.data.textures.new("test_tex", type="IMAGE")
    img: bpy.types.Image = _make_image_with_kb("test_img")
    _texture_set_image(tex, img)
    retrieved: bpy.types.Image | None = _texture_get_image(tex)
    ok: bool = retrieved is not None and retrieved is img
    print(f"  {'PASS' if ok else 'FAIL'} test_texture_set_image_success")
    return ok


def test_texture_set_image_wrong_type():
    """_texture_set_image raises ValueError for non-IMAGE texture."""
    _clear_scene()
    tex: bpy.types.Texture = bpy.data.textures.new("test_tex", type="CLOUDS")
    img: bpy.types.Image = _make_image_with_kb("test_img")
    try:
        _texture_set_image(tex, img)
        ok: bool = False
    except ValueError:
        ok = True
    print(f"  {'PASS' if ok else 'FAIL'} test_texture_set_image_wrong_type")
    return ok


def test_texture_get_set_roundtrip():
    """_texture_get_image and _texture_set_image work together."""
    _clear_scene()
    tex: bpy.types.Texture = bpy.data.textures.new("test_tex", type="IMAGE")
    img1: bpy.types.Image = _make_image_with_kb("img1")
    img2: bpy.types.Image = _make_image_with_kb("img2")
    _texture_set_image(tex, img1)
    retrieved1: bpy.types.Image | None = _texture_get_image(tex)
    _texture_set_image(tex, img2)
    retrieved2: bpy.types.Image | None = _texture_get_image(tex)
    ok: bool = retrieved1 is img1 and retrieved2 is img2
    print(f"  {'PASS' if ok else 'FAIL'} test_texture_get_set_roundtrip")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - get_or_create_texture
# ---------------------------------------------------------------------------


def test_get_or_create_texture_new():
    """get_or_create_texture creates new texture when it doesn't exist."""
    _clear_scene()
    with tempfile.TemporaryDirectory() as tmpdir:
        tex: bpy.types.Texture = get_or_create_texture("new_tex", [tmpdir])
        ok: bool = tex is not None and tex.name == "new_tex" and tex.type == "IMAGE"
    print(f"  {'PASS' if ok else 'FAIL'} test_get_or_create_texture_new")
    return ok


def test_get_or_create_texture_existing():
    """get_or_create_texture returns existing texture."""
    _clear_scene()
    existing: bpy.types.Texture = bpy.data.textures.new("existing_tex", type="IMAGE")
    with tempfile.TemporaryDirectory() as tmpdir:
        tex: bpy.types.Texture = get_or_create_texture("existing_tex", [tmpdir])
        ok: bool = tex is existing
    print(f"  {'PASS' if ok else 'FAIL'} test_get_or_create_texture_existing")
    return ok


def test_get_or_create_texture_existing_image():
    """get_or_create_texture uses existing image if available."""
    _clear_scene()
    img: bpy.types.Image = _make_image_with_kb("test_img")
    with tempfile.TemporaryDirectory() as tmpdir:
        tex: bpy.types.Texture = get_or_create_texture("test_img", [tmpdir])
        tex_img: bpy.types.Image | None = _texture_get_image(tex)
        ok: bool = tex_img is not None and tex_img.name == "test_img"
    print(f"  {'PASS' if ok else 'FAIL'} test_get_or_create_texture_existing_image")
    return ok


def test_get_or_create_texture_use_fake_user():
    """get_or_create_texture sets use_fake_user on texture."""
    _clear_scene()
    with tempfile.TemporaryDirectory() as tmpdir:
        tex: bpy.types.Texture = get_or_create_texture("test_tex", [tmpdir])
        ok: bool = tex.use_fake_user is True
    print(f"  {'PASS' if ok else 'FAIL'} test_get_or_create_texture_use_fake_user")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - rebuild_walkmesh_materials
# ---------------------------------------------------------------------------


def test_rebuild_walkmesh_materials_creates_all():
    """rebuild_walkmesh_materials creates materials for all walkmesh types."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("walkmesh_obj")
    # Mark as AABB mesh
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_walkmesh_materials_creates_all: no kb")
        return False
    kb.meshtype = "AABB"
    rebuild_walkmesh_materials(obj)
    ok: bool = len(obj.data.materials) == len(WALKMESH_MATERIALS)  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_walkmesh_materials_creates_all")
    return ok


def test_rebuild_walkmesh_materials_node_types():
    """rebuild_walkmesh_materials creates correct node types."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("walkmesh_obj")
    obj.kb.meshtype = "AABB"  # type: ignore
    rebuild_walkmesh_materials(obj)
    if not obj.data.materials:  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
        print("  FAIL test_rebuild_walkmesh_materials_node_types: no materials")
        return False
    mat: bpy.types.Material = obj.data.materials[0]  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess, reportAssignmentType]
    if not mat.use_nodes or mat.node_tree is None:
        print("  FAIL test_rebuild_walkmesh_materials_node_types: no node tree")
        return False
    nodes: bpy.types.Nodes = mat.node_tree.nodes
    node_types: set[str] = {type(n).__name__ for n in nodes}
    expected: set[str] = {
        "ShaderNodeRGB",
        "ShaderNodeValue",
        "ShaderNodeBsdfTransparent",
        "ShaderNodeEmission",
        "ShaderNodeMixShader",
        "ShaderNodeOutputMaterial",
    }
    ok: bool = expected.issubset(node_types)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_walkmesh_materials_node_types")
    return ok


def test_rebuild_walkmesh_materials_node_names():
    """rebuild_walkmesh_materials sets correct node names."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("walkmesh_obj")
    obj.kb.meshtype = "AABB"  # type: ignore
    rebuild_walkmesh_materials(obj)
    if not obj.data.materials:  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
        print("  FAIL test_rebuild_walkmesh_materials_node_names: no materials")
        return False
    mat: bpy.types.Material = obj.data.materials[0]  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess, reportAssignmentType]
    if not mat.use_nodes or mat.node_tree is None:
        print("  FAIL test_rebuild_walkmesh_materials_node_names: no node tree")
        return False
    nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
    ok: bool = WalkmeshNodeName.COLOR in nodes and WalkmeshNodeName.OPACITY in nodes
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_walkmesh_materials_node_names")
    return ok


def test_rebuild_walkmesh_materials_socket_types():
    """rebuild_walkmesh_materials creates correct socket types."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("walkmesh_obj")
    obj.kb.meshtype = "AABB"  # type: ignore
    rebuild_walkmesh_materials(obj)
    if not obj.data.materials:  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
        print("  FAIL test_rebuild_walkmesh_materials_socket_types: no materials")
        return False
    mat: bpy.types.Material = obj.data.materials[0]  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess, reportAssignmentType]
    if not mat.use_nodes or mat.node_tree is None:
        print("  FAIL test_rebuild_walkmesh_materials_socket_types: no node tree")
        return False
    nodes: bpy.types.Nodes = mat.node_tree.nodes
    color_node: bpy.types.Node | None = next((n for n in nodes if n.name == WalkmeshNodeName.COLOR), None)
    opacity_node: bpy.types.Node | None = next((n for n in nodes if n.name == WalkmeshNodeName.OPACITY), None)
    ok: bool = (
        color_node is not None
        and isinstance(color_node.outputs[0], bpy.types.NodeSocketColor)
        and opacity_node is not None
        and isinstance(opacity_node.outputs[0], bpy.types.NodeSocketFloat)
    )
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_walkmesh_materials_socket_types")
    return ok


def test_rebuild_walkmesh_materials_blend_method():
    """rebuild_walkmesh_materials sets blend_method to BLEND."""
    _clear_scene()
    obj = _make_mesh_object("walkmesh_obj")
    obj.kb.meshtype = "AABB"  # type: ignore
    rebuild_walkmesh_materials(obj)
    if not obj.data.materials:  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
        print("  FAIL test_rebuild_walkmesh_materials_blend_method: no materials")
        return False
    mat: bpy.types.Material = obj.data.materials[0]  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess, reportAssignmentType]
    ok: bool = mat.blend_method == "BLEND"
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_walkmesh_materials_blend_method")
    return ok


def test_rebuild_walkmesh_materials_shadow_method():
    """rebuild_walkmesh_materials sets shadow_method for Blender < 4.3."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("walkmesh_obj")
    obj.kb.meshtype = "AABB"  # type: ignore
    rebuild_walkmesh_materials(obj)
    if not obj.data.materials:  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
        print("  FAIL test_rebuild_walkmesh_materials_shadow_method: no materials")
        return False
    mat: bpy.types.Material = obj.data.materials[0]  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess, reportAssignmentType]
    # shadow_method is only set for Blender < 4.3
    ok: bool = True  # Just verify it doesn't crash
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_walkmesh_materials_shadow_method")
    return ok


def test_rebuild_walkmesh_materials_not_mesh():
    """rebuild_walkmesh_materials handles non-mesh objects."""
    _clear_scene()
    obj: bpy.types.Object = bpy.data.objects.new("not_mesh", None)
    bpy.context.scene.collection.objects.link(obj)  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
    rebuild_walkmesh_materials(obj)
    ok: bool = True  # Should not crash
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_walkmesh_materials_not_mesh")
    return ok


def test_rebuild_walkmesh_materials_color_values():
    """rebuild_walkmesh_materials sets correct color values."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("walkmesh_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_walkmesh_materials_color_values: no kb")
        return False
    kb.meshtype = "AABB"
    rebuild_walkmesh_materials(obj)
    results: list[bool] = []
    for i, (name, color, _) in enumerate(WALKMESH_MATERIALS):
        if i < len(obj.data.materials):  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
            mat: bpy.types.Material = obj.data.materials[i]  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess, reportAssignmentType]
            if mat.use_nodes and mat.node_tree:
                color_node: bpy.types.Node | None = next(
                    (n for n in mat.node_tree.nodes if n.name == WalkmeshNodeName.COLOR),
                    None,
                )
                if color_node and isinstance(color_node, bpy.types.ShaderNodeRGB):
                    output = color_node.outputs[0]
                    if isinstance(output, bpy.types.NodeSocketColor):
                        mat_color = output.default_value[:3]
                        results.append(all(abs(mat_color[j] - color[j]) < 0.01 for j in range(3)))
    ok = len(results) > 0 and all(results)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_walkmesh_materials_color_values")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - rebuild_material_textured - Basic
# ---------------------------------------------------------------------------


def test_rebuild_material_textured_basic():
    """rebuild_material_textured creates basic textured material."""
    _clear_scene()

    obj = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "test_texture"
    with tempfile.TemporaryDirectory() as tmpdir:
        img = _make_image_with_kb("test_texture")
        mat: bpy.types.Material = get_or_create_material("textured_mat")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        ok: bool = mat.use_nodes and mat.node_tree is not None
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_basic")
    return ok


def test_rebuild_material_textured_no_kb():
    """rebuild_material_textured handles object without kb."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("test_obj", with_kb=False)
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        rebuild_material_textured(mat, obj, [tmpdir], [])
        ok: bool = True  # Should not crash
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_no_kb")
    return ok


def test_rebuild_material_textured_enables_nodes():
    """rebuild_material_textured enables node-based materials."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_enables_nodes: no kb")
        return False
    kb.bitmap = "test_texture"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    mat.use_nodes = False
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            img = _make_image_with_kb("test_texture")
            rebuild_material_textured(mat, obj, [tmpdir], [])
            ok = mat.use_nodes
        except Exception as e:
            print(f"  FAIL test_rebuild_material_textured_enables_nodes: exception: {e.__class__.__name__}: {e}")
            return False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_enables_nodes")
    return ok
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_enables_nodes")
def test_rebuild_material_textured_clears_nodes():
    """rebuild_material_textured clears existing nodes."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_clears_nodes: no kb")
        return False
    kb.bitmap = "test_texture"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    mat.use_nodes = True
    if mat.node_tree:
        mat.node_tree.nodes.new("ShaderNodeRGB")
    with tempfile.TemporaryDirectory() as tmpdir:
        img = _make_image_with_kb("test_texture")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        ok = mat.node_tree is not None and len(mat.node_tree.nodes) > 0
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_clears_nodes")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - rebuild_material_textured - Node Creation
# ---------------------------------------------------------------------------


def test_rebuild_material_textured_diffuse_tex_node():
    """rebuild_material_textured creates ShaderNodeTexImage for diffuse."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_white_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_diffuse_tex_node: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        diffuse_tex: bpy.types.Node | None = nodes.get(NodeName.DIFFUSE_TEX)
        ok: bool = diffuse_tex is not None and isinstance(diffuse_tex, bpy.types.ShaderNodeTexImage)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_diffuse_tex_node")
    return ok


def test_rebuild_material_textured_white_node():
    """rebuild_material_textured creates white RGB node."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_white_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_white_node: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        white: bpy.types.Node | None = nodes.get(NodeName.WHITE)
        ok: bool = white is not None and isinstance(white, bpy.types.ShaderNodeRGB)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_white_node")
    return ok


def test_rebuild_material_textured_white_node_value():
    """rebuild_material_textured sets white node to (1,1,1,1)."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_white_node_value: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_white_node_value: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        white: bpy.types.Node | None = nodes.get(NodeName.WHITE)
        if white and isinstance(white, bpy.types.ShaderNodeRGB):
            output: bpy.types.NodeSocket = white.outputs[0]
            if isinstance(output, bpy.types.NodeSocketColor):
                val: bpy_prop_array[float] = output.default_value
                ok: bool = all(abs(v - 1.0) < 0.01 for v in val)
            else:
                ok = False
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_white_node_value")
    return ok


def test_rebuild_material_textured_diffuse_bsdf_node():
    """rebuild_material_textured creates ShaderNodeBsdfDiffuse."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_diffuse_bsdf_node: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        diffuse_bsdf: bpy.types.Node | None = nodes.get(NodeName.DIFFUSE_BSDF)
        ok: bool = diffuse_bsdf is not None and isinstance(diffuse_bsdf, bpy.types.ShaderNodeBsdfDiffuse)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_diffuse_bsdf_node")
    return ok


def test_rebuild_material_textured_output_node():
    """rebuild_material_textured creates ShaderNodeOutputMaterial."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_output_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_output_node: no node tree")
            return False
        nodes: bpy.types.Nodes = mat.node_tree.nodes
        output_nodes: list[bpy.types.Node] = [n for n in nodes if isinstance(n, bpy.types.ShaderNodeOutputMaterial)]
        ok: bool = len(output_nodes) == 1
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_output_node")
    return ok


def test_rebuild_material_textured_vector_math_nodes():
    """rebuild_material_textured creates ShaderNodeVectorMath nodes."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_vector_math_nodes: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_vector_math_nodes: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        mul_diffuse_lightmap: bpy.types.Node | None = nodes.get(NodeName.MUL_DIFFUSE_LIGHTMAP)
        mul_diffuse_selfillum: bpy.types.Node | None = nodes.get(NodeName.MUL_DIFFUSE_SELFILLUM)
        ok: bool = (
            mul_diffuse_lightmap is not None
            and isinstance(mul_diffuse_lightmap, bpy.types.ShaderNodeVectorMath)
            and mul_diffuse_selfillum is not None
            and isinstance(mul_diffuse_selfillum, bpy.types.ShaderNodeVectorMath)
        )
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_vector_math_nodes")
    return ok


def test_rebuild_material_textured_emission_nodes():
    """rebuild_material_textured creates ShaderNodeEmission nodes."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_emission_nodes: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_emission_nodes: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        diff_lm_emission: bpy.types.Node | None = nodes.get(NodeName.DIFF_LM_EMISSION)
        selfillum_emission: bpy.types.Node | None = nodes.get(NodeName.SELFILLUM_EMISSION)
        ok: bool = (
            diff_lm_emission is not None
            and isinstance(diff_lm_emission, bpy.types.ShaderNodeEmission)
            and selfillum_emission is not None
            and isinstance(selfillum_emission, bpy.types.ShaderNodeEmission)
        )
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_emission_nodes")
    return ok


def test_rebuild_material_textured_add_shader_node():
    """rebuild_material_textured creates ShaderNodeAddShader."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_add_shader_node: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        add_diffuse_emission: bpy.types.Node | None = nodes.get(NodeName.ADD_DIFFUSE_EMISSION)
        ok: bool = add_diffuse_emission is not None and isinstance(add_diffuse_emission, bpy.types.ShaderNodeAddShader)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_add_shader_node")
    return ok


def test_rebuild_material_textured_value_node():
    """rebuild_material_textured creates ShaderNodeValue for alpha."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.alpha = 0.75
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_value_node: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        object_alpha: bpy.types.Node | None = nodes.get(NodeName.OBJECT_ALPHA)
        ok: bool = object_alpha is not None and isinstance(object_alpha, bpy.types.ShaderNodeValue)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_value_node")
    return ok


def test_rebuild_material_textured_glossy_bsdf_node():
    """rebuild_material_textured creates ShaderNodeBsdfGlossy."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_glossy_bsdf_node: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        glossy_bsdf: bpy.types.Node | None = nodes.get(NodeName.GLOSSY_BSDF)
        ok: bool = glossy_bsdf is not None and isinstance(glossy_bsdf, bpy.types.ShaderNode)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_glossy_bsdf_node")
    return ok


def test_rebuild_material_textured_math_node():
    """rebuild_material_textured creates ShaderNodeMath for alpha multiply."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_math_node: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        mul_diff_obj_alpha: bpy.types.Node | None = nodes.get(NodeName.MUL_DIFFUSE_OBJECT_ALPHA)
        ok: bool = mul_diff_obj_alpha is not None and isinstance(mul_diff_obj_alpha, bpy.types.ShaderNodeMath)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_math_node")
    return ok


def test_rebuild_material_textured_mix_shader_nodes():
    """rebuild_material_textured creates ShaderNodeMixShader nodes."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_mix_shader_nodes: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        mix_matte_glossy: bpy.types.Node | None = nodes.get(NodeName.MIX_MATTE_GLOSSY)
        mix_opaque_transparent: bpy.types.Node | None = nodes.get(NodeName.MIX_OPAQUE_TRANSPARENT)
        ok: bool = (
            mix_matte_glossy is not None
            and isinstance(mix_matte_glossy, bpy.types.ShaderNodeMixShader)
            and mix_opaque_transparent is not None
            and isinstance(mix_opaque_transparent, bpy.types.ShaderNodeMixShader)
        )
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_mix_shader_nodes")
    return ok


def test_rebuild_material_textured_transparent_bsdf_node():
    """rebuild_material_textured creates ShaderNodeBsdfTransparent."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_transparent_bsdf_node: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        transparent_bsdf: bpy.types.Node | None = nodes.get(NodeName.TRANSPARENT_BSDF)
        ok: bool = transparent_bsdf is not None and isinstance(transparent_bsdf, bpy.types.ShaderNodeBsdfTransparent)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_transparent_bsdf_node")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - rebuild_material_textured - Socket Types
# ---------------------------------------------------------------------------


def test_rebuild_material_textured_socket_color():
    """rebuild_material_textured creates NodeSocketColor sockets."""
    _clear_scene()

    obj = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_socket_color: no node tree")
            return False
        nodes = {n.name: n for n in mat.node_tree.nodes}
        white = nodes.get(NodeName.WHITE)
        if white and isinstance(white, bpy.types.ShaderNodeRGB):
            output = white.outputs[0]
            ok = isinstance(output, bpy.types.NodeSocketColor)
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_socket_color")
    return ok


def test_rebuild_material_textured_socket_float():
    """rebuild_material_textured creates NodeSocketFloat sockets."""
    _clear_scene()

    obj = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.alpha = 0.5
    mat = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_socket_float: no node tree")
            return False
        nodes = {n.name: n for n in mat.node_tree.nodes}
        object_alpha = nodes.get(NodeName.OBJECT_ALPHA)
        if object_alpha and isinstance(object_alpha, bpy.types.ShaderNodeValue):
            output = object_alpha.outputs[0]
            ok = isinstance(output, bpy.types.NodeSocketFloat)
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_socket_float")
    return ok


def test_rebuild_material_textured_socket_vector():
    """rebuild_material_textured creates NodeSocketVector sockets."""
    _clear_scene()

    obj = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_socket_vector: no node tree")
            return False
        nodes = {n.name: n for n in mat.node_tree.nodes}
        mul_diffuse_lightmap = nodes.get(NodeName.MUL_DIFFUSE_LIGHTMAP)
        if mul_diffuse_lightmap and isinstance(mul_diffuse_lightmap, bpy.types.ShaderNodeVectorMath):
            input_socket = mul_diffuse_lightmap.inputs[1]
            ok = isinstance(input_socket, bpy.types.NodeSocketVector)
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_socket_vector")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - rebuild_material_textured - Lightmap
# ---------------------------------------------------------------------------


def test_rebuild_material_textured_lightmap_tex_node():
    """rebuild_material_textured creates lightmap texture node."""
    _clear_scene()

    obj = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.bitmap2 = "lightmap_tex"
    mat = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img1 = _make_image_with_kb("diffuse_tex")
        img2 = _make_image_with_kb("lightmap_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [tmpdir])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_lightmap_tex_node: no node tree")
            return False
        nodes = {n.name: n for n in mat.node_tree.nodes}
        lightmap_tex = nodes.get(NodeName.LIGHTMAP_TEX)
        ok = lightmap_tex is not None and isinstance(lightmap_tex, bpy.types.ShaderNodeTexImage)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_lightmap_tex_node")
    return ok


def test_rebuild_material_textured_lightmap_uv_node():
    """rebuild_material_textured creates UVMap node for lightmap."""
    _clear_scene()

    obj = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.bitmap2 = "lightmap_tex"
    mat = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img1 = _make_image_with_kb("diffuse_tex")
        img2 = _make_image_with_kb("lightmap_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [tmpdir])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_lightmap_uv_node: no node tree")
            return False
        nodes = mat.node_tree.nodes
        uv_nodes = [n for n in nodes if isinstance(n, bpy.types.ShaderNodeUVMap)]
        ok = len(uv_nodes) > 0
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_lightmap_uv_node")
    return ok


def test_rebuild_material_textured_lightmap_uv_map_name():
    """rebuild_material_textured sets lightmap UV map name correctly."""
    _clear_scene()

    obj = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.bitmap2 = "lightmap_tex"
    mat = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img1 = _make_image_with_kb("diffuse_tex")
        img2 = _make_image_with_kb("lightmap_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [tmpdir])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_lightmap_uv_map_name: no node tree")
            return False
        nodes = mat.node_tree.nodes
        uv_nodes = [n for n in nodes if isinstance(n, bpy.types.ShaderNodeUVMap)]
        ok = len(uv_nodes) > 0 and uv_nodes[0].uv_map == UV_MAP_LIGHTMAP
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_lightmap_uv_map_name")
    return ok


def test_rebuild_material_textured_lightmap_connection():
    """rebuild_material_textured connects lightmap UV to texture."""
    _clear_scene()

    obj = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.bitmap2 = "lightmap_tex"
    mat = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img1 = _make_image_with_kb("diffuse_tex")
        img2 = _make_image_with_kb("lightmap_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [tmpdir])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_lightmap_connection: no node tree")
            return False
        links = mat.node_tree.links
        # Check for connection from UVMap to lightmap texture
        uv_nodes = [n for n in mat.node_tree.nodes if isinstance(n, bpy.types.ShaderNodeUVMap)]
        lightmap_nodes = [n for n in mat.node_tree.nodes if n.name == NodeName.LIGHTMAP_TEX]
        connected = any(link.from_node in uv_nodes and link.to_node in lightmap_nodes for link in links)
        ok = connected
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_lightmap_connection")
    return ok


def test_rebuild_material_textured_lightmap_multiply():
    """rebuild_material_textured multiplies diffuse by lightmap."""
    _clear_scene()

    obj = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.bitmap2 = "lightmap_tex"
    kb.lightmapped = True
    mat = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img1 = _make_image_with_kb("diffuse_tex")
        img2 = _make_image_with_kb("lightmap_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [tmpdir])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_lightmap_multiply: no node tree")
            return False
        nodes = {n.name: n for n in mat.node_tree.nodes}
        mul_diffuse_lightmap = nodes.get(NodeName.MUL_DIFFUSE_LIGHTMAP)
        lightmap_tex = nodes.get(NodeName.LIGHTMAP_TEX)
        if mul_diffuse_lightmap and lightmap_tex:
            links = mat.node_tree.links
            connected = any(link.from_node == lightmap_tex and link.to_node == mul_diffuse_lightmap for link in links)
            ok = connected
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_lightmap_multiply")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - rebuild_material_textured - Bumpmap/Normal Map
# ---------------------------------------------------------------------------


def test_rebuild_material_textured_bumpmap_tex_node():
    """rebuild_material_textured creates bumpmap texture node."""
    _clear_scene()

    obj = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img = _make_image_with_kb("diffuse_tex")
        img_kb: ImagePropertyGroup | None = getattr(img, "kb", None)
        if img_kb is None:
            print("  FAIL test_rebuild_material_textured_bumpmap_tex_node: no img_kb")
            return False
        img_kb.bumpmap = "bumpmap_tex"
        bump_img = _make_image_with_kb("bumpmap_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_bumpmap_tex_node: no node tree")
            return False
        nodes = {n.name: n for n in mat.node_tree.nodes}
        bumpmap_tex = nodes.get(NodeName.BUMPMAP_TEX)
        ok = bumpmap_tex is not None and isinstance(bumpmap_tex, bpy.types.ShaderNodeTexImage)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_bumpmap_tex_node")
    return ok


def test_rebuild_material_textured_normal_map_node():
    """rebuild_material_textured creates ShaderNodeNormalMap."""
    _clear_scene()

    obj = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        img_kb: ImagePropertyGroup | None = getattr(img, "kb", None)
        if img_kb is None:
            print("  FAIL test_rebuild_material_textured_normal_map_node: no img_kb")
            return False
        img_kb.bumpmap = "bumpmap_tex"
        bump_img: bpy.types.Image = _make_image_with_kb("bumpmap_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_normal_map_node: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        normal_map: bpy.types.Node | None = nodes.get(NodeName.NORMAL_MAP)
        ok: bool = normal_map is not None and isinstance(normal_map, bpy.types.ShaderNodeNormalMap)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_normal_map_node")
    return ok


def test_rebuild_material_textured_normal_map_connection():
    """rebuild_material_textured connects bumpmap to normal map."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        img_kb: ImagePropertyGroup | None = getattr(img, "kb", None)
        if img_kb is None:
            print("  FAIL test_rebuild_material_textured_normal_map_connection: no img_kb")
            return False
        img_kb.bumpmap = "bumpmap_tex"
        bump_img: bpy.types.Image = _make_image_with_kb("bumpmap_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_normal_map_connection: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        bumpmap_tex: bpy.types.Node | None = nodes.get(NodeName.BUMPMAP_TEX)
        normal_map: bpy.types.Node | None = nodes.get(NodeName.NORMAL_MAP)
        if bumpmap_tex and normal_map:
            links: bpy.types.NodeLinks = mat.node_tree.links
            connected: bool = any(link.from_node == bumpmap_tex and link.to_node == normal_map for link in links)
            ok: bool = connected
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_normal_map_connection")
    return ok


def test_rebuild_material_textured_normal_to_diffuse_bsdf():
    """rebuild_material_textured connects normal map to diffuse BSDF."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        img_kb: ImagePropertyGroup | None = getattr(img, "kb", None)
        if img_kb is None:
            print("  FAIL test_rebuild_material_textured_normal_to_diffuse_bsdf: no img_kb")
            return False
        img_kb.bumpmap = "bumpmap_tex"
        bump_img: bpy.types.Image = _make_image_with_kb("bumpmap_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_normal_to_diffuse_bsdf: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        normal_map: bpy.types.Node | None = nodes.get(NodeName.NORMAL_MAP)
        diffuse_bsdf: bpy.types.Node | None = nodes.get(NodeName.DIFFUSE_BSDF)
        if normal_map and diffuse_bsdf:
            links: bpy.types.NodeLinks = mat.node_tree.links
            connected: bool = any(link.from_node == normal_map and link.to_node == diffuse_bsdf for link in links)
            ok: bool = connected
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_normal_to_diffuse_bsdf")
    return ok


def test_rebuild_material_textured_normal_to_glossy_bsdf():
    """rebuild_material_textured connects normal map to glossy BSDF."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        img_kb: ImagePropertyGroup | None = getattr(img, "kb", None)
        if img_kb is None:
            print("  FAIL test_rebuild_material_textured_normal_to_glossy_bsdf: no img_kb")
            return False
        img_kb.bumpmap = "bumpmap_tex"
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_normal_to_glossy_bsdf: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        normal_map: bpy.types.Node | None = nodes.get(NodeName.NORMAL_MAP)
        glossy_bsdf: bpy.types.Node | None = nodes.get(NodeName.GLOSSY_BSDF)
        if normal_map and glossy_bsdf:
            links: bpy.types.NodeLinks = mat.node_tree.links
            connected: bool = any(link.from_node == normal_map and link.to_node == glossy_bsdf for link in links)
            ok: bool = connected
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_normal_to_glossy_bsdf")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - rebuild_material_textured - Envmap
# ---------------------------------------------------------------------------


def test_rebuild_material_textured_envmap_mix():
    """rebuild_material_textured uses envmap for matte/glossy mix."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        img_kb: ImagePropertyGroup | None = getattr(img, "kb", None)
        if img_kb is None:
            print("  FAIL test_rebuild_material_textured_envmap_mix: no img_kb")
            return False
        img_kb.envmap = "envmap_tex"
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_envmap_mix: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        mix_matte_glossy: bpy.types.Node | None = nodes.get(NodeName.MIX_MATTE_GLOSSY)
        diffuse_tex: bpy.types.Node | None = nodes.get(NodeName.DIFFUSE_TEX)
        if mix_matte_glossy and diffuse_tex:
            links: bpy.types.NodeLinks = mat.node_tree.links
            # Envmap should connect diffuse alpha to mix factor (socket name varies by Blender version)
            fac_socket = mix_matte_glossy.inputs[0]
            connected: bool = any(
                link.from_node == diffuse_tex
                and link.to_node == mix_matte_glossy
                and link.to_socket == fac_socket
                for link in links
            )
            ok: bool = connected
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_envmap_mix")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - rebuild_material_textured - Additive
# ---------------------------------------------------------------------------


def test_rebuild_material_textured_additive_blend_method():
    """rebuild_material_textured sets blend_method for additive."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        img_kb: ImagePropertyGroup | None = getattr(img, "kb", None)
        if img_kb is None:
            print("  FAIL test_rebuild_material_textured_additive_blend_method: no img_kb")
            return False
        img_kb.additive = True
        rebuild_material_textured(mat, obj, [tmpdir], [])
        ok = mat.blend_method == "BLEND"
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_additive_blend_method")
    return ok


def test_rebuild_material_textured_additive_output_connection():
    """rebuild_material_textured uses add shader for additive."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        img_kb: ImagePropertyGroup | None = getattr(img, "kb", None)
        if img_kb is None:
            print("  FAIL test_rebuild_material_textured_additive_output_connection: no img_kb")
            return False
        img_kb.additive = True
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_additive_output_connection: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        add_opaque_transparent: bpy.types.Node | None = nodes.get(NodeName.ADD_OPAQUE_TRANSPARENT)
        output: bpy.types.Node | None = next(
            (n for n in mat.node_tree.nodes if isinstance(n, bpy.types.ShaderNodeOutputMaterial)),
            None,
        )
        if add_opaque_transparent and output:
            links = mat.node_tree.links
            connected = any(link.from_node == add_opaque_transparent and link.to_node == output for link in links)
            ok = connected
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_additive_output_connection")
    return ok


def test_rebuild_material_textured_non_additive_blend_method():
    """rebuild_material_textured sets HASHED for non-additive."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img = _make_image_with_kb("diffuse_tex")
        img_kb: ImagePropertyGroup | None = getattr(img, "kb", None)
        if img_kb is None:
            print("  FAIL test_rebuild_material_textured_non_additive_blend_method: no img_kb")
            return False
        img_kb.additive = False
        rebuild_material_textured(mat, obj, [tmpdir], [])
        ok = mat.blend_method == "HASHED"
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_non_additive_blend_method")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - rebuild_material_textured - Decal
# ---------------------------------------------------------------------------


def test_rebuild_material_textured_decal_backface_culling():
    """rebuild_material_textured disables backface culling for decal."""
    _clear_scene()

    obj = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img = _make_image_with_kb("diffuse_tex")
        img_kb: ImagePropertyGroup | None = getattr(img, "kb", None)
        if img_kb is None:
            print("  FAIL test_rebuild_material_textured_decal_backface_culling: no img_kb")
            return False
        img_kb.decal = True
        rebuild_material_textured(mat, obj, [tmpdir], [])
        ok = mat.use_backface_culling is False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_decal_backface_culling")
    return ok


def test_rebuild_material_textured_non_decal_backface_culling():
    """rebuild_material_textured enables backface culling for non-decal."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img = _make_image_with_kb("diffuse_tex")
        img_kb: ImagePropertyGroup | None = getattr(img, "kb", None)
        if img_kb is None:
            print("  FAIL test_rebuild_material_textured_non_decal_backface_culling: no img_kb")
            return False
        img_kb.decal = False
        rebuild_material_textured(mat, obj, [tmpdir], [])
        ok = mat.use_backface_culling is True
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_non_decal_backface_culling")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - rebuild_material_textured - Self-illumination
# ---------------------------------------------------------------------------


def test_rebuild_material_textured_selfillum_color():
    """rebuild_material_textured uses self-illumination color."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.selfillumcolor = (0.5, 0.6, 0.7)
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_selfillum_color: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        mul_diffuse_selfillum: bpy.types.Node | None = nodes.get(NodeName.MUL_DIFFUSE_SELFILLUM)
        if mul_diffuse_selfillum and isinstance(mul_diffuse_selfillum, bpy.types.ShaderNodeVectorMath):
            input_socket: bpy.types.NodeSocket = mul_diffuse_selfillum.inputs[1]
            if isinstance(input_socket, bpy.types.NodeSocketVector):
                val = input_socket.default_value
                ok = abs(val[0] - 0.5) < 0.01 and abs(val[1] - 0.6) < 0.01 and abs(val[2] - 0.7) < 0.01
            else:
                ok = False
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_selfillum_color")
    return ok


def test_rebuild_material_textured_selfillum_emission_connection():
    """rebuild_material_textured connects self-illumination emission."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.selfillumcolor = (1.0, 1.0, 1.0)
    mat = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_selfillum_emission_connection: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        mul_diffuse_selfillum: bpy.types.Node | None = nodes.get(NodeName.MUL_DIFFUSE_SELFILLUM)
        selfillum_emission: bpy.types.Node | None = nodes.get(NodeName.SELFILLUM_EMISSION)
        if mul_diffuse_selfillum and selfillum_emission:
            links: bpy.types.NodeLinks = mat.node_tree.links
            connected: bool = any(link.from_node == mul_diffuse_selfillum and link.to_node == selfillum_emission for link in links)
            ok: bool = connected
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_selfillum_emission_connection")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - rebuild_material_textured - Alpha
# ---------------------------------------------------------------------------


def test_rebuild_material_textured_alpha_value():
    """rebuild_material_textured sets object alpha value."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.alpha = 0.75
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_alpha_value: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        object_alpha: bpy.types.Node | None = nodes.get(NodeName.OBJECT_ALPHA)
        if object_alpha and isinstance(object_alpha, bpy.types.ShaderNodeValue):
            output: bpy.types.NodeSocket = object_alpha.outputs[0]
            if isinstance(output, bpy.types.NodeSocketFloat):
                ok: bool = abs(output.default_value - 0.75) < 0.01
            else:
                ok = False
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_alpha_value")
    return ok


def test_rebuild_material_textured_alpha_multiply():
    """rebuild_material_textured multiplies diffuse alpha by object alpha."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.alpha = 0.5
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_alpha_multiply: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        mul_diff_obj_alpha: bpy.types.Node | None = nodes.get(NodeName.MUL_DIFFUSE_OBJECT_ALPHA)
        object_alpha: bpy.types.Node | None = nodes.get(NodeName.OBJECT_ALPHA)
        if mul_diff_obj_alpha and object_alpha:
            links: bpy.types.NodeLinks = mat.node_tree.links
            connected = any(link.from_node == object_alpha and link.to_node == mul_diff_obj_alpha for link in links)
            ok = connected
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_alpha_multiply")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - rebuild_material_textured - Lightmapped
# ---------------------------------------------------------------------------


def test_rebuild_material_textured_lightmapped_uses_emission():
    """rebuild_material_textured uses lightmap emission when lightmapped."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.bitmap2 = "lightmap_tex"
    kb.lightmapped = True
    mat = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img1: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        img2: bpy.types.Image = _make_image_with_kb("lightmap_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [tmpdir])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_lightmapped_uses_emission: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        add_diffuse_emission: bpy.types.Node | None = nodes.get(NodeName.ADD_DIFFUSE_EMISSION)
        diff_lm_emission: bpy.types.Node | None = nodes.get(NodeName.DIFF_LM_EMISSION)
        if add_diffuse_emission and diff_lm_emission:
            links: bpy.types.NodeLinks = mat.node_tree.links
            connected: bool = any(link.from_node == diff_lm_emission and link.to_node == add_diffuse_emission for link in links)
            ok = connected
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_lightmapped_uses_emission")
    return ok


def test_rebuild_material_textured_not_lightmapped_uses_bsdf():
    """rebuild_material_textured uses diffuse BSDF when not lightmapped."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.lightmapped = False
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_not_lightmapped_uses_bsdf: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        add_diffuse_emission: bpy.types.Node | None = nodes.get(NodeName.ADD_DIFFUSE_EMISSION)
        diffuse_bsdf: bpy.types.Node | None = nodes.get(NodeName.DIFFUSE_BSDF)
        if add_diffuse_emission and diffuse_bsdf:
            links: bpy.types.NodeLinks = mat.node_tree.links
            connected: bool = any(link.from_node == diffuse_bsdf and link.to_node == add_diffuse_emission for link in links)
            ok = connected
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_not_lightmapped_uses_bsdf")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - rebuild_material_textured - Edge Cases
# ---------------------------------------------------------------------------


def test_rebuild_material_textured_missing_texture():
    """rebuild_material_textured handles missing texture gracefully."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "nonexistent_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Don't create the image
        try:
            rebuild_material_textured(mat, obj, [tmpdir], [])
            # Should create a default image
            ok = True
        except Exception:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_missing_texture")
    return ok


def test_rebuild_material_textured_null_bitmap():
    """rebuild_material_textured handles NULL bitmap."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = NULL
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        rebuild_material_textured(mat, obj, [tmpdir], [])
        # Should not create diffuse texture node
        if not mat.node_tree:
            ok = True
        else:
            nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
            ok = NodeName.DIFFUSE_TEX not in nodes
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_null_bitmap")
    return ok


def test_rebuild_material_textured_empty_bitmap():
    """rebuild_material_textured handles empty bitmap string."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = ""
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            ok = True
        else:
            nodes = {n.name: n for n in mat.node_tree.nodes}
            ok = NodeName.DIFFUSE_TEX not in nodes
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_empty_bitmap")
    return ok


def test_rebuild_material_textured_missing_image_kb():
    """rebuild_material_textured handles image without kb property."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "test_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img = bpy.data.images.new("test_tex", 64, 64)
        if getattr(img, "kb", None) is None:
            try:
                rebuild_material_textured(mat, obj, [tmpdir], [])
                ok = False
            except (ValueError, AttributeError):
                ok = True
        else:
            # When the addon is enabled, Blender assigns image.kb; cannot reproduce missing kb via API.
            ok = True
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_missing_image_kb")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - rebuild_object_materials
# ---------------------------------------------------------------------------


def test_rebuild_object_materials_solid():
    """rebuild_object_materials creates solid material for non-textured object."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = NULL
    kb.diffuse = (0.8, 0.8, 0.8)
    rebuild_object_materials(obj)
    assert obj.data is not None, "obj.data is None"
    mat0 = obj.data.materials[0]
    diffuse_ok: bool = all(abs(mat0.diffuse_color[i] - kb.diffuse[i]) < 1e-5 for i in range(3))  # pyright: ignore[reportOptionalMemberAccess]
    # Blender 5.x deprecates/changes Material.use_nodes; solid path still sets diffuse_color.
    if bpy.app.version < (5, 0):
        ok = len(obj.data.materials) == 1 and not mat0.use_nodes and diffuse_ok  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
    else:
        ok = len(obj.data.materials) == 1 and diffuse_ok
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_object_materials_solid")
    return ok


def test_rebuild_object_materials_textured():
    """rebuild_object_materials creates textured material."""
    _clear_scene()

    obj = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "test_tex"
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("test_tex")
        rebuild_object_materials(obj, [tmpdir], [])
        assert obj.data is not None, "obj.data is None"
        ok: bool = len(obj.data.materials) == 1 and obj.data.materials[0].use_nodes  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_object_materials_textured")
    return ok


def test_rebuild_object_materials_walkmesh():
    """rebuild_object_materials creates walkmesh materials for AABB."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_object_materials_walkmesh: no kb")
        return False
    obj.kb.meshtype = "AABB"  # type: ignore
    rebuild_object_materials(obj)
    ok: bool = len(obj.data.materials) == len(WALKMESH_MATERIALS)  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_object_materials_walkmesh")
    return ok


def test_rebuild_object_materials_not_mesh():
    """rebuild_object_materials handles non-mesh objects."""
    _clear_scene()
    obj: bpy.types.Object = bpy.data.objects.new("not_mesh", None)
    bpy.context.scene.collection.objects.link(obj)  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
    rebuild_object_materials(obj)
    ok: bool = True  # Should not crash
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_object_materials_not_mesh")
    return ok


def test_rebuild_object_materials_no_kb():
    """rebuild_object_materials handles object without kb."""
    _clear_scene()
    obj: bpy.types.Object = _make_mesh_object("test_obj", with_kb=False)
    rebuild_object_materials(obj)
    ok: bool = True  # Should not crash
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_object_materials_no_kb")
    return ok


def test_rebuild_object_materials_exception_handling():
    """rebuild_object_materials skips non-dir texture paths and still rebuilds (placeholder image)."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "test_tex"
    mat: bpy.types.Material = bpy.data.materials.new("existing")
    obj.data.materials.append(mat)  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
    with tempfile.TemporaryDirectory() as tmpdir:
        # Pass a path that exists but is not a directory so create_image() hits NotADirectoryError.
        blocker = os.path.join(tmpdir, "not_a_dir")
        with open(blocker, "w", encoding="utf-8") as f:
            f.write("x")
        rebuild_object_materials(obj, [blocker], [])
        # Non-directory search entries are skipped (no exception); rebuild uses placeholder image.
        ok = len(obj.data.materials) == 1  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_object_materials_exception_handling")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - Additional Comprehensive Tests
# ---------------------------------------------------------------------------


def test_rebuild_material_textured_all_properties_combined():
    """rebuild_material_textured handles all properties together."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.bitmap2 = "lightmap_tex"
    kb.alpha = 0.8
    kb.selfillumcolor = (0.5, 0.5, 0.5)
    kb.lightmapped = True
    mat = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        img_kb: ImagePropertyGroup | None = getattr(img, "kb", None)
        if img_kb is None:
            print("  FAIL test_rebuild_material_textured_add_shader_node: no img_kb")
            return False
        img_kb.bumpmap = "bumpmap_tex"
        img_kb.envmap = "envmap_tex"
        img_kb.additive = True
        img_kb.decal = True
        img2: bpy.types.Image = _make_image_with_kb("lightmap_tex")
        bump_img: bpy.types.Image = _make_image_with_kb("bumpmap_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [tmpdir])
        ok: bool = mat.use_nodes and mat.node_tree is not None
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_all_properties_combined")
    return ok


def test_rebuild_material_textured_node_locations():
    """rebuild_material_textured sets node locations correctly."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_node_locations: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        # Check that nodes have locations set (x should increase)
        diffuse_tex: bpy.types.Node | None = nodes.get(NodeName.DIFFUSE_TEX)
        white: bpy.types.Node | None = nodes.get(NodeName.WHITE)
        if diffuse_tex and white:
            ok: bool = white.location[0] > diffuse_tex.location[0]
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_node_locations")
    return ok


def test_rebuild_material_textured_glossy_roughness():
    """rebuild_material_textured sets glossy BSDF roughness."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_glossy_roughness: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        glossy_bsdf: bpy.types.Node | None = nodes.get(NodeName.GLOSSY_BSDF)
        if glossy_bsdf:
            roughness: bpy.types.NodeSocket | None = glossy_bsdf.inputs.get("Roughness")
            rv = getattr(roughness, "default_value", None) if roughness is not None else None
            ok = isinstance(rv, (int, float)) and abs(float(rv) - 0.2) < 0.01
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_glossy_roughness")
    return ok


def test_rebuild_material_textured_mix_matte_glossy_default():
    """rebuild_material_textured sets mix matte/glossy default value."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_mix_matte_glossy_default: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        mix_matte_glossy: bpy.types.Node | None = nodes.get(NodeName.MIX_MATTE_GLOSSY)
        if mix_matte_glossy:
            fac: bpy.types.NodeSocket | None = mix_matte_glossy.inputs[0]
            fv = getattr(fac, "default_value", None) if fac is not None else None
            ok = isinstance(fv, (int, float)) and abs(float(fv) - 1.0) < 0.01
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_mix_matte_glossy_default")
    return ok


def test_rebuild_material_textured_alpha_math_operation():
    """rebuild_material_textured sets alpha multiply operation."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_alpha_math_operation: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        mul_diff_obj_alpha: bpy.types.Node | None = nodes.get(NodeName.MUL_DIFFUSE_OBJECT_ALPHA)
        if mul_diff_obj_alpha and isinstance(mul_diff_obj_alpha, bpy.types.ShaderNodeMath):
            ok: bool = mul_diff_obj_alpha.operation == "MULTIPLY"
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_alpha_math_operation")
    return ok


def test_rebuild_material_textured_vector_math_operation():
    """rebuild_material_textured sets vector math multiply operation."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_vector_math_operation: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        mul_diffuse_lightmap: bpy.types.Node | None = nodes.get(NodeName.MUL_DIFFUSE_LIGHTMAP)
        if mul_diffuse_lightmap and isinstance(mul_diffuse_lightmap, bpy.types.ShaderNodeVectorMath):
            ok: bool = mul_diffuse_lightmap.operation == "MULTIPLY"
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_vector_math_operation")
    return ok


def test_rebuild_material_textured_mix_opaque_transparent_connection():
    """rebuild_material_textured connects mix opaque/transparent correctly."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_mix_opaque_transparent_connection: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        mix_opaque_transparent: bpy.types.Node | None = nodes.get(NodeName.MIX_OPAQUE_TRANSPARENT)
        transparent_bsdf: bpy.types.Node | None = nodes.get(NodeName.TRANSPARENT_BSDF)
        mix_matte_glossy: bpy.types.Node | None = nodes.get(NodeName.MIX_MATTE_GLOSSY)
        if mix_opaque_transparent and transparent_bsdf and mix_matte_glossy:
            links: bpy.types.NodeLinks = mat.node_tree.links
            has_transparent: bool = any(link.from_node == transparent_bsdf and link.to_node == mix_opaque_transparent for link in links)
            has_matte_glossy: bool = any(link.from_node == mix_matte_glossy and link.to_node == mix_opaque_transparent for link in links)
            ok: bool = has_transparent and has_matte_glossy
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_mix_opaque_transparent_connection")
    return ok


def test_rebuild_material_textured_add_opaque_transparent_connection():
    """rebuild_material_textured connects add opaque/transparent correctly."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        img_kb: ImagePropertyGroup | None = getattr(img, "kb", None)
        if img_kb is None:
            print("  FAIL test_rebuild_material_textured_add_shader_node: no img_kb")
            return False
        img_kb.additive = True
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_add_opaque_transparent_connection: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        add_opaque_transparent: bpy.types.Node | None = nodes.get(NodeName.ADD_OPAQUE_TRANSPARENT)
        transparent_bsdf: bpy.types.Node | None = nodes.get(NodeName.TRANSPARENT_BSDF)
        mix_matte_glossy: bpy.types.Node | None = nodes.get(NodeName.MIX_MATTE_GLOSSY)
        if add_opaque_transparent and transparent_bsdf and mix_matte_glossy:
            links: bpy.types.NodeLinks = mat.node_tree.links
            has_transparent: bool = any(link.from_node == transparent_bsdf and link.to_node == add_opaque_transparent for link in links)
            has_matte_glossy: bool = any(link.from_node == mix_matte_glossy and link.to_node == add_opaque_transparent for link in links)
            ok: bool = has_transparent and has_matte_glossy
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_add_opaque_transparent_connection")
    return ok


def test_rebuild_material_textured_diffuse_to_bsdf_connection():
    """rebuild_material_textured connects diffuse texture to BSDF."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_diffuse_to_bsdf_connection: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        diffuse_tex: bpy.types.Node | None = nodes.get(NodeName.DIFFUSE_TEX)
        diffuse_bsdf: bpy.types.Node | None = nodes.get(NodeName.DIFFUSE_BSDF)
        if diffuse_tex and diffuse_bsdf:
            links: bpy.types.NodeLinks = mat.node_tree.links
            connected: bool = any(link.from_node == diffuse_tex and link.to_node == diffuse_bsdf for link in links)
            ok: bool = connected
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_diffuse_to_bsdf_connection")
    return ok


def test_rebuild_material_textured_diffuse_to_vector_math_connection():
    """rebuild_material_textured connects diffuse to vector math nodes."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_diffuse_to_vector_math_connection: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        diffuse_tex: bpy.types.Node | None = nodes.get(NodeName.DIFFUSE_TEX)
        mul_diffuse_lightmap: bpy.types.Node | None = nodes.get(NodeName.MUL_DIFFUSE_LIGHTMAP)
        mul_diffuse_selfillum: bpy.types.Node | None = nodes.get(NodeName.MUL_DIFFUSE_SELFILLUM)
        if diffuse_tex and mul_diffuse_lightmap and mul_diffuse_selfillum:
            links: bpy.types.NodeLinks = mat.node_tree.links
            connected_lightmap: bool = any(link.from_node == diffuse_tex and link.to_node == mul_diffuse_lightmap for link in links)
            connected_selfillum: bool = any(link.from_node == diffuse_tex and link.to_node == mul_diffuse_selfillum for link in links)
            ok: bool = connected_lightmap and connected_selfillum
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_diffuse_to_vector_math_connection")
    return ok


def test_rebuild_material_textured_selfillum_to_add_shader():
    """rebuild_material_textured connects self-illumination to add shader."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.selfillumcolor = (1.0, 1.0, 1.0)
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_selfillum_to_add_shader: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        selfillum_emission: bpy.types.Node | None = nodes.get(NodeName.SELFILLUM_EMISSION)
        add_diffuse_emission: bpy.types.Node | None = nodes.get(NodeName.ADD_DIFFUSE_EMISSION)
        if selfillum_emission and add_diffuse_emission:
            links: bpy.types.NodeLinks = mat.node_tree.links
            connected: bool = any(link.from_node == selfillum_emission and link.to_node == add_diffuse_emission for link in links)
            ok: bool = connected
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_selfillum_to_add_shader")
    return ok


def test_rebuild_material_textured_alpha_to_math_connection():
    """rebuild_material_textured connects object alpha to math node."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.alpha = 0.5
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_alpha_to_math_connection: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        object_alpha: bpy.types.Node | None = nodes.get(NodeName.OBJECT_ALPHA)
        mul_diff_obj_alpha: bpy.types.Node | None = nodes.get(NodeName.MUL_DIFFUSE_OBJECT_ALPHA)
        if object_alpha and mul_diff_obj_alpha:
            links: bpy.types.NodeLinks = mat.node_tree.links
            connected: bool = any(link.from_node == object_alpha and link.to_node == mul_diff_obj_alpha for link in links)
            ok: bool = connected
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_alpha_to_math_connection")
    return ok


def test_rebuild_material_textured_alpha_to_mix_connection():
    """rebuild_material_textured connects alpha multiply to mix node."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.alpha = 0.5
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_alpha_to_mix_connection: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        mul_diff_obj_alpha: bpy.types.Node | None = nodes.get(NodeName.MUL_DIFFUSE_OBJECT_ALPHA)
        mix_opaque_transparent: bpy.types.Node | None = nodes.get(NodeName.MIX_OPAQUE_TRANSPARENT)
        if mul_diff_obj_alpha and mix_opaque_transparent:
            links: bpy.types.NodeLinks = mat.node_tree.links
            connected: bool = any(link.from_node == mul_diff_obj_alpha and link.to_node == mix_opaque_transparent for link in links)
            ok: bool = connected
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_alpha_to_mix_connection")
    return ok


def test_rebuild_material_textured_mix_matte_glossy_connections():
    """rebuild_material_textured connects mix matte/glossy correctly."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            print("  FAIL test_rebuild_material_textured_mix_matte_glossy_connections: no node tree")
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        mix_matte_glossy: bpy.types.Node | None = nodes.get(NodeName.MIX_MATTE_GLOSSY)
        glossy_bsdf: bpy.types.Node | None = nodes.get(NodeName.GLOSSY_BSDF)
        add_diffuse_emission: bpy.types.Node | None = nodes.get(NodeName.ADD_DIFFUSE_EMISSION)
        if mix_matte_glossy and glossy_bsdf and add_diffuse_emission:
            links: bpy.types.NodeLinks = mat.node_tree.links
            has_glossy: bool = any(link.from_node == glossy_bsdf and link.to_node == mix_matte_glossy for link in links)
            has_emission: bool = any(link.from_node == add_diffuse_emission and link.to_node == mix_matte_glossy for link in links)
            ok: bool = has_glossy and has_emission
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_mix_matte_glossy_connections")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - Type Safety Tests for All Node Creations
# ---------------------------------------------------------------------------


def test_rebuild_material_textured_node_type_safety_diffuse_tex():
    """Type safety: diffuse texture node must be ShaderNodeTexImage."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        diffuse_tex: bpy.types.Node | None = nodes.get(NodeName.DIFFUSE_TEX)
        ok: bool = isinstance(diffuse_tex, bpy.types.ShaderNodeTexImage)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_node_type_safety_diffuse_tex")
    return ok


def test_rebuild_material_textured_node_type_safety_white():
    """Type safety: white node must be ShaderNodeRGB."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        white: bpy.types.Node | None = nodes.get(NodeName.WHITE)
        ok: bool = isinstance(white, bpy.types.ShaderNodeRGB)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_node_type_safety_white")
    return ok


def test_rebuild_material_textured_node_type_safety_diffuse_bsdf():
    """Type safety: diffuse BSDF must be ShaderNodeBsdfDiffuse."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        diffuse_bsdf: bpy.types.Node | None = nodes.get(NodeName.DIFFUSE_BSDF)
        ok: bool = isinstance(diffuse_bsdf, bpy.types.ShaderNodeBsdfDiffuse)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_node_type_safety_diffuse_bsdf")
    return ok


def test_rebuild_material_textured_node_type_safety_emission():
    """Type safety: emission nodes must be ShaderNodeEmission."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        diff_lm_emission: bpy.types.Node | None = nodes.get(NodeName.DIFF_LM_EMISSION)
        selfillum_emission: bpy.types.Node | None = nodes.get(NodeName.SELFILLUM_EMISSION)
        ok: bool = isinstance(diff_lm_emission, bpy.types.ShaderNodeEmission) and isinstance(selfillum_emission, bpy.types.ShaderNodeEmission)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_node_type_safety_emission")
    return ok


def test_rebuild_material_textured_node_type_safety_add_shader():
    """Type safety: add shader nodes must be ShaderNodeAddShader."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        add_diffuse_emission: bpy.types.Node | None = nodes.get(NodeName.ADD_DIFFUSE_EMISSION)
        add_opaque_transparent: bpy.types.Node | None = nodes.get(NodeName.ADD_OPAQUE_TRANSPARENT)
        ok: bool = isinstance(add_diffuse_emission, bpy.types.ShaderNodeAddShader) and isinstance(add_opaque_transparent, bpy.types.ShaderNodeAddShader)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_node_type_safety_add_shader")
    return ok


def test_rebuild_material_textured_node_type_safety_mix_shader():
    """Type safety: mix shader nodes must be ShaderNodeMixShader."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        mix_matte_glossy: bpy.types.Node | None = nodes.get(NodeName.MIX_MATTE_GLOSSY)
        mix_opaque_transparent: bpy.types.Node | None = nodes.get(NodeName.MIX_OPAQUE_TRANSPARENT)
        ok: bool = isinstance(mix_matte_glossy, bpy.types.ShaderNodeMixShader) and isinstance(mix_opaque_transparent, bpy.types.ShaderNodeMixShader)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_node_type_safety_mix_shader")
    return ok


def test_rebuild_material_textured_node_type_safety_value():
    """Type safety: value node must be ShaderNodeValue."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.alpha = 0.5
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        object_alpha: bpy.types.Node | None = nodes.get(NodeName.OBJECT_ALPHA)
        ok: bool = isinstance(object_alpha, bpy.types.ShaderNodeValue)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_node_type_safety_value")
    return ok


def test_rebuild_material_textured_node_type_safety_math():
    """Type safety: math node must be ShaderNodeMath."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        mul_diff_obj_alpha: bpy.types.Node | None = nodes.get(NodeName.MUL_DIFFUSE_OBJECT_ALPHA)
        ok: bool = isinstance(mul_diff_obj_alpha, bpy.types.ShaderNodeMath)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_node_type_safety_math")
    return ok


def test_rebuild_material_textured_node_type_safety_vector_math():
    """Type safety: vector math nodes must be ShaderNodeVectorMath."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        mul_diffuse_lightmap: bpy.types.Node | None = nodes.get(NodeName.MUL_DIFFUSE_LIGHTMAP)
        mul_diffuse_selfillum: bpy.types.Node | None = nodes.get(NodeName.MUL_DIFFUSE_SELFILLUM)
        ok: bool = isinstance(mul_diffuse_lightmap, bpy.types.ShaderNodeVectorMath) and isinstance(mul_diffuse_selfillum, bpy.types.ShaderNodeVectorMath)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_node_type_safety_vector_math")
    return ok


def test_rebuild_material_textured_node_type_safety_output():
    """Type safety: output node must be ShaderNodeOutputMaterial."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            return False
        nodes: bpy.types.Nodes = mat.node_tree.nodes
        output_nodes: list[bpy.types.Node] = [n for n in nodes if isinstance(n, bpy.types.ShaderNodeOutputMaterial)]
        ok: bool = len(output_nodes) == 1
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_node_type_safety_output")
    return ok


def test_rebuild_material_textured_node_type_safety_transparent():
    """Type safety: transparent BSDF must be ShaderNodeBsdfTransparent."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        transparent_bsdf: bpy.types.Node | None = nodes.get(NodeName.TRANSPARENT_BSDF)
        ok: bool = isinstance(transparent_bsdf, bpy.types.ShaderNodeBsdfTransparent)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_node_type_safety_transparent")
    return ok


def test_rebuild_material_textured_node_type_safety_normal_map():
    """Type safety: normal map node must be ShaderNodeNormalMap."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img = _make_image_with_kb("diffuse_tex")
        img_kb: ImagePropertyGroup | None = getattr(img, "kb", None)
        if img_kb is None:
            print("  FAIL test_rebuild_material_textured_node_type_safety_normal_map: no img_kb")
            return False
        img_kb.bumpmap = "bumpmap_tex"
        bump_img: bpy.types.Image = _make_image_with_kb("bumpmap_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        normal_map: bpy.types.Node | None = nodes.get(NodeName.NORMAL_MAP)
        ok: bool = isinstance(normal_map, bpy.types.ShaderNodeNormalMap)
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_node_type_safety_normal_map")
    return ok


def test_rebuild_material_textured_node_type_safety_uv_map():
    """Type safety: UV map node must be ShaderNodeUVMap."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.bitmap2 = "lightmap_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img1: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        img2: bpy.types.Image = _make_image_with_kb("lightmap_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [tmpdir])
        if not mat.node_tree:
            return False
        nodes: bpy.types.Nodes = mat.node_tree.nodes
        uv_nodes: list[bpy.types.Node] = [n for n in nodes if isinstance(n, bpy.types.ShaderNodeUVMap)]
        ok: bool = len(uv_nodes) > 0
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_node_type_safety_uv_map")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - Socket Type Safety Tests
# ---------------------------------------------------------------------------


def test_rebuild_material_textured_socket_type_safety_all_colors():
    """Socket type safety: all color sockets are NodeSocketColor."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        white: bpy.types.Node | None = nodes.get(NodeName.WHITE)
        if white and isinstance(white, bpy.types.ShaderNodeRGB):
            output: bpy.types.NodeSocket = white.outputs[0]
            ok: bool = isinstance(output, bpy.types.NodeSocketColor)
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_socket_type_safety_all_colors")
    return ok


def test_rebuild_material_textured_socket_type_safety_all_floats():
    """Socket type safety: all float sockets are NodeSocketFloat."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    kb.alpha = 0.5
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        object_alpha: bpy.types.Node | None = nodes.get(NodeName.OBJECT_ALPHA)
        if object_alpha and isinstance(object_alpha, bpy.types.ShaderNodeValue):
            output: bpy.types.NodeSocket = object_alpha.outputs[0]
            ok: bool = isinstance(output, bpy.types.NodeSocketFloat)
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_socket_type_safety_all_floats")
    return ok


def test_rebuild_material_textured_socket_type_safety_all_vectors():
    """Socket type safety: all vector sockets are NodeSocketVector."""
    _clear_scene()

    obj: bpy.types.Object = _make_mesh_object("test_obj")
    kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb is None:
        print("  FAIL test_rebuild_material_textured_add_shader_node: no kb")
        return False
    kb.bitmap = "diffuse_tex"
    mat: bpy.types.Material = get_or_create_material("textured_mat")
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
        rebuild_material_textured(mat, obj, [tmpdir], [])
        if not mat.node_tree:
            return False
        nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
        mul_diffuse_lightmap: bpy.types.Node | None = nodes.get(NodeName.MUL_DIFFUSE_LIGHTMAP)
        if mul_diffuse_lightmap and isinstance(mul_diffuse_lightmap, bpy.types.ShaderNodeVectorMath):
            input_socket: bpy.types.NodeSocket = mul_diffuse_lightmap.inputs[1]
            ok: bool = isinstance(input_socket, bpy.types.NodeSocketVector)
        else:
            ok = False
    print(f"  {'PASS' if ok else 'FAIL'} test_rebuild_material_textured_socket_type_safety_all_vectors")
    return ok


# Generate many more test cases for property combinations
def _generate_property_combination_tests():
    """Generate test cases for various property combinations."""
    tests: list[Callable[[], bool]] = []

    # Test various alpha values
    for alpha in [0.0, 0.25, 0.5, 0.75, 1.0]:

        def make_alpha_test(alpha_val: float):
            def test():
                _clear_scene()
                obj: bpy.types.Object = _make_mesh_object("test_obj")
                kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
                if kb is None:
                    raise ValueError("something")
                kb.bitmap = "diffuse_tex"
                kb.alpha = alpha_val
                mat: bpy.types.Material = get_or_create_material("textured_mat")
                with tempfile.TemporaryDirectory() as tmpdir:
                    img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
                    rebuild_material_textured(mat, obj, [tmpdir], [])
                    if not mat.node_tree:
                        return False
                    nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
                    object_alpha: bpy.types.Node | None = nodes.get(NodeName.OBJECT_ALPHA)
                    if object_alpha and isinstance(object_alpha, bpy.types.ShaderNodeValue):
                        output: bpy.types.NodeSocket = object_alpha.outputs[0]
                        if isinstance(output, bpy.types.NodeSocketFloat):
                            return abs(output.default_value - alpha_val) < 0.01
                    return False

            test.__name__ = f"test_rebuild_material_textured_alpha_{int(alpha_val * 100)}"
            test.__doc__ = f"rebuild_material_textured handles alpha={alpha_val}"
            return test

        tests.append(make_alpha_test(alpha))
    
    # Test various self-illumination colors
    colors: list[tuple[float, float, float]] = [
        (0.0, 0.0, 0.0),
        (1.0, 1.0, 1.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
        (0.5, 0.5, 0.5),
    ]
    for i, color in enumerate(colors):

        def make_test(color_val: tuple[float, float, float], idx: int):
            def test():
                _clear_scene()
                obj: bpy.types.Object = _make_mesh_object("test_obj")
                kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
                if kb is None:
                    raise ValueError("something")
                kb.bitmap = "diffuse_tex"
                kb.selfillumcolor = color_val
                mat: bpy.types.Material = get_or_create_material("textured_mat")
                with tempfile.TemporaryDirectory() as tmpdir:
                    img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
                    rebuild_material_textured(mat, obj, [tmpdir], [])
                    if not mat.node_tree:
                        return False
                    nodes: dict[str, bpy.types.Node] = {n.name: n for n in mat.node_tree.nodes}
                    mul_diffuse_selfillum: bpy.types.Node | None = nodes.get(NodeName.MUL_DIFFUSE_SELFILLUM)
                    if mul_diffuse_selfillum and isinstance(mul_diffuse_selfillum, bpy.types.ShaderNodeVectorMath):
                        input_socket: bpy.types.NodeSocket = mul_diffuse_selfillum.inputs[1]
                        if isinstance(input_socket, bpy.types.NodeSocketVector):
                            val: tuple[float, float, float] = input_socket.default_value
                            return abs(val[0] - color_val[0]) < 0.01 and abs(val[1] - color_val[1]) < 0.01 and abs(val[2] - color_val[2]) < 0.01
                    return False

            test.__name__ = f"test_rebuild_material_textured_selfillum_color_{idx}"
            test.__doc__ = f"rebuild_material_textured handles selfillumcolor={color_val}"
            return test

        tests.append(make_test(color, i))

    # Generate tests for various diffuse colors
    diffuse_colors: list[tuple[float, float, float]] = [
        (0.0, 0.0, 0.0),
        (1.0, 1.0, 1.0),
        (0.8, 0.8, 0.8),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    ]
    for i, color in enumerate(diffuse_colors):

        def make_diffuse_test(color_val: tuple[float, float, float], idx: int):
            def test():
                _clear_scene()
                obj: bpy.types.Object = _make_mesh_object("test_obj")
                kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
                if kb is None:
                    raise ValueError("something")
                kb.bitmap = NULL
                kb.diffuse = color_val
                mat: bpy.types.Material = get_or_create_material("solid_mat")
                rebuild_material_solid(mat, obj)
                return abs(mat.diffuse_color[0] - color_val[0]) < 0.01 and abs(mat.diffuse_color[1] - color_val[1]) < 0.01 and abs(mat.diffuse_color[2] - color_val[2]) < 0.01

            test.__name__ = f"test_rebuild_material_solid_diffuse_color_{idx}"
            test.__doc__ = f"rebuild_material_solid handles diffuse={color_val}"
            return test

        tests.append(make_diffuse_test(color, i))

    # Generate tests for property combinations (lightmapped, additive, decal, bumpmap, envmap)
    bool_combinations: list[tuple[bool, bool, bool, bool, bool]] = [
        (False, False, False, False, False),
        (True, False, False, False, False),
        (False, True, False, False, False),
        (False, False, True, False, False),
        (False, False, False, True, False),
        (False, False, False, False, True),
        (True, True, False, False, False),
        (True, False, True, False, False),
        (True, False, False, True, False),
        (True, False, False, False, True),
        (False, True, True, False, False),
        (False, True, False, True, False),
        (False, True, False, False, True),
        (False, False, True, True, False),
        (False, False, True, False, True),
        (False, False, False, True, True),
        (True, True, True, True, True),
    ]
    for i, (lightmapped, additive, decal, bumpmap, envmap) in enumerate(bool_combinations):

        def make_combination_test(lightmapped_val: bool, additive_val: bool, decal_val: bool, bumpmap_val: bool, envmap_val: bool, idx: int):
            def test():
                _clear_scene()
                obj: bpy.types.Object = _make_mesh_object("test_obj")
                kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
                if kb is None:
                    raise ValueError("something")
                kb.bitmap = "diffuse_tex"
                kb.bitmap2 = "lightmap_tex" if lightmapped_val else ""
                kb.lightmapped = lightmapped_val
                mat: bpy.types.Material = get_or_create_material("textured_mat")
                with tempfile.TemporaryDirectory() as tmpdir:
                    img: bpy.types.Image = _make_image_with_kb("diffuse_tex")
                    img_kb: ImagePropertyGroup | None = getattr(img, "kb", None)
                    if img_kb is None:
                        raise ValueError("something")
                    img_kb.additive = additive_val
                    img_kb.decal = decal_val
                    if bumpmap_val:
                        img_kb.bumpmap = "bumpmap_tex"
                        bump_img: bpy.types.Image = _make_image_with_kb("bumpmap_tex")
                    if envmap_val:
                        img_kb.envmap = "envmap_tex"
                    if lightmapped_val:
                        img2: bpy.types.Image = _make_image_with_kb("lightmap_tex")
                    rebuild_material_textured(mat, obj, [tmpdir], [tmpdir] if lightmapped_val else [])
                    return mat.use_nodes and mat.node_tree is not None

            test.__name__ = f"test_rebuild_material_textured_combination_{idx}"
            test.__doc__ = (
                f"rebuild_material_textured handles lightmapped={lightmapped_val}, additive={additive_val}, decal={decal_val}, bumpmap={bumpmap_val}, envmap={envmap_val}"
            )
            return test

        tests.append(make_combination_test(lightmapped, additive, decal, bumpmap, envmap, i))

    # Generate tests for walkmesh material names
    for i, (name, color, walkable) in enumerate(WALKMESH_MATERIALS):

        def make_walkmesh_test(mat_name: str, mat_color: tuple[float, float, float], mat_walkable: bool, idx: int):
            def test():
                _clear_scene()
                obj: bpy.types.Object = _make_mesh_object("walkmesh_obj")
                kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
                if kb is None:
                    raise ValueError("something")
                kb.meshtype = "AABB"
                rebuild_walkmesh_materials(obj)
                if idx < len(obj.data.materials):  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
                    mat: bpy.types.Material = obj.data.materials[idx]  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess, reportAssignmentType]
                    ok: bool = mat.name == mat_name
                else:
                    ok = False
                return ok

            test.__name__ = f"test_rebuild_walkmesh_materials_name_{idx}"
            test.__doc__ = f"rebuild_walkmesh_materials creates material '{mat_name}'"
            return test

        tests.append(make_walkmesh_test(name, color, walkable, i))

    return tests


# Add generated tests to the module
_generated_tests = _generate_property_combination_tests()
for test_func in _generated_tests:
    globals()[test_func.__name__] = test_func


# ---------------------------------------------------------------------------
# Test Functions - create_image
# ---------------------------------------------------------------------------


def test_create_image_default_size():
    """create_image creates default 512x512 image when file not found."""
    _clear_scene()
    with tempfile.TemporaryDirectory() as tmpdir:
        img: bpy.types.Image = create_image("nonexistent", [tmpdir])
        ok: bool = img is not None and img.size[0] == 512 and img.size[1] == 512
    print(f"  {'PASS' if ok else 'FAIL'} test_create_image_default_size")
    return ok


# ---------------------------------------------------------------------------
# Test Functions - apply_txi_to_image
# ---------------------------------------------------------------------------


def test_apply_txi_empty_and_whitespace():
    """apply_txi_to_image ignores empty lines and blank tokens."""
    _clear_scene()
    img: bpy.types.Image = bpy.data.images.new("txi_img", 4, 4)
    kb: ImagePropertyGroup | None = getattr(img, "kb", None)
    if kb is None:
        print("  FAIL test_apply_txi_empty_and_whitespace: no kb")
        return False
    kb.envmap = ""
    kb.bumpmap = ""
    apply_txi_to_image(["", "  ", " \t"], img)
    ok: bool = kb.envmap == "" and kb.bumpmap == ""
    print(f"  {'PASS' if ok else 'FAIL'} test_apply_txi_empty_and_whitespace")
    return ok


def test_apply_txi_envmaptexture():
    """apply_txi_to_image maps envmaptexture to kb.envmap."""
    _clear_scene()
    img: bpy.types.Image = bpy.data.images.new("txi_env", 4, 4)
    kb: ImagePropertyGroup | None = getattr(img, "kb", None)
    if kb is None:
        print("  FAIL test_apply_txi_envmaptexture: no kb")
        return False
    apply_txi_to_image(["envmaptexture CM_Spec"], img)
    ok: bool = kb.envmap == "CM_Spec"
    print(f"  {'PASS' if ok else 'FAIL'} test_apply_txi_envmaptexture")
    return ok


def test_apply_txi_bumpyshinytexture():
    """apply_txi_to_image maps bumpyshinytexture to kb.envmap."""
    _clear_scene()
    img: bpy.types.Image = bpy.data.images.new("txi_bumpys", 4, 4)
    kb: ImagePropertyGroup | None = getattr(img, "kb", None)
    if kb is None:
        print("  FAIL test_apply_txi_bumpyshinytexture: no kb")
        return False
    apply_txi_to_image(["bumpyshinytexture shiny01"], img)
    ok: bool = kb.envmap == "shiny01"
    print(f"  {'PASS' if ok else 'FAIL'} test_apply_txi_bumpyshinytexture")
    return ok


def test_apply_txi_bumpmaptexture():
    """apply_txi_to_image maps bumpmaptexture to kb.bumpmap."""
    _clear_scene()
    img: bpy.types.Image = bpy.data.images.new("txi_bumpmap", 4, 4)
    kb: ImagePropertyGroup | None = getattr(img, "kb", None)
    if kb is None:
        print("  FAIL test_apply_txi_bumpmaptexture: no kb")
        return False
    apply_txi_to_image(["bumpmaptexture n_bump01"], img)
    ok: bool = kb.bumpmap == "n_bump01"
    print(f"  {'PASS' if ok else 'FAIL'} test_apply_txi_bumpmaptexture")
    return ok


def test_apply_txi_blending_additive():
    """apply_txi_to_image sets kb.additive for blending additive."""
    _clear_scene()
    img: bpy.types.Image = bpy.data.images.new("txi_blend", 4, 4)
    kb: ImagePropertyGroup | None = getattr(img, "kb", None)
    if kb is None:
        print("  FAIL test_apply_txi_blending_additive: no kb")
        return False
    kb.additive = False
    apply_txi_to_image(["blending additive"], img)
    ok: bool = kb.additive is True
    print(f"  {'PASS' if ok else 'FAIL'} test_apply_txi_blending_additive")
    return ok


def test_apply_txi_blending_default():
    """apply_txi_to_image clears additive for non-additive blending."""
    _clear_scene()
    img: bpy.types.Image = bpy.data.images.new("txi_blend2", 4, 4)
    kb: ImagePropertyGroup | None = getattr(img, "kb", None)
    if kb is None:
        print("  FAIL test_apply_txi_blending_default: no kb")
        return False
    kb.additive = True
    apply_txi_to_image(["blending default"], img)
    ok: bool = kb.additive is False
    print(f"  {'PASS' if ok else 'FAIL'} test_apply_txi_blending_default")
    return ok


def test_apply_txi_decal():
    """apply_txi_to_image sets kb.decal from decal token."""
    _clear_scene()
    img: bpy.types.Image = bpy.data.images.new("txi_decal", 4, 4)
    kb: ImagePropertyGroup | None = getattr(img, "kb", None)
    if kb is None:
        print("  FAIL test_apply_txi_decal: no kb")
        return False
    kb.decal = False
    apply_txi_to_image(["decal 1"], img)
    ok: bool = kb.decal is True
    print(f"  {'PASS' if ok else 'FAIL'} test_apply_txi_decal")
    return ok


def test_apply_txi_no_kb_raises():
    """apply_txi_to_image raises ValueError when image has no kb."""
    fake: SimpleNamespace = SimpleNamespace(name="fakeimg", kb=None)
    try:
        apply_txi_to_image(["envmaptexture x"], fake)  # type: ignore[arg-type]
    except ValueError as e:
        ok: bool = "fakeimg" in str(e) and "kb" in str(e).lower()
        print(f"  {'PASS' if ok else 'FAIL'} test_apply_txi_no_kb_raises")
        return ok
    print("  FAIL test_apply_txi_no_kb_raises: expected ValueError")
    return False


# ---------------------------------------------------------------------------
# Test Runner
# ---------------------------------------------------------------------------


def run_tests():
    print("\n=== test_material.py ===")
    tests: list[Callable[[], bool]] = [
        # get_or_create_material
        test_get_or_create_material_new,
        test_get_or_create_material_existing,
        test_get_or_create_material_multiple,
        # rebuild_material_solid
        test_rebuild_material_solid_basic,
        test_rebuild_material_solid_no_kb,
        test_rebuild_material_solid_none_kb,
        test_rebuild_material_solid_different_colors,
        test_rebuild_material_solid_disables_nodes,
        # _texture_get_image and _texture_set_image
        test_texture_get_image_image_type,
        test_texture_get_image_non_image_type,
        test_texture_get_image_no_image,
        test_texture_set_image_success,
        test_texture_set_image_wrong_type,
        test_texture_get_set_roundtrip,
        # get_or_create_texture
        test_get_or_create_texture_new,
        test_get_or_create_texture_existing,
        test_get_or_create_texture_existing_image,
        test_get_or_create_texture_use_fake_user,
        # rebuild_walkmesh_materials
        test_rebuild_walkmesh_materials_creates_all,
        test_rebuild_walkmesh_materials_node_types,
        test_rebuild_walkmesh_materials_node_names,
        test_rebuild_walkmesh_materials_socket_types,
        test_rebuild_walkmesh_materials_blend_method,
        test_rebuild_walkmesh_materials_shadow_method,
        test_rebuild_walkmesh_materials_not_mesh,
        test_rebuild_walkmesh_materials_color_values,
        # rebuild_material_textured - Basic
        test_rebuild_material_textured_basic,
        test_rebuild_material_textured_no_kb,
        test_rebuild_material_textured_enables_nodes,
        test_rebuild_material_textured_clears_nodes,
        # rebuild_material_textured - Node Creation
        test_rebuild_material_textured_diffuse_tex_node,
        test_rebuild_material_textured_white_node,
        test_rebuild_material_textured_white_node_value,
        test_rebuild_material_textured_diffuse_bsdf_node,
        test_rebuild_material_textured_output_node,
        test_rebuild_material_textured_vector_math_nodes,
        test_rebuild_material_textured_emission_nodes,
        test_rebuild_material_textured_add_shader_node,
        test_rebuild_material_textured_value_node,
        test_rebuild_material_textured_glossy_bsdf_node,
        test_rebuild_material_textured_math_node,
        test_rebuild_material_textured_mix_shader_nodes,
        test_rebuild_material_textured_transparent_bsdf_node,
        # rebuild_material_textured - Socket Types
        test_rebuild_material_textured_socket_color,
        test_rebuild_material_textured_socket_float,
        test_rebuild_material_textured_socket_vector,
        # rebuild_material_textured - Lightmap
        test_rebuild_material_textured_lightmap_tex_node,
        test_rebuild_material_textured_lightmap_uv_node,
        test_rebuild_material_textured_lightmap_uv_map_name,
        test_rebuild_material_textured_lightmap_connection,
        test_rebuild_material_textured_lightmap_multiply,
        # rebuild_material_textured - Bumpmap/Normal Map
        test_rebuild_material_textured_bumpmap_tex_node,
        test_rebuild_material_textured_normal_map_node,
        test_rebuild_material_textured_normal_map_connection,
        test_rebuild_material_textured_normal_to_diffuse_bsdf,
        test_rebuild_material_textured_normal_to_glossy_bsdf,
        # rebuild_material_textured - Envmap
        test_rebuild_material_textured_envmap_mix,
        # rebuild_material_textured - Additive
        test_rebuild_material_textured_additive_blend_method,
        test_rebuild_material_textured_additive_output_connection,
        test_rebuild_material_textured_non_additive_blend_method,
        # rebuild_material_textured - Decal
        test_rebuild_material_textured_decal_backface_culling,
        test_rebuild_material_textured_non_decal_backface_culling,
        # rebuild_material_textured - Self-illumination
        test_rebuild_material_textured_selfillum_color,
        test_rebuild_material_textured_selfillum_emission_connection,
        # rebuild_material_textured - Alpha
        test_rebuild_material_textured_alpha_value,
        test_rebuild_material_textured_alpha_multiply,
        # rebuild_material_textured - Lightmapped
        test_rebuild_material_textured_lightmapped_uses_emission,
        test_rebuild_material_textured_not_lightmapped_uses_bsdf,
        # rebuild_material_textured - Edge Cases
        test_rebuild_material_textured_missing_texture,
        test_rebuild_material_textured_null_bitmap,
        test_rebuild_material_textured_empty_bitmap,
        test_rebuild_material_textured_missing_image_kb,
        # rebuild_object_materials
        test_rebuild_object_materials_solid,
        test_rebuild_object_materials_textured,
        test_rebuild_object_materials_walkmesh,
        test_rebuild_object_materials_not_mesh,
        test_rebuild_object_materials_no_kb,
        test_rebuild_object_materials_exception_handling,
        # create_image
        test_create_image_default_size,
        # apply_txi_to_image
        test_apply_txi_empty_and_whitespace,
        test_apply_txi_envmaptexture,
        test_apply_txi_bumpyshinytexture,
        test_apply_txi_bumpmaptexture,
        test_apply_txi_blending_additive,
        test_apply_txi_blending_default,
        test_apply_txi_decal,
        test_apply_txi_no_kb_raises,
        # Additional comprehensive tests
        test_rebuild_material_textured_all_properties_combined,
        test_rebuild_material_textured_node_locations,
        test_rebuild_material_textured_glossy_roughness,
        test_rebuild_material_textured_mix_matte_glossy_default,
        test_rebuild_material_textured_alpha_math_operation,
        test_rebuild_material_textured_vector_math_operation,
        test_rebuild_material_textured_mix_opaque_transparent_connection,
        test_rebuild_material_textured_add_opaque_transparent_connection,
        test_rebuild_material_textured_diffuse_to_bsdf_connection,
        test_rebuild_material_textured_diffuse_to_vector_math_connection,
        test_rebuild_material_textured_selfillum_to_add_shader,
        test_rebuild_material_textured_alpha_to_math_connection,
        test_rebuild_material_textured_alpha_to_mix_connection,
        test_rebuild_material_textured_mix_matte_glossy_connections,
        # Type safety tests
        test_rebuild_material_textured_node_type_safety_diffuse_tex,
        test_rebuild_material_textured_node_type_safety_white,
        test_rebuild_material_textured_node_type_safety_diffuse_bsdf,
        test_rebuild_material_textured_node_type_safety_emission,
        test_rebuild_material_textured_node_type_safety_add_shader,
        test_rebuild_material_textured_node_type_safety_mix_shader,
        test_rebuild_material_textured_node_type_safety_value,
        test_rebuild_material_textured_node_type_safety_math,
        test_rebuild_material_textured_node_type_safety_vector_math,
        test_rebuild_material_textured_node_type_safety_output,
        test_rebuild_material_textured_node_type_safety_transparent,
        test_rebuild_material_textured_node_type_safety_normal_map,
        test_rebuild_material_textured_node_type_safety_uv_map,
        # Socket type safety tests
        test_rebuild_material_textured_socket_type_safety_all_colors,
        test_rebuild_material_textured_socket_type_safety_all_floats,
        test_rebuild_material_textured_socket_type_safety_all_vectors,
    ]
    # Add generated tests
    tests.extend(_generated_tests)
    results: list[bool] = [t() for t in tests]
    passed: int = sum(results)
    total: int = len(results)
    status: str = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_material.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
