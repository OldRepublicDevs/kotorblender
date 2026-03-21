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

from ...utils import is_path_point


class KB_OT_delete_path_connection(bpy.types.Operator):
    bl_idname = "kb.remove_path_connection"
    bl_label = "Remove KotOR Path Connection"
    bl_description = "Remove the selected connection from this path point"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj: bpy.types.Object | None = context.object
        if not is_path_point(obj):
            cls.poll_message_set(context, "Select a KotOR path point object")
            return False
        kb = getattr(obj, "kb", None) if obj else None
        if kb is None:
            return False
        if len(kb.path_connection_list) == 0:
            cls.poll_message_set(context, "Path point has no connections to remove")
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
        kb.path_connection_list.remove(kb.path_connection_idx)
        return {"FINISHED"}
