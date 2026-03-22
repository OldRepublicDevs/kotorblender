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

"""Open KotorBlender add-on preferences (works for extension id or legacy package name)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import bpy

from ...constants import ADDON_PREFERENCE_MODULE_KEYS
from ...diagnostic_log import run_simple_operator_logged
from ...log_config import get_kb_logger

if TYPE_CHECKING:
    from bpy.stub_internal.rna_enums import OperatorReturnItems


class KB_OT_open_addon_preferences(bpy.types.Operator):
    bl_idname = "kb.open_addon_preferences"
    bl_label = "KotorBlender Preferences"
    bl_description = "Open Preferences to this add-on (texture/lightmap search paths, optional external diff tool). Same as Edit → Preferences → Add-ons → search KotorBlender"

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        log = get_kb_logger("ops.misc.open_addon_preferences")

        def _body() -> set[str]:
            for mod in ADDON_PREFERENCE_MODULE_KEYS:
                try:
                    bpy.ops.preferences.addon_show(module=mod)
                    return {"FINISHED"}
                except RuntimeError:
                    continue
            self.report({"WARNING"}, "Could not open add-on preferences (module id mismatch).")
            return {"CANCELLED"}

        return run_simple_operator_logged(log, "kb.open_addon_preferences", _body)
