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

from ....constants import MeshType, P2PType, PropertyName, UpdateType
from ....utils import is_mesh_type


class KB_PT_emitter(bpy.types.Panel):
    bl_label = "Emitter"
    bl_parent_id = "KB_PT_modelnode"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return is_mesh_type(context.object, MeshType.EMITTER)

    def draw(self, context: bpy.types.Context) -> None:
        obj: bpy.types.Object | None = context.object
        if obj is None:
            raise ValueError("Object is None")
        layout = self.layout
        if layout is None:
            raise ValueError("Layout is None")
        layout.use_property_split = True

        row = layout.row()
        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError("Object.kb is None")

        row.prop(kb, PropertyName.UPDATE)
        row = layout.row()
        row.prop(kb, PropertyName.EMITTER_RENDER)
        row = layout.row()
        row.prop(kb, PropertyName.BLEND)
        row = layout.row()
        row.prop(kb, PropertyName.SPAWNTYPE)

        row = layout.row()
        col = row.column(align=True)
        col.prop(kb, PropertyName.XSIZE, text="Size X")
        col.prop(kb, PropertyName.YSIZE, text="Y")

        row = layout.row()
        row.prop(kb, PropertyName.TEXTURE)

        if kb.depth_texture:
            row = layout.row()
            row.prop(kb, PropertyName.DEPTH_TEXTURE_NAME, text="Depth Texture")

        row = layout.row()
        row.prop(kb, PropertyName.CHUNK_NAME, text="Chunk")

        row = layout.row()
        row.prop(kb, PropertyName.NUM_BRANCHES)
        row = layout.row()
        row.prop(kb, PropertyName.RENDERORDER)
        row = layout.row()
        row.prop(kb, PropertyName.THRESHOLD)

        row = layout.row()
        row.prop(kb, PropertyName.COMBINETIME)
        row = layout.row()
        row.prop(kb, PropertyName.DEADSPACE)

        row = layout.row()
        col = row.column(align=True)
        col.prop(kb, PropertyName.TWOSIDEDTEX)
        col.prop(kb, PropertyName.DEPTH_TEXTURE)
        col.prop(kb, PropertyName.P2P)

        row = layout.row()
        col = row.column(align=True, heading="Inheritance")
        col.prop(kb, PropertyName.INHERIT, text="Inherit")
        col.prop(kb, PropertyName.INHERIT_LOCAL, text="Local")
        col.prop(kb, PropertyName.INHERITVEL, text="Velocity")
        col.prop(kb, PropertyName.INHERIT_PART, text="Particle")


class KB_PT_emitter_particles(bpy.types.Panel):
    bl_label = "Particles"
    bl_parent_id = "KB_PT_emitter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return is_mesh_type(context.object, MeshType.EMITTER)

    def draw(self, context: bpy.types.Context) -> None:
        obj: bpy.types.Object | None = context.object
        if obj is None:
            raise ValueError("Object is None")
        layout = self.layout
        if layout is None:
            raise ValueError("Layout is None")
        layout.use_property_split = True

        row = layout.row()
        col = row.column(align=True)
        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError("Object.kb is None")
        col.prop(kb, PropertyName.PERCENTSTART, text="Percent Start")
        col.prop(kb, PropertyName.PERCENTMID, text="Mid")
        col.prop(kb, PropertyName.PERCENTEND, text="End")

        row = layout.row()
        col = row.column(align=True)
        col.prop(kb, PropertyName.COLORSTART, text="Color Start")
        col.prop(kb, PropertyName.COLORMID, text="Mid")
        col.prop(kb, PropertyName.COLOREND, text="End")

        row = layout.row()
        col = row.column(align=True)
        col.prop(kb, PropertyName.ALPHASTART, text="Alpha Start")
        col.prop(kb, PropertyName.ALPHAMID, text="Mid")
        col.prop(kb, PropertyName.ALPHAEND, text="End")

        row = layout.row()
        col = row.column(align=True)
        col.prop(kb, PropertyName.SIZESTART, text="Size Start")
        col.prop(kb, PropertyName.SIZEMID, text="Mid")
        col.prop(kb, PropertyName.SIZEEND, text="End")

        row = layout.row()
        col = row.column(align=True)
        col.prop(kb, PropertyName.SIZESTART_Y, text="Y Size Start")
        col.prop(kb, PropertyName.SIZEMID_Y, text="Mid")
        col.prop(kb, PropertyName.SIZEEND_Y, text="End")

        row = layout.row()
        col = row.column(align=True)
        col.prop(kb, PropertyName.BIRTHRATE, text="Birthrate")
        col.prop(kb, PropertyName.RANDOMBIRTHRATE, text="Random")

        row = layout.row()
        row.prop(kb, PropertyName.LIFEEXP)
        row = layout.row()
        row.prop(kb, PropertyName.MASS)
        row = layout.row()
        row.prop(kb, PropertyName.SPREAD)
        row = layout.row()
        row.prop(kb, PropertyName.PARTICLEROT, text="Rotation")

        row = layout.row()
        col = row.column(align=True)
        col.prop(kb, PropertyName.VELOCITY, text="Velocity")
        col.prop(kb, PropertyName.RANDVEL, text="Random")

        row = layout.row()
        row.prop(kb, PropertyName.BLURLENGTH)
        row = layout.row()
        row.prop(kb, PropertyName.TARGETSIZE)

        row = layout.row()
        col = row.column(align=True)
        col.prop(kb, PropertyName.TANGENTSPREAD, text="Tangent Spread")
        col.prop(kb, PropertyName.TANGENTLENGTH, text="Length")

        row = layout.row()
        col = row.column(align=True)
        col.prop(kb, PropertyName.BLASTRADIUS, text="Blast Radius")
        col.prop(kb, PropertyName.BLASTLENGTH, text="Length")

        if kb.bounce:
            row = layout.row()
            row.prop(kb, PropertyName.BOUNCE_CO)

        row = layout.row()
        col = row.column(align=True)
        col.prop(kb, PropertyName.BOUNCE)
        col.prop(kb, PropertyName.LOOP)
        col.prop(kb, PropertyName.SPLAT)
        col.prop(kb, PropertyName.AFFECTED_BY_WIND)
        col.prop(kb, PropertyName.TINTED)


class KB_PT_emitter_texture_anim(bpy.types.Panel):
    bl_label = "Texture Animation"
    bl_parent_id = "KB_PT_emitter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return is_mesh_type(context.object, MeshType.EMITTER)

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
        col = row.column(align=True)
        col.prop(kb, PropertyName.XGRID, text="Grid X")
        col.prop(kb, PropertyName.YGRID, text="Y")

        row = layout.row()
        col = row.column(align=True)
        col.prop(kb, PropertyName.FRAMESTART, text="Frame Start")
        col.prop(kb, PropertyName.FRAMEEND, text="End")

        row = layout.row()
        row.prop(kb, PropertyName.FPS)

        row = layout.row()
        col = row.column(align=True)
        col.prop(kb, PropertyName.FRAME_BLENDING)
        col.prop(kb, PropertyName.RANDOM)


class KB_PT_emitter_lighting(bpy.types.Panel):
    bl_label = "Lighting"
    bl_parent_id = "KB_PT_emitter"
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
        return is_mesh_type(obj, MeshType.EMITTER) and kb.update == UpdateType.LIGHTNING

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
        row.prop(kb, PropertyName.LIGHTNINGDELAY, text="Delay")
        row = layout.row()
        row.prop(kb, PropertyName.LIGHTNINGRADIUS, text="Radius")
        row = layout.row()
        row.prop(kb, PropertyName.LIGHTNINGSUBDIV, text="Subdivisions")
        row = layout.row()
        row.prop(kb, PropertyName.LIGHTNINGSCALE, text="Scale")
        row = layout.row()
        row.prop(kb, PropertyName.LIGHTNINGZIGZAG, text="Zig-Zag")


class KB_PT_emitter_p2p(bpy.types.Panel):
    bl_label = "P2P"
    bl_parent_id = "KB_PT_emitter"
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
        return is_mesh_type(obj, MeshType.EMITTER) and kb.p2p

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
        row.prop(kb, PropertyName.P2P_TYPE)

        if kb.p2p_type == P2PType.BEZIER:
            row = layout.row()
            row.prop(kb, PropertyName.P2P_BEZIER2)
            row = layout.row()
            row.prop(kb, PropertyName.P2P_BEZIER3)
        elif kb.p2p_type == P2PType.GRAVITY:
            row = layout.row()
            row.prop(kb, PropertyName.GRAV)
            row = layout.row()
            row.prop(kb, PropertyName.DRAG)


class KB_PT_emitter_control_points(bpy.types.Panel):
    bl_label = "Control Points"
    bl_parent_id = "KB_PT_emitter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return is_mesh_type(context.object, MeshType.EMITTER)

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
        row.prop(kb, PropertyName.NUMCONTROLPTS, text="Number of Points")
        row = layout.row()
        row.prop(kb, PropertyName.CONTROLPTRADIUS, text="Radius")
        row = layout.row()
        row.prop(kb, PropertyName.CONTROLPTDELAY, text="Delay")
        row = layout.row()
        row.prop(kb, PropertyName.CONTROLPTSMOOTHING, text="Smoothing")
