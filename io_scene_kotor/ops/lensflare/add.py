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

from ...constants import NULL
from ...diagnostic_log import run_simple_operator_logged
from ...log_config import get_kb_logger


class KB_OT_add_lens_flare(bpy.types.Operator):
    bl_idname = "kb.add_lens_flare"
    bl_label = "Add lens flare to the list"
    bl_description = "Add a new lens flare entry to the light's flare list"

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
        return True

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.lensflare.add")

        def _body() -> set[str]:
            obj: bpy.types.Object | None = context.object
            if obj is None:
                self.report({"ERROR"}, "No object selected")
                return {"CANCELLED"}
            kb = getattr(obj, "kb", None)
            if kb is None:
                self.report({"ERROR"}, "Object.kb is None")
                return {"CANCELLED"}
            flare = kb.flare_list.add()
            flare.texture = NULL
            return {"FINISHED"}

        return run_simple_operator_logged(log, "kb.add_lens_flare", _body)
