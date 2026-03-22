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

import bpy

from ...diagnostic_log import run_simple_operator_logged
from ...log_config import get_kb_logger
from ...vendor.pykotor_adapter import (
    is_pykotor_available,
    resolve_game_install_path,
    run_pykotor_clone_module,
)


class KB_OT_clone_module(bpy.types.Operator):
    bl_idname = "kb.clone_module"
    bl_label = "Clone Module"
    bl_description = (
        "Clone the selected module to a new name using PyKotor (ARE/GIT/IFO/LYT/VIS, optional textures "
        "and pathing) — same options as HolocronToolset Clone Module"
    )
    bl_options = {"REGISTER"}

    new_module_name: bpy.props.StringProperty(
        name="New Module Name",
        description="New module resref without .mod (lowercase, e.g. myarea)",
        default="",
    )
    module_prefix: bpy.props.StringProperty(
        name="Prefix",
        description="3-letter prefix for textures/lightmaps (Holocron default: first 3 chars of new name)",
        default="",
    )
    area_display_name: bpy.props.StringProperty(
        name="Area Display Name",
        description="Human-readable name written to the cloned ARE (defaults to new module name)",
        default="",
    )
    copy_textures: bpy.props.BoolProperty(
        name="Copy Textures",
        description="Copy and rename TPC/TGA textures (can take a long time)",
        default=False,
    )
    copy_lightmaps: bpy.props.BoolProperty(
        name="Copy Lightmaps",
        description="Copy and rename lightmap textures for MDL meshes",
        default=False,
    )
    keep_doors: bpy.props.BoolProperty(
        name="Keep Doors",
        description="Include door placeables in the cloned GIT",
        default=False,
    )
    keep_placeables: bpy.props.BoolProperty(
        name="Keep Placeables",
        description="Include placeables in the cloned GIT",
        default=False,
    )
    keep_sounds: bpy.props.BoolProperty(
        name="Keep Sounds",
        description="Include sound markers in the cloned GIT",
        default=False,
    )
    keep_pathing: bpy.props.BoolProperty(
        name="Keep Pathing",
        description="Copy PTH into the new module",
        default=False,
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "new_module_name")
        layout.prop(self, "module_prefix")
        layout.prop(self, "area_display_name")
        box = layout.box()
        box.label(text="Include in clone", icon="MODIFIER")
        col = box.column(align=True)
        col.prop(self, "copy_textures")
        col.prop(self, "copy_lightmaps")
        col.prop(self, "keep_doors")
        col.prop(self, "keep_placeables")
        col.prop(self, "keep_sounds")
        col.prop(self, "keep_pathing")

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.tools.clone_module")

        def _body() -> set[str]:
            if not is_pykotor_available():
                self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
                return {"CANCELLED"}

            scene = context.scene
            kb = scene.kb
            if kb.module_list_idx < 0 or kb.module_list_idx >= len(kb.module_list):
                self.report({"ERROR"}, "No module selected in the scene module list.")
                return {"CANCELLED"}

            install = resolve_game_install_path(kb)
            if not install:
                self.report({"ERROR"}, "Game installation path not set or not found.")
                return {"CANCELLED"}

            src_name = kb.module_list[kb.module_list_idx].name
            dst_name = (self.new_module_name or "").strip().lower()
            if not dst_name or any(c in dst_name for c in r'\/:*?"<>|'):
                self.report({"ERROR"}, "Invalid new module name.")
                return {"CANCELLED"}

            dst_path = os.path.join(install, "modules", dst_name + ".mod")
            if os.path.exists(dst_path):
                self.report({"ERROR"}, f"Target already exists: {dst_path}")
                return {"CANCELLED"}

            prefix = (self.module_prefix or "").strip().lower()
            if not prefix:
                prefix = dst_name[:3].lower() if len(dst_name) >= 3 else dst_name.lower()

            area_name = (self.area_display_name or "").strip() or dst_name

            if self.copy_textures:
                self.report(
                    {"WARNING"},
                    "Copy textures is enabled — cloning may take several minutes.",
                )

            wm = context.window_manager
            progress = getattr(wm, "progress_begin", None)
            progress_end = getattr(wm, "progress_end", None)
            if callable(progress):
                progress(0, 9999)
            try:
                run_pykotor_clone_module(
                    install,
                    src_name,
                    dst_name,
                    prefix,
                    area_name,
                    copy_textures=self.copy_textures,
                    copy_lightmaps=self.copy_lightmaps,
                    keep_doors=self.keep_doors,
                    keep_placeables=self.keep_placeables,
                    keep_sounds=self.keep_sounds,
                    keep_pathing=self.keep_pathing,
                )
            except ValueError as e:
                self.report({"ERROR"}, f"Clone failed: {e}")
                return {"CANCELLED"}
            except OSError as e:
                self.report({"ERROR"}, f"Clone failed: {e}")
                return {"CANCELLED"}
            except RuntimeError as e:
                self.report({"ERROR"}, str(e))
                return {"CANCELLED"}
            finally:
                if callable(progress_end):
                    progress_end()

            item = kb.module_list.add()
            item.name = dst_name
            self.report({"INFO"}, f"Cloned module to {dst_path}. Refresh modules if the list is stale.")
            return {"FINISHED"}

        return run_simple_operator_logged(log, "kb.clone_module", _body)
