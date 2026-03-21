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

import os
from typing import TYPE_CHECKING

import bpy

from ...constants import PropertyName
from ...vendor.pykotor_adapter import is_pykotor_available, resolve_game_install_path

if TYPE_CHECKING:
    from ...ui.props.scene import ScenePropertyGroup


class KB_PT_module_browser(bpy.types.Panel):
    bl_label = "KotOR Module Browser"
    bl_description = "Browse and open resources from your game install: pick a tab, refresh, then open or extract. Use the checkbox column for batch extract"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KotOR"

    def draw(self, context: bpy.types.Context) -> None:
        scene: bpy.types.Scene | None = context.scene
        if scene is None:
            return
        layout: bpy.types.UILayout | None = self.layout
        if layout is None:
            return

        kb: ScenePropertyGroup | None = getattr(scene, "kb", None)
        if kb is None:
            return

        if not is_pykotor_available():
            box: bpy.types.UILayout = layout.box()
            box.label(text="PyKotor not loaded", icon="ERROR")
            box.label(text="Bundle the wheel (see README) to browse modules.")
            layout.separator()
        else:
            install = resolve_game_install_path(kb)
            if not install or not os.path.isdir(install):
                box = layout.box()
                box.label(text="No game path yet", icon="ERROR")
                box.label(text="Scene Properties → KotOR Game Installation")
                r = box.row(align=True)
                r.operator("kb.autodetect_game_installation", text="Autodetect", icon="FILE_REFRESH")
                r.operator("kb.select_game_installation", text="Browse", icon="FILE_FOLDER")
                layout.separator()

        row: bpy.types.UILayout = layout.row(align=True)
        row.operator("kb.refresh_module_resources", icon="FILE_REFRESH", text="Refresh List")
        row.operator("kb.file_search", icon="VIEWZOOM", text="Search")

        row = layout.row()
        row.prop(kb, PropertyName.MODULE_LIST_IDX, text="Module")
        if kb.module_list:
            if 0 <= kb.module_list_idx < len(kb.module_list):
                row.label(text=kb.module_list[kb.module_list_idx].name)

        row = layout.row()
        row.prop(kb, "resource_name_filter", text="Filter")

        row = layout.row()
        row.scale_y = 1.2
        tabs = row.row(align=True)
        tabs.prop(kb, PropertyName.RESOURCE_TAB, expand=True)

        row = layout.row()
        row.template_list(
            "KB_UL_resources",
            "resources",
            kb,
            "resource_list",
            kb,
            PropertyName.RESOURCE_LIST_IDX,
            rows=8,
        )

        col: bpy.types.UILayout = row.column(align=True)
        col.operator("kb.open_resource", icon="IMPORT", text="")
        col.operator("kb.extract_resource", icon="EXPORT", text="")
        col.operator("kb.batch_extract_resources", icon="FILE_FOLDER", text="")

        hint: bpy.types.UILayout = layout.box()
        hint.label(text="Batch: tick rows, then batch extract", icon="LAYER_ACTIVE")

        box = layout.box()
        box.label(text="Extract Options")
        row = box.row()
        row.prop(kb, PropertyName.EXTRACT_TPC_DECOMPILE, text="TPC Decompile")
        row = box.row()
        row.prop(kb, PropertyName.EXTRACT_TPC_TXI, text="Extract TXI")
        row = box.row()
        row.prop(kb, PropertyName.EXTRACT_MDL_DECOMPILE, text="MDL Decompile")
        row = box.row()
        row.prop(kb, PropertyName.EXTRACT_MDL_TEXTURES, text="Extract Textures")
