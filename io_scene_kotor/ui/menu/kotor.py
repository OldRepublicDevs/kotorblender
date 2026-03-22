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
from bpy.types import Menu


class KB_MT_kotor_lightmaps(Menu):
    bl_label = "Lightmaps"
    bl_description = "Bake lightmaps for KotOR UVMap_lm on selected / scene geometry"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        assert layout is not None, "Layout is None"
        layout.operator("kb.bake_lightmaps_auto", text="Bake (auto)")
        layout.operator("kb.bake_lightmaps_manual", text="Bake (manual)")


class KB_MT_kotor_minimap(Menu):
    bl_label = "Minimap"
    bl_description = "Render area minimap images from the current scene layout"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        assert layout is not None, "Layout is None"
        layout.operator("kb.render_minimap_auto", text="Render (auto)")
        layout.operator("kb.render_minimap_manual", text="Render (manual)")


class KB_MT_kotor_quick(Menu):
    """Frequent actions + discoverability (F3, sidebar, preferences, docs)."""

    bl_label = "Quick access"
    bl_description = (
        "Shortcuts to module tools, search, validation, and preferences — "
        "useful if you work from menus, header, or F3 operator search"
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        assert layout is not None, "Layout is None"
        col = layout.column(align=False)
        col.label(text="Search: F3 → type KotOR, module, MDL…")
        col.separator()
        row = col.row(align=True)
        row.operator("kb.module_designer", icon="SETTINGS", text="Sidebar")
        row.operator("kb.open_addon_preferences", icon="PREFERENCES", text="Prefs")
        col.separator()
        col.operator("kb.file_search", icon="VIEWZOOM", text="Search game files…")
        col.operator("kb.validate_module", icon="VIEWZOOM", text="Validate install / module")
        col.operator("kb.refresh_module_resources", icon="FILE_REFRESH", text="Refresh resource list")
        col.separator()
        op = col.operator("wm.url_open", text="README (browser)", icon="URL")
        op.url = "https://github.com/OldRepublicDevs/KotorBlender/blob/main/README.md"


class KB_MT_kotor_showhide(Menu):
    bl_label = "Show/Hide"
    bl_description = "Toggle visibility of walkmeshes, lights, emitters, and common dummy groups"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        assert layout is not None, "Layout is None"
        layout.operator("kb.show_walkmeshes", icon="MESH_CUBE")
        layout.operator("kb.show_untextured", icon="IMAGE_RGB")
        layout.operator("kb.show_unlightmapped", icon="IMAGE_ALPHA")
        layout.operator("kb.show_lights", icon="OUTLINER_OB_LIGHT")
        layout.operator("kb.show_emitters", icon="PARTICLES")
        layout.operator("kb.show_blockers", icon="FULLSCREEN_EXIT")
        layout.operator("kb.show_char_bones", icon="BONE_DATA")
        layout.operator("kb.show_char_dummies", icon="OUTLINER_OB_EMPTY")
        layout.separator()
        layout.operator("kb.show_characters", icon="OUTLINER_OB_ARMATURE")
        layout.operator("kb.show_placeables", icon="CUBE")
        layout.operator("kb.show_doors", icon="MESH_CUBE")
        layout.operator("kb.show_items", icon="MESH_ICOSPHERE")
        layout.operator("kb.show_triggers", icon="FORCE_FORCE")
        layout.operator("kb.show_waypoints", icon="EMPTY_AXIS")
        layout.separator()
        layout.operator("kb.hide_walkmeshes", icon="MESH_CUBE")
        layout.operator("kb.hide_untextured", icon="IMAGE_RGB")
        layout.operator("kb.hide_unlightmapped", icon="IMAGE_ALPHA")
        layout.operator("kb.hide_lights", icon="OUTLINER_OB_LIGHT")
        layout.operator("kb.hide_emitters", icon="PARTICLES")
        layout.operator("kb.hide_blockers", icon="FULLSCREEN_EXIT")
        layout.operator("kb.hide_char_bones", icon="BONE_DATA")
        layout.operator("kb.hide_char_dummies", icon="OUTLINER_OB_EMPTY")
        layout.separator()
        layout.operator("kb.hide_characters", icon="OUTLINER_OB_ARMATURE")
        layout.operator("kb.hide_placeables", icon="CUBE")
        layout.operator("kb.hide_doors", icon="MESH_CUBE")
        layout.operator("kb.hide_items", icon="MESH_ICOSPHERE")
        layout.operator("kb.hide_triggers", icon="FORCE_FORCE")
        layout.operator("kb.hide_waypoints", icon="EMPTY_AXIS")


class KB_MT_kotor_game(Menu):
    bl_label = "Game"
    bl_description = "Point Blender at your KotOR install and refresh the module list"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        assert layout is not None, "Layout is None"
        layout.operator("kb.select_game_installation", text="Select Installation")
        layout.operator("kb.autodetect_game_installation", text="Autodetect Installation")
        layout.separator()
        layout.operator("kb.refresh_modules", text="Refresh Modules")
        layout.operator("kb.open_module", text="Open Module")


class KB_MT_kotor_module(Menu):
    bl_label = "Modules"
    bl_description = "Pack, unpack, clone, validate — same actions live in the KotOR sidebar (N)"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        assert layout is not None, "Layout is None"
        layout.operator("kb.module_designer", text="Module Designer")
        layout.operator("kb.indoor_map_builder", text="Indoor Map Builder")
        layout.separator()
        layout.operator("kb.git_import_instances", text="Import GIT Instances…")
        layout.operator("kb.git_export_instances", text="Export GIT from Empties…")
        layout.operator("kb.git_select_linked", text="Select GIT Objects")
        layout.operator("kb.git_frame_linked", text="Frame GIT in 3D View")
        layout.separator()
        layout.operator("kb.clone_module", text="Clone Module")
        layout.operator("kb.validate_module", text="Validate Module / Install")
        layout.operator("kb.pack_module", text="Pack Module")
        layout.operator("kb.unpack_module", text="Unpack Module")


class KB_MT_kotor_resources(Menu):
    bl_label = "Resources"
    bl_description = "Create new GFF resources or extract from the module browser list"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        assert layout is not None, "Layout is None"
        layout.menu("KB_MT_kotor_resources_new")
        layout.separator()
        layout.operator("kb.extract_resource", text="Extract Selected")
        layout.operator("kb.batch_extract_resources", text="Batch Extract")


class KB_MT_kotor_resources_new(Menu):
    bl_label = "New"
    bl_description = "Create empty UTC, UTP, DLG, TLK, and other resource stubs on disk"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        assert layout is not None, "Layout is None"
        layout.operator("kb.new_utc", text="Creature (UTC)")
        layout.operator("kb.new_utp", text="Placeable (UTP)")
        layout.operator("kb.new_utd", text="Door (UTD)")
        layout.operator("kb.new_uti", text="Item (UTI)")
        layout.operator("kb.new_uts", text="Sound (UTS)")
        layout.operator("kb.new_utt", text="Trigger (UTT)")
        layout.operator("kb.new_utm", text="Merchant (UTM)")
        layout.operator("kb.new_utw", text="Waypoint (UTW)")
        layout.operator("kb.new_ute", text="Encounter (UTE)")
        layout.separator()
        layout.operator("kb.new_dlg", text="Dialog (DLG)")
        layout.operator("kb.new_nss", text="Script (NSS)")
        layout.operator("kb.new_tlk", text="Talk Table (TLK)")
        layout.separator()
        layout.operator("kb.new_erf", text="ERF Archive")
        layout.operator("kb.new_gff", text="GFF File")


class KB_MT_kotor_tools(Menu):
    bl_label = "Tools"
    bl_description = "Search files, diff resources, edit TSLPatchData — some open dialogs or external tools"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        assert layout is not None, "Layout is None"
        layout.operator("kb.file_search", text="File Search")
        layout.operator("kb.kotor_diff", text="KotorDiff")
        layout.operator("kb.tslpatchdata_editor", text="TSLPatchData Editor")


class KB_MT_kotor_editors(Menu):
    bl_label = "Editors"
    bl_description = "Open KotOR data files for editing (NSS uses the Text Editor when available)"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        assert layout is not None, "Layout is None"
        layout.operator("kb.edit_tlk", text="Edit Talk Table")
        layout.operator("kb.edit_jrl", text="Edit Journal")
        layout.separator()
        layout.operator("kb.edit_utc", text="Edit Creature")
        layout.operator("kb.edit_utp", text="Edit Placeable")
        layout.operator("kb.edit_utd", text="Edit Door")
        layout.operator("kb.edit_uti", text="Edit Item")
        layout.operator("kb.edit_uts", text="Edit Sound")
        layout.operator("kb.edit_utt", text="Edit Trigger")
        layout.operator("kb.edit_utm", text="Edit Merchant")
        layout.operator("kb.edit_utw", text="Edit Waypoint")
        layout.operator("kb.edit_ute", text="Edit Encounter")
        layout.operator("kb.edit_dlg", text="Edit Dialog")
        layout.operator("kb.edit_nss", text="Edit Script")
        layout.separator()
        layout.operator("kb.edit_erf", text="Edit ERF Archive")
        layout.operator("kb.edit_gff", text="Edit GFF File")


class KB_MT_kotor(Menu):
    bl_label = "KotOR"
    bl_description = (
        "Star Wars: KotOR I & II tools — also in 3D View header, F3 search, "
        "and File → Import/Export"
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        assert layout is not None, "Layout is None"
        layout.menu("KB_MT_kotor_quick")
        layout.separator()
        layout.menu("KB_MT_kotor_game")
        layout.menu("KB_MT_kotor_module")
        layout.menu("KB_MT_kotor_resources")
        layout.menu("KB_MT_kotor_tools")
        layout.menu("KB_MT_kotor_editors")
        layout.separator()
        layout.menu("KB_MT_kotor_lightmaps")
        layout.menu("KB_MT_kotor_minimap")
        layout.menu("KB_MT_kotor_showhide")


def _is_kotor_object(context: bpy.types.Context) -> bool:
    """Check if active or any selected object has KotOR (kb) properties.

    Args:
        context: Blender context

    Returns:
        True if any selected object or the active object has kb properties
    """
    obj = context.active_object
    if obj is not None and getattr(obj, "kb", None) is not None:
        return True
    for obj in (context.selected_objects or []):
        if getattr(obj, "kb", None) is not None:
            return True
    return False


def draw_kotor_context_view3d(self, context: bpy.types.Context) -> None:
    """Draw KotOR submenu in 3D View object context menu when selection has kb.

    Appended to VIEW3D_MT_object_context_menu. Only shows when selection
    contains objects with KotOR properties (kb).

    Args:
        self: Menu draw function (bound to menu class)
        context: Blender context
    """
    if not _is_kotor_object(context):
        return
    self.layout.separator()
    self.layout.menu("KB_MT_kotor")


def draw_kotor_context_outliner(self, context: bpy.types.Context) -> None:
    """Draw KotOR submenu in Outliner context menu when selection has kb.

    Appended to OUTLINER_MT_context_menu. Only shows when selection
    contains objects with KotOR properties (kb).

    Args:
        self: Menu draw function (bound to menu class)
        context: Blender context
    """
    if not _is_kotor_object(context):
        return
    self.layout.separator()
    self.layout.menu("KB_MT_kotor")


def draw_kotor_header_view3d(self, context: bpy.types.Context) -> None:
    """Draw KotOR menu button in 3D View header.

    Appended to VIEW3D_HT_header. Always visible; cheap draw with no file I/O.

    Args:
        self: Header draw function (bound to header class)
        context: Blender context
    """
    self.layout.menu("KB_MT_kotor", text="KotOR")
