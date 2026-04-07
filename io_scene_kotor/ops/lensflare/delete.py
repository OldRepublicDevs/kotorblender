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

import bpy


class KB_OT_delete_lens_flare(bpy.types.Operator):
    bl_idname = "kb.delete_lens_flare"
    bl_label = "Delete lens flare from the list"
    bl_description = "Remove the selected lens flare from the light's flare list"

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj:
            cls.poll_message_set(context, "Select an object")
            return False
        if obj.type != "LIGHT":
            cls.poll_message_set(context, "Select a light object")
            return False
        if not obj.kb.lensflares:
            cls.poll_message_set(context, "Light must have lens flares enabled")
            return False
        flare_list = obj.kb.flare_list
        flare_list_idx = obj.kb.flare_list_idx
        if flare_list_idx < 0 or flare_list_idx >= len(flare_list):
            cls.poll_message_set(context, "Select a lens flare in the list")
            return False
        return True

    def execute(self, context):
        obj = context.object
        flare_list = obj.kb.flare_list
        flare_list_idx = obj.kb.flare_list_idx

        if flare_list_idx == len(flare_list) - 1 and flare_list_idx > 0:
            obj.kb.flare_list_idx = flare_list_idx - 1

        flare_list.remove(flare_list_idx)

        return {"FINISHED"}
