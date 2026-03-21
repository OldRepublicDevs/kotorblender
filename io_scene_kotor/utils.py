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

import logging
import os
from collections.abc import Callable

import bpy

from .constants import *  # noqa: F403
from .log_config import get_kb_logger


def logger() -> logging.Logger:
    """Legacy alias: child logger under the configured ``io_scene_kotor`` tree."""
    return get_kb_logger("utils")


def is_dummy_type(obj: bpy.types.Object | None, dummytype: str) -> bool:
    return obj is not None and obj.type == "EMPTY" and obj.kb.dummytype == dummytype


def is_mdl_root(obj: bpy.types.Object | None) -> bool:
    return is_dummy_type(obj, DummyType.MDLROOT)


def is_pwk_root(obj: bpy.types.Object | None) -> bool:
    return is_dummy_type(obj, DummyType.PWKROOT)


def is_dwk_root(obj: bpy.types.Object | None) -> bool:
    return is_dummy_type(obj, DummyType.DWKROOT)


def is_path_point(obj: bpy.types.Object | None) -> bool:
    return is_dummy_type(obj, DummyType.PATHPOINT)


def is_mesh_type(obj: bpy.types.Object | None, meshtype: str) -> bool:
    return obj is not None and obj.type == "MESH" and obj.kb.meshtype == meshtype


def is_skin_mesh(obj: bpy.types.Object | None) -> bool:
    return is_mesh_type(obj, MeshType.SKIN)


def is_aabb_mesh(obj: bpy.types.Object | None) -> bool:
    return is_mesh_type(obj, MeshType.AABB)


def is_char_dummy(obj: bpy.types.Object | None) -> bool:
    dummy = obj is not None and is_dummy_type(obj, DummyType.NONE)
    if not dummy:
        return False
    root = find_mdl_root_of(obj)
    return root is not None and root.kb.classification == Classification.CHARACTER


def is_char_bone(obj: bpy.types.Object | None) -> bool:
    mesh = obj is not None and is_mesh_type(obj, MeshType.TRIMESH)
    if not mesh:
        return False
    root = find_mdl_root_of(obj)
    if not root or root.kb.classification != Classification.CHARACTER:
        return False
    return mesh and ((not obj.kb.render) or (obj.kb.render and is_null(obj.kb.bitmap)))


def is_exported_to_mdl(obj: bpy.types.Object | None) -> bool:
    if not obj:
        return False
    if obj.type in ["MESH", "LIGHT"]:
        return True
    return obj.type == "EMPTY" and obj.kb.dummytype in [
        DummyType.NONE,
        DummyType.MDLROOT,
        DummyType.REFERENCE,
    ]


def find_mdl_root_of(obj: bpy.types.Object | None) -> bpy.types.Object | None:
    if obj is None:
        return None
    if is_mdl_root(obj):
        return obj
    if not obj.parent:
        return None
    return find_mdl_root_of(obj.parent)


def find_object(
    obj: bpy.types.Object,
    test: Callable[[bpy.types.Object], bool] = lambda _: True,
) -> bpy.types.Object | None:
    if test(obj):
        return obj
    for child in obj.children:
        match = find_object(child, test)
        if match:
            return match
    return None


def find_objects(
    obj: bpy.types.Object,
    test: Callable[[bpy.types.Object], bool] = lambda _: True,
) -> list[bpy.types.Object]:
    nodes: list[bpy.types.Object] = []
    if test(obj):
        nodes.append(obj)
    for child in obj.children:
        nodes.extend(find_objects(child, test))
    return nodes


def time_to_frame(time: float) -> int:
    return round(ANIM_FPS * time)


def frame_to_time(frame: int) -> float:
    return frame / ANIM_FPS


def is_null(s: str | None) -> bool:
    return not s or s.lower() == NULL.lower()


def is_not_null(s: str | None) -> bool:
    return not is_null(s)


def is_close(a: float, b: float, epsilon: float = 1e-4) -> bool:
    return abs(a - b) <= epsilon


def is_close_2(a: tuple[float, float], b: tuple[float, float], epsilon: float = 1e-4) -> bool:
    return is_close(a[0], b[0], epsilon) and is_close(a[1], b[1], epsilon)


def is_close_3(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    epsilon: float = 1e-4,
) -> bool:
    return all(is_close(a[i], b[i], epsilon) for i in range(3))


def color_to_hex(color: tuple[float, float, float]) -> str:
    return f"{int_to_hex(float_to_byte(color[0]))}{int_to_hex(float_to_byte(color[1]))}{int_to_hex(float_to_byte(color[2]))}"


def float_to_byte(val: float) -> int:
    return int(val * 255)


def int_to_hex(val: int) -> str:
    return f"{val:02X}"


def semicolon_separated_to_absolute_paths(
    paths_str: object,
    working_dir: str,
) -> list[str]:
    """Convert semicolon-separated path string to list of absolute paths.

    Coerces Blender addon preference values (including _PropertyDeferred) to str.
    """
    if isinstance(paths_str, str):
        raw = paths_str
    else:
        try:
            raw = str(paths_str)
        except Exception:
            raw = ""
    abs_paths: list[str] = []
    try:
        rel_paths: list[str] = raw.split(";")
    except (AttributeError, TypeError):
        rel_paths = str(raw).split(";")
    for rel_path in rel_paths:
        abs_path = rel_path if os.path.isabs(rel_path) else os.path.join(working_dir, rel_path)
        abs_paths.append(abs_path)
    if working_dir not in abs_paths:
        abs_paths.insert(0, working_dir)
    return abs_paths


def kotor_addon_preferences() -> bpy.types.AddonPreferences | None:
    """Resolve this add-on's preferences for Blender 4.x extensions and legacy installs.

    Avoids hard-coding a single module id (e.g. ``io_scene_kotor`` vs ``bl_ext.user_default.*``).
    """
    try:
        addons = bpy.context.preferences.addons
    except (AttributeError, ReferenceError):
        return None
    for key in ADDON_PREFERENCE_MODULE_KEYS:
        if key in addons:
            return addons[key].preferences
    return None
