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

from ...constants import GameType
from ...vendor.pykotor_adapter import find_kotor_paths_from_default, is_pykotor_available

if TYPE_CHECKING:
    from bpy.stub_internal.rna_enums import OperatorReturnItems

    from ...ui.props.scene import ScenePropertyGroup


class KB_OT_refresh_modules(bpy.types.Operator):
    bl_idname = "kb.refresh_modules"
    bl_label = "Refresh Modules"
    bl_description = "Refresh the list of available modules from the game installation"

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        scene: bpy.types.Scene | None = context.scene
        if scene is None:
            self.report({"ERROR"}, "Scene is None")
            return {"CANCELLED"}

        kb: ScenePropertyGroup | None = getattr(scene, "kb", None)
        if kb is None:
            self.report({"ERROR"}, "Scene.kb is None")
            return {"CANCELLED"}

        if not is_pykotor_available():
            self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
            return {"CANCELLED"}

        # Determine installation path (autofill from find_kotor_paths_from_default when KOTOR1/KOTOR2 and path empty)
        if kb.game_type == GameType.CUSTOM:
            install_path = kb.game_installation_path
        else:
            install_path = kb.game_installation_path
            if not install_path or not os.path.exists(install_path):
                paths = find_kotor_paths_from_default()
                install_path = paths.get(kb.game_type, "") or ""

        if not install_path or not os.path.exists(install_path):
            self.report({"ERROR"}, f"Game installation path not found: {install_path}")
            return {"CANCELLED"}

        # Clear existing module list
        kb.module_list.clear()

        # Module list: scan for .mod files in the modules directory (PyKotor discovery optional later).
        modules_dir: str = os.path.join(install_path, "modules")
        if os.path.exists(modules_dir):
            for filename in os.listdir(modules_dir):
                if filename.endswith(".mod"):
                    module_name = filename[:-4]  # Remove .mod extension
                    item = kb.module_list.add()
                    item.name = module_name

        self.report({"INFO"}, f"Found {len(kb.module_list)} modules")
        return {"FINISHED"}
