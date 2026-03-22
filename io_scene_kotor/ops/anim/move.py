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

import bpy

from ...constants import Direction
from ...diagnostic_log import run_simple_operator_logged
from ...log_config import get_kb_logger
from ...utils import is_mdl_root


class KB_OT_move_animation(bpy.types.Operator):
    bl_idname = "kb.move_animation"
    bl_label = "Move an animation in the list, without affecting keyframes"
    bl_description = (
        "Reorder the selected animation up or down in the list without changing keyframes"
    )
    bl_options = {"UNDO"}

    direction: bpy.props.EnumProperty(
        items=[
            (Direction.UP, "Up", ""),
            (Direction.DOWN, "Down", ""),
        ],
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj: bpy.types.Object | None = context.object
        if obj is None or not is_mdl_root(obj):
            cls.poll_message_set(context, "Select a KotOR model object")
            return False
        kb = getattr(obj, "kb", None)
        if kb is None:
            return False
        anim_list = kb.anim_list
        anim_list_idx = kb.anim_list_idx
        num_anims = len(anim_list)
        if anim_list_idx < 0 or anim_list_idx >= num_anims:
            cls.poll_message_set(context, "Select an animation in the list")
            return False
        if num_anims < 2:
            cls.poll_message_set(context, "At least two animations required to reorder")
            return False
        return True

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.anim.move")

        def _body() -> set[str]:
            mdl_root: bpy.types.Object | None = context.object
            if mdl_root is None:
                self.report({"ERROR"}, "No object selected")
                return {"CANCELLED"}
            kb = getattr(mdl_root, "kb", None)
            if kb is None:
                self.report({"ERROR"}, "Object.kb is None")
                return {"CANCELLED"}
            anim_list = kb.anim_list
            prev_idx = kb.anim_list_idx

            if self.direction == Direction.DOWN:
                new_idx = min(len(anim_list) - 1, prev_idx + 1)
            elif self.direction == Direction.UP:
                new_idx = max(0, prev_idx - 1)
            else:
                return {"CANCELLED"}

            if new_idx == prev_idx:
                return {"CANCELLED"}

            anim_list.move(prev_idx, new_idx)
            kb.anim_list_idx = new_idx
            return {"FINISHED"}

        return run_simple_operator_logged(log, "kb.move_animation", _body)
