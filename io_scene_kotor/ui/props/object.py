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

from ...constants import (
    NULL,
    BlendType,
    Classification,
    DummyType,
    EmitterRenderType,
    MeshType,
    P2PType,
    SpawnType,
    UpdateType,
    git_geometry_role_enum_items,
    git_instance_section_enum_items,
)
from ...scene.modelnode.light import LightNode
from .anim import AnimPropertyGroup
from .lensflare import LensFlarePropertyGroup
from .pathconnection import PathConnectionPropertyGroup


def on_update_light_power(self: object, context: bpy.types.Context) -> None:
    obj: bpy.types.Object | None = context.object
    if obj is not None and obj.type == "LIGHT":
        LightNode.calc_light_power(obj)


class ObjectPropertyGroup(bpy.types.PropertyGroup):
    # Model Node
    node_number: bpy.props.IntProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Node Number",
        description="Must be unique per model and equal to this node number in supermodel",
        default=-1,
        min=-1,
        max=1000,
    )
    export_order: bpy.props.IntProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Export Order",
        description="Export order relative to parent",
        min=0,
        max=1000,
    )

    # Model
    supermodel: bpy.props.StringProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Supermodel",
        description="Name of the model to inherit animations from",
        default=NULL,
    )
    classification: bpy.props.EnumProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Classification",
        items=[
            (Classification.OTHER, "Other", "Unknown", 0),
            (Classification.EFFECT, "Effect", "", 1),
            (Classification.TILE, "Tile", "", 2),
            (Classification.CHARACTER, "Character", "Creatures and placeables", 3),
            (Classification.DOOR, "Door", "", 4),
            (Classification.LIGHTSABER, "Lightsaber", "", 5),
            (Classification.PLACEABLE, "Placeable", "Placeables and items", 6),
            (Classification.FLYER, "Flyer", "Non-interactive scene elements", 7),
        ],
        default=Classification.OTHER,
    )
    subclassification: bpy.props.IntProperty(name="Subclassification")  # pyright: ignore[reportInvalidTypeForm]
    affected_by_fog: bpy.props.BoolProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Affected by Fog",
        description="This model should be affected by area fog",
        default=True,
    )
    animroot: bpy.props.StringProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Anim Root",
        description="Animations should only affect children of selected object",
        default=NULL,
    )
    animscale: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Anim Scale",
        description="Scale of this model relative to its supermodel",
        default=1.0,
        min=0.0,
    )
    classification_unk1: bpy.props.IntProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Classification Unknown",
        description="Preserved unknown model-header byte",
        default=0,
        min=0,
        max=255,
    )
    bounding_box_min: bpy.props.FloatVectorProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Bounding Box Min",
        description="Preserved model-space minimum bounds",
        subtype="XYZ",
        default=(0.0, 0.0, 0.0),
    )
    bounding_box_max: bpy.props.FloatVectorProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Bounding Box Max",
        description="Preserved model-space maximum bounds",
        subtype="XYZ",
        default=(0.0, 0.0, 0.0),
    )
    model_radius: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Model Radius",
        description="Preserved model header radius",
        default=0.0,
        min=0.0,
    )

    # Animations
    anim_list: bpy.props.CollectionProperty(type=AnimPropertyGroup)
    anim_list_idx: bpy.props.IntProperty()  # pyright: ignore[reportInvalidTypeForm]
    # Dummy Node
    dummytype: bpy.props.EnumProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Type",
        items=[
            (DummyType.NONE, "None", "", 0),
            (DummyType.MDLROOT, "MDL Root", "Root of MDL model", 1),
            (DummyType.DWKROOT, "DWK Root", "Root of door walkmesh", 2),
            (DummyType.PWKROOT, "PWK Root", "Root of placeable walkmesh", 3),
            (DummyType.PTHROOT, "PTH Root", "", 4),
            (DummyType.REFERENCE, "Reference", "", 5),
            (DummyType.PATHPOINT, "Path Point", "", 6),
            (DummyType.USE1, "Walkmesh: Use 1", "'Use 1' animation position", 7),
            (DummyType.USE2, "Walkmesh: Use 2", "'Use 2' animation position", 8),
        ],
        default=DummyType.NONE,
    )

    # Reference Node
    refmodel: bpy.props.StringProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Reference Model",
        description="Name of another model",
        default="fx_ref",
    )
    reattachable: bpy.props.BoolProperty(name="Reattachable")  # pyright: ignore[reportInvalidTypeForm]
    # Mesh Node
    meshtype: bpy.props.EnumProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Type",
        items=[
            (MeshType.TRIMESH, "Trimesh", "", 0),
            (MeshType.DANGLYMESH, "Danglymesh", "", 1),
            (MeshType.SKIN, "Skinmesh", "", 2),
            (MeshType.AABB, "AABB", "", 3),
            (MeshType.EMITTER, "Emitter", "", 4),
            (MeshType.LIGHTSABER, "Lightsaber", "", 5),
        ],
        default=MeshType.TRIMESH,
    )
    bitmap: bpy.props.StringProperty(name="Main Texture")  # pyright: ignore[reportInvalidTypeForm]
    bitmap2: bpy.props.StringProperty(name="Lightmap")  # pyright: ignore[reportInvalidTypeForm]
    alpha: bpy.props.FloatProperty(name="Alpha", default=1.0, min=0.0, max=1.0)  # pyright: ignore[reportInvalidTypeForm]
    render: bpy.props.BoolProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Render",
        description="This object should be rendered",
        default=True,
    )
    shadow: bpy.props.BoolProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Shadow",
        description="This object should cast shadows",
        default=True,
    )
    lightmapped: bpy.props.BoolProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Lightmapped",
        description="This object is lightmapped",
    )
    beaming: bpy.props.BoolProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Beaming",
        description="This object should cast beams",
    )
    tangentspace: bpy.props.BoolProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Tangent Space",
        description="This object is normal mapped",
    )
    rotatetexture: bpy.props.BoolProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Rotate Texture",
        description="Texture should be automatically rotated to prevent seams",
    )
    background_geometry: bpy.props.BoolProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Background Geometry",
        description="This object is part of background geometry",
    )
    dirt_enabled: bpy.props.BoolProperty(
        name="Dirt",
        description="Enable dirt (TSL only)",
    )
    dirt_texture: bpy.props.IntProperty(name="Dirt Texture", default=1)
    dirt_worldspace: bpy.props.IntProperty(name="Dirt World Space", default=1)
    hologram_donotdraw: bpy.props.BoolProperty(
        name="Hide in Hologram",
        description="This object should be hidden in hologram mode (e.g., tongue)",
    )
    animateuv: bpy.props.BoolProperty(
        name="Animate UV",
        description="Animate texture coordinates",
    )
    uvdirectionx: bpy.props.FloatProperty(name="X Direction", default=1.0)
    uvdirectiony: bpy.props.FloatProperty(name="Y Direction")
    uvjitter: bpy.props.FloatProperty(name="Jitter Amount")
    uvjitterspeed: bpy.props.FloatProperty(name="Jitter Speed")
    transparencyhint: bpy.props.IntProperty(name="Transparency Hint", min=0, max=32)
    selfillumcolor: bpy.props.FloatVectorProperty(
        name="Self-illum. Color",
        description="This object should glow, but not emit light",
        subtype="COLOR_GAMMA",
        min=0.0,
        max=1.0,
    )
    diffuse: bpy.props.FloatVectorProperty(
        name="Diffuse Color",
        subtype="COLOR_GAMMA",
        default=(0.8, 0.8, 0.8),
        min=0.0,
        max=1.0,
    )
    ambient: bpy.props.FloatVectorProperty(
        name="Ambient Color",
        subtype="COLOR_GAMMA",
        default=(0.2, 0.2, 0.2),
        min=0.0,
        max=1.0,
    )
    lytposition: bpy.props.FloatVectorProperty(
        name="LYT Position",
        description="Room position in LYT file",
        subtype="XYZ",
    )

    # Danglymesh
    period: bpy.props.FloatProperty(name="Period", default=1.0, min=0.0, max=32.0)  # pyright: ignore[reportInvalidTypeForm]
    tightness: bpy.props.FloatProperty(name="Tightness", default=1.0, min=0.0, max=32.0)  # pyright: ignore[reportInvalidTypeForm]
    displacement: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Displacement",
        default=0.5,
        min=0.0,
        max=32.0,
    )
    constraints: bpy.props.StringProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Constraints",
        description="Name of the vertex group to store constraints in",
    )

    # Light
    ambientonly: bpy.props.BoolProperty(name="Ambient Only")  # pyright: ignore[reportInvalidTypeForm]
    lightpriority: bpy.props.IntProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Light Priority",
        default=3,
        soft_min=1,
        soft_max=5,
    )
    fadinglight: bpy.props.BoolProperty(name="Fading Light")  # pyright: ignore[reportInvalidTypeForm]
    dynamictype: bpy.props.IntProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Dynamic Type",
        description="This light should affect: 0 - ???\n1 - Area geometry AND dynamic objects\n2 - Dynamic objects ONLY",
        min=0,
        max=2,
    )
    affectdynamic: bpy.props.BoolProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Affect Dynamic",
        description="This light should affect dynamic objects",
    )
    lensflares: bpy.props.BoolProperty(name="Lens Flares")  # pyright: ignore[reportInvalidTypeForm]
    flareradius: bpy.props.FloatProperty(name="Flare Radius", min=0.0, max=1e6)  # pyright: ignore[reportInvalidTypeForm]
    flare_list: bpy.props.CollectionProperty(type=LensFlarePropertyGroup)  # pyright: ignore[reportInvalidTypeForm]
    flare_list_idx: bpy.props.IntProperty()  # pyright: ignore[reportInvalidTypeForm]
    radius: bpy.props.FloatProperty(
        name="Radius",  # pyright: ignore[reportInvalidTypeForm]
        min=0.0,
        max=1e6,
        update=on_update_light_power,
    )
    multiplier: bpy.props.FloatProperty(
        name="Multiplier",  # pyright: ignore[reportInvalidTypeForm]
        default=1.0,
        min=0.0,
        max=10.0,
        update=on_update_light_power,
    )
    negativelight: bpy.props.BoolProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Negative Light",
        update=on_update_light_power,
    )
    shadowradius: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Shadow Radius",
        description="Animated light shadow radius",
        default=0.0,
        min=0.0,
        max=1e6,
    )
    verticaldisplacement: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Vertical Displacement",
        description="Animated light vertical displacement",
        default=0.0,
        min=-1e6,
        max=1e6,
    )

    # Emitter
    alphaend: bpy.props.FloatProperty(name="Alpha End", default=1.0, min=0.0, max=1.0)  # pyright: ignore[reportInvalidTypeForm]
    alphastart: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Alpha Start",
        default=1.0,
        min=0.0,
        max=1.0,
    )
    birthrate: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Birthrate",
        default=10.0,
        soft_min=-90.0,
        soft_max=400.0,
    )
    bounce_co: bpy.props.FloatProperty(name="Bounce Coefficient", min=0.0, max=1.0)  # pyright: ignore[reportInvalidTypeForm]
    combinetime: bpy.props.FloatProperty(name="Combine Time", min=0.0, soft_max=3.0)  # pyright: ignore[reportInvalidTypeForm]
    drag: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Drag",
        description="Drag (m/s²)",
        min=0.0,
        max=1.0,
    )
    fps: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="FPS",
        description="Frames Per Second",
        default=24.0,
        min=0.0,
        soft_max=60.0,
    )
    frameend: bpy.props.FloatProperty(name="End Frame", min=0.0, soft_max=255.0)  # pyright: ignore[reportInvalidTypeForm]
    framestart: bpy.props.FloatProperty(name="Start Frame", min=0.0, soft_max=255.0)  # pyright: ignore[reportInvalidTypeForm]
    grav: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Gravity",
        description="Gravity (m/s²)",
        min=0.0,
        soft_max=10.0,
    )
    lifeexp: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Life Expectancy",
        default=1.0,
        soft_min=-1.0,
        soft_max=92.0,
    )
    mass: bpy.props.FloatProperty(name="Mass", default=1.0, soft_min=-0.5, soft_max=9.0)  # pyright: ignore[reportInvalidTypeForm]
    p2p_bezier2: bpy.props.FloatProperty(name="Bezier 2", min=0.0, soft_max=0.2)  # pyright: ignore[reportInvalidTypeForm]
    p2p_bezier3: bpy.props.FloatProperty(name="Bezier 3", min=0.0, soft_max=3.0)  # pyright: ignore[reportInvalidTypeForm]
    particlerot: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Particle Rotation",
        soft_min=-5.0,
        soft_max=720.0,
    )
    randvel: bpy.props.FloatProperty(name="Random Velocity", min=0.0, soft_max=20.0)  # pyright: ignore[reportInvalidTypeForm]
    sizestart: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Size Start",
        default=1.0,
        min=0.0,
        soft_max=255.0,
    )
    sizeend: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Size End",
        default=1.0,
        min=0.0,
        soft_max=255.0,
    )
    sizestart_y: bpy.props.FloatProperty(name="Y Size Start", min=0.0, soft_max=40.0)  # pyright: ignore[reportInvalidTypeForm]
    sizeend_y: bpy.props.FloatProperty(name="Y Size End", min=0.0, soft_max=60.0)  # pyright: ignore[reportInvalidTypeForm]
    spread: bpy.props.FloatProperty(name="Spread", min=0.0, soft_max=360.0)  # pyright: ignore[reportInvalidTypeForm]
    threshold: bpy.props.FloatProperty(name="Threshold", min=0.0, max=1.0)  # pyright: ignore[reportInvalidTypeForm]
    velocity: bpy.props.FloatProperty(name="Velocity", soft_min=-2.0, soft_max=200.0)  # pyright: ignore[reportInvalidTypeForm]
    xsize: bpy.props.FloatProperty(name="Size X", min=0.0, soft_max=10000.0)  # pyright: ignore[reportInvalidTypeForm]
    ysize: bpy.props.FloatProperty(name="Size Y", min=0.0, soft_max=10000.0)  # pyright: ignore[reportInvalidTypeForm]
    blurlength: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Blur Length",
        default=10.0,
        min=0.0,
        soft_max=10.0,
    )
    lightningdelay: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Lightning Delay",
        description="Lighting delay (seconds)",
        min=0.0,
        soft_max=0.15,
    )
    lightningradius: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Lightning Radius",
        description="Lighting radius (meters)",
        min=0.0,
        soft_max=0.5,
    )
    lightningsubdiv: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Lightning Subdivisions",
        min=0.0,
        soft_max=10.0,
    )
    lightningscale: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Lightning Scale",
        default=1.0,
        min=0.0,
        max=1.0,
    )
    lightningzigzag: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Lightning Zig-Zag",
        min=0.0,
        soft_max=25,
    )
    alphamid: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Alpha Mid",
        default=1.0,
        soft_min=-100.0,
        soft_max=100.0,
    )
    percentstart: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Percent Start",
        default=1.0,
        min=0.0,
        max=1.0,
    )
    percentmid: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Percent Mid",
        default=1.0,
        min=0.0,
        max=1.0,
    )
    percentend: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Percent End",
        default=1.0,
        min=0.0,
        max=1.0,
    )
    sizemid: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="sizeMid",
        default=1.0,
        min=0.0,
        soft_max=255.0,
    )
    sizemid_y: bpy.props.FloatProperty(name="sizeMid_y", min=0.0, soft_max=50.0)  # pyright: ignore[reportInvalidTypeForm]
    randombirthrate: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Random Birthrate",
        default=10.0,
        soft_min=-40.0,
        soft_max=100.0,
    )
    targetsize: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Target Size",
        default=1.0,
        min=0.0,
        soft_max=2.0,
    )
    numcontrolpts: bpy.props.FloatProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Number of Control Points",
        min=0.0,
        max=1.0,
    )
    controlptradius: bpy.props.FloatProperty(
        name="Control Point Radius",
        min=0.0,
        soft_max=2.0,
    )
    controlptdelay: bpy.props.FloatProperty(
        name="Control Point Delay",
        min=0.0,
        soft_max=22.0,
    )
    tangentspread: bpy.props.FloatProperty(
        name="Tangent Spread",
        description="Tangent spread (degrees)",
        min=0.0,
        soft_max=45.0,
    )
    tangentlength: bpy.props.FloatProperty(name="Tangent Length", min=0.0, soft_max=2.0)
    colormid: bpy.props.FloatVectorProperty(
        name="Color Mid",
        subtype="COLOR_GAMMA",
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
    )
    colorend: bpy.props.FloatVectorProperty(
        name="Color End",
        subtype="COLOR_GAMMA",
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
    )
    colorstart: bpy.props.FloatVectorProperty(
        name="Color Start",
        subtype="COLOR_GAMMA",
        default=(1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
    )
    deadspace: bpy.props.FloatProperty(name="Dead Space", min=0.0)
    blastradius: bpy.props.FloatProperty(
        name="Blast Radius",
        description="Blast radius (meters)",
        min=0.0,
    )
    blastlength: bpy.props.FloatProperty(
        name="Blast Length",
        description="Blast length (seconds)",
        min=0.0,
    )
    num_branches: bpy.props.IntProperty(name="Number of Branches")
    controlptsmoothing: bpy.props.FloatProperty(name="Control Point Smoothing")
    xgrid: bpy.props.IntProperty(name="X Grid")
    ygrid: bpy.props.IntProperty(name="Y Grid")
    spawntype: bpy.props.EnumProperty(
        name="Spawn",
        description="Spawn type",
        items=[
            (SpawnType.NORMAL, "Normal", "", 0),
            (SpawnType.TRAIL, "Trail", "", 1),
        ],
        default=SpawnType.NORMAL,
    )
    update: bpy.props.EnumProperty(
        name="Update",
        description="Update type",
        items=[
            (UpdateType.NONE, "", "", 0),
            (UpdateType.FOUNTAIN, "Fountain", "", 1),
            (UpdateType.SINGLE, "Single", "", 2),
            (UpdateType.EXPLOSION, "Explosion", "", 3),
            (UpdateType.LIGHTNING, "Lightning", "", 4),
        ],
        default=UpdateType.NONE,
    )
    emitter_render: bpy.props.EnumProperty(
        name="Render",
        items=[
            (EmitterRenderType.NONE, "", "", 0),
            (EmitterRenderType.NORMAL, "Normal", "", 1),
            (EmitterRenderType.LINKED, "Linked", "", 2),
            (EmitterRenderType.BILLBOARD_TO_LOCAL_Z, "Billboard to local Z", "", 3),
            (EmitterRenderType.BILLBOARD_TO_WORLD_Z, "Billboard to world Z", "", 4),
            (EmitterRenderType.ALIGNED_TO_WORLD_Z, "Aligned to world Z", "", 5),
            (EmitterRenderType.ALIGNED_TO_PARTICLE_DIR, "Aligned to particle dir.", "", 6),
            (EmitterRenderType.MOTION_BLUR, "Motion Blur", "", 7),
        ],
        default=EmitterRenderType.NONE,
    )
    blend: bpy.props.EnumProperty(
        name="Blend",
        items=[
            (BlendType.NONE, "", "", 0),
            (BlendType.NORMAL, "Normal", "", 1),
            (BlendType.PUNCH_THROUGH, "Punch-Through", "", 2),
            (BlendType.LIGHTEN, "Lighten", "", 3),
        ],
        default=BlendType.NONE,
    )
    texture: bpy.props.StringProperty(name="Texture", maxlen=32)
    chunk_name: bpy.props.StringProperty(name="Chunk Name", maxlen=16)
    twosidedtex: bpy.props.BoolProperty(name="Two-Sided Texture")
    loop: bpy.props.BoolProperty(name="Loop")
    renderorder: bpy.props.IntProperty(name="Render Order", min=0)
    frame_blending: bpy.props.BoolProperty(name="Frame Blending")
    depth_texture_name: bpy.props.StringProperty(
        name="Depth Texture Name",
        default=NULL,
        maxlen=32,
    )
    p2p: bpy.props.BoolProperty(name="P2P")
    p2p_type: bpy.props.EnumProperty(
        name="Type",
        items=[
            (P2PType.BEZIER, "Bezier", "Bezier", 0),
            (P2PType.GRAVITY, "Gravity", "Gravity", 1),
        ],
        default=P2PType.BEZIER,
    )
    affected_by_wind: bpy.props.BoolProperty(name="Affected By Wind")
    tinted: bpy.props.BoolProperty(
        name="Tinted",
        description="Texture should be tinted with start, mid, and end color",
    )
    bounce: bpy.props.BoolProperty(name="Bounce")
    random: bpy.props.BoolProperty(name="Random")
    flag13: bpy.props.BoolProperty(name="Flag 13")
    inherit: bpy.props.BoolProperty(name="Inherit")
    inheritvel: bpy.props.BoolProperty(name="Inherit Velocity")
    inherit_local: bpy.props.BoolProperty(name="Inherit Local")
    splat: bpy.props.BoolProperty(name="Splat")
    inherit_part: bpy.props.BoolProperty(name="Inherit Particle")
    depth_texture: bpy.props.BoolProperty(name="Depth Texture")
    emitter_unknown_flags: bpy.props.IntProperty(
        name="Extra Flags",
        description="Preserved emitter flag bits not otherwise exposed",
        default=0,
        min=0,
        max=0xFFFF,
    )
    detonate: bpy.props.FloatProperty(name="Detonate", default=0.0)
    # Path Points
    path_connection_list: bpy.props.CollectionProperty(type=PathConnectionPropertyGroup)
    path_connection_idx: bpy.props.IntProperty()

    # GIT viewport instances (see ops/tools/git_instances.py)
    git_instance_section: bpy.props.EnumProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="GIT List",
        description="Which GIT instance list this empty belongs to (set by GIT import)",
        items=git_instance_section_enum_items(),
        default="NONE",
    )
    git_instance_index: bpy.props.IntProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="GIT Row Index",
        description="Zero-based index in that GIT list; do not duplicate or export may overwrite",
        default=0,
        min=0,
    )
    git_instance_resref: bpy.props.StringProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="GIT ResRef",
        description="Template ResRef at import time (informational)",
        default="",
        maxlen=32,
    )
    git_geometry_role: bpy.props.EnumProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="GIT Geometry",
        description="Trigger/encounter hull mesh or encounter spawn linkage",
        items=git_geometry_role_enum_items(),
        default="NONE",
    )
    git_spawn_index: bpy.props.IntProperty(  # pyright: ignore[reportInvalidTypeForm]
        name="Spawn Index",
        description="Encounter spawn point index within the encounter row",
        default=0,
        min=0,
    )
