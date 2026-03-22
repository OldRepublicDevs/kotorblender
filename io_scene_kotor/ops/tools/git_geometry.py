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

"""GIT trigger/encounter hull meshes and spawn empties (Blender geometry ↔ PyKotor GIT)."""

from __future__ import annotations

from typing import Any

import bpy
from mathutils import Euler

from ...constants import GitGeometryRole, GitInstanceSection
from ...diagnostic_log import begin_scene_work_span, end_scene_work_span
from ...log_config import get_kb_logger


def _polygon3_to_verts(geometry: Any) -> list[tuple[float, float, float]]:
    out: list[tuple[float, float, float]] = []
    if geometry is None:
        return out
    if hasattr(geometry, "points"):
        for p in geometry.points:
            out.append((float(p.x), float(p.y), float(p.z)))
        return out
    for p in geometry:
        out.append((float(p.x), float(p.y), float(p.z)))
    return out


def _link_geom(
    obj: bpy.types.Object,
    section: str,
    idx: int,
    role: str,
    resref: str,
    spawn_index: int = 0,
) -> None:
    kb = getattr(obj, "kb", None)
    if kb is None:
        return
    kb.git_instance_section = section
    kb.git_instance_index = idx
    kb.git_geometry_role = role
    kb.git_instance_resref = (resref or "")[:32]
    kb.git_spawn_index = int(spawn_index)


def _ensure_hull_material(name: str, rgba: tuple[float, float, float, float]) -> bpy.types.Material:
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.blend_method = "BLEND"
    nt = mat.node_tree
    if nt is None:
        return mat
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (rgba[0], rgba[1], rgba[2], rgba[3])
    em.inputs["Strength"].default_value = 0.4
    out.location = (200, 0)
    em.location = (0, 0)
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def _create_hull_mesh(
    coll: bpy.types.Collection,
    stem: str,
    verts: list[tuple[float, float, float]],
    section: str,
    idx: int,
    role: str,
    resref: str,
    mat: bpy.types.Material,
) -> bpy.types.Object | None:
    if len(verts) < 3:
        return None
    mesh = bpy.data.meshes.new(stem)
    mesh.from_pydata(verts, [], [tuple(range(len(verts)))])
    mesh.update()
    obj = bpy.data.objects.new(stem, mesh)
    mesh.materials.append(mat)
    coll.objects.link(obj)
    _link_geom(obj, section, idx, role, resref, 0)
    return obj


def import_git_polygons_and_spawns(
    coll: bpy.types.Collection,
    git: Any,
) -> int:
    """Create hull meshes for triggers/encounters and empties for encounter spawns."""
    log = get_kb_logger("git_geometry")
    span = begin_scene_work_span(
        log,
        "ops.tools.git_geometry.import_git_polygons_and_spawns",
        coll.name if coll is not None else "",
    )
    err = False
    try:
        return _import_git_polygons_and_spawns_body(coll, git)
    except BaseException:
        err = True
        raise
    finally:
        end_scene_work_span(span, error=err)


def _import_git_polygons_and_spawns_body(
    coll: bpy.types.Collection,
    git: Any,
) -> int:
    mat_tr = _ensure_hull_material(
        "_KB_GIT_TriggerHull",
        (0.15, 0.9, 0.35, 0.35),
    )
    mat_enc = _ensure_hull_material(
        "_KB_GIT_EncounterHull",
        (0.95, 0.4, 0.12, 0.35),
    )
    n = 0
    triggers = getattr(git, "triggers", None)
    if isinstance(triggers, list):
        for i, tr in enumerate(triggers):
            verts = _polygon3_to_verts(getattr(tr, "geometry", None))
            rr_o = getattr(tr, "resref", None)
            rr = str(rr_o) if rr_o is not None else ""
            stem = f"git.triggers.{i}.hull"
            if _create_hull_mesh(coll, stem, verts, GitInstanceSection.TRIGGERS.value, i, GitGeometryRole.TRIGGER_HULL.value, rr, mat_tr):
                n += 1

    encounters = getattr(git, "encounters", None)
    if isinstance(encounters, list):
        for i, enc in enumerate(encounters):
            verts = _polygon3_to_verts(getattr(enc, "geometry", None))
            rre = getattr(enc, "resref", None)
            rr = str(rre) if rre is not None else ""
            stem = f"git.encounters.{i}.hull"
            if _create_hull_mesh(coll, stem, verts, GitInstanceSection.ENCOUNTERS.value, i, GitGeometryRole.ENCOUNTER_HULL.value, rr, mat_enc):
                n += 1

            spawns = getattr(enc, "spawn_points", None)
            if isinstance(spawns, list):
                for j, sp in enumerate(spawns):
                    emp = bpy.data.objects.new(f"git.encounters.{i}.spawn.{j}", None)
                    emp.empty_display_type = "SPHERE"
                    emp.empty_display_size = 0.35
                    emp.location = (float(sp.x), float(sp.y), float(sp.z))
                    emp.rotation_mode = "XYZ"
                    emp.rotation_euler = Euler((0.0, 0.0, float(sp.orientation)), "XYZ")
                    coll.objects.link(emp)
                    _link_geom(emp, GitInstanceSection.ENCOUNTERS.value, i, GitGeometryRole.ENCOUNTER_SPAWN.value, rr, j)
                    n += 1
    return n


def sync_git_geometry_from_blender(git: Any) -> tuple[int, int]:
    """Write hull meshes + spawn empties back onto a loaded PyKotor ``GIT`` object.

    Returns:
        (hull_rows_updated, spawn_rows_updated) approximate counts.

    """
    log = get_kb_logger("git_geometry")
    span = begin_scene_work_span(log, "ops.tools.git_geometry.sync_git_geometry_from_blender", "")
    err = False
    try:
        return _sync_git_geometry_from_blender_body(git)
    except BaseException:
        err = True
        raise
    finally:
        end_scene_work_span(span, error=err)


def _sync_git_geometry_from_blender_body(git: Any) -> tuple[int, int]:
    from utility.common.geometry import Vector3  # PyKotor dependency

    hull_n = 0
    spawn_n = 0

    for obj in bpy.data.objects:
        kb = getattr(obj, "kb", None)
        if kb is None:
            continue
        role = getattr(kb, "git_geometry_role", None)
        if not role or role == GitGeometryRole.NONE.value:
            continue
        section = getattr(kb, "git_instance_section", "")
        idx = int(getattr(kb, "git_instance_index", 0))

        if role == GitGeometryRole.TRIGGER_HULL.value:
            if section != GitInstanceSection.TRIGGERS.value:
                continue
            tl = getattr(git, "triggers", None)
            if not isinstance(tl, list) or idx < 0 or idx >= len(tl):
                continue
            tr = tl[idx]
            geom = getattr(tr, "geometry", None)
            if geom is None or obj.type != "MESH":
                continue
            mesh = obj.data
            if not isinstance(mesh, bpy.types.Mesh) or not mesh.polygons:
                continue
            poly = mesh.polygons[0]
            mw = obj.matrix_world
            geom.points.clear()
            for vi in poly.vertices:
                co = mw @ mesh.vertices[vi].co
                geom.append(Vector3(float(co.x), float(co.y), float(co.z)))
            hull_n += 1

        elif role == GitGeometryRole.ENCOUNTER_HULL.value:
            if section != GitInstanceSection.ENCOUNTERS.value:
                continue
            el = getattr(git, "encounters", None)
            if not isinstance(el, list) or idx < 0 or idx >= len(el):
                continue
            enc = el[idx]
            geom = getattr(enc, "geometry", None)
            if geom is None or obj.type != "MESH":
                continue
            mesh = obj.data
            if not isinstance(mesh, bpy.types.Mesh) or not mesh.polygons:
                continue
            poly = mesh.polygons[0]
            mw = obj.matrix_world
            geom.points.clear()
            for vi in poly.vertices:
                co = mw @ mesh.vertices[vi].co
                geom.append(Vector3(float(co.x), float(co.y), float(co.z)))
            hull_n += 1

        elif role == GitGeometryRole.ENCOUNTER_SPAWN.value:
            if section != GitInstanceSection.ENCOUNTERS.value:
                continue
            el = getattr(git, "encounters", None)
            if not isinstance(el, list) or idx < 0 or idx >= len(el):
                continue
            enc = el[idx]
            spawns = getattr(enc, "spawn_points", None)
            if not isinstance(spawns, list):
                continue
            j = int(getattr(kb, "git_spawn_index", 0))
            if j < 0 or j >= len(spawns):
                continue
            sp = spawns[j]
            w = obj.matrix_world.translation
            sp.x = float(w.x)
            sp.y = float(w.y)
            sp.z = float(w.z)
            sp.orientation = float(obj.rotation_euler.z)
            spawn_n += 1

    return hull_n, spawn_n
