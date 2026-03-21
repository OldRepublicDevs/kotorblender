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

from ...constants import ResourceStorage
from ...vendor.pykotor_adapter import is_pykotor_available, resolve_game_install_path
from ..module.resource_helpers import add_resource_entry, clear_resource_list

_MAX_RESULTS = 800
_SEARCH_SUBDIRS = ("modules", "override", "data", "texturepacks", "Textures", "saves", "streamwaves")


class KB_OT_file_search(bpy.types.Operator):
    bl_idname = "kb.file_search"
    bl_label = "File Search"
    bl_description = (
        "Search under your game folder (modules, override, textures…); results appear in the "
        "KotOR sidebar list — use Open / Extract like a normal resource"
    )

    search_query: bpy.props.StringProperty(
        name="Search Query",
        description="Substring to match against file names (case-insensitive)",
        default="",
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not is_pykotor_available():
            self.report({"ERROR"}, "PyKotor is not available. Install PyKotor to use this feature.")
            return {"CANCELLED"}

        scene = context.scene
        kb = scene.kb
        install = resolve_game_install_path(kb)
        if not install:
            self.report({"ERROR"}, "Game installation path not set or not found.")
            return {"CANCELLED"}

        q = (self.search_query or "").strip().lower()
        if len(q) < 2:
            self.report({"WARNING"}, "Enter at least 2 characters to search.")
            return {"CANCELLED"}

        clear_resource_list(kb)
        found = 0
        for sub in _SEARCH_SUBDIRS:
            root = os.path.join(install, sub)
            if not os.path.isdir(root):
                continue
            for dirpath, _dirnames, filenames in os.walk(root):
                for name in filenames:
                    if q not in name.lower():
                        continue
                    path = os.path.join(dirpath, name)
                    rel = os.path.relpath(path, install).replace("\\", "/")
                    base, ext = os.path.splitext(name)
                    ext = ext.lstrip(".").lower()
                    add_resource_entry(
                        kb,
                        label=rel,
                        resref=base,
                        restype_ext=ext or "dat",
                        storage=ResourceStorage.LOOSE,
                        loose_path=path,
                    )
                    found += 1
                    if found >= _MAX_RESULTS:
                        break
                if found >= _MAX_RESULTS:
                    break
            if found >= _MAX_RESULTS:
                break

        kb.resource_list_idx = 0
        kb.resource_name_filter = self.search_query
        self.report(
            {"INFO"},
            f"Found {found} file(s). Open View3D → KotOR sidebar to browse; use Refresh for tab listings.",
        )
        return {"FINISHED"}
