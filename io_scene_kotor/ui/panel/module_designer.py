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

"""View3D sidebar: HolocronToolset-style module workflow (pack, BIF path, refresh, validate)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import bpy

from ...vendor.pykotor_adapter import is_pykotor_available

if TYPE_CHECKING:
    from ...ui.props.scene import ScenePropertyGroup


class KB_PT_module_designer(bpy.types.Panel):
    """Incremental Module Designer UI: paths + pack/unpack/clone + BIF tab support."""

    bl_label = "Module Designer"
    bl_description = (
        "Pack loose files into .mod, set BIF path for the BIF tab, validate your install — "
        "complements the Module Browser panel above"
    )
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KotOR"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 5

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        if layout is None:
            raise ValueError("Layout is None")
        scene = context.scene
        kb: ScenePropertyGroup | None = getattr(scene, "kb", None)
        if kb is None:
            layout.label(text="Scene.kb missing")
            return

        tips = layout.box()
        tips.label(text="Access", icon="INFO")
        tips.label(text="· Also: Editor → KotOR → Quick access")
        tips.label(text="· F3 → search “pack” or “validate”")
        layout.separator()

        col = layout.column(align=True)
        col.label(text="Pack loose folder into .mod / .erf")
        col.prop(kb, "pack_source_directory", text="Source")
        row = col.row(align=True)
        row.operator("kb.pack_module", text="Pack…", icon="PACKAGE")
        row.operator("kb.unpack_module", text="Unpack…", icon="IMPORT")
        col.operator("kb.clone_module", icon="DUPLICATE")

        layout.separator()
        box = layout.box()
        box.label(text="BIF tab (Module Browser)")
        box.prop(kb, "active_bif_path", text="BIF file")
        row = box.row(align=True)
        row.operator("kb.refresh_module_resources", text="Refresh lists", icon="FILE_REFRESH")
        row.operator("kb.validate_module", text="Validate", icon="VIEWZOOM")

        report: str = (kb.last_validation_report or "").strip()
        if report:
            layout.separator()
            rbox = layout.box()
            rbox.label(text="Last validation (preview)", icon="INFO")
            for line in report.split("\n")[:14]:
                if line.strip():
                    rbox.label(text=line[:70] + ("…" if len(line) > 70 else ""))

        if not is_pykotor_available():
            layout.separator()
            w = layout.box()
            w.label(text="PyKotor not available", icon="ERROR")
            w.label(text="Install the bundled wheel for pack/BIF.")
