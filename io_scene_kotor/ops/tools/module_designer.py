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

from typing import TYPE_CHECKING

import bpy

from ...vendor.pykotor_adapter import is_pykotor_available

if TYPE_CHECKING:
    from bpy.stub_internal.rna_enums import OperatorReturnItems


def _show_view3d_sidebar(context: bpy.types.Context) -> None:
    if context.window_manager is None:
        return
    for win in context.window_manager.windows:
        if win is None:
            continue
        for area in win.screen.areas:
            if area is None:
                continue
            if area.type != "VIEW_3D":
                continue
            space: bpy.types.Space | None = area.spaces.active
            if space is None:
                continue
            show_ui: bool | None = getattr(space, "show_region_ui", None)
            if show_ui is not None:
                space.show_region_ui = True  # pyright: ignore[reportAttributeAccessIssue]
            return


class KB_OT_module_designer(bpy.types.Operator):
    bl_idname = "kb.module_designer"
    bl_label = "Module Designer"
    bl_description = "Opens the right sidebar (N) in the 3D View — open the KotOR tab → Module Designer or Module Browser. Same path: Editor → KotOR → Quick access"

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        if not is_pykotor_available():
            self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
            return {"CANCELLED"}

        _show_view3d_sidebar(context)
        self.report(
            {"INFO"},
            "Sidebar (N) → KotOR → Module Designer: pack folder, BIF path, refresh.",
        )
        return {"FINISHED"}
