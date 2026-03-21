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
from collections.abc import Generator

import bpy

from ..constants import MeshType
from ..utils import is_dwk_root, is_exported_to_mdl, is_null, is_pwk_root


class _Op:
    def report(self, level: str | None, message: str) -> None:
        tag = next(iter(level)) if level else "INFO"
        print(f"    [{tag}] {message}")


_op = _Op()


def _normalized_export_name(obj: bpy.types.Object) -> str:
    name = obj.name
    if re.match(r".+\.\d{3}$", name):
        name = name[:-4]
    return name


def _iter_exportable_objects(root_obj: bpy.types.Object) -> Generator[bpy.types.Object, None, None]:
    stack = [root_obj]
    while stack:
        obj = stack.pop()
        if is_pwk_root(obj) or is_dwk_root(obj):
            continue
        if is_exported_to_mdl(obj):
            yield obj
        stack.extend(reversed(obj.children))


def validate_mdl_export(operator: _Op, root_obj: bpy.types.Object) -> None:
    export_objects = list(_iter_exportable_objects(root_obj))
    # Use actual Blender object names for duplicate check so MDLs with duplicate
    # node names (e.g. community models) roundtrip: Blender deduplicates to .001, .002.
    exported_names = [obj.name for obj in export_objects]
    lowered_actual = [name.lower() for name in exported_names]
    normalized_for_animroot = [_normalized_export_name(obj) for obj in export_objects]

    # Duplicate check: only actual duplicate Blender names (same string) are invalid.
    seen_actual = set()
    for name in lowered_actual:
        if name in seen_actual:
            raise RuntimeError(f"Duplicate exported node names are not allowed: {name}")
        seen_actual.add(name)

    # For animroot we accept either actual or normalized name.
    seen_names = set(lowered_actual) | {n.lower() for n in normalized_for_animroot}

    # Invalid names (validate the name that gets written: obj.name).
    for obj in export_objects:
        name = obj.name
        if not name:
            raise RuntimeError(f"Object '{obj.name}' has an empty exported name")
        if " " in name or "\t" in name:
            raise RuntimeError(
                f"Object '{obj.name}' has an invalid exported name '{name}'",
            )
        if name.lower() == "root":
            raise RuntimeError(f"Object '{obj.name}' has the reserved exported name 'root'")
        # Node names have no 16-char limit in the binary format; only root model name does.

    if len(_normalized_export_name(root_obj)) > 16:
        raise RuntimeError(
            f"Model name '{_normalized_export_name(root_obj)}' exceeds the 16 character limit",
        )

    # Animroot must point to an exported node.
    if not is_null(root_obj.kb.animroot):
        animroot_name = root_obj.kb.animroot.lower()
        if animroot_name not in seen_names:
            raise RuntimeError(
                f"Anim Root '{root_obj.kb.animroot}' does not match any exported node",
            )

    # Only one collision/AABB mesh is allowed on the main model.
    aabb_meshes = [
        obj for obj in export_objects if obj.type == "MESH" and obj.kb.meshtype == MeshType.AABB
    ]
    if len(aabb_meshes) > 1:
        raise RuntimeError(
            "Multiple AABB meshes found in model export: {}".format(
                ", ".join(obj.name for obj in aabb_meshes),
            ),
        )

    overweight_vertices = []
    for obj in export_objects:
        if obj.type == "MESH":
            if (
                obj.kb.meshtype
                in {
                    MeshType.TRIMESH,
                    MeshType.DANGLYMESH,
                    MeshType.SKIN,
                    MeshType.AABB,
                    MeshType.LIGHTSABER,
                }
                and len(obj.data.polygons) == 0
            ):
                raise RuntimeError(
                    f"Mesh object '{obj.name}' has no faces and cannot be exported",
                )

            for texture_label, texture_name in (
                ("bitmap", obj.kb.bitmap),
                ("bitmap2", obj.kb.bitmap2),
            ):
                if texture_name and len(texture_name) > 16:
                    raise RuntimeError(
                        f"Object '{obj.name}' has {texture_label} '{texture_name}' longer than 16 characters",
                    )

            if obj.kb.meshtype == MeshType.SKIN:
                for vert in obj.data.vertices:
                    non_zero_groups = sum(
                        1 for group_weight in vert.groups if group_weight.weight > 0.0
                    )
                    if non_zero_groups > 4:
                        overweight_vertices.append((obj.name, vert.index, non_zero_groups))

    if overweight_vertices:
        grouped = {}
        for obj_name, _, _ in overweight_vertices:
            grouped[obj_name] = grouped.get(obj_name, 0) + 1
        detail = ", ".join(f"{obj_name}:{count} verts" for obj_name, count in grouped.items())
        operator.report(
            {"WARNING"},
            f"Skin weights exceed 4 influences on export; top 4 will be kept ({detail})",
        )
