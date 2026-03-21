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

from ...constants import GameType, ResourceStorage, ResourceTab


class ModulePropertyGroup(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Module Name")  # pyright: ignore[reportInvalidTypeForm]


class ResourceEntryPropertyGroup(bpy.types.PropertyGroup):
    """One row in the KotOR module browser / file search result list."""

    label: bpy.props.StringProperty(name="Label", default="", description="Shown in the UI list")  # pyright: ignore[reportInvalidTypeForm]
    resref: bpy.props.StringProperty(name="ResRef", default="")  # pyright: ignore[reportInvalidTypeForm]
    restype_ext: bpy.props.StringProperty(name="Type", default="", description="Lowercase extension, e.g. mdl")  # pyright: ignore[reportInvalidTypeForm]
    storage: bpy.props.EnumProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Storage",
        items=[
            (ResourceStorage.LOOSE, "Loose file", "File on disk"),
            (ResourceStorage.ERF, "ERF/MOD", "Inside a .mod / .erf archive"),
            (ResourceStorage.BIF, "BIF", "Inside a .bif archive (path in Archive Path)"),
        ],
        default=ResourceStorage.LOOSE,
    )
    erf_path: bpy.props.StringProperty(name="Archive Path", default="", subtype="FILE_PATH")  # pyright: ignore[reportInvalidTypeForm]
    loose_path: bpy.props.StringProperty(name="Loose Path", default="", subtype="FILE_PATH")  # pyright: ignore[reportInvalidTypeForm]
    bulk_select: bpy.props.BoolProperty(name="Select for batch", default=False)  # pyright: ignore[reportInvalidTypeForm]


class VisEdgePropertyGroup(bpy.types.PropertyGroup):
    room_a: bpy.props.StringProperty(name="Room A", default="")  # pyright: ignore[reportInvalidTypeForm]
    room_b: bpy.props.StringProperty(name="Room B", default="")  # pyright: ignore[reportInvalidTypeForm]


class ScenePropertyGroup(bpy.types.PropertyGroup):
    bake_samples: bpy.props.IntProperty(name="Samples", min=1, max=(1 << 24), default=1024)  # pyright: ignore[reportInvalidTypeForm]

    # Game installation properties
    game_type: bpy.props.EnumProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Game",
        items=[
            (GameType.KOTOR1, "KotOR 1", "Star Wars: Knights of the Old Republic"),
            (
                GameType.KOTOR2,
                "KotOR 2",
                "Star Wars: Knights of the Old Republic II - The Sith Lords",
            ),
            (GameType.CUSTOM, "Custom Path", "Custom installation path"),
        ],
        default=GameType.KOTOR1,
    )
    game_installation_path: bpy.props.StringProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Installation Path",
        description="Path to the KotOR game installation directory",
        subtype="DIR_PATH",
        default="",
    )
    module_list_idx: bpy.props.IntProperty(name="Module List Index", default=0)  # pyright: ignore[reportInvalidTypeForm]
    module_list: bpy.props.CollectionProperty(type=ModulePropertyGroup)  # pyright: ignore[reportInvalidTypeForm]

    # Module browser
    resource_tab: bpy.props.EnumProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Resource Tab",
        items=[
            (ResourceTab.CORE, "Core", "Core game data (override folder listing; BIF tools use File menu)"),
            (ResourceTab.MODULES, "Module", "Resources inside the selected .mod"),
            (ResourceTab.OVERRIDE, "Override", "Loose files in the Override folder"),
            (ResourceTab.TEXTURES, "Textures", "Loose textures under TexturePacks / data"),
            (ResourceTab.SAVES, "Saves", "Save games folder"),
            (ResourceTab.BIF, "BIF", "Active .bif file (set path below, then refresh)"),
        ],
        default=ResourceTab.MODULES,
    )
    resource_list_idx: bpy.props.IntProperty(name="Resource List Index", default=0)  # pyright: ignore[reportInvalidTypeForm]
    resource_list: bpy.props.CollectionProperty(type=ResourceEntryPropertyGroup)  # pyright: ignore[reportInvalidTypeForm]
    resource_name_filter: bpy.props.StringProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Filter",
        description="Substring filter applied when refreshing the resource list",
        default="",
    )
    extract_tpc_decompile: bpy.props.BoolProperty(name="TPC Decompile", default=False)  # pyright: ignore[reportInvalidTypeForm]
    extract_tpc_txi: bpy.props.BoolProperty(name="Extract TXI", default=False)  # pyright: ignore[reportInvalidTypeForm]
    extract_mdl_decompile: bpy.props.BoolProperty(name="MDL Decompile", default=False)  # pyright: ignore[reportInvalidTypeForm]
    extract_mdl_textures: bpy.props.BoolProperty(name="Extract Textures", default=False)  # pyright: ignore[reportInvalidTypeForm]

    # Area / VIS editing (Indoor Map Builder workflow)
    kotor_area_edit_active: bpy.props.BoolProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="KotOR Area Edit",
        description="When enabled, show area-editing gizmos and helpers in the 3D View",
        default=False,
    )
    active_are_path: bpy.props.StringProperty(name="Active ARE", default="", subtype="FILE_PATH")  # pyright: ignore[reportInvalidTypeForm]
    active_git_path: bpy.props.StringProperty(name="Active GIT", default="", subtype="FILE_PATH")  # pyright: ignore[reportInvalidTypeForm]
    active_vis_path: bpy.props.StringProperty(name="Active VIS", default="", subtype="FILE_PATH")  # pyright: ignore[reportInvalidTypeForm]
    vis_edges: bpy.props.CollectionProperty(type=VisEdgePropertyGroup)  # pyright: ignore[reportInvalidTypeForm]
    are_tag: bpy.props.StringProperty(name="ARE Tag", default="")  # pyright: ignore[reportInvalidTypeForm]
    are_name: bpy.props.StringProperty(name="ARE Name", default="")  # pyright: ignore[reportInvalidTypeForm]

    # Module validation / designer
    last_validation_report: bpy.props.StringProperty(name="Last Validation", default="", maxlen=65535)  # pyright: ignore[reportInvalidTypeForm]
    pack_source_directory: bpy.props.StringProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Pack Source Folder",
        description="Folder of loose resources to pack into a .mod (see Module Designer panel)",
        subtype="DIR_PATH",
        default="",
    )

    # 2DA text buffer name (Text datablock) for simple editor workflow
    active_twoda_text_name: bpy.props.StringProperty(name="Active 2DA Text", default="")  # pyright: ignore[reportInvalidTypeForm]

    active_bif_path: bpy.props.StringProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="BIF Path",
        description="Path to a .bif archive for the BIF resource tab",
        subtype="FILE_PATH",
        default="",
    )

    tslpatchdata_filepath: bpy.props.StringProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="TSLPatchData File",
        subtype="FILE_PATH",
        default="",
    )
    tslpatchdata_report: bpy.props.StringProperty(name="TSLPatch Report", default="", maxlen=65535)  # pyright: ignore[reportInvalidTypeForm]

    # Timeline / sequencing (lightweight notes per scene)
    timeline_notes: bpy.props.StringProperty(name="Timeline Notes", default="", maxlen=65535)  # pyright: ignore[reportInvalidTypeForm]
