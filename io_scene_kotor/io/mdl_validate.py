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

import re

from ..constants import MeshType
from ..utils import is_dwk_root, is_exported_to_mdl, is_null, is_pwk_root


def _normalized_export_name(obj):
    name = obj.name
    if re.match(r".+\.\d{3}$", name):
        name = name[:-4]
    return name


def _iter_exportable_objects(root_obj):
    stack = [root_obj]
    while stack:
        obj = stack.pop()
        if is_pwk_root(obj) or is_dwk_root(obj):
            continue
        if is_exported_to_mdl(obj):
            yield obj
        stack.extend(reversed(obj.children))


def validate_mdl_export(operator, root_obj):
    export_objects = list(_iter_exportable_objects(root_obj))
    exported_names = [_normalized_export_name(obj) for obj in export_objects]
    lowered_names = [name.lower() for name in exported_names]

    # Duplicate names under a case-insensitive check.
    duplicate_names = []
    seen_names = set()
    for name in lowered_names:
        if name in seen_names and name not in duplicate_names:
            duplicate_names.append(name)
        seen_names.add(name)
    if duplicate_names:
        duplicates = ", ".join(sorted(duplicate_names))
        raise RuntimeError(
            "Duplicate exported node names are not allowed: {}".format(duplicates)
        )

    # Invalid names.
    for obj, name in zip(export_objects, exported_names):
        if not name:
            raise RuntimeError("Object '{}' has an empty exported name".format(obj.name))
        if " " in name or "\t" in name:
            raise RuntimeError(
                "Object '{}' has an invalid exported name '{}'".format(obj.name, name)
            )
        if name.lower() == "root":
            raise RuntimeError(
                "Object '{}' has the reserved exported name 'root'".format(obj.name)
            )

    if len(_normalized_export_name(root_obj)) > 16:
        raise RuntimeError(
            "Model name '{}' exceeds the 16 character limit".format(
                _normalized_export_name(root_obj)
            )
        )

    # Animroot must point to an exported node.
    if not is_null(root_obj.kb.animroot):
        animroot_name = root_obj.kb.animroot.lower()
        if animroot_name not in seen_names:
            raise RuntimeError(
                "Anim Root '{}' does not match any exported node".format(
                    root_obj.kb.animroot
                )
            )

    # Only one collision/AABB mesh is allowed on the main model.
    aabb_meshes = [
        obj
        for obj in export_objects
        if obj.type == "MESH" and obj.kb.meshtype == MeshType.AABB
    ]
    if len(aabb_meshes) > 1:
        raise RuntimeError(
            "Multiple AABB meshes found in model export: {}".format(
                ", ".join(obj.name for obj in aabb_meshes)
            )
        )

    overweight_vertices = []
    for obj in export_objects:
        if obj.type == "MESH":
            if obj.kb.meshtype in {
                MeshType.TRIMESH,
                MeshType.DANGLYMESH,
                MeshType.SKIN,
                MeshType.AABB,
                MeshType.LIGHTSABER,
            } and len(obj.data.polygons) == 0:
                raise RuntimeError(
                    "Mesh object '{}' has no faces and cannot be exported".format(
                        obj.name
                    )
                )

            for texture_label, texture_name in (
                ("bitmap", obj.kb.bitmap),
                ("bitmap2", obj.kb.bitmap2),
            ):
                if texture_name and len(texture_name) > 16:
                    raise RuntimeError(
                        "Object '{}' has {} '{}' longer than 16 characters".format(
                            obj.name, texture_label, texture_name
                        )
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
        detail = ", ".join(
            "{}:{} verts".format(obj_name, count) for obj_name, count in grouped.items()
        )
        operator.report(
            {"WARNING"},
            "Skin weights exceed 4 influences on export; top 4 will be kept ({})".format(
                detail
            ),
        )
