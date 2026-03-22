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

from ...diagnostic_log import run_simple_operator_logged
from ...log_config import get_kb_logger
from ...vendor.pykotor_adapter import is_pykotor_available


class KB_OT_indoor_map_builder(bpy.types.Operator):
    bl_idname = "kb.indoor_map_builder"
    bl_label = "Indoor Map Builder"
    bl_options = {"REGISTER"}
    bl_description = (
        "Enable KotOR area-edit mode and open the Indoor Map Builder sidebar section: "
        "import LYT, set ARE/GIT/VIS paths; use HolocronToolset for full indoor kit"
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.tools.indoor_map_builder")

        def _body() -> set[str]:
            if not is_pykotor_available():
                self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
                return {"CANCELLED"}

            context.scene.kb.kotor_area_edit_active = True
            self.report(
                {"INFO"},
                "Area edit mode on. Sidebar (N) → KotOR → Indoor Map Builder: LYT import, ARE/GIT/VIS paths. "
                "Full GIT/VIS editing: HolocronToolset (see PyKotor vendor help wiki).",
            )
            return {"FINISHED"}

        return run_simple_operator_logged(log, "kb.indoor_map_builder", _body)
