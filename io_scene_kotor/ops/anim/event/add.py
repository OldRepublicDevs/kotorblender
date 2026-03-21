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

from ....scene.animation import Animation
from ....utils import is_mdl_root


class KB_OT_add_anim_event(bpy.types.Operator):
    bl_idname = "kb.add_anim_event"
    bl_label = "Add event to the animation"
    bl_description = "Add a new event to the selected animation (e.g. for sound or script triggers)"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj: bpy.types.Object | None = context.object
        if obj is None or not is_mdl_root(obj):
            cls.poll_message_set(context, "Select a KotOR model object")
            return False
        return True

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj: bpy.types.Object | None = context.object
        if obj is None:
            self.report({"ERROR"}, "No object selected")
            return {"CANCELLED"}
        kb = getattr(obj, "kb", None)
        if kb is None:
            self.report({"ERROR"}, "Object.kb is None")
            return {"CANCELLED"}
        anim_list = kb.anim_list
        anim_list_idx = kb.anim_list_idx

        if anim_list_idx < 0 or anim_list_idx >= len(anim_list):
            return {"CANCELLED"}

        anim = anim_list[anim_list_idx]
        Animation.append_event_to_object_anim(anim, "newevent", 0)

        return {"FINISHED"}
