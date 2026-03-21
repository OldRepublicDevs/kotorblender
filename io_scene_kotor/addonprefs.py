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
from bpy.props import EnumProperty, StringProperty
from bpy.types import AddonPreferences

from . import log_config
from .constants import PACKAGE_NAME
from .vendor.pykotor_adapter import is_pykotor_available

DEF_TEXTURE_SEARCH_PATHS = "textures;../textures;../texturepacks/swpc_tex_tpa"
DEF_LIGHTMAP_SEARCH_PATHS = "lightmaps;../lightmaps"


class KotorBlenderAddonPreferences(AddonPreferences):
    bl_idname = PACKAGE_NAME

    # Use assignment only (no type annotation) to avoid typing.get_type_hints failing in Blender 4.4+
    texture_search_paths = StringProperty(
        name="Texture Search Paths",
        description="Semicolon-separated list of paths. Can be relative to the imported layout or absolute.",
        default=DEF_TEXTURE_SEARCH_PATHS,
    )

    lightmap_search_paths = StringProperty(
        name="Lightmap Search Paths",
        description="Semicolon-separated list of paths. Can be relative to the imported layout or absolute.",
        default=DEF_LIGHTMAP_SEARCH_PATHS,
    )

    external_diff_path = StringProperty(
        name="External Diff Tool",
        description=(
            "Optional trusted diff/merge executable (e.g. Meld, KDiff3). "
            "KotorBlender invokes it as [exe, file_a, file_b] with no shell — "
            "point only at programs you trust."
        ),
        subtype="FILE_PATH",
        default="",
    )

    log_verbosity = EnumProperty(
        name="Logging verbosity",
        description="How much KotorBlender writes to the system console (stderr). Use Debug when troubleshooting autodetect / PyKotor",
        items=(
            ("DISABLED", "Off", "No KotorBlender log output"),
            ("ERROR", "Error", "Errors only"),
            ("WARNING", "Warning", "Warnings and errors"),
            ("INFO", "Info", "Normal messages"),
            ("DEBUG", "Debug", "Verbose: every install candidate and PyKotor step"),
        ),
        default="INFO",
        update=log_config.on_log_verbosity_updated,
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(text="Tip: press F3 in Blender and search “KotOR” to jump to any action", icon="INFO")
        status = layout.box()
        status.label(text="Runtime status", icon="OPTIONS")
        if is_pykotor_available():
            status.label(
                text="PyKotor is available (module browser, pack/unpack, BIF, and related tools).",
                icon="CHECKMARK",
            )
        else:
            status.label(
                text="PyKotor is not available. Run `make wheel-download` from the repo, then rebuild/install the extension.",
                icon="ERROR",
            )
        status.label(
            text="Game install folder is set per scene: Scene properties → KotOR Game Installation.",
            icon="INFO",
        )
        status.label(
            text="Optional shortcuts (when not in background mode): Ctrl+Alt+O Open Module; "
            "Ctrl+Alt+W show walkmeshes; Shift+Ctrl+Alt+W hide walkmeshes.",
            icon="KEYING",
        )
        layout.separator()
        layout.label(
            text="Paths used when resolving textures and lightmaps for imported models (semicolon-separated).",
        )
        layout.prop(self, "texture_search_paths")
        layout.prop(self, "lightmap_search_paths")
        layout.separator()
        layout.prop(self, "external_diff_path")
        layout.separator()
        box = layout.box()
        box.label(text="Diagnostics", icon="CONSOLE")
        box.prop(self, "log_verbosity")
