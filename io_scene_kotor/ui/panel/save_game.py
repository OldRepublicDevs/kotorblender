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

from ...vendor.pykotor_adapter import is_pykotor_available


class KB_PT_save_game(bpy.types.Panel):
    bl_label = "KotOR Save Game"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        if layout is None:
            raise ValueError("Layout is None")
        layout.label(text="Save Game Editor")
        layout.label(text="Open a save: Editor → KotOR → Save → Open Save Editor", icon="INFO")

        if not is_pykotor_available():
            box = layout.box()
            box.label(text="PyKotor not available", icon="ERROR")
            box.label(text="Install PyKotor to use save game features")
