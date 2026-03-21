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

from ..constants import DummyType, ImportOptions
from ..utils import find_mdl_root_of

from . import mdl


def load_lyt(
    operator: bpy.types.Operator,
    filepath: str,
    options: ImportOptions,
) -> None:
    operator.report({"INFO"}, f"Loading area layout from '{filepath}'")

    MAX_ROOMS = 10000

    # Read lines
    fp = os.fsencode(filepath)
    with open(fp) as f:
        lines = [line.strip() for line in f.read().splitlines()]

    # Parse room models
    rooms = []
    rooms_to_read = 0
    for line in lines:
        tokens = line.split()
        if not tokens:
            continue
        if rooms_to_read > 0:
            if len(tokens) < 4:
                operator.report(
                    {"WARNING"},
                    f"Skipping malformed room entry in LYT: '{line}'",
                )
                rooms_to_read -= 1
                if rooms_to_read == 0:
                    break
                continue
            room_name = tokens[0].lower()
            x = float(tokens[1])
            y = float(tokens[2])
            z = float(tokens[3])
            rooms.append((room_name, x, y, z))
            rooms_to_read -= 1
            if rooms_to_read == 0:
                break
        elif tokens[0].startswith("roomcount"):
            if len(tokens) < 2:
                operator.report({"WARNING"}, "Malformed roomcount line in LYT")
                continue
            rooms_to_read = min(int(tokens[1]), MAX_ROOMS)

    # Load room models
    path, _ = os.path.split(filepath)
    for room in rooms:
        mdl_path = os.path.join(path, room[0] + ".mdl")
        if not os.path.exists(mdl_path):
            operator.report({"WARNING"}, f"Room model '{mdl_path}' not found")
            continue
        mdl.load_mdl(operator, mdl_path, options, room[1:])


def save_lyt(
    operator: bpy.types.Operator,
    filepath: str,
) -> None:
    def describe_object(obj: bpy.types.Object) -> str:
        parent = find_mdl_root_of(obj)
        orientation = obj.rotation_euler.to_quaternion()
        return "{} {} {:.7g} {:.7g} {:.7g} {:.7g} {:.7g} {:.7g} {:.7g}".format(
            parent.name if parent else "NULL",
            obj.name,
            *obj.matrix_world.translation,
            *orientation,
        )

    operator.report({"INFO"}, f"Saving area layout to '{filepath}'")

    with open(filepath, "w") as f:
        rooms = []
        doors = []
        others = []

        objects = (
            bpy.context.selected_objects
            if len(bpy.context.selected_objects) > 0
            else bpy.context.collection.objects
        )
        for obj in objects:
            if obj.type == "EMPTY":
                if obj.kb.dummytype == DummyType.MDLROOT:
                    rooms.append(obj)
                elif obj.name.lower().startswith("door"):
                    doors.append(obj)
                elif obj.kb.dummytype not in [DummyType.PTHROOT, DummyType.PATHPOINT]:
                    others.append(obj)

        f.write("beginlayout\n")
        f.write(f"  roomcount {len(rooms)}\n")
        f.writelines(
            "    {} {:.7g} {:.7g} {:.7g}\n".format(room.name, *room.location) for room in rooms
        )
        f.write("  trackcount 0\n")
        f.write("  obstaclecount 0\n")
        f.write(f"  doorhookcount {len(doors)}\n")
        f.writelines(f"    {describe_object(door)}\n" for door in doors)
        f.write(f"  othercount {len(others)}\n")
        f.writelines(f"    {describe_object(other)}\n" for other in others)
        f.write("donelayout\n")
