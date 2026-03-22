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

from typing import TYPE_CHECKING

import bpy

from ...constants import Direction
from ...diagnostic_log import run_simple_operator_logged
from ...log_config import get_kb_logger

if TYPE_CHECKING:
    from bpy.stub_internal.rna_enums import OperatorReturnItems

    from ...ui.props.object import ObjectPropertyGroup
    from ...scene.modelnode.light import FlareList


class KB_OT_move_lens_flare(bpy.types.Operator):
    bl_idname = "kb.move_lens_flare"
    bl_label = "Move lens flare within the list"
    bl_description = "Reorder the selected lens flare up or down in the list"

    direction: bpy.props.EnumProperty(  # pyright: ignore[reportInvalidTypeForm]
        items=[
            (Direction.UP, "Up", ""),
            (Direction.DOWN, "Down", ""),
        ],
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj: bpy.types.Object | None = context.object
        if obj is None:
            cls.poll_message_set(context, "Select an object")
            return False
        if obj.type != "LIGHT":
            cls.poll_message_set(context, "Select a light object")
            return False
        kb = getattr(obj, "kb", None)
        if kb is None:
            return False
        if not kb.lensflares:
            cls.poll_message_set(context, "Light must have lens flares enabled")
            return False
        flare_list = kb.flare_list
        flare_list_idx = kb.flare_list_idx
        num_flares = len(flare_list)
        if flare_list_idx < 0 or flare_list_idx >= num_flares:
            cls.poll_message_set(context, "Select a lens flare in the list")
            return False
        if num_flares < 2:
            cls.poll_message_set(context, "At least two lens flares required to reorder")
            return False
        return True

    def move_index(self, context: bpy.types.Context) -> None:
        obj: bpy.types.Object | None = context.object
        if obj is None:
            return
        kb = getattr(obj, "kb", None)
        if kb is None:
            return
        flare_list: FlareList = kb.flare_list
        flare_list_idx: int = kb.flare_list_idx

        listLength: int = len(flare_list) - 1
        new_idx = 0
        if self.direction == Direction.UP:
            new_idx = flare_list_idx - 1
        elif self.direction == Direction.DOWN:
            new_idx = flare_list_idx + 1

        new_idx = max(0, min(new_idx, listLength))
        kb.flare_list_idx = new_idx

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        log = get_kb_logger("ops.lensflare.move")

        def _body() -> set[str]:
            obj: bpy.types.Object | None = context.object
            if obj is None:
                self.report({"ERROR"}, "No object selected")
                return {"CANCELLED"}
            kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
            if kb is None:
                self.report({"ERROR"}, "Object.kb is None")
                return {"CANCELLED"}
            flare_list: FlareList = kb.flare_list
            flare_list_idx = kb.flare_list_idx

            if self.direction == Direction.DOWN:
                neighbour = flare_list_idx + 1
                flare_list.move(flare_list_idx, neighbour)
                self.move_index(context)
            elif self.direction == Direction.UP:
                neighbour = flare_list_idx - 1
                flare_list.move(neighbour, flare_list_idx)
                self.move_index(context)
            else:
                return {"CANCELLED"}

            return {"FINISHED"}

        return run_simple_operator_logged(log, "kb.move_lens_flare", _body)
