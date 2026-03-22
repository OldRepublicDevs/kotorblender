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

from ...constants import ResourceStorage, ResourceTab
from ...diagnostic_log import run_simple_operator_logged
from ...log_config import get_kb_logger
from ...vendor.pykotor_adapter import (
    is_pykotor_available,
    list_erf_mod_resources,
    resolve_game_install_path,
    try_list_bif_resources,
)
from .resource_helpers import add_resource_entry, clear_resource_list

_MAX_LOOSE_SCAN = 4000
_TEXTURE_EXT = (".tpc", ".tga", ".txi")


def _passes_filter(kb: bpy.types.PropertyGroup, label: str) -> bool:
    q = (kb.resource_name_filter or "").strip().lower()
    if not q:
        return True
    return q in label.lower()


class KB_OT_refresh_module_resources(bpy.types.Operator):
    bl_idname = "kb.refresh_module_resources"
    bl_label = "Refresh Resource List"
    bl_description = "Populate the resource list from the current tab and game installation"

    def execute(self, context: bpy.types.Context) -> set[str]:
        log = get_kb_logger("ops.module.refresh_module_resources")

        def _body() -> set[str]:
            return self._refresh_module_resources_body(context)

        return run_simple_operator_logged(log, "kb.refresh_module_resources", _body)

    def _refresh_module_resources_body(self, context: bpy.types.Context) -> set[str]:
        scene = context.scene
        kb = scene.kb

        if not is_pykotor_available():
            self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
            return {"CANCELLED"}

        install = resolve_game_install_path(kb)
        if not install:
            self.report({"ERROR"}, "Game installation path not set or not found.")
            return {"CANCELLED"}

        clear_resource_list(kb)
        tab = kb.resource_tab
        added = 0

        if tab == ResourceTab.MODULES:
            if kb.module_list_idx < 0 or kb.module_list_idx >= len(kb.module_list):
                self.report({"WARNING"}, "Select a module in the list, then refresh.")
                return {"FINISHED"}
            mod_name = kb.module_list[kb.module_list_idx].name
            mod_path = os.path.join(install, "modules", mod_name + ".mod")
            if not os.path.isfile(mod_path):
                self.report({"ERROR"}, f"Module file not found: {mod_path}")
                return {"CANCELLED"}
            for resref, ext, _data in list_erf_mod_resources(mod_path):
                label = f"{resref}.{ext}"
                if not _passes_filter(kb, label):
                    continue
                add_resource_entry(
                    kb,
                    label=label,
                    resref=resref,
                    restype_ext=ext,
                    storage=ResourceStorage.ERF,
                    erf_path=mod_path,
                )
                added += 1
                if added >= _MAX_LOOSE_SCAN:
                    break

        elif tab == ResourceTab.OVERRIDE:
            ovr = os.path.join(install, "override")
            if not os.path.isdir(ovr):
                self.report({"WARNING"}, f"No Override folder: {ovr}")
                return {"FINISHED"}
            for name in sorted(os.listdir(ovr)):
                path = os.path.join(ovr, name)
                if not os.path.isfile(path):
                    continue
                if not _passes_filter(kb, name):
                    continue
                base, ext = os.path.splitext(name)
                ext = ext.lstrip(".").lower()
                add_resource_entry(
                    kb,
                    label=name,
                    resref=base,
                    restype_ext=ext or "dat",
                    storage=ResourceStorage.LOOSE,
                    loose_path=path,
                )
                added += 1
                if added >= _MAX_LOOSE_SCAN:
                    break

        elif tab == ResourceTab.CORE:
            # Loose files only; BIF/KEY browsing uses dedicated operators.
            data_dir = os.path.join(install, "data")
            if os.path.isdir(data_dir):
                for name in sorted(os.listdir(data_dir))[:500]:
                    path = os.path.join(data_dir, name)
                    if not os.path.isfile(path):
                        continue
                    if not _passes_filter(kb, name):
                        continue
                    base, ext = os.path.splitext(name)
                    ext = ext.lstrip(".").lower()
                    add_resource_entry(
                        kb,
                        label=f"data/{name}",
                        resref=base,
                        restype_ext=ext or "dat",
                        storage=ResourceStorage.LOOSE,
                        loose_path=path,
                    )
                    added += 1
            if added == 0:
                self.report(
                    {"INFO"},
                    "Core tab: listed data/ loose files if any. Use KotOR → Tools → Browse BIF for archives.",
                )

        elif tab == ResourceTab.TEXTURES:
            roots = [
                os.path.join(install, "texturepacks"),
                os.path.join(install, "Textures"),
            ]
            for root in roots:
                if not os.path.isdir(root):
                    continue
                for dirpath, _dirnames, filenames in os.walk(root):
                    for name in filenames:
                        if not name.lower().endswith(_TEXTURE_EXT):
                            continue
                        path = os.path.join(dirpath, name)
                        rel = os.path.relpath(path, install)
                        if not _passes_filter(kb, rel):
                            continue
                        base, ext = os.path.splitext(name)
                        ext = ext.lstrip(".").lower()
                        add_resource_entry(
                            kb,
                            label=rel.replace("\\", "/"),
                            resref=base,
                            restype_ext=ext,
                            storage=ResourceStorage.LOOSE,
                            loose_path=path,
                        )
                        added += 1
                        if added >= _MAX_LOOSE_SCAN:
                            break
                    if added >= _MAX_LOOSE_SCAN:
                        break
                if added >= _MAX_LOOSE_SCAN:
                    break

        elif tab == ResourceTab.BIF:
            bif_path = (kb.active_bif_path or "").strip()
            if not bif_path or not os.path.isfile(bif_path):
                self.report({"WARNING"}, "Set a valid .bif path in Scene properties (KotOR Area & Data) or Module Designer.")
                return {"FINISHED"}
            for resref, ext in try_list_bif_resources(bif_path):
                label = f"{resref}.{ext}"
                if not _passes_filter(kb, label):
                    continue
                add_resource_entry(
                    kb,
                    label=label,
                    resref=resref,
                    restype_ext=ext,
                    storage=ResourceStorage.BIF,
                    erf_path=bif_path,
                )
                added += 1
                if added >= _MAX_LOOSE_SCAN:
                    break

        elif tab == ResourceTab.SAVES:
            saves = os.path.join(install, "saves")
            if not os.path.isdir(saves):
                self.report({"WARNING"}, f"No saves folder: {saves}")
                return {"FINISHED"}
            for name in sorted(os.listdir(saves)):
                if not name.lower().endswith(".sav"):
                    continue
                path = os.path.join(saves, name)
                if not _passes_filter(kb, name):
                    continue
                base, _ = os.path.splitext(name)
                add_resource_entry(
                    kb,
                    label=name,
                    resref=base,
                    restype_ext="sav",
                    storage=ResourceStorage.LOOSE,
                    loose_path=path,
                )
                added += 1

        kb.resource_list_idx = 0
        self.report({"INFO"}, f"Listed {added} resource(s).")
        return {"FINISHED"}
