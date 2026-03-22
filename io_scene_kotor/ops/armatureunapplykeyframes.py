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

from ..constants import Classification
from ..diagnostic_log import run_simple_operator_logged
from ..log_config import get_kb_logger
from ..scene import armature
from ..utils import find_objects, is_mdl_root, is_skin_mesh


class KB_OT_armature_unapply_keyframes(bpy.types.Operator):
    bl_idname = "kb.armature_unapply_keyframes"
    bl_label = "Unapply Object Keyframes"
    bl_description = "Recreate bone object keyframes from armature"

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
        if not find_objects(
            obj,
            lambda obj: is_skin_mesh(obj) and any(mod.type == "ARMATURE" for mod in obj.modifiers),
        ):
            cls.poll_message_set(
                context,
                "Model must have a skinned mesh with an armature modifier",
            )
            return False
        return True

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.armatureunapplykeyframes")

        def _body() -> set[str]:
            root: bpy.types.Object | None = context.object
            if root is None:
                self.report({"ERROR"}, "No object selected")
                return {"CANCELLED"}
            stack: list[bpy.types.Object] = [root]
            while stack:
                obj = stack.pop()
                if is_skin_mesh(obj):
                    armature_mod = next(
                        iter(mod for mod in obj.modifiers if mod.type == "ARMATURE"),
                        None,
                    )
                    if armature_mod is None:
                        return {"CANCELLED"}
                    armature_obj: bpy.types.Object | None = armature_mod.object
                    if armature_obj is None:
                        return {"CANCELLED"}
                    armature.unapply_object_keyframes(root, armature_obj)
                    break
                for child in obj.children:
                    stack.insert(0, child)
            return {"FINISHED"}

        return run_simple_operator_logged(log, "kb.armature_unapply_keyframes", _body)
