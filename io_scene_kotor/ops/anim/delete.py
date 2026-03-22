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

from ...diagnostic_log import run_simple_operator_logged
from ...log_config import get_kb_logger
from ...utils import is_mdl_root

if TYPE_CHECKING:
    import bpy.stub_internal.rna_enums as rna_enums

class KB_OT_delete_animation(bpy.types.Operator):
    bl_idname = "kb.delete_animation"
    bl_label = "Delete animation from the list"
    bl_description = (
        "Remove the selected animation from the KotOR model's animation list"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj: bpy.types.Object | None = context.object
        if obj is None or not is_mdl_root(obj):
            cls.poll_message_set("Select a KotOR model object")
            return False
        kb = getattr(obj, "kb", None)
        if kb is None:
            return False
        anim_list = kb.anim_list
        anim_list_idx = kb.anim_list_idx
        if anim_list_idx < 0 or anim_list_idx >= len(anim_list):
            cls.poll_message_set("Select an animation in the list")
            return False
        return True

    def execute(self, context: bpy.types.Context) -> set[rna_enums.OperatorReturnItems]:
        log = get_kb_logger("ops.anim.delete")

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
            anim_list_idx = kb.anim_list_idx

            if anim_list_idx == len(anim_list) - 1 and anim_list_idx > 0:
                kb.anim_list_idx = anim_list_idx - 1

            anim_list.remove(anim_list_idx)
            return {"FINISHED"}

        return run_simple_operator_logged(log, "kb.delete_animation", _body)
