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
import shutil

import bpy

from ...vendor.pykotor_adapter import is_pykotor_available, resolve_game_install_path


class KB_OT_clone_module(bpy.types.Operator):
    bl_idname = "kb.clone_module"
    bl_label = "Clone Module"
    bl_description = "Copy the selected .mod to a new name in the modules folder"

    new_module_name: bpy.props.StringProperty(
        name="New Module Name",
        description="Base name without .mod (e.g. myarea)",
        default="",
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not is_pykotor_available():
            self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
            return {"CANCELLED"}

        scene = context.scene
        kb = scene.kb
        install = resolve_game_install_path(kb)
        if not install:
            self.report({"ERROR"}, "Game installation path not set or not found.")
            return {"CANCELLED"}

        if kb.module_list_idx < 0 or kb.module_list_idx >= len(kb.module_list):
            self.report({"ERROR"}, "No module selected in the scene module list.")
            return {"CANCELLED"}

        src_name = kb.module_list[kb.module_list_idx].name
        dst_name = (self.new_module_name or "").strip().lower()
        if not dst_name or any(c in dst_name for c in r'\/:*?"<>|'):
            self.report({"ERROR"}, "Invalid new module name.")
            return {"CANCELLED"}

        src_path = os.path.join(install, "modules", src_name + ".mod")
        dst_path = os.path.join(install, "modules", dst_name + ".mod")
        if not os.path.isfile(src_path):
            self.report({"ERROR"}, f"Source module not found: {src_path}")
            return {"CANCELLED"}
        if os.path.exists(dst_path):
            self.report({"ERROR"}, f"Target already exists: {dst_path}")
            return {"CANCELLED"}

        try:
            shutil.copy2(src_path, dst_path)
        except OSError as e:
            self.report({"ERROR"}, f"Clone failed: {e}")
            return {"CANCELLED"}

        item = kb.module_list.add()
        item.name = dst_name
        self.report({"INFO"}, f"Cloned to {dst_path}. Refresh modules if the list is stale.")
        return {"FINISHED"}
