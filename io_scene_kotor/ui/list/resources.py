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


class KB_UL_resources(bpy.types.UIList):
    def draw_item(
        self,
        context: bpy.types.Context | None,
        layout: bpy.types.UILayout,
        data: object,
        item: object,
        icon: int,
        active_data: object,
        active_propname: str,
        index: int = 0,
    ) -> None:
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row(align=True)
            if hasattr(item, "bulk_select"):
                row.prop(item, "bulk_select", text="")
            if hasattr(item, "label") and item.label:
                row.label(text=item.label)
            elif hasattr(item, "name"):
                row.label(text=item.name)
            elif hasattr(item, "resource_name"):
                row.label(text=item.resource_name)
            else:
                row.label(text=str(item))
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)
