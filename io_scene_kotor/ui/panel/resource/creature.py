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

from ....constants import Classification
from ....utils import is_mdl_root


class KB_PT_creature(bpy.types.Panel):
    bl_label = "KotOR Creature"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.object
        return is_mdl_root(obj) and obj.kb.classification == Classification.CHARACTER

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        if layout is None:
            raise ValueError("Layout is None")
        obj = context.object
        if obj is None:
            return
        layout.label(text="Creature (UTC) — model root")
        layout.prop(obj.kb, "classification", text="Classification")
        layout.prop(obj.kb, "animroot", text="Anim Root")
