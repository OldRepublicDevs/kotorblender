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

from typing import ClassVar

import bpy

from ..constants import Classification
from ..diagnostic_log import run_simple_operator_logged
from ..log_config import get_kb_logger
from ..scene import armature
from ..utils import is_mdl_root


class KB_OT_rebuild_armature(bpy.types.Operator):
    bl_idname: ClassVar[str] = "kb.rebuild_armature"
    bl_label: ClassVar[str] = "Rebuild Armature"
    bl_description: ClassVar[str] = "Rebuild an armature from bone objects"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj: bpy.types.Object | None = context.object
        if obj is None or not is_mdl_root(obj):
            cls.poll_message_set(context, "Select a KotOR model object")
            return False
        kb = getattr(obj, "kb", None)
        if kb is None:
            return False
        if kb.classification != Classification.CHARACTER:
            cls.poll_message_set(context, "Select a KotOR character model")
            return False
        return True

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.rebuildarmature")

        def _body() -> set[str]:
            obj: bpy.types.Object | None = context.object
            if obj is None:
                self.report({"ERROR"}, "No object selected")
                return {"CANCELLED"}
            armature.rebuild_armature(obj)
            return {"FINISHED"}

        return run_simple_operator_logged(log, "kb.rebuild_armature", _body)
