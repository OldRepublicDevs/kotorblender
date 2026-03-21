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

from ...constants import Direction
from ...utils import find_objects, is_mdl_root, is_skin_mesh


class KB_PT_animations(bpy.types.Panel):
    bl_label = "KotOR Animations"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return is_mdl_root(context.object)

    def draw(self, context: bpy.types.Context) -> None:
        obj: bpy.types.Object | None = context.object
        if obj is None:
            raise ValueError("Object is None")
        layout = self.layout
        if layout is None:
            raise ValueError("Layout is None")
        layout.use_property_split = True

        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError("Object.kb is None")

        row = layout.row()
        row.template_list(
            "UI_UL_list",
            "animations",
            kb,
            "anim_list",
            kb,
            "anim_list_idx",
            rows=7,
        )
        col = row.column(align=True)
        col.operator("kb.add_animation", icon="ADD", text="")
        col.operator("kb.delete_animation", icon="REMOVE", text="")
        col.separator()
        col.operator("kb.move_animation", icon="TRIA_UP", text="").direction = Direction.UP
        col.operator("kb.move_animation", icon="TRIA_DOWN", text="").direction = Direction.DOWN
        col.separator()
        col.operator("kb.play_animation", icon="PLAY", text="")

        anim_list = kb.anim_list
        anim_list_idx = kb.anim_list_idx
        if anim_list_idx >= 0 and anim_list_idx < len(anim_list):
            anim = anim_list[anim_list_idx]
            row = layout.row()
            col = row.column(align=True)
            col.prop(anim, "frame_start", text="Frame Start")
            col.prop(anim, "frame_end", text="End")
            row = layout.row()
            row.prop(anim, "transtime")
            row = layout.row()
            row.prop_search(anim, "root", context.collection, "objects")


class KB_PT_animations_events(bpy.types.Panel):
    bl_label = "Events"
    bl_parent_id = "KB_PT_animations"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj: bpy.types.Object | None = context.object
        if obj is None:
            return False
        kb = getattr(obj, "kb", None)
        if kb is None:
            return False
        anim_list_idx = kb.anim_list_idx
        return is_mdl_root(obj) and anim_list_idx >= 0 and anim_list_idx < len(kb.anim_list)

    def draw(self, context: bpy.types.Context) -> None:
        obj: bpy.types.Object | None = context.object
        if obj is None:
            raise ValueError("Object is None")
        layout = self.layout
        if layout is None:
            raise ValueError("Layout is None")
        layout.use_property_split = True

        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError("Object.kb is None")

        # Event List
        anim = kb.anim_list[kb.anim_list_idx]
        row = layout.row()
        row.template_list("UI_UL_list", "anim_events", anim, "event_list", anim, "event_list_idx")
        col = row.column(align=True)
        col.operator("kb.add_anim_event", text="", icon="ADD")
        col.operator("kb.delete_anim_event", text="", icon="REMOVE")
        col.separator()
        col.operator("kb.move_anim_event", icon="TRIA_UP", text="").direction = Direction.UP
        col.operator("kb.move_anim_event", icon="TRIA_DOWN", text="").direction = Direction.DOWN

        # Selected Event
        event_list = anim.event_list
        event_list_idx = anim.event_list_idx
        if event_list_idx >= 0 and event_list_idx < len(event_list):
            event = event_list[event_list_idx]
            row = layout.row()
            row.prop(event, "frame")


class KB_PT_animations_armature(bpy.types.Panel):
    bl_label = "Armature"
    bl_parent_id = "KB_PT_animations"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        mdl_root: bpy.types.Object | None = context.object
        if mdl_root is None:
            return False
        return is_mdl_root(mdl_root) and find_objects(mdl_root, lambda obj: is_skin_mesh(obj))

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        if layout is None:
            raise ValueError("Layout is None")

        row = layout.row()
        row.operator("kb.rebuild_armature")
        row = layout.row()
        row.operator("kb.armature_apply_keyframes")
        row = layout.row()
        row.operator("kb.armature_unapply_keyframes")
