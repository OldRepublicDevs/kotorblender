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
from typing import Any

import bpy

from ..constants import DummyType
from ..diagnostic_log import begin_io_file_span, end_io_file_span
from ..log_config import get_kb_logger
from ..format.gff.reader import GffReader
from ..format.gff.writer import GffWriter
from ..utils import is_path_point
from ..vendor.pykotor_adapter import convert_pykotor_gff_to_tree, convert_tree_to_pykotor_gff, get_use_pykotor_readers, load_gff_via_pykotor, save_gff_via_pykotor


def load_pth(
    operator: bpy.types.Operator,
    filepath: str,
) -> None:
    span = begin_io_file_span(get_kb_logger("io.pth"), "load_pth", filepath)
    err = False
    try:
        _load_pth_body(operator, filepath)
    except BaseException:
        err = True
        raise
    finally:
        end_io_file_span(span, error=err)


def _load_pth_body(
    operator: bpy.types.Operator,
    filepath: str,
) -> None:
    def get_point_name(idx: int) -> str:
        return f"PathPoint{idx:0>3}"

    basename = os.path.basename(filepath)
    pathname = "Path_" + os.path.splitext(basename)[0]
    if pathname in bpy.data.objects:
        path_object = bpy.data.objects[pathname]
    else:
        path_object = bpy.data.objects.new(pathname, None)
        kb = getattr(path_object, "kb", None)
        if kb is None:
            raise ValueError(f"Object '{path_object.name}' has no kb attribute")
        kb.dummytype = DummyType.PTHROOT
        collection = bpy.context.collection
        if collection is None:
            raise ValueError("No collection found")
        collection.objects.link(path_object)

    operator.report({"INFO"}, f"Loading path from '{filepath}'")
    tree = None
    if get_use_pykotor_readers():
        pykotor_gff = load_gff_via_pykotor(filepath)
        if pykotor_gff:
            tree = convert_pykotor_gff_to_tree(pykotor_gff)
        if not tree:
            # Fallback to current reader
            loader = GffReader(filepath, "PTH")
            tree = loader.load()
    else:
        loader = GffReader(filepath, "PTH")
        tree = loader.load()
    points = []

    for i, point in enumerate(tree["Path_Points"]):
        name = get_point_name(i)
        object = bpy.data.objects.new(name, None)
        object.parent = path_object
        object.location = [point["X"], point["Y"], 0.0]
        kb = getattr(object, "kb", None)
        if kb is None:
            raise ValueError(f"Object '{object.name}' has no kb attribute")
        kb.dummytype = DummyType.PATHPOINT
        collection = bpy.context.collection
        if collection is None:
            raise ValueError("No collection found")
        collection.objects.link(object)
        points.append((point, object))

    for point, object in points:
        start = point["First_Conection"]
        stop = start + point["Conections"]
        conections = tree["Path_Conections"][start:stop]
        for conection in conections:
            name = get_point_name(conection["Destination"])
            if name in bpy.data.objects:
                connection = object.kb.path_connection_list.add()
                connection.point = name


def save_pth(
    operator: bpy.types.Operator,
    filepath: str,
) -> None:
    span = begin_io_file_span(get_kb_logger("io.pth"), "save_pth", filepath)
    err = False
    try:
        _save_pth_body(operator, filepath)
    except BaseException:
        err = True
        raise
    finally:
        end_io_file_span(span, error=err)


def _save_pth_body(
    operator: bpy.types.Operator,
    filepath: str,
) -> None:
    point_objects = [obj for obj in bpy.data.objects if is_path_point(obj)]

    point_idx_by_name = dict()
    for idx, obj in enumerate(point_objects):
        point_idx_by_name[obj.name] = idx

    points: list[dict[str, Any]] = []
    conections: list[dict[str, Any]] = []
    for obj in point_objects:
        first_conection = len(conections)
        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError("obj is None")

        for object_connection in kb.path_connection_list:
            conection = dict()
            conection["_type"] = 3
            conection["_fields"] = {"Destination": 4}
            conection["Destination"] = point_idx_by_name[object_connection.point]
            conections.append(conection)

        point = dict()
        point["_type"] = 2
        point["_fields"] = {"Conections": 4, "First_Conection": 4, "X": 8, "Y": 8}
        point["Conections"] = len(kb.path_connection_list)
        point["First_Conection"] = first_conection
        point["X"] = obj.location[0]
        point["Y"] = obj.location[1]
        points.append(point)

    tree = dict()
    tree["_type"] = 0xFFFFFFFF
    tree["_fields"] = {"Path_Points": 15, "Path_Conections": 15}
    tree["Path_Points"] = points
    tree["Path_Conections"] = conections

    operator.report({"INFO"}, f"Saving path to '{filepath}'")
    if get_use_pykotor_readers():
        pykotor_gff = convert_tree_to_pykotor_gff(tree, "PTH")
        if pykotor_gff is not None:
            if save_gff_via_pykotor(pykotor_gff, filepath):
                return
        # Fallback to current writer
    try:
        saver = GffWriter(tree, filepath, "PTH")
        saver.save()
    except Exception as e:
        operator.report({"ERROR"}, f"Failed to save PTH: {e.__class__.__name__}: {e}")
        return

    operator.report({"INFO"}, f"Saved path to '{filepath}'")
    return
