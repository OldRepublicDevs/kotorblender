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
from bpy_extras.io_utils import unpack_list

from ...constants import BlendType, EmitterRenderType, ExportOptions, ImportOptions, MeshType, NodeType, NULL, P2PType, SpawnType, UpdateType
from ...diagnostic_log import begin_scene_work_span, end_scene_work_span, sanitize_scene_context
from ...log_config import get_kb_logger

from .base import BaseNode, _log_modelnode


class EmitterNode(BaseNode):
    EMITTER_ATTRS = [
        "deadspace",
        "blastradius",
        "blastlength",
        "num_branches",
        "controlptsmoothing",
        "xgrid",
        "ygrid",
        "spawntype",
        "update",
        "emitter_render",
        "blend",
        "texture",
        "chunk_name",
        "twosidedtex",
        "loop",
        "renderorder",
        "frame_blending",
        "depth_texture_name",
        "p2p",
        "p2p_sel",
        "affected_by_wind",
        "tinted",
        "bounce",
        "random",
        "inherit",
        "inheritvel",
        "inherit_local",
        "splat",
        "inherit_part",
        "depth_texture",
        "alphastart",
        "alphamid",
        "alphaend",
        "birthrate",
        "randombirthrate",
        "bounce_co",
        "combinetime",
        "drag",
        "fps",
        "frameend",
        "framestart",
        "grav",
        "lifeexp",
        "mass",
        "p2p_bezier2",
        "p2p_bezier3",
        "particlerot",
        "randvel",
        "sizestart",
        "sizemid",
        "sizeend",
        "sizestart_y",
        "sizemid_y",
        "sizeend_y",
        "spread",
        "threshold",
        "velocity",
        "xsize",
        "ysize",
        "blurlength",
        "lightningdelay",
        "lightningradius",
        "lightningsubdiv",
        "lightningscale",
        "lightningzigzag",
        "percentstart",
        "percentmid",
        "percentend",
        "targetsize",
        "numcontrolpts",
        "controlptradius",
        "controlptdelay",
        "tangentspread",
        "tangentlength",
        "detonate",
        "colorstart",
        "colormid",
        "colorend",
    ]

    def __init__(self, name: str = "UNNAMED") -> None:
        BaseNode.__init__(self, name)
        self.nodetype: str = NodeType.EMITTER
        self.meshtype: str = MeshType.EMITTER
        # object data
        self.deadspace: float = 0.0
        self.blastradius: float = 0.0
        self.blastlength: float = 0.0
        self.num_branches: int = 0
        self.controlptsmoothing: int = 0
        self.xgrid: int = 0
        self.ygrid: int = 0
        self.spawntype: int = 0
        self.update: str = ""
        self.emitter_render: str = ""
        self.blend: str = ""
        self.texture: str = ""
        self.chunk_name: str = ""
        self.twosidedtex: bool = False
        self.loop: bool = False
        self.renderorder: int = 0
        self.frame_blending: bool = False
        self.depth_texture_name: str = NULL
        # flags
        self.p2p: bool = False
        self.p2p_sel: bool = False
        self.affected_by_wind: bool = False
        self.tinted: bool = False
        self.bounce: bool = False
        self.random: bool = False
        self.inherit: bool = False
        self.inheritvel: bool = False
        self.inherit_local: bool = False
        self.splat: bool = False
        self.inherit_part: bool = False
        self.depth_texture: bool = False
        self.flag13: bool = False
        self.extra_flags: int = 0
        # controllers
        self.alphastart: float = 0.0
        self.alphamid: float = 0.0
        self.alphaend: float = 0.0
        self.birthrate: float = 0.0
        self.randombirthrate: float = 0.0
        self.bounce_co: float = 0.0
        self.combinetime: float = 0.0
        self.drag: float = 0.0
        self.fps: float = 0.0
        self.frameend: float = 0.0
        self.framestart: float = 0.0
        self.grav: float = 0.0
        self.lifeexp: float = 0.0
        self.mass: float = 0.0
        self.p2p_bezier2: float = 0.0
        self.p2p_bezier3: float = 0.0
        self.particlerot: float = 0.0
        self.randvel: float = 0.0
        self.sizestart: float = 0.0
        self.sizemid: float = 0.0
        self.sizeend: float = 0.0
        self.sizestart_y: float = 0.0
        self.sizemid_y: float = 0.0
        self.sizeend_y: float = 0.0
        self.spread: float = 0.0
        self.threshold: float = 0.0
        self.velocity: float = 0.0
        self.xsize: float = 2.0
        self.ysize: float = 2.0
        self.blurlength: float = 0.0
        self.lightningdelay: float = 0.0
        self.lightningradius: float = 0.0
        self.lightningsubdiv: float = 0.0
        self.lightningscale: float = 0.0
        self.lightningzigzag: float = 0.0
        self.percentstart: float = 0.0
        self.percentmid: float = 0.0
        self.percentend: float = 0.0
        self.targetsize: float = 0.0
        self.numcontrolpts: float = 0.0
        self.controlptradius: float = 0.0
        self.controlptdelay: float = 0.0
        self.tangentspread: float = 0.0
        self.tangentlength: float = 0.0
        self.detonate: float = 0.0
        self.colorstart: tuple[float, float, float] = (1.0, 1.0, 1.0)
        self.colormid: tuple[float, float, float] = (1.0, 1.0, 1.0)
        self.colorend: tuple[float, float, float] = (1.0, 1.0, 1.0)

    def add_to_collection(
        self, collection: bpy.types.Collection, options: ImportOptions
    ) -> bpy.types.Object:
        log = get_kb_logger("scene.modelnode.emitter")
        span = begin_scene_work_span(
            log, "scene.modelnode.EmitterNode.add_to_collection", sanitize_scene_context(self.name)
        )
        err = False
        try:
            mesh = self.create_mesh(self.name)
            obj = bpy.data.objects.new(self.name, mesh)

            self.set_object_data(obj, options)
            collection.objects.link(obj)
            _log_modelnode("EmitterNode.add_to_collection", self)
            return obj
        except BaseException:
            err = True
            raise
        finally:
            end_scene_work_span(span, error=err)

    def create_mesh(self, name: str) -> bpy.types.Mesh:
        verts = [
            ((self.xsize / 2) / 100.0, (self.ysize / 2) / 100.0, 0.0),
            ((self.xsize / 2) / 100.0, (-self.ysize / 2) / 100.0, 0.0),
            ((-self.xsize / 2) / 100.0, (-self.ysize / 2) / 100.0, 0.0),
            ((-self.xsize / 2) / 100.0, (self.ysize / 2) / 100.0, 0.0),
        ]
        indices = [(0, 1, 2), (0, 2, 3)]
        # Create the mesh itself
        mesh = bpy.data.meshes.new(name)
        mesh.vertices.add(len(verts))
        mesh.vertices.foreach_set("co", unpack_list(verts))
        num_faces = len(indices)
        mesh.loops.add(3 * num_faces)
        mesh.loops.foreach_set("vertex_index", unpack_list(indices))
        mesh.polygons.add(num_faces)
        mesh.polygons.foreach_set("loop_start", range(0, 3 * num_faces, 3))
        mesh.polygons.foreach_set("loop_total", (3,) * num_faces)
        mesh.update()
        return mesh

    def set_object_data(self, obj: bpy.types.Object, options: ImportOptions) -> None:
        BaseNode.set_object_data(self, obj, options)

        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError(f"Object [{obj.name}] has no kb attribute")
        kb.meshtype = self.meshtype

        for attrname in self.EMITTER_ATTRS:
            value = getattr(self, attrname)
            if attrname == "spawntype":
                if value == 0:
                    value = SpawnType.NORMAL
                elif value == 1:
                    value = SpawnType.TRAIL
            elif attrname == "update":
                normalized = value.title() if isinstance(value, str) else str(value)
                if normalized not in [
                    UpdateType.FOUNTAIN,
                    UpdateType.SINGLE,
                    UpdateType.EXPLOSION,
                    UpdateType.LIGHTNING,
                ]:
                    value = UpdateType.NONE
                else:
                    value = normalized
            elif attrname == "emitter_render":
                if value not in [
                    EmitterRenderType.NORMAL,
                    EmitterRenderType.LINKED,
                    EmitterRenderType.BILLBOARD_TO_LOCAL_Z,
                    EmitterRenderType.BILLBOARD_TO_WORLD_Z,
                    EmitterRenderType.ALIGNED_TO_WORLD_Z,
                    EmitterRenderType.ALIGNED_TO_PARTICLE_DIR,
                    EmitterRenderType.MOTION_BLUR,
                ]:
                    value = EmitterRenderType.NONE
            elif attrname == "blend":
                if isinstance(value, str) and value.lower() == "punchthrough":
                    value = BlendType.PUNCH_THROUGH
                else:
                    normalized = value.title() if isinstance(value, str) else str(value)
                    if normalized not in [
                        BlendType.LIGHTEN,
                        BlendType.NORMAL,
                        BlendType.PUNCH_THROUGH,
                    ]:
                        value = BlendType.NONE
                    else:
                        value = normalized
            elif attrname == "p2p_sel":
                if self.p2p_sel:
                    kb.p2p_type = P2PType.BEZIER
                else:
                    kb.p2p_type = P2PType.GRAVITY
                continue
            setattr(kb, attrname, value)
        kb.flag13 = self.flag13
        kb.emitter_unknown_flags = self.extra_flags

    def load_object_data(
        self, obj: bpy.types.Object, eval_obj: bpy.types.Object, options: ExportOptions
    ) -> None:
        BaseNode.load_object_data(self, obj, eval_obj, options)

        kb = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError(f"Object [{obj.name}] has no kb attribute")
        for attrname in self.EMITTER_ATTRS:
            value = getattr(kb, attrname, None)

            if attrname == "spawntype":
                if value == SpawnType.NORMAL:
                    value = 0
                elif value == SpawnType.TRAIL:
                    value = 1
                else:
                    continue
            elif attrname == "update":
                if value not in [
                    UpdateType.FOUNTAIN,
                    UpdateType.SINGLE,
                    UpdateType.EXPLOSION,
                    UpdateType.LIGHTNING,
                ]:
                    continue
            elif attrname == "emitter_render":
                if value not in [
                    EmitterRenderType.NORMAL,
                    EmitterRenderType.LINKED,
                    EmitterRenderType.BILLBOARD_TO_LOCAL_Z,
                    EmitterRenderType.BILLBOARD_TO_WORLD_Z,
                    EmitterRenderType.ALIGNED_TO_WORLD_Z,
                    EmitterRenderType.ALIGNED_TO_PARTICLE_DIR,
                    EmitterRenderType.MOTION_BLUR,
                ]:
                    continue
            elif attrname == "blend":
                if value == BlendType.PUNCH_THROUGH:
                    value = "PunchThrough"
                elif value not in [BlendType.LIGHTEN, BlendType.NORMAL]:
                    continue
            elif attrname == "p2p_sel":
                self.p2p_sel = kb.p2p_type == P2PType.BEZIER
                continue

            setattr(self, attrname, value)
        self.flag13 = kb.flag13
        self.extra_flags = kb.emitter_unknown_flags
