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

from enum import Enum, IntEnum
from typing import Any

PACKAGE_NAME = __package__

# ``bpy.context.preferences.addons`` keys: Blender 4.x extension id vs legacy add-on package name.
ADDON_PREFERENCE_MODULE_KEYS: tuple[str, ...] = (
    "bl_ext.user_default.io_scene_kotor",
    PACKAGE_NAME,
)

NULL = "NULL"

ANIM_REST_POSE_OFFSET = 5
ANIM_PADDING = 60
ANIM_FPS = 30

WALKMESH_MATERIALS: list[list[Any]] = [
    ["wok_NotDefined", (0.400, 0.400, 0.400), False],
    ["wok_Dirt", (0.610, 0.235, 0.050), True],
    ["wok_Obscuring", (0.100, 0.100, 0.100), False],
    ["wok_Grass", (0.000, 0.600, 0.000), True],
    ["wok_Stone", (0.162, 0.216, 0.279), True],
    ["wok_Wood", (0.258, 0.059, 0.007), True],
    ["wok_Water", (0.000, 0.000, 1.000), True],
    ["wok_Nonwalk", (1.000, 0.000, 0.000), False],
    ["wok_Transparent", (1.000, 1.000, 1.000), False],
    ["wok_Carpet", (1.000, 0.000, 1.000), True],
    ["wok_Metal", (0.434, 0.552, 0.730), True],
    ["wok_Puddles", (0.509, 0.474, 0.147), True],
    ["wok_Swamp", (0.216, 0.216, 0.000), True],
    ["wok_Mud", (0.091, 0.147, 0.028), True],
    ["wok_Leaves", (1.000, 0.262, 0.000), True],
    ["wok_Lava", (0.300, 0.000, 0.000), False],
    ["wok_BottomlessPit", (0.000, 0.000, 0.000), True],
    ["wok_DeepWater", (0.000, 0.000, 0.216), False],
    ["wok_Door", (0.000, 0.000, 0.000), True],
    ["wok_Snow", (0.800, 0.800, 0.800), False],
    ["wok_Sand", (1.000, 1.000, 0.000), True],
    ["wok_BareBones", (0.500, 0.500, 0.100), True],
    ["wok_StoneBridge", (0.081, 0.108, 0.139), True],
]
NAME_TO_WALKMESH_MATERIAL = {mat[0]: mat for mat in WALKMESH_MATERIALS}
NON_WALKABLE = [mat_idx for mat_idx, mat in enumerate(WALKMESH_MATERIALS) if not mat[2]]

UV_MAP_MAIN = "UVMap"
UV_MAP_LIGHTMAP = "UVMap_lm"

# Feature flag for PyKotor format readers (default False during migration).
# When True and PyKotor is available, MDL/TPC/GFF load/save may use PyKotor.
USE_PYKOTOR_READERS: bool = False


class Classification(str, Enum):
    OTHER = "OTHER"
    TILE = "TILE"
    CHARACTER = "CHARACTER"
    DOOR = "DOOR"
    EFFECT = "EFFECT"
    GUI = "GUI"
    LIGHTSABER = "LIGHTSABER"
    PLACEABLE = "PLACEABLE"
    FLYER = "FLYER"


class RootType(str, Enum):
    MODEL = "MODEL"
    WALKMESH = "WALKMESH"


class NodeType(str, Enum):
    DUMMY = "DUMMY"
    REFERENCE = "REFERENCE"
    TRIMESH = "TRIMESH"
    DANGLYMESH = "DANGLYMESH"
    SKIN = "SKIN"
    EMITTER = "EMITTER"
    LIGHT = "LIGHT"
    AABB = "AABB"
    LIGHTSABER = "LIGHTSABER"
    UNDEFINED = "UNDEFINED"


class DummyType(str, Enum):
    NONE = "NONE"
    MDLROOT = "MDLROOT"
    PWKROOT = "PWKROOT"
    DWKROOT = "DWKROOT"
    PTHROOT = "PTHROOT"
    REFERENCE = "REFERENCE"
    PATHPOINT = "PATHPOINT"
    USE1 = "USE1"
    USE2 = "USE2"


class MeshType(str, Enum):
    TRIMESH = "TRIMESH"
    DANGLYMESH = "DANGLYMESH"
    LIGHTSABER = "LIGHTSABER"
    SKIN = "SKIN"
    AABB = "AABB"
    EMITTER = "EMITTER"


class WalkmeshType(str, Enum):
    WOK = "WOK"
    PWK = "PWK"
    DWK = "DWK"


class ImportOptions:
    def __init__(self):
        self.import_geometry: bool = True
        self.import_animations: bool = True
        self.import_walkmeshes: bool = True
        self.build_materials: bool = True
        self.build_armature: bool = False
        self.texture_search_paths: list[str] = []
        self.lightmap_search_paths: list[str] = []


class ExportOptions:
    def __init__(self):
        self.export_for_tsl: bool = False
        self.export_for_xbox: bool = False
        self.export_animations: bool = True
        self.export_walkmeshes: bool = True
        self.compress_quaternions: bool = False


class Compression(IntEnum):
    DISABLED = 0
    ENABLED = 1


class SpawnType(str, Enum):
    NORMAL = "Normal"
    TRAIL = "Trail"


class UpdateType(str, Enum):
    NONE = "NONE"
    FOUNTAIN = "Fountain"
    SINGLE = "Single"
    EXPLOSION = "Explosion"
    LIGHTNING = "Lightning"


class EmitterRenderType(str, Enum):
    NONE = "NONE"
    NORMAL = "Normal"
    LINKED = "Linked"
    BILLBOARD_TO_LOCAL_Z = "Billboard_to_Local_Z"
    BILLBOARD_TO_WORLD_Z = "Billboard_to_World_Z"
    ALIGNED_TO_WORLD_Z = "Aligned_to_World_Z"
    ALIGNED_TO_PARTICLE_DIR = "Aligned_to_Particle_Dir"
    MOTION_BLUR = "Motion_Blur"


class BlendType(str, Enum):
    NONE = "NONE"
    NORMAL = "Normal"
    PUNCH_THROUGH = "Punch-Through"
    LIGHTEN = "Lighten"


class P2PType(str, Enum):
    BEZIER = "Bezier"
    GRAVITY = "Gravity"


class GameType(str, Enum):
    KOTOR1 = "KOTOR1"
    KOTOR2 = "KOTOR2"
    CUSTOM = "CUSTOM"


class GitInstanceSection(str, Enum):
    """GIT list names on ``pykotor.resource.generics.git.GIT`` (viewport empty linkage)."""

    NONE = "NONE"
    CREATURES = "creatures"
    DOORS = "doors"
    ENCOUNTERS = "encounters"
    STORES = "stores"
    PLACEABLES = "placeables"
    SOUNDS = "sounds"
    TRIGGERS = "triggers"
    WAYPOINTS = "waypoints"
    CAMERAS = "cameras"


class GitGeometryRole(str, Enum):
    """Linked GIT mesh/empty beyond the root instance marker."""

    NONE = "NONE"
    TRIGGER_HULL = "TRIGGER_HULL"
    ENCOUNTER_HULL = "ENCOUNTER_HULL"
    ENCOUNTER_SPAWN = "ENCOUNTER_SPAWN"


def git_geometry_role_enum_items() -> list[tuple[str, str, str, int]]:
    return [
        (GitGeometryRole.NONE.value, "None", "Not GIT geometry helper", 0),
        (GitGeometryRole.TRIGGER_HULL.value, "Trigger hull", "GIT trigger polygon (mesh)", 1),
        (GitGeometryRole.ENCOUNTER_HULL.value, "Encounter hull", "GIT encounter polygon (mesh)", 2),
        (GitGeometryRole.ENCOUNTER_SPAWN.value, "Encounter spawn", "GIT encounter spawn point (empty)", 3),
    ]


def git_instance_section_enum_items() -> list[tuple[str, str, str, int]]:
    """RNA enum items for :class:`GitInstanceSection` (Blender ``EnumProperty``)."""

    return [
        (GitInstanceSection.NONE.value, "None", "Object is not linked to a GIT instance row", 0),
        (GitInstanceSection.CREATURES.value, "Creatures", "GIT Creature List", 1),
        (GitInstanceSection.DOORS.value, "Doors", "GIT Door List", 2),
        (GitInstanceSection.ENCOUNTERS.value, "Encounters", "GIT Encounter List", 3),
        (GitInstanceSection.STORES.value, "Stores", "GIT StoreList", 4),
        (GitInstanceSection.PLACEABLES.value, "Placeables", "GIT Placeable List", 5),
        (GitInstanceSection.SOUNDS.value, "Sounds", "GIT SoundList", 6),
        (GitInstanceSection.TRIGGERS.value, "Triggers", "GIT TriggerList", 7),
        (GitInstanceSection.WAYPOINTS.value, "Waypoints", "GIT WaypointList", 8),
        (GitInstanceSection.CAMERAS.value, "Cameras", "GIT CameraList", 9),
    ]


class ResourceTab(str, Enum):
    CORE = "CORE"
    MODULES = "MODULES"
    OVERRIDE = "OVERRIDE"
    TEXTURES = "TEXTURES"
    SAVES = "SAVES"
    BIF = "BIF"


class ResourceStorage(str, Enum):
    """How a module browser / search entry is resolved on disk."""

    LOOSE = "LOOSE"
    ERF = "ERF"
    BIF = "BIF"


class Direction(str, Enum):
    UP = "UP"
    DOWN = "DOWN"


class LogReasonCode(str, Enum):
    """Stable ``reason_code`` strings for package logging (grep-friendly)."""

    OK = "OK"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    MISSING_FILE = "MISSING_FILE"
    PARSE_ERROR = "PARSE_ERROR"
    IO_ERROR = "IO_ERROR"
    CONFIG_ERROR = "CONFIG_ERROR"


class PropertyName(str, Enum):
    """Constants for property names used in UI panels and operators."""

    # Model properties
    CLASSIFICATION = "classification"
    SUPERMODEL = "supermodel"
    ANIMSCALE = "animscale"
    ANIMROOT = "animroot"
    AFFECTED_BY_FOG = "affected_by_fog"

    # Model node properties
    DUMMYTYPE = "dummytype"
    MESHTYPE = "meshtype"
    NODE_NUMBER = "node_number"

    # Reference node properties
    REFMODEL = "refmodel"
    REATTACHABLE = "reattachable"

    # Mesh properties
    BITMAP = "bitmap"
    BITMAP2 = "bitmap2"
    DIFFUSE = "diffuse"
    AMBIENT = "ambient"
    SELFILLUMCOLOR = "selfillumcolor"
    ALPHA = "alpha"
    TRANSPARENCYHINT = "transparencyhint"
    RENDER = "render"
    SHADOW = "shadow"
    LIGHTMAPPED = "lightmapped"
    TANGENTSPACE = "tangentspace"
    BACKGROUND_GEOMETRY = "background_geometry"
    BEAMING = "beaming"
    ROTATETEXTURE = "rotatetexture"
    ANIMATEUV = "animateuv"
    UVDIRECTIONX = "uvdirectionx"
    UVDIRECTIONY = "uvdirectiony"
    UVJITTER = "uvjitter"
    UVJITTERSPEED = "uvjitterspeed"
    HOLOGRAM_DONOTDRAW = "hologram_donotdraw"
    DIRT_ENABLED = "dirt_enabled"
    DIRT_TEXTURE = "dirt_texture"
    DIRT_WORLDSPACE = "dirt_worldspace"
    CONSTRAINTS = "constraints"
    PERIOD = "period"
    TIGHTNESS = "tightness"
    DISPLACEMENT = "displacement"
    LYTPOSITION = "lytposition"

    # Light properties
    LIGHTPRIORITY = "lightpriority"
    RADIUS = "radius"
    MULTIPLIER = "multiplier"
    DYNAMICTYPE = "dynamictype"
    AMBIENTONLY = "ambientonly"
    AFFECTDYNAMIC = "affectdynamic"
    FADINGLIGHT = "fadinglight"
    LENSFLARES = "lensflares"
    FLARERADIUS = "flareradius"
    NEGATIVELIGHT = "negativelight"

    # Emitter properties
    SPAWNTYPE = "spawntype"
    UPDATE = "update"
    EMITTER_RENDER = "emitter_render"
    BLEND = "blend"
    TEXTURE = "texture"
    DEPTH_TEXTURE_NAME = "depth_texture_name"
    CHUNK_NAME = "chunk_name"
    NUM_BRANCHES = "num_branches"
    RENDERORDER = "renderorder"
    THRESHOLD = "threshold"
    COMBINETIME = "combinetime"
    DEADSPACE = "deadspace"
    TWOSIDEDTEX = "twosidedtex"
    DEPTH_TEXTURE = "depth_texture"
    P2P = "p2p"
    INHERIT = "inherit"
    INHERIT_LOCAL = "inherit_local"
    INHERITVEL = "inheritvel"
    INHERIT_PART = "inherit_part"
    PERCENTSTART = "percentstart"
    PERCENTMID = "percentmid"
    PERCENTEND = "percentend"
    COLORSTART = "colorstart"
    COLORMID = "colormid"
    COLOREND = "colorend"
    ALPHASTART = "alphastart"
    ALPHAMID = "alphamid"
    ALPHAEND = "alphaend"
    SIZESTART = "sizestart"
    SIZEMID = "sizemid"
    SIZEEND = "sizeend"
    SIZESTART_Y = "sizestart_y"
    SIZEMID_Y = "sizemid_y"
    SIZEEND_Y = "sizeend_y"
    BIRTHRATE = "birthrate"
    RANDOMBIRTHRATE = "randombirthrate"
    LIFEEXP = "lifeexp"
    MASS = "mass"
    SPREAD = "spread"
    PARTICLEROT = "particlerot"
    VELOCITY = "velocity"
    RANDVEL = "randvel"
    BLURLENGTH = "blurlength"
    TARGETSIZE = "targetsize"
    TANGENTSPREAD = "tangentspread"
    TANGENTLENGTH = "tangentlength"
    BLASTRADIUS = "blastradius"
    BLASTLENGTH = "blastlength"
    BOUNCE_CO = "bounce_co"
    BOUNCE = "bounce"
    LOOP = "loop"
    SPLAT = "splat"
    AFFECTED_BY_WIND = "affected_by_wind"
    TINTED = "tinted"
    XSIZE = "xsize"
    YSIZE = "ysize"
    XGRID = "xgrid"
    YGRID = "ygrid"
    FRAMESTART = "framestart"
    FRAMEEND = "frameend"
    FPS = "fps"
    FRAME_BLENDING = "frame_blending"
    RANDOM = "random"
    LIGHTNINGDELAY = "lightningdelay"
    LIGHTNINGRADIUS = "lightningradius"
    LIGHTNINGSUBDIV = "lightningsubdiv"
    LIGHTNINGSCALE = "lightningscale"
    LIGHTNINGZIGZAG = "lightningzigzag"
    P2P_TYPE = "p2p_type"
    P2P_BEZIER2 = "p2p_bezier2"
    P2P_BEZIER3 = "p2p_bezier3"
    GRAV = "grav"
    DRAG = "drag"
    NUMCONTROLPTS = "numcontrolpts"
    CONTROLPTRADIUS = "controlptradius"
    CONTROLPTSMOOTHING = "controlptsmoothing"
    CONTROLPTDELAY = "controlptdelay"

    # Scene properties
    GAME_TYPE = "game_type"
    GAME_INSTALLATION_PATH = "game_installation_path"
    MODULE_LIST_IDX = "module_list_idx"
    ACTIVE_GIT_PATH = "active_git_path"
    RESOURCE_TAB = "resource_tab"
    RESOURCE_LIST_IDX = "resource_list_idx"
    EXTRACT_TPC_DECOMPILE = "extract_tpc_decompile"
    EXTRACT_TPC_TXI = "extract_tpc_txi"
    EXTRACT_MDL_DECOMPILE = "extract_mdl_decompile"
    EXTRACT_MDL_TEXTURES = "extract_mdl_textures"

    # GIT viewport link (object.kb)
    GIT_INSTANCE_SECTION = "git_instance_section"
    GIT_INSTANCE_INDEX = "git_instance_index"
    GIT_INSTANCE_RESREF = "git_instance_resref"
    GIT_GEOMETRY_ROLE = "git_geometry_role"
    GIT_SPAWN_INDEX = "git_spawn_index"

    KOTOR_WALKMESH_OVERLAY = "kotor_walkmesh_overlay"


class NodeName(str, Enum):
    DIFFUSE_TEX = "diffuse_tex"
    BUMPMAP_TEX = "bumpmap_tex"
    LIGHTMAP_TEX = "lightmap_tex"
    WHITE = "white"
    NORMAL_MAP = "normal_map"
    MUL_DIFFUSE_LIGHTMAP = "mul_diffuse_lightmap"
    MUL_DIFFUSE_SELFILLUM = "mul_diffuse_selfillum"
    DIFFUSE_BSDF = "diffuse_bsdf"
    DIFF_LM_EMISSION = "diff_lm_emission"
    SELFILLUM_EMISSION = "selfillum_emission"
    GLOSSY_BSDF = "glossy_bsdf"
    ADD_DIFFUSE_EMISSION = "add_diffuse_emission"
    MIX_MATTE_GLOSSY = "mix_matte_glossy"
    OBJECT_ALPHA = "object_alpha"
    MUL_DIFFUSE_OBJECT_ALPHA = "mul_diffuse_object_alpha"
    TRANSPARENT_BSDF = "transparent_bsdf"
    MIX_OPAQUE_TRANSPARENT = "mix_opaque_transparent"
    ADD_OPAQUE_TRANSPARENT = "add_opaque_transparent"


class WalkmeshNodeName(str, Enum):
    COLOR = "color"
    OPACITY = "opacity"


# ASCII MDL format keywords
class AsciiMdlKeyword(str, Enum):
    """Constants for ASCII MDL format keywords."""

    # Model-level keywords
    NEWMODEL = "newmodel"
    SETSUPERMODEL = "setsupermodel"
    CLASSIFICATION = "classification"
    CLASSIFICATION_UNK1 = "classification_unk1"
    IGNOREFOG = "ignorefog"
    COMPRESS_QUATERNIONS = "compress_quaternions"
    HEADLINK = "headlink"
    SETANIMATIONSCALE = "setanimationscale"
    LAYOUTPOSITION = "layoutposition"
    BEGINMODELGEOM = "beginmodelgeom"
    ENDMODELGEOM = "endmodelgeom"
    DONEMODEL = "donemodel"

    # Node keywords
    NODE = "node"
    ENDNODE = "endnode"
    PARENT = "parent"
    POSITION = "position"
    ORIENTATION = "orientation"
    SCALE = "scale"
    WIRECOLOR = "wirecolor"

    # Trimesh keywords
    RENDER = "render"
    SHADOW = "shadow"
    LIGHTMAPPED = "lightmapped"
    BEAMING = "beaming"
    TANGENTSPACE = "tangentspace"
    ROTATETEXTURE = "rotatetexture"
    INHERITCOLOR = "inheritcolor"
    BACKGROUND_GEOMETRY = "m_bIsBackgroundGeometry"
    DIRT_ENABLED = "dirt_enabled"
    DIRT_TEXTURE = "dirt_texture"
    DIRT_WORLDSPACE = "dirt_worldspace"
    HOLOGRAM_DONOTDRAW = "hologram_donotdraw"
    ANIMATEUV = "animateuv"
    UVDIRECTIONX = "uvdirectionx"
    UVDIRECTIONY = "uvdirectiony"
    UVJITTER = "uvjitter"
    UVJITTERSPEED = "uvjitterspeed"
    ALPHA = "alpha"
    TRANSPARENCYHINT = "transparencyhint"
    SELFILLUMCOLOR = "selfillumcolor"
    AMBIENT = "ambient"
    DIFFUSE = "diffuse"
    BITMAP = "bitmap"
    BITMAP2 = "bitmap2"
    CENTER = "center"
    VERTS = "verts"
    FACES = "faces"
    TVERTS = "tverts"
    TVERTS1 = "tverts1"
    TEXINDICES1 = "texindices1"
    ROOMLINKS = "roomlinks"
    COLORS = "colors"
    COLORINDICES = "colorindices"

    # Danglymesh keywords
    PERIOD = "period"
    TIGHTNESS = "tightness"
    DISPLACEMENT = "displacement"
    CONSTRAINTS = "constraints"

    # Skinmesh keywords
    WEIGHTS = "weights"

    # Reference node keywords
    REFMODEL = "refmodel"
    REATTACHABLE = "reattachable"

    # Light node keywords
    RADIUS = "radius"
    MULTIPLIER = "multiplier"
    COLOR = "color"
    AMBIENTONLY = "ambientonly"
    NDYNAMICTYPE = "ndynamictype"
    ISDYNAMIC = "isdynamic"
    AFFECTDYNAMIC = "affectdynamic"
    NEGATIVELIGHT = "negativelight"
    LIGHTPRIORITY = "lightpriority"
    FADINGLIGHT = "fadinglight"
    LENSFLARES = "lensflares"
    FLARERADIUS = "flareradius"
    TEXTURENAMES = "texturenames"
    FLAREPOSITIONS = "flarepositions"
    FLARESIZES = "flaresizes"
    FLARECOLORSHIFTS = "flarecolorshifts"

    # AABB keywords
    AABB = "aabb"

    # Animation keywords
    NEWANIM = "newanim"
    DONEANIM = "doneanim"
    LENGTH = "length"
    TRANS_TIME = "transtime"
    ANIMROOT = "animroot"
    EVENT = "event"
    EVENTLIST = "eventlist"

    # Emitter keywords (subset - full list in emitter parsing)
    DEADSPACE = "deadspace"
    BLASTRADIUS = "blastradius"
    BLASTLENGTH = "blastlength"
    NUMBRANCHES = "numBranches"
    CONTROLPTMOOTHING = "controlptsmoothing"
    XGRID = "xgrid"
    YGRID = "ygrid"
    SPAWNTYPE = "spawntype"
    UPDATE = "update"
    EMITTER_RENDER = "emitter_render"
    BLEND = "blend"
    TEXTURE = "texture"
    CHUNKNAME = "chunkName"
    TWOSIDEDTEX = "twosidedtex"
    LOOP = "loop"
    RENDERORDER = "renderorder"
    FRAME_BLENDING = "m_bFrameBlending"
    DEPTH_TEXTURE_NAME = "m_sDepthTextureName"
    P2P = "p2p"
    P2P_SEL = "p2p_sel"
    AFFECTEDBYWIND = "affectedByWind"
    TINTED = "m_isTinted"
    BOUNCE = "bounce"
    RANDOM = "random"
    INHERIT = "inherit"
    INHERITVEL = "inheritvel"
    INHERIT_LOCAL = "inherit_local"
    SPLAT = "splat"
    INHERIT_PART = "inherit_part"
    DEPTH_TEXTURE = "depth_texture"
