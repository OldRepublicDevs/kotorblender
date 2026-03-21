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

from ...constants import GameType, PropertyName
from ...vendor.pykotor_adapter import is_pykotor_available


class KB_PT_game_installation(bpy.types.Panel):
    bl_label = "KotOR Game Installation"
    bl_description = (
        "Tell Blender where KotOR is installed, then refresh modules. "
        "Links to the same data as the 3D View KotOR sidebar (N)"
    )
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context: bpy.types.Context) -> None:
        scene: bpy.types.Scene = context.scene
        layout = self.layout
        if layout is None:
            raise ValueError("Layout is None")
        layout.use_property_split = True

        kb = getattr(scene, "kb", None)
        if kb is None:
            raise ValueError("Scene.kb is None")

        row = layout.row()
        row.prop(kb, PropertyName.GAME_TYPE)

        if kb.game_type == GameType.CUSTOM:
            row = layout.row()
            row.prop(kb, PropertyName.GAME_INSTALLATION_PATH)
            row = layout.row()
            row.operator("kb.select_game_installation", icon="FILE_FOLDER", text="Browse")
        else:
            # For KOTOR1/KOTOR2 show path and allow autofill from PyKotor
            row = layout.row()
            row.prop(kb, PropertyName.GAME_INSTALLATION_PATH)
            row = layout.row()
            row.operator("kb.select_game_installation", icon="FILE_FOLDER", text="Browse")
            row.operator("kb.autodetect_game_installation", icon="FILE_REFRESH", text="Autodetect")
            tip = layout.row()
            tip.label(
                text="If autodetect fails: Preferences → KotorBlender → Logging → Debug, then System Console",
                icon="INFO",
            )

        row = layout.row()
        row.operator("kb.refresh_modules", icon="FILE_REFRESH", text="Refresh Modules")

        # Module list
        row = layout.row()
        row.template_list(
            "KB_UL_modules",
            "modules",
            kb,
            "module_list",
            kb,
            PropertyName.MODULE_LIST_IDX,
            rows=5,
        )

        col = row.column(align=True)
        col.operator("kb.open_module", icon="IMPORT", text="")

        layout.separator()
        q = layout.box()
        q.label(text="Quick: 3D View sidebar (N → KotOR)", icon="VIEW3D")
        r = q.row(align=True)
        r.operator("kb.module_designer", text="Designer", icon="SETTINGS")
        r.operator("kb.file_search", text="Search", icon="VIEWZOOM")
        r.operator("kb.validate_module", text="Validate", icon="VIEWZOOM")

        layout.separator()
        area = layout.box()
        area.label(text="Area edit flag (WIP)", icon="MOD_BUILD")
        area.prop(kb, "kotor_area_edit_active")
        area.label(text="For future gizmos; import LYT as usual today")

        if not is_pykotor_available():
            box = layout.box()
            box.label(text="PyKotor not available", icon="ERROR")
            box.label(text="Install PyKotor to use game installation features")
