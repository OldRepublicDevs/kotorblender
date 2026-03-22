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
from ...scene.animation import Animation
from ...utils import is_mdl_root

if TYPE_CHECKING:
    import bpy.stub_internal.rna_enums as rna_enums


class KB_OT_add_animation(bpy.types.Operator):
    bl_idname = "kb.add_animation"
    bl_label = "Add animation to the list"
    bl_description = "Add a new animation entry to the KotOR model's animation list"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj: bpy.types.Object | None = context.object
        if obj is None or not is_mdl_root(obj):
            cls.poll_message_set("Select a KotOR model object")
            return False
        return True

    def execute(self, context: bpy.types.Context) -> set[rna_enums.OperatorReturnItems]:
        log = get_kb_logger("ops.anim.add")

        def _body() -> set[str]:
            obj: bpy.types.Object | None = context.object
            if obj is None:
                self.report({"ERROR"}, "No object selected")
                return {"CANCELLED"}
            Animation.append_to_object(obj, "newanim", 0, 0.25, obj.name)
            return {"FINISHED"}

        return run_simple_operator_logged(log, "kb.add_animation", _body)
