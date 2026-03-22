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

"""Sidebar: GIT editor (instances, hull meshes, spawns) + walkmesh overlay."""

from __future__ import annotations

import bpy

from ...constants import GitGeometryRole, GitInstanceSection, PropertyName
from ...vendor.pykotor_adapter import is_pykotor_available


class KB_PT_git_instances(bpy.types.Panel):
    bl_label = "GIT & Walkmesh"
    bl_idname = "KB_PT_git_instances"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KotOR"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 7

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        kb = context.scene.kb

        wm = layout.box()
        wm.label(text="Walkmesh overlay (GPU)", icon="MESH_DATA")
        wm.prop(kb, PropertyName.KOTOR_WALKMESH_OVERLAY.value)
        col = wm.column(align=True)
        col.active = bool(getattr(kb, "kotor_walkmesh_overlay", False))
        col.prop(kb, "kotor_walkmesh_overlay_fill")
        col.prop(kb, "kotor_walkmesh_overlay_edges")
        col.prop(kb, "kotor_walkmesh_overlay_alpha")
        col.prop(kb, "kotor_walkmesh_overlay_edge_alpha")
        wm.label(text="Uses scene AABB walkmesh meshes (MDL/BWM).")

        layout.separator()

        if not is_pykotor_available():
            layout.label(text="PyKotor required for GIT I/O.", icon="ERROR")
            return

        git = layout.box()
        git.label(text="GIT (game instances)", icon="EMPTY_AXIS")
        git.label(text="Import → empties + optional hull meshes.")
        git.label(text="Export writes roots, hulls, spawns.")

        layout.operator("kb.git_import_instances", icon="IMPORT")
        row = layout.row(align=True)
        row.operator("kb.git_export_instances", icon="EXPORT")
        row.operator("kb.git_select_linked", icon="RESTRICT_SELECT_OFF")
        row.operator("kb.git_frame_linked", icon="VIEW_PERSPECTIVE")
        layout.prop(kb, PropertyName.ACTIVE_GIT_PATH.value)

        obj = context.active_object
        okb = getattr(obj, "kb", None) if obj is not None else None
        if okb is not None:
            sec = getattr(okb, PropertyName.GIT_INSTANCE_SECTION.value, GitInstanceSection.NONE.value)
            role = getattr(okb, PropertyName.GIT_GEOMETRY_ROLE.value, GitGeometryRole.NONE.value)
            if (sec and sec != GitInstanceSection.NONE.value) or (role and role != GitGeometryRole.NONE.value):
                layout.separator()
                sub = layout.box()
                sub.label(text="Active object (GIT link)", icon="OBJECT_DATA")
                sub.prop(okb, PropertyName.GIT_INSTANCE_SECTION.value)
                sub.prop(okb, PropertyName.GIT_INSTANCE_INDEX.value)
                sub.prop(okb, PropertyName.GIT_INSTANCE_RESREF.value)
                sub.prop(okb, PropertyName.GIT_GEOMETRY_ROLE.value)
                sub.prop(okb, PropertyName.GIT_SPAWN_INDEX.value)
