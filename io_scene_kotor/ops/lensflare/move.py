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


class KB_OT_move_lens_flare(bpy.types.Operator):
    bl_idname = "kb.move_lens_flare"
    bl_label = "Move lens flare within the list"
    bl_description = "Reorder the selected lens flare up or down in the list"

    direction: bpy.props.EnumProperty(items=(("UP", "Up", ""), ("DOWN", "Down", "")))

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
        num_flares = len(flare_list)
        if flare_list_idx < 0 or flare_list_idx >= num_flares:
            cls.poll_message_set(context, "Select a lens flare in the list")
            return False
        if num_flares < 2:
            cls.poll_message_set(context, "At least two lens flares required to reorder")
            return False
        return True

    def move_index(self, context):
        obj = context.object
        flare_list = obj.kb.flare_list
        flare_list_idx = obj.kb.flare_list_idx

        listLength = len(flare_list) - 1
        new_idx = 0
        if self.direction == "UP":
            new_idx = flare_list_idx - 1
        elif self.direction == "DOWN":
            new_idx = flare_list_idx + 1

        new_idx = max(0, min(new_idx, listLength))
        obj.kb.flare_list_idx = new_idx

    def execute(self, context):
        obj = context.object
        flare_list = obj.kb.flare_list
        flare_list_idx = obj.kb.flare_list_idx

        if self.direction == "DOWN":
            neighbour = flare_list_idx + 1
            flare_list.move(flare_list_idx, neighbour)
            self.move_index(context)
        elif self.direction == "UP":
            neighbour = flare_list_idx - 1
            flare_list.move(neighbour, flare_list_idx)
            self.move_index(context)
        else:
            return {"CANCELLED"}

        return {"FINISHED"}
