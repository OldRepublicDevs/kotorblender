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

from typing import Any

import bpy

from .addonprefs import KotorBlenderAddonPreferences
from .ops.anim.add import KB_OT_add_animation
from .ops.anim.delete import KB_OT_delete_animation
from .ops.anim.event.add import KB_OT_add_anim_event
from .ops.anim.event.delete import KB_OT_delete_anim_event
from .ops.anim.event.move import KB_OT_move_anim_event
from .ops.anim.move import KB_OT_move_animation
from .ops.anim.play import KB_OT_play_animation
from .ops.armatureapplykeyframes import KB_OT_armature_apply_keyframes
from .ops.armatureunapplykeyframes import KB_OT_armature_unapply_keyframes
from .ops.bakelightmaps import (
    KB_OT_bake_lightmaps_auto,
    KB_OT_bake_lightmaps_manual,
)
from .ops.editor.edit_dlg import KB_OT_edit_dlg
from .ops.editor.edit_erf import KB_OT_edit_erf
from .ops.editor.edit_gff import KB_OT_edit_gff
from .ops.editor.edit_jrl import KB_OT_edit_jrl
from .ops.editor.edit_nss import KB_OT_edit_nss
from .ops.editor.edit_tlk import KB_OT_edit_tlk
from .ops.editor.edit_utc import KB_OT_edit_utc
from .ops.editor.edit_utd import KB_OT_edit_utd
from .ops.editor.edit_ute import KB_OT_edit_ute
from .ops.editor.edit_uti import KB_OT_edit_uti
from .ops.editor.edit_utm import KB_OT_edit_utm
from .ops.editor.edit_utp import KB_OT_edit_utp
from .ops.editor.edit_uts import KB_OT_edit_uts
from .ops.editor.edit_utt import KB_OT_edit_utt
from .ops.editor.edit_utw import KB_OT_edit_utw
from .ops.bwm.importop import KB_OT_import_bwm
from .ops.file_handler_drop import (
    KB_FH_import_ascii_mdl,
    KB_FH_import_bwm,
    KB_FH_import_lyt,
    KB_FH_import_mdl,
    KB_FH_import_pth,
)
from .ops.game.autodetect_installation import KB_OT_autodetect_game_installation
from .ops.game.open_module import KB_OT_open_module
from .ops.game.refresh_modules import KB_OT_refresh_modules
from .ops.game.select_installation import KB_OT_select_game_installation
from .ops.lensflare.add import KB_OT_add_lens_flare
from .ops.lensflare.delete import KB_OT_delete_lens_flare
from .ops.lensflare.move import KB_OT_move_lens_flare
from .ops.lyt.export import KB_OT_export_lyt
from .ops.lyt.importop import KB_OT_import_lyt
from .ops.mdl.ascii_export import KB_OT_export_ascii_mdl
from .ops.mdl.ascii_importop import KB_OT_import_ascii_mdl
from .ops.mdl.export import KB_OT_export_mdl
from .ops.misc.open_addon_preferences import KB_OT_open_addon_preferences
from .ops.mdl.importop import KB_OT_import_mdl
from .ops.module.batch_extract import KB_OT_batch_extract_resources
from .ops.module.refresh_module_resources import KB_OT_refresh_module_resources
from .ops.module.validate_module import KB_OT_validate_module
from .ops.module.extract_mdl_textures import KB_OT_extract_mdl_textures
from .ops.module.extract_resource import KB_OT_extract_resource
from .ops.module.extract_tpc import KB_OT_extract_tpc
from .ops.module.open_resource import KB_OT_open_resource
from .ops.module.pack_module import KB_OT_pack_module
from .ops.module.unpack_module import KB_OT_unpack_module
from .ops.pth.addconnection import KB_OT_add_path_connection
from .ops.pth.export import KB_OT_export_pth
from .ops.pth.importop import KB_OT_import_pth
from .ops.pth.removeconnection import KB_OT_delete_path_connection
from .ops.rebuildallmaterials import KB_OT_rebuild_all_materials
from .ops.rebuildarmature import KB_OT_rebuild_armature
from .ops.rebuildmaterial import KB_OT_rebuild_material
from .ops.renderminimap import KB_OT_render_minimap_auto, KB_OT_render_minimap_manual
from .ops.resource.new_dlg import KB_OT_new_dlg
from .ops.resource.new_erf import KB_OT_new_erf
from .ops.resource.new_gff import KB_OT_new_gff
from .ops.resource.new_nss import KB_OT_new_nss
from .ops.resource.new_tlk import KB_OT_new_tlk
from .ops.resource.new_utc import KB_OT_new_utc
from .ops.resource.new_utd import KB_OT_new_utd
from .ops.resource.new_ute import KB_OT_new_ute
from .ops.resource.new_uti import KB_OT_new_uti
from .ops.resource.new_utm import KB_OT_new_utm
from .ops.resource.new_utp import KB_OT_new_utp
from .ops.resource.new_uts import KB_OT_new_uts
from .ops.resource.new_utt import KB_OT_new_utt
from .ops.resource.new_utw import KB_OT_new_utw
from .ops.save.extract import KB_OT_extract_save
from .ops.save.open_editor import KB_OT_open_save_editor
from .ops.showhideobjects import (
    KB_OT_hide_blockers,
    KB_OT_hide_char_bones,
    KB_OT_hide_char_dummies,
    KB_OT_hide_characters,
    KB_OT_hide_doors,
    KB_OT_hide_emitters,
    KB_OT_hide_items,
    KB_OT_hide_lights,
    KB_OT_hide_placeables,
    KB_OT_hide_triggers,
    KB_OT_hide_unlightmapped,
    KB_OT_hide_untextured,
    KB_OT_hide_walkmeshes,
    KB_OT_hide_waypoints,
    KB_OT_show_blockers,
    KB_OT_show_char_bones,
    KB_OT_show_char_dummies,
    KB_OT_show_characters,
    KB_OT_show_doors,
    KB_OT_show_emitters,
    KB_OT_show_items,
    KB_OT_show_lights,
    KB_OT_show_placeables,
    KB_OT_show_triggers,
    KB_OT_show_unlightmapped,
    KB_OT_show_untextured,
    KB_OT_show_walkmeshes,
    KB_OT_show_waypoints,
)
from .ops.texture.batch_convert_textures import KB_OT_batch_convert_textures
from .ops.texture.convert_tga_to_tpc import KB_OT_convert_tga_to_tpc
from .ops.texture.convert_tpc_to_tga import KB_OT_convert_tpc_to_tga
from .ops.texture.extract_tpc_textures import KB_OT_extract_tpc_textures
from .ops.tools.clone_module import KB_OT_clone_module
from .ops.tools.file_search import KB_OT_file_search
from .ops.tools.indoor_map_builder import KB_OT_indoor_map_builder
from .ops.tools.kotor_diff import KB_OT_kotor_diff
from .ops.tools.module_designer import KB_OT_module_designer
from .ops.tools.tslpatchdata_editor import KB_OT_tslpatchdata_editor
from .ui.list.lensflares import KB_UL_lens_flares
from .ui.list.modules import KB_UL_modules
from .ui.list.pathpoints import KB_UL_path_points
from .ui.list.resources import KB_UL_resources
from .ui.menu.kotor import (
    KB_MT_kotor,
    KB_MT_kotor_editors,
    KB_MT_kotor_game,
    KB_MT_kotor_lightmaps,
    KB_MT_kotor_minimap,
    KB_MT_kotor_module,
    KB_MT_kotor_quick,
    KB_MT_kotor_resources,
    KB_MT_kotor_resources_new,
    KB_MT_kotor_showhide,
    KB_MT_kotor_tools,
    draw_kotor_context_outliner,
    draw_kotor_context_view3d,
    draw_kotor_header_view3d,
)
from .ui.panel.animations import (
    KB_PT_animations,
    KB_PT_animations_armature,
    KB_PT_animations_events,
)
from .ui.panel.game_installation import KB_PT_game_installation
from .ui.panel.model import KB_PT_model
from .ui.panel.modelnode.emitter import (
    KB_PT_emitter,
    KB_PT_emitter_control_points,
    KB_PT_emitter_lighting,
    KB_PT_emitter_p2p,
    KB_PT_emitter_particles,
    KB_PT_emitter_texture_anim,
)
from .ui.panel.modelnode.light import KB_PT_light, KB_PT_light_lens_flares
from .ui.panel.modelnode.mesh import (
    KB_PT_mesh,
    KB_PT_mesh_aabb,
    KB_PT_mesh_dangly,
    KB_PT_mesh_dirt,
    KB_PT_mesh_uv_anim,
)
from .ui.panel.modelnode.modelnode import KB_PT_modelnode
from .ui.panel.modelnode.reference import KB_PT_reference
from .ui.panel.module_browser import KB_PT_module_browser
from .ui.panel.module_designer import KB_PT_module_designer
from .ui.panel.pathpoint import KB_PT_path_point
from .ui.panel.resource.creature import KB_PT_creature
from .ui.panel.resource.dialog import KB_PT_dialog
from .ui.panel.resource.door import KB_PT_door
from .ui.panel.resource.encounter import KB_PT_encounter
from .ui.panel.resource.item import KB_PT_item
from .ui.panel.resource.merchant import KB_PT_merchant
from .ui.panel.resource.placeable import KB_PT_placeable
from .ui.panel.resource.sound import KB_PT_sound
from .ui.panel.resource.trigger import KB_PT_trigger
from .ui.panel.resource.waypoint import KB_PT_waypoint
from .ui.panel.save_game import KB_PT_save_game
from .ui.props.anim import AnimPropertyGroup
from .ui.props.animevent import AnimEventPropertyGroup
from .ui.props.image import ImagePropertyGroup
from .ui.props.lensflare import LensFlarePropertyGroup
from .ui.props.object import ObjectPropertyGroup
from .ui.props.pathconnection import PathConnectionPropertyGroup
from .ui.props.scene import (
    ModulePropertyGroup,
    ResourceEntryPropertyGroup,
    ScenePropertyGroup,
    VisEdgePropertyGroup,
)

bl_info: dict[str, Any] = {
    "name": "KotorBlender",
    "author": "OldRepublicDevs ft. th3w1zard1, Synchro; OpenKotOR; originally ndix UR",
    "version": (5, 0, 0),
    "blender": (3, 6, 0),
    "location": (
        "File > Import-Export · Editor > KotOR · 3D View header / Outliner · "
        "Object & Scene properties (model, nodes, animations, path, resources)"
    ),
    "description": (
        "Star Wars: Knights of the Old Republic I & II — import/export binary and ASCII MDL/MDX, "
        "area layouts (LYT), navigation paths (PTH), and walkmeshes (WOK/PWK/DWK); import TPC/TXI. "
        "Tie Blender to a game install: autodetect, browse modules, open resources, pack/unpack, "
        "batch extract, MDL/TPC texture extraction. Create or edit GFF-backed data (creatures, placeables, "
        "doors, items, sounds, triggers, merchants, waypoints, encounters, dialogs, TLK, NSS, journals, "
        "ERF, generic GFF) and inspect saves. Model workflow: KotOR node types, animations & events, "
        "armature tools, materials, lightmap bake, minimap render, lens flares, path connections. "
        "Utilities: show/hide scene layers, Module Designer, Indoor Map Builder, file search, KotorDiff, "
        "TSLPatchData editor. Drag-and-drop MDL/LYT/PTH. Optional PyKotor (bundled wheel) for advanced use."
    ),
    "category": "Import-Export",
    "doc_url": "https://github.com/OldRepublicDevs/KotorBlender/blob/main/README.md",
    "tracker_url": "https://github.com/OldRepublicDevs/KotorBlender/issues",
    "support": "COMMUNITY",
    "warning": "",
}

# Keymaps registered by register(); cleared in unregister()
addon_keymaps: list[tuple[Any, Any]] = []  # pyright: ignore[reportAttributeAccessIssue]


def menu_func_import_mdl(self, context: bpy.types.Context) -> None:
    self.layout.operator(KB_OT_import_mdl.bl_idname, text="KotOR Model (.mdl)")


def menu_func_import_ascii_mdl(self, context: bpy.types.Context) -> None:
    self.layout.operator(KB_OT_import_ascii_mdl.bl_idname, text="KotOR ASCII Model (.mdl.ascii)")


def menu_func_import_lyt(self, context: bpy.types.Context) -> None:
    self.layout.operator(KB_OT_import_lyt.bl_idname, text="KotOR Layout (.lyt)")


def menu_func_import_pth(self, context: bpy.types.Context) -> None:
    self.layout.operator(KB_OT_import_pth.bl_idname, text="KotOR Path (.pth)")


def menu_func_import_bwm(self, context: bpy.types.Context) -> None:
    self.layout.operator(KB_OT_import_bwm.bl_idname, text="KotOR Walkmesh (.wok/.pwk/.dwk)")


def menu_func_import_module(self, context: bpy.types.Context) -> None:
    from .ops.game.open_module import KB_OT_open_module

    self.layout.operator(KB_OT_open_module.bl_idname, text="KotOR Module (.mod)")


def menu_func_import_save(self, context: bpy.types.Context) -> None:
    from .ops.save.open_editor import KB_OT_open_save_editor

    self.layout.operator(KB_OT_open_save_editor.bl_idname, text="KotOR Save Game (.sav)")


def menu_func_export_mdl(self, context: bpy.types.Context) -> None:
    self.layout.operator(KB_OT_export_mdl.bl_idname, text="KotOR Model (.mdl)")


def menu_func_export_ascii_mdl(self, context: bpy.types.Context) -> None:
    self.layout.operator(KB_OT_export_ascii_mdl.bl_idname, text="KotOR ASCII Model (.mdl.ascii)")


def menu_func_export_lyt(self, context: bpy.types.Context) -> None:
    self.layout.operator(KB_OT_export_lyt.bl_idname, text="KotOR Layout (.lyt)")


def menu_func_export_pth(self, context: bpy.types.Context) -> None:
    self.layout.operator(KB_OT_export_pth.bl_idname, text="KotOR Path (.pth)")


def menu_func_kotor(self, context: bpy.types.Context) -> None:
    self.layout.menu("KB_MT_kotor")


classes = (
    KotorBlenderAddonPreferences,
    # Property Groups
    PathConnectionPropertyGroup,
    AnimEventPropertyGroup,
    AnimPropertyGroup,
    LensFlarePropertyGroup,
    ObjectPropertyGroup,
    ResourceEntryPropertyGroup,
    VisEdgePropertyGroup,
    ModulePropertyGroup,
    ScenePropertyGroup,
    ImagePropertyGroup,
    # Operators
    KB_OT_add_anim_event,
    KB_OT_add_animation,
    KB_OT_add_lens_flare,
    KB_OT_add_path_connection,
    KB_OT_armature_apply_keyframes,
    KB_OT_armature_unapply_keyframes,
    KB_OT_bake_lightmaps_auto,
    KB_OT_bake_lightmaps_manual,
    KB_OT_delete_anim_event,
    KB_OT_delete_animation,
    KB_OT_delete_lens_flare,
    KB_OT_delete_path_connection,
    KB_OT_export_lyt,
    KB_OT_export_mdl,
    KB_OT_export_ascii_mdl,
    KB_OT_export_pth,
    KB_OT_hide_blockers,
    KB_OT_hide_untextured,
    KB_OT_hide_char_bones,
    KB_OT_hide_char_dummies,
    KB_OT_hide_emitters,
    KB_OT_hide_lights,
    KB_OT_hide_unlightmapped,
    KB_OT_hide_walkmeshes,
    KB_OT_hide_characters,
    KB_OT_hide_doors,
    KB_OT_hide_items,
    KB_OT_hide_placeables,
    KB_OT_hide_triggers,
    KB_OT_hide_waypoints,
    KB_OT_import_lyt,
    KB_OT_import_mdl,
    KB_OT_import_ascii_mdl,
    KB_OT_import_pth,
    KB_OT_import_bwm,
    KB_OT_move_anim_event,
    KB_OT_move_animation,
    KB_OT_move_lens_flare,
    KB_OT_play_animation,
    KB_OT_rebuild_all_materials,
    KB_OT_rebuild_armature,
    KB_OT_rebuild_material,
    KB_OT_render_minimap_auto,
    KB_OT_render_minimap_manual,
    KB_OT_show_blockers,
    KB_OT_show_untextured,
    KB_OT_show_char_bones,
    KB_OT_show_char_dummies,
    KB_OT_show_emitters,
    KB_OT_show_lights,
    KB_OT_show_unlightmapped,
    KB_OT_show_walkmeshes,
    KB_OT_show_characters,
    KB_OT_show_doors,
    KB_OT_show_items,
    KB_OT_show_placeables,
    KB_OT_show_triggers,
    KB_OT_show_waypoints,
    # Game operators
    KB_OT_open_module,
    KB_OT_autodetect_game_installation,
    KB_OT_refresh_modules,
    KB_OT_select_game_installation,
    # Module operators
    KB_OT_batch_extract_resources,
    KB_OT_refresh_module_resources,
    KB_OT_validate_module,
    KB_OT_extract_mdl_textures,
    KB_OT_extract_resource,
    KB_OT_extract_tpc,
    KB_OT_open_resource,
    KB_OT_pack_module,
    KB_OT_unpack_module,
    # Resource creation operators
    KB_OT_new_dlg,
    KB_OT_new_erf,
    KB_OT_new_gff,
    KB_OT_new_nss,
    KB_OT_new_tlk,
    KB_OT_new_utc,
    KB_OT_new_utd,
    KB_OT_new_ute,
    KB_OT_new_uti,
    KB_OT_new_utm,
    KB_OT_new_utp,
    KB_OT_new_uts,
    KB_OT_new_utt,
    KB_OT_new_utw,
    # Save operators
    KB_OT_extract_save,
    KB_OT_open_save_editor,
    # Texture operators
    KB_OT_batch_convert_textures,
    KB_OT_convert_tga_to_tpc,
    KB_OT_convert_tpc_to_tga,
    KB_OT_extract_tpc_textures,
    # Tool operators
    KB_OT_clone_module,
    KB_OT_file_search,
    KB_OT_open_addon_preferences,
    KB_OT_indoor_map_builder,
    KB_OT_kotor_diff,
    KB_OT_module_designer,
    KB_OT_tslpatchdata_editor,
    # Editor operators
    KB_OT_edit_dlg,
    KB_OT_edit_erf,
    KB_OT_edit_gff,
    KB_OT_edit_jrl,
    KB_OT_edit_nss,
    KB_OT_edit_tlk,
    KB_OT_edit_utc,
    KB_OT_edit_utd,
    KB_OT_edit_ute,
    KB_OT_edit_uti,
    KB_OT_edit_utm,
    KB_OT_edit_utp,
    KB_OT_edit_uts,
    KB_OT_edit_utt,
    KB_OT_edit_utw,
    # Panels
    KB_PT_model,
    KB_PT_animations,
    KB_PT_animations_events,
    KB_PT_animations_armature,
    KB_PT_modelnode,
    KB_PT_reference,  # child of KB_PT_modelnode
    KB_PT_path_point,  # child of KB_PT_modelnode
    KB_PT_mesh,  # child of KB_PT_modelnode
    KB_PT_mesh_uv_anim,
    KB_PT_mesh_dirt,
    KB_PT_mesh_dangly,
    KB_PT_mesh_aabb,
    KB_PT_light,  # child of KB_PT_modelnode
    KB_PT_light_lens_flares,
    KB_PT_emitter,  # child of KB_PT_modelnode
    KB_PT_emitter_particles,
    KB_PT_emitter_texture_anim,
    KB_PT_emitter_lighting,
    KB_PT_emitter_p2p,
    KB_PT_emitter_control_points,
    KB_PT_game_installation,
    KB_PT_module_browser,
    KB_PT_module_designer,
    KB_PT_save_game,
    # Resource panels
    KB_PT_creature,
    KB_PT_dialog,
    KB_PT_door,
    KB_PT_encounter,
    KB_PT_item,
    KB_PT_merchant,
    KB_PT_placeable,
    KB_PT_sound,
    KB_PT_trigger,
    KB_PT_waypoint,
    # UI Lists
    KB_UL_lens_flares,
    KB_UL_modules,
    KB_UL_path_points,
    KB_UL_resources,
    # Menus
    KB_MT_kotor,
    KB_MT_kotor_editors,
    KB_MT_kotor_game,
    KB_MT_kotor_lightmaps,
    KB_MT_kotor_minimap,
    KB_MT_kotor_module,
    KB_MT_kotor_quick,
    KB_MT_kotor_resources,
    KB_MT_kotor_resources_new,
    KB_MT_kotor_showhide,
    KB_MT_kotor_tools,
    # Drag-and-drop file handlers (Blender 3.2+)
    KB_FH_import_mdl,
    KB_FH_import_ascii_mdl,
    KB_FH_import_lyt,
    KB_FH_import_pth,
    KB_FH_import_bwm,
)


def register():
    from .log_config import apply_preferences_log_level_safe, configure_package_logging

    import logging

    configure_package_logging(logging.INFO)
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.kb = bpy.props.PointerProperty(type=ObjectPropertyGroup)  # pyright: ignore[reportAttributeAccessIssue]
    bpy.types.Scene.kb = bpy.props.PointerProperty(type=ScenePropertyGroup)  # pyright: ignore[reportAttributeAccessIssue]
    bpy.types.Image.kb = bpy.props.PointerProperty(type=ImagePropertyGroup)  # pyright: ignore[reportAttributeAccessIssue]

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_mdl)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_ascii_mdl)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_lyt)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_pth)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_bwm)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_module)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_save)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export_mdl)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export_ascii_mdl)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export_lyt)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export_pth)

    bpy.types.TOPBAR_MT_editor_menus.append(menu_func_kotor)

    # Optional: 3D View topbar duplicate (viewport-heavy workflows)
    bpy.types.VIEW3D_MT_editor_menus.append(menu_func_kotor)

    # Context menus: KotOR submenu when selection has kb
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_kotor_context_view3d)
    bpy.types.OUTLINER_MT_context_menu.append(draw_kotor_context_outliner)
    # 3D View header: KotOR menu button
    bpy.types.VIEW3D_HT_header.append(draw_kotor_header_view3d)

    # Optional addon keymaps (2–3 high-frequency operators); skip in background mode
    assert bpy.context.window_manager is not None, "Window manager is None"
    assert bpy.context.window_manager.keyconfigs is not None, "Keyconfigs is None"
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc is not None:
        km = kc.keymaps.new(name="Window", space_type="EMPTY")
        kmi = km.keymap_items.new("kb.open_module", "O", "PRESS", ctrl=True, alt=True)
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new("kb.show_walkmeshes", "W", "PRESS", ctrl=True, alt=True)
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new("kb.hide_walkmeshes", "W", "PRESS", shift=True, ctrl=True, alt=True)
        addon_keymaps.append((km, kmi))

    apply_preferences_log_level_safe()


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_pth)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_lyt)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_ascii_mdl)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_mdl)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_save)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_module)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_bwm)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_pth)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_lyt)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_ascii_mdl)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_mdl)

    bpy.types.TOPBAR_MT_editor_menus.remove(menu_func_kotor)
    bpy.types.VIEW3D_MT_editor_menus.remove(menu_func_kotor)

    bpy.types.VIEW3D_HT_header.remove(draw_kotor_header_view3d)
    bpy.types.OUTLINER_MT_context_menu.remove(draw_kotor_context_outliner)
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_kotor_context_view3d)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
