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
from ...diagnostic_log import run_simple_operator_logged
from ...log_config import get_kb_logger
from ...vendor.pykotor_adapter import find_kotor_paths_from_default, is_pykotor_available

if TYPE_CHECKING:
    from bpy.stub_internal.rna_enums import OperatorReturnItems

    from ...ui.props.scene import ModulePropertyGroup, ScenePropertyGroup


class KB_OT_open_module(bpy.types.Operator):  # pyright: ignore[reportIncompatibleMethodOverride]
    bl_idname = "kb.open_module"
    bl_label = "Open Module"
    bl_description = "Open the selected module in the module browser"

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        log = get_kb_logger("ops.game.open_module")

        def _body() -> set[str]:
            scene: bpy.types.Scene | None = context.scene
            if scene is None:
                self.report({"ERROR"}, "Scene is None")
                return {"CANCELLED"}

            kb: ScenePropertyGroup | None = getattr(scene, "kb", None)
            if kb is None:
                self.report({"ERROR"}, "Scene.kb is None")
                return {"CANCELLED"}

            if kb.module_list_idx < 0 or kb.module_list_idx >= len(kb.module_list):
                self.report({"ERROR"}, "No module selected")
                return {"CANCELLED"}

            if not is_pykotor_available():
                self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
                return {"CANCELLED"}

            selected_module: ModulePropertyGroup | None = kb.module_list[kb.module_list_idx]
            if selected_module is None:
                self.report({"ERROR"}, "No module selected")
                return {"CANCELLED"}

            module_name: str = selected_module.name

            # Determine installation path (autofill from find_kotor_paths_from_default when KOTOR1/KOTOR2 and path empty)
            if kb.game_type == GameType.CUSTOM:
                install_path = kb.game_installation_path
            else:
                install_path = kb.game_installation_path
                if not install_path or not os.path.exists(install_path):
                    paths = find_kotor_paths_from_default()
                    install_path = paths.get(kb.game_type, "") or ""

            if not install_path or not os.path.exists(install_path):
                self.report({"ERROR"}, f"Game installation path not found: {install_path or '(empty)'}")
                return {"CANCELLED"}

            self.report(
                {"INFO"},
                f"Module '{module_name}' selected. Open the Module Browser (3D Viewport sidebar) to browse resources.",
            )
            return {"FINISHED"}

        return run_simple_operator_logged(log, "kb.open_module", _body)
