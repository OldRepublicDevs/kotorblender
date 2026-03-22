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

"""View3D sidebar: TSLPatchData (Holocron-style sections; MVP load/save + stubs)."""

from __future__ import annotations

import bpy


class KB_PT_tslpatchdata(bpy.types.Panel):
    bl_label = "TSLPatchData"
    bl_idname = "KB_PT_tslpatchdata"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KotOR"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 7

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        if layout is None:
            raise ValueError("Layout is None")
        kb = getattr(context.scene, "kb", None)
        if kb is None:
            layout.label(text="Scene.kb missing")
            return

        layout.operator("kb.tslpatchdata_editor", icon="FILEBROWSER", text="Browse changes.ini…")
        layout.prop(kb, "tslpatchdata_folder", text="Folder")
        layout.prop(kb, "tslpatchdata_filepath", text="INI path")
        row = layout.row(align=True)
        row.operator("kb.tslpatchdata_load_changes_ini", icon="IMPORT", text="Load")
        row.operator("kb.tslpatchdata_save_changes_ini", icon="EXPORT", text="Save")
        layout.separator()
        layout.prop(kb, "tslpatchdata_mod_name", text="Mod name")
        layout.prop(kb, "tslpatchdata_mod_author", text="Author")
        layout.prop(kb, "tslpatchdata_ini_body", text="INI text")


class KB_PT_tslpatchdata_files(bpy.types.Panel):
    bl_label = "Files to package"
    bl_idname = "KB_PT_tslpatchdata_files"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KotOR"
    bl_parent_id = "KB_PT_tslpatchdata"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        kb = context.scene.kb
        layout.label(text="Holocron parity: list UI only.", icon="INFO")
        layout.template_list(
            "KB_UL_tslpatch_package",
            "",
            kb,
            "tslpatch_package_list",
            kb,
            "tslpatch_package_list_idx",
            rows=3,
        )
        layout.label(text="Add/remove files: not wired (edit INI text).", icon="BLANK1")


class KB_PT_tslpatchdata_2da(bpy.types.Panel):
    bl_label = "2DA memory"
    bl_idname = "KB_PT_tslpatchdata_2da"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KotOR"
    bl_parent_id = "KB_PT_tslpatchdata"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        self.layout.label(text="Not implemented (edit INI text above).", icon="BLANK1")


class KB_PT_tslpatchdata_tlk(bpy.types.Panel):
    bl_label = "TLK strings"
    bl_idname = "KB_PT_tslpatchdata_tlk"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KotOR"
    bl_parent_id = "KB_PT_tslpatchdata"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        self.layout.label(text="Not implemented (edit INI text above).", icon="BLANK1")


class KB_PT_tslpatchdata_gff(bpy.types.Panel):
    bl_label = "GFF fields"
    bl_idname = "KB_PT_tslpatchdata_gff"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KotOR"
    bl_parent_id = "KB_PT_tslpatchdata"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        self.layout.label(text="Not implemented (edit INI text above).", icon="BLANK1")


class KB_PT_tslpatchdata_scripts(bpy.types.Panel):
    bl_label = "Scripts"
    bl_idname = "KB_PT_tslpatchdata_scripts"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KotOR"
    bl_parent_id = "KB_PT_tslpatchdata"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        self.layout.label(text="Not implemented (edit INI text above).", icon="BLANK1")
