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

"""Viewport overlay: semi-transparent walkmesh (AABB) fill + edges using Blender GPU API."""

from __future__ import annotations

import bpy
import gpu
from gpu_extras.batch import batch_for_shader

from ..constants import NAME_TO_WALKMESH_MATERIAL
from ..log_config import get_kb_logger
from ..utils import is_aabb_mesh

_draw_handle: object | None = None


def tag_all_view3d_redraw() -> None:
    wm = bpy.context.window_manager
    for win in wm.windows:
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


def _walkmesh_rgba_for_object(obj: bpy.types.Object) -> tuple[float, float, float, float]:
    mesh = obj.data
    if not isinstance(mesh, bpy.types.Mesh) or not mesh.materials or not mesh.polygons:
        return (0.45, 0.45, 0.5, 0.22)
    poly = mesh.polygons[0]
    mid = poly.material_index
    if mid < 0 or mid >= len(mesh.materials):
        return (0.45, 0.45, 0.5, 0.22)
    mat = mesh.materials[mid]
    if mat is None:
        return (0.45, 0.45, 0.5, 0.22)
    row = NAME_TO_WALKMESH_MATERIAL.get(mat.name)
    if row is None:
        return (0.45, 0.45, 0.5, 0.22)
    rgb = row[1]
    walkable = row[2]
    a = 0.24 if walkable else 0.14
    return (float(rgb[0]), float(rgb[1]), float(rgb[2]), a)


def _builtin_uniform_color_shader():
    for name in ("UNIFORM_COLOR", "3D_UNIFORM_COLOR"):
        try:
            return gpu.shader.from_builtin(name)
        except (TypeError, ValueError, KeyError):
            continue
    return gpu.shader.from_builtin("UNIFORM_COLOR")


def _draw_walkmesh_overlay() -> None:
    context = bpy.context
    scene = context.scene
    if scene is None:
        return
    kb = getattr(scene, "kb", None)
    if kb is None or not bool(getattr(kb, "kotor_walkmesh_overlay", False)):
        return

    show_fill = bool(getattr(kb, "kotor_walkmesh_overlay_fill", True))
    show_edges = bool(getattr(kb, "kotor_walkmesh_overlay_edges", True))
    edge_alpha = float(getattr(kb, "kotor_walkmesh_overlay_edge_alpha", 0.55))
    global_alpha = max(0.0, min(1.0, float(getattr(kb, "kotor_walkmesh_overlay_alpha", 1.0))))

    depsgraph = context.evaluated_depsgraph_get()
    line_coords: list[tuple[float, float, float]] = []

    try:
        shader_u = _builtin_uniform_color_shader()
    except Exception:
        return

    gpu.state.depth_test_set(True)
    gpu.state.blend_set("ALPHA")

    if show_fill:
        for obj in scene.objects:
            if not is_aabb_mesh(obj) or obj.type != "MESH":
                continue
            if obj.hide_viewport:
                continue
            eval_obj = obj.evaluated_get(depsgraph)
            data = eval_obj.data
            if not isinstance(data, bpy.types.Mesh):
                continue
            mw = eval_obj.matrix_world
            data.calc_loop_triangles()
            flat: list[tuple[float, float, float]] = []
            for tri in data.loop_triangles:
                for i in range(3):
                    vi = tri.vertices[i]
                    co = data.vertices[vi].co
                    w = mw @ co
                    flat.append((w.x, w.y, w.z))
            if not flat:
                continue
            r, g, b, a = _walkmesh_rgba_for_object(obj)
            batch = batch_for_shader(shader_u, "TRIS", {"pos": flat})
            shader_u.bind()
            shader_u.uniform_float("color", (r, g, b, a * global_alpha))
            batch.draw(shader_u)

    if show_edges:
        for obj in scene.objects:
            if not is_aabb_mesh(obj) or obj.type != "MESH":
                continue
            if obj.hide_viewport:
                continue
            eval_obj = obj.evaluated_get(depsgraph)
            data = eval_obj.data
            if not isinstance(data, bpy.types.Mesh):
                continue
            mw = eval_obj.matrix_world
            for edge in data.edges:
                v0 = data.vertices[edge.vertices[0]].co
                v1 = data.vertices[edge.vertices[1]].co
                p0 = mw @ v0
                p1 = mw @ v1
                line_coords.append((p0.x, p0.y, p0.z))
                line_coords.append((p1.x, p1.y, p1.z))

    if show_edges and line_coords:
        batch_l = batch_for_shader(shader_u, "LINES", {"pos": line_coords})
        shader_u.bind()
        shader_u.uniform_float("color", (0.05, 0.05, 0.08, edge_alpha * global_alpha))
        batch_l.draw(shader_u)

    gpu.state.blend_set("NONE")


def register_walkmesh_overlay() -> None:
    global _draw_handle
    log = get_kb_logger("view3d.walkmesh_overlay")
    if _draw_handle is not None:
        log.debug("event=walkmesh_overlay_register skipped=already_active")
        return
    _draw_handle = bpy.types.SpaceView3D.draw_handler_add(
        _draw_walkmesh_overlay,
        (),
        "WINDOW",
        "POST_VIEW",
    )
    log.debug("event=walkmesh_overlay_register phase=handler_added")


def unregister_walkmesh_overlay() -> None:
    global _draw_handle
    log = get_kb_logger("view3d.walkmesh_overlay")
    if _draw_handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, "WINDOW")
        _draw_handle = None
        log.debug("event=walkmesh_overlay_unregister phase=handler_removed")
    else:
        log.debug("event=walkmesh_overlay_unregister skipped=no_handler")
