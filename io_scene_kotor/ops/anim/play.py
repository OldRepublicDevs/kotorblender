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

    from ...ui.props.object import ObjectPropertyGroup


class KB_OT_play_animation(bpy.types.Operator):
    bl_idname = "kb.play_animation"
    bl_label = "Set start and end frame of the scene to this animation"
    bl_description = (
        "Set the scene's frame range to match the selected animation for playback"
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
        if anim_list_idx < 0 or anim_list_idx >= len(anim_list):
            cls.poll_message_set(context, "Select an animation in the list")
            return False
        return True

    def execute(self, context: bpy.types.Context) -> set[rna_enums.OperatorReturnItems]:
        log = get_kb_logger("ops.anim.play")

        def _body() -> set[str]:
            mdl_root: bpy.types.Object | None = context.object
            if mdl_root is None:
                self.report({"ERROR"}, "No object selected")
                return {"CANCELLED"}
            kb: ObjectPropertyGroup | None = getattr(mdl_root, "kb", None)
            if kb is None:
                self.report({"ERROR"}, "Object.kb is None")
                return {"CANCELLED"}
            anim_list = kb.anim_list
            anim_list_idx = kb.anim_list_idx

            scene: bpy.types.Scene | None = context.scene
            if scene is None:
                self.report({"ERROR"}, "Scene is None")
                return {"CANCELLED"}
            scene.frame_current = anim_list[anim_list_idx].frame_start
            scene.frame_start = anim_list[anim_list_idx].frame_start
            scene.frame_end = anim_list[anim_list_idx].frame_end
            return {"FINISHED"}

        return run_simple_operator_logged(log, "kb.play_animation", _body)
