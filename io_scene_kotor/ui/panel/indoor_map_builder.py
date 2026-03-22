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

"""View3D sidebar: Indoor Map Builder workflow (narrow MVP; full tools remain in Holocron)."""

from __future__ import annotations

import bpy


class KB_PT_indoor_map_builder(bpy.types.Panel):
    bl_label = "Indoor Map Builder"
    bl_idname = "KB_PT_indoor_map_builder"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KotOR"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 6

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        kb = context.scene.kb
        layout.operator("kb.indoor_map_builder", icon="HOME", text="Start / focus workflow")
        layout.separator()
        layout.prop(kb, "kotor_area_edit_active", text="Area edit mode")
        layout.label(text="Import LYT: File → Import → KotOR Layout", icon="INFO")
        layout.label(text="Walkmeshes: edit in Blender; export via MDL pipeline.", icon="INFO")
        layout.prop(kb, "active_are_path", text="ARE")
        layout.prop(kb, "active_git_path", text="GIT")
        layout.prop(kb, "active_vis_path", text="VIS")
        tips = layout.box()
        tips.label(text="Full GIT/VIS kit: HolocronToolset", icon="URL")
        tips.label(text="Vendor wiki: Indoor-Map-Builder-User-Guide.md")
