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
    from ...ui.props.scene import ScenePropertyGroup


class KB_OT_autodetect_game_installation(bpy.types.Operator):
    bl_idname = "kb.autodetect_game_installation"
    bl_label = "Autodetect Installation"
    bl_description = (
        "Detect install folder: PyKotor (if bundled), Windows registry, GOG, Steam "
        "libraryfolders.vdf, and Steam common-folder scan. "
        "Verbose traces: Add-on Preferences → Logging → Debug + System Console"
    )

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        log = get_kb_logger("ops.game.autodetect_installation")

        def _body() -> set[str]:
            scene: bpy.types.Scene | None = context.scene
            if scene is None:
                self.report({"ERROR"}, "Scene is None")
                return {"CANCELLED"}

            kb: ScenePropertyGroup | None = getattr(scene, "kb", None)
            if kb is None:
                self.report({"ERROR"}, "Scene.kb is None")
                return {"CANCELLED"}
            if kb.game_type == GameType.CUSTOM:
                self.report({"INFO"}, "Select KotOR 1 or KotOR 2 to autodetect path.")
                return {"CANCELLED"}

            log.info("Autodetect requested for game_type=%s", kb.game_type)
            if not is_pykotor_available():
                log.info("PyKotor import unavailable; using native registry/Steam/GOG heuristics only")
            paths = find_kotor_paths_from_default()
            log.info("find_kotor_paths_from_default() -> %r", paths)
            path = paths.get(kb.game_type, "") or ""
            if not path or not os.path.exists(path):
                msg = (
                    f"No {kb.game_type} install found. "
                    "Set Add-on Preferences → Logging to Debug, open Window → Toggle System Console, "
                    "then Autodetect again to see every candidate path."
                )
                log.warning(msg)
                self.report({"WARNING"}, msg)
                return {"CANCELLED"}

            kb.game_installation_path = path
            log.info("Set game_installation_path=%s", path)
            self.report({"INFO"}, f"Set path to: {path}")
            return {"FINISHED"}

        return run_simple_operator_logged(log, "kb.autodetect_game_installation", _body)
