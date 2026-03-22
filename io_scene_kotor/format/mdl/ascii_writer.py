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

import os
import re
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

import bpy
from mathutils import Quaternion

from ...constants import NULL, AsciiMdlKeyword, BlendType, EmitterRenderType, SpawnType, UpdateType
from ...diagnostic_log import begin_format_file_span, end_format_file_span
from ...log_config import get_kb_logger
from ...scene.model import Model
from ...scene.animation import Animation
from ...scene.animnode import AnimationNode
from ...scene.modelnode.base import BaseNode
from ...scene.modelnode.reference import ReferenceNode
from ...scene.modelnode.trimesh import TrimeshNode
from ...scene.modelnode.danglymesh import DanglymeshNode
from ...scene.modelnode.skinmesh import SkinmeshNode
from ...scene.modelnode.emitter import EmitterNode
from ...scene.modelnode.light import LightNode
from ...scene.modelnode.aabb import AabbNode
from ...utils import is_not_null

if TYPE_CHECKING:
    pass


def _enum_value_for_ascii(enum_cls: type[Enum], raw: object) -> str | None:
    """String to emit in ASCII MDL for a str/int enum field, or None if unset."""
    if raw is None:
        return None
    if isinstance(raw, enum_cls):
        val = raw.value
        return str(val) if val not in (None, "") else None
    if isinstance(raw, str):
        s = raw.strip()
        return s if s else None
    try:
        return str(enum_cls(raw).value)
    except (ValueError, TypeError):
        for m in enum_cls:
            if m == raw or m.value == raw:
                return str(m.value)
    return None


class AsciiMdlWriter:
    """Writer for ASCII MDL format files (.mdl.ascii)."""

    def __init__(self, path: str, model: Model):
        self.path: str = path
        self.model: Model = model
        self.lines: list[str] = []
        self.name_map: dict[str, str] = {}

    def save(self) -> None:
        """Write the model to an ASCII MDL file."""
        log = get_kb_logger("format")
        span = begin_format_file_span(log, "format.mdl.ascii_writer.AsciiMdlWriter.save", self.path)
        err = False
        try:
            self.lines = []

            # Build name map for .001 suffix handling
            self._build_name_map()

            # Write header
            self._write_header()

            # Write geometry
            self._write_geometry()

            # Write animations
            self._write_animations()

            # Write footer
            self._write_footer()

            # Write to file
            with open(self.path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.lines))
                if self.lines:
                    f.write("\n")
        except BaseException:
            err = True
            raise
        finally:
            end_format_file_span(span, error=err)

    def _build_name_map(self) -> None:
        """Build a map of .001 suffix names to base names."""
        all_nodes: list[BaseNode] = []

        def collect_nodes(node: BaseNode) -> None:
            all_nodes.append(node)
            for child in node.children:
                collect_nodes(child)

        if self.model.root_node:
            collect_nodes(self.model.root_node)

        for node in all_nodes:
            match = re.match(r"^(.+)\.\d{3}$", node.name)
            if match:
                base_name = match.group(1)
                # Check if base name exists
                base_exists = any(
                    n.name.lower() == base_name.lower() for n in all_nodes if n != node
                )
                # Check if already mapped
                already_mapped = base_name in self.name_map.values()

                if not base_exists and not already_mapped:
                    self.name_map[node.name] = base_name

    def _write_header(self) -> None:
        """Write the model header section."""
        current_time: datetime = datetime.now()
        blend_file_name: str = os.path.basename(bpy.data.filepath) if bpy.data.filepath else "unknown"

        self.lines.append(f"# Exported from blender at {current_time.strftime('%A, %Y-%m-%d')}")
        self.lines.append(f"filedependancy {blend_file_name}")

        model_name: str = self.name_map.get(self.model.name, self.model.name)
        self.lines.append(f"{AsciiMdlKeyword.NEWMODEL.value} {model_name}")

        supermodel: str = self.model.supermodel if is_not_null(self.model.supermodel) else NULL
        self.lines.append(f"{AsciiMdlKeyword.SETSUPERMODEL.value} {model_name} {supermodel}")

        classification_str = getattr(
            self.model.classification, "value", self.model.classification
        )
        self.lines.append(
            f"{AsciiMdlKeyword.CLASSIFICATION.value} {classification_str}"
        )
        self.lines.append(
            f"{AsciiMdlKeyword.CLASSIFICATION_UNK1.value} {self.model.classification_unk1}"
        )
        self.lines.append(
            f"{AsciiMdlKeyword.IGNOREFOG.value} {1 if not self.model.affected_by_fog else 0}"
        )
        self.lines.append(
            f"{AsciiMdlKeyword.SETANIMATIONSCALE.value} {round(self.model.animscale, 7)}"
        )

        # Layout position for AABB nodes
        if hasattr(self.model, "lytposition") and self.model.lytposition:
            lyt_pos = self.model.lytposition
            self.lines.append(
                f"  {AsciiMdlKeyword.LAYOUTPOSITION.value} {lyt_pos[0]:.7g} {lyt_pos[1]:.7g} {lyt_pos[2]:.7g}"
            )

    def _write_geometry(self) -> None:
        """Write the geometry section."""
        model_name: str = self.name_map.get(self.model.name, self.model.name)
        self.lines.append(f"{AsciiMdlKeyword.BEGINMODELGEOM.value} {model_name}")

        if self.model.root_node is not None:
            self._write_node(self.model.root_node, indent=0)

        self.lines.append(f"{AsciiMdlKeyword.ENDMODELGEOM.value} {model_name}")

    def _write_node(self, node: BaseNode, indent: int = 0) -> None:
        """Write a node and its children recursively."""
        indent_str = "  " * indent

        # Get node name (with remapping)
        node_name = self.name_map.get(node.name, node.name)

        # Write node declaration (nodetype may be enum or string from Blender)
        node_type_val = node.nodetype.value
        node_type = (
            node_type_val.lower()
            if isinstance(node_type_val, str)
            else str(node_type_val).lower()
        )
        self.lines.append(f"{indent_str}{AsciiMdlKeyword.NODE.value} {node_type} {node_name}")

        # Write parent
        if node.parent is not None:
            parent_name = self.name_map.get(node.parent.name, node.parent.name)
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.PARENT.value} {parent_name}")
        else:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.PARENT.value} {NULL}")

        # Write position
        pos = node.position
        self.lines.append(
            f"{indent_str}  {AsciiMdlKeyword.POSITION.value} {pos[0]:.7g} {pos[1]:.7g} {pos[2]:.7g}"
        )

        # Write orientation (convert quaternion to axis-angle)
        quat = Quaternion(node.orientation)
        axis, angle = quat.to_axis_angle()
        self.lines.append(
            f"{indent_str}  {AsciiMdlKeyword.ORIENTATION.value} {axis.x:.7g} {axis.y:.7g} {axis.z:.7g} {angle:.7g}"
        )

        # Write scale
        if node.scale != 1.0:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.SCALE.value} {node.scale:.3g}")

        # Write node-type specific properties
        if isinstance(node, TrimeshNode):
            self._write_trimesh_properties(node, indent)
        elif isinstance(node, DanglymeshNode):
            self._write_danglymesh_properties(node, indent)
        elif isinstance(node, SkinmeshNode):
            self._write_skinmesh_properties(node, indent)
        elif isinstance(node, EmitterNode):
            self._write_emitter_properties(node, indent)
        elif isinstance(node, LightNode):
            self._write_light_properties(node, indent)
        elif isinstance(node, AabbNode):
            self._write_aabb_properties(node, indent)
        elif isinstance(node, ReferenceNode):
            self._write_reference_properties(node, indent)

        # Write endnode
        self.lines.append(f"{indent_str}{AsciiMdlKeyword.ENDNODE.value}")

        # Write children
        for child in node.children:
            self._write_node(child, indent + 1)

    def _write_trimesh_properties(self, node: TrimeshNode, indent: int) -> None:
        """Write trimesh-specific properties."""
        indent_str = "  " * indent

        # Basic flags
        if node.render != 1:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.RENDER.value} {node.render}")
        if node.shadow != 1:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.SHADOW.value} {node.shadow}")
        if node.lightmapped != 0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.LIGHTMAPPED.value} {node.lightmapped}"
            )
        if node.beaming != 0:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.BEAMING.value} {node.beaming}")
        if node.tangentspace != 0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.TANGENTSPACE.value} {node.tangentspace}"
            )
        if node.rotatetexture != 0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.ROTATETEXTURE.value} {node.rotatetexture}"
            )
        if node.background_geometry != 0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.BACKGROUND_GEOMETRY.value} {node.background_geometry}"
            )
        if node.dirt_enabled != 0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.DIRT_ENABLED.value} {node.dirt_enabled}"
            )
        if node.dirt_texture != 1:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.DIRT_TEXTURE.value} {node.dirt_texture}"
            )
        if node.dirt_worldspace != 1:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.DIRT_WORLDSPACE.value} {node.dirt_worldspace}"
            )
        if node.hologram_donotdraw != 0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.HOLOGRAM_DONOTDRAW.value} {node.hologram_donotdraw}"
            )
        if node.animateuv != 0:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.ANIMATEUV.value} {node.animateuv}")
        if node.uvdirectionx != 1.0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.UVDIRECTIONX.value} {node.uvdirectionx:.7g}"
            )
        if node.uvdirectiony != 1.0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.UVDIRECTIONY.value} {node.uvdirectiony:.7g}"
            )
        if node.uvjitter != 0.0:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.UVJITTER.value} {node.uvjitter:.7g}")
        if node.uvjitterspeed != 0.0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.UVJITTERSPEED.value} {node.uvjitterspeed:.7g}"
            )
        if node.alpha != 1.0:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.ALPHA.value} {node.alpha:.7g}")
        if node.transparencyhint != 0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.TRANSPARENCYHINT.value} {node.transparencyhint}"
            )

        # Colors
        if node.selfillumcolor != (0.0, 0.0, 0.0):
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.SELFILLUMCOLOR.value} "
                f"{node.selfillumcolor[0]:.7g} {node.selfillumcolor[1]:.7g} {node.selfillumcolor[2]:.7g}"
            )
        if node.ambient != (0.0, 0.0, 0.0):
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.AMBIENT.value} "
                f"{node.ambient[0]:.7g} {node.ambient[1]:.7g} {node.ambient[2]:.7g}"
            )
        if node.diffuse != (0.0, 0.0, 0.0):
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.DIFFUSE.value} "
                f"{node.diffuse[0]:.7g} {node.diffuse[1]:.7g} {node.diffuse[2]:.7g}"
            )

        # Textures
        bitmap = node.bitmap if is_not_null(node.bitmap) else NULL
        self.lines.append(f"{indent_str}  {AsciiMdlKeyword.BITMAP.value} {bitmap}")
        bitmap2 = node.bitmap2 if is_not_null(node.bitmap2) else NULL
        self.lines.append(f"{indent_str}  {AsciiMdlKeyword.BITMAP2.value} {bitmap2}")

        # Geometry data
        if node.verts:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.VERTS.value} {len(node.verts)}")
            for vert in node.verts:
                self.lines.append(f"{indent_str}    {vert[0]:.7g} {vert[1]:.7g} {vert[2]:.7g}")

        if node.facelist and node.facelist.vertices:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.FACES.value} {len(node.facelist.vertices)}"
            )
            for i, face_verts in enumerate(node.facelist.vertices):
                line = f"{indent_str}    {face_verts[0]} {face_verts[1]} {face_verts[2]}"
                # Add smooth group
                if node.facelist.normals and i < len(node.facelist.normals):
                    smooth_group = (
                        node.facelist.normals[i] if isinstance(node.facelist.normals[i], int) else 0
                    )
                    line += f" {smooth_group}"
                else:
                    line += " 0"
                # Add UV indices
                if node.facelist.uv and i < len(node.facelist.uv):
                    uv_face = node.facelist.uv[i]
                    line += f" {uv_face[0]} {uv_face[1]} {uv_face[2]}"
                else:
                    line += f" {face_verts[0]} {face_verts[1]} {face_verts[2]}"
                # Add material ID
                if node.facelist.materials and i < len(node.facelist.materials):
                    line += f" {node.facelist.materials[i]}"
                else:
                    line += " 0"
                self.lines.append(line)

        if node.uv1:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.TVERTS.value} {len(node.uv1)}")
            for uv in node.uv1:
                self.lines.append(f"{indent_str}    {uv[0]:.7g} {uv[1]:.7g}")

        if node.uv2:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.TVERTS1.value} {len(node.uv2)}")
            for uv in node.uv2:
                self.lines.append(f"{indent_str}    {uv[0]:.7g} {uv[1]:.7g} 0")

    def _write_danglymesh_properties(self, node: DanglymeshNode, indent: int) -> None:
        """Write danglymesh-specific properties."""
        indent_str = "  " * indent

        # Write trimesh properties first
        self._write_trimesh_properties(node, indent)

        # Danglymesh-specific
        if node.period != 1.0:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.PERIOD.value} {node.period:.7g}")
        if node.tightness != 1.0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.TIGHTNESS.value} {node.tightness:.7g}"
            )
        if node.displacement != 1.0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.DISPLACEMENT.value} {node.displacement:.7g}"
            )

        if node.constraints:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.CONSTRAINTS.value} {len(node.constraints)}"
            )
            for constraint in node.constraints:
                self.lines.append(f"{indent_str}    {int(constraint)}")

    def _write_skinmesh_properties(self, node: SkinmeshNode, indent: int) -> None:
        """Write skinmesh-specific properties."""
        indent_str = "  " * indent

        # Write trimesh properties first
        self._write_trimesh_properties(node, indent)

        # Skinmesh-specific (weights)
        if node.weights:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.WEIGHTS.value} {len(node.weights)}")
            for vert_weights in node.weights:
                weight_str = " ".join(
                    f"{bone_name} {weight:.7g}" for bone_name, weight in vert_weights
                )
                self.lines.append(f"{indent_str}    {weight_str}")

    def _write_emitter_properties(self, node: EmitterNode, indent: int) -> None:
        """Write emitter-specific properties."""
        indent_str = "  " * indent

        # Basic properties
        if node.deadspace != 0.0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.DEADSPACE.value} {node.deadspace:.7g}"
            )
        if node.blastradius != 0.0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.BLASTRADIUS.value} {node.blastradius:.7g}"
            )
        if node.blastlength != 0.0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.BLASTLENGTH.value} {node.blastlength:.7g}"
            )
        if node.num_branches != 0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.NUMBRANCHES.value} {node.num_branches}"
            )
        if node.controlptsmoothing != 0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.CONTROLPTMOOTHING.value} {node.controlptsmoothing}"
            )
        if node.xgrid != 0:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.XGRID.value} {node.xgrid}")
        if node.ygrid != 0:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.YGRID.value} {node.ygrid}")

        # Enums (support int from binary or string from ASCII)
        spawntype_str = _enum_value_for_ascii(SpawnType, node.spawntype)
        if spawntype_str:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.SPAWNTYPE.value} {spawntype_str}"
            )
        update_str = _enum_value_for_ascii(UpdateType, node.update)
        if update_str:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.UPDATE.value} {update_str}")
        emitter_render_str = _enum_value_for_ascii(EmitterRenderType, node.emitter_render)
        if emitter_render_str:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.EMITTER_RENDER.value} {emitter_render_str}"
            )
        blend_str = _enum_value_for_ascii(BlendType, node.blend)
        if blend_str:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.BLEND.value} {blend_str}")

        # Strings
        if node.texture:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.TEXTURE.value} {node.texture}")
        if node.chunk_name:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.CHUNKNAME.value} {node.chunk_name}")
        if node.depth_texture_name and is_not_null(node.depth_texture_name):
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.DEPTH_TEXTURE_NAME.value} {node.depth_texture_name}"
            )

        # Flags
        if node.twosidedtex:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.TWOSIDEDTEX.value} 1")
        if node.loop:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.LOOP.value} 1")
        if node.frame_blending:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.FRAME_BLENDING.value} 1")
        if node.renderorder != 0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.RENDERORDER.value} {node.renderorder}"
            )

        if node.p2p:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.P2P.value} 1")
        if node.p2p_sel:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.P2P_SEL.value} 1")
        if node.affected_by_wind:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.AFFECTEDBYWIND.value} 1")
        if node.tinted:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.TINTED.value} 1")
        if node.bounce:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.BOUNCE.value} 1")
        if node.random:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.RANDOM.value} 1")
        if node.inherit:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.INHERIT.value} 1")
        if node.inheritvel:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.INHERITVEL.value} 1")
        if node.inherit_local:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.INHERIT_LOCAL.value} 1")
        if node.splat:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.SPLAT.value} 1")
        if node.inherit_part:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.INHERIT_PART.value} 1")
        if node.depth_texture:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.DEPTH_TEXTURE.value} 1")

        # Controllers (write if non-zero/default)
        if node.alphastart != 0.0:
            self.lines.append(f"{indent_str}  alphastart {node.alphastart:.7g}")
        if node.alphamid != 0.0:
            self.lines.append(f"{indent_str}  alphamid {node.alphamid:.7g}")
        if node.alphaend != 0.0:
            self.lines.append(f"{indent_str}  alphaend {node.alphaend:.7g}")
        if node.birthrate != 0.0:
            self.lines.append(f"{indent_str}  birthrate {node.birthrate:.7g}")
        if node.randombirthrate != 0.0:
            self.lines.append(f"{indent_str}  m_frandombirthrate {node.randombirthrate:.7g}")
        if node.bounce_co != 0.0:
            self.lines.append(f"{indent_str}  bounce_co {node.bounce_co:.7g}")
        if node.combinetime != 0.0:
            self.lines.append(f"{indent_str}  combinetime {node.combinetime:.7g}")
        if node.drag != 0.0:
            self.lines.append(f"{indent_str}  drag {node.drag:.7g}")
        if node.fps != 0.0:
            self.lines.append(f"{indent_str}  fps {node.fps:.7g}")
        if node.frameend != 0.0:
            self.lines.append(f"{indent_str}  frameend {node.frameend:.7g}")
        if node.framestart != 0.0:
            self.lines.append(f"{indent_str}  framestart {node.framestart:.7g}")
        if node.grav != 0.0:
            self.lines.append(f"{indent_str}  grav {node.grav:.7g}")
        if node.lifeexp != 0.0:
            self.lines.append(f"{indent_str}  lifeexp {node.lifeexp:.7g}")
        if node.mass != 0.0:
            self.lines.append(f"{indent_str}  mass {node.mass:.7g}")
        if node.p2p_bezier2 != 0.0:
            self.lines.append(f"{indent_str}  p2p_bezier2 {node.p2p_bezier2:.7g}")
        if node.p2p_bezier3 != 0.0:
            self.lines.append(f"{indent_str}  p2p_bezier3 {node.p2p_bezier3:.7g}")
        if node.particlerot != 0.0:
            self.lines.append(f"{indent_str}  particlerot {node.particlerot:.7g}")
        if node.randvel != 0.0:
            self.lines.append(f"{indent_str}  randvel {node.randvel:.7g}")
        if node.sizestart != 0.0:
            self.lines.append(f"{indent_str}  sizestart {node.sizestart:.7g}")
        if node.sizemid != 0.0:
            self.lines.append(f"{indent_str}  sizemid {node.sizemid:.7g}")
        if node.sizeend != 0.0:
            self.lines.append(f"{indent_str}  sizeend {node.sizeend:.7g}")
        if node.sizestart_y != 0.0:
            self.lines.append(f"{indent_str}  sizestart_y {node.sizestart_y:.7g}")
        if node.sizemid_y != 0.0:
            self.lines.append(f"{indent_str}  sizemid_y {node.sizemid_y:.7g}")
        if node.sizeend_y != 0.0:
            self.lines.append(f"{indent_str}  sizeend_y {node.sizeend_y:.7g}")
        if node.spread != 0.0:
            self.lines.append(f"{indent_str}  spread {node.spread:.7g}")
        if node.threshold != 0.0:
            self.lines.append(f"{indent_str}  threshold {node.threshold:.7g}")
        if node.velocity != 0.0:
            self.lines.append(f"{indent_str}  velocity {node.velocity:.7g}")
        if node.xsize != 2.0:
            self.lines.append(f"{indent_str}  xsize {node.xsize:.7g}")
        if node.ysize != 2.0:
            self.lines.append(f"{indent_str}  ysize {node.ysize:.7g}")
        if node.blurlength != 0.0:
            self.lines.append(f"{indent_str}  blurlength {node.blurlength:.7g}")
        if node.lightningdelay != 0.0:
            self.lines.append(f"{indent_str}  lightningdelay {node.lightningdelay:.7g}")
        if node.lightningradius != 0.0:
            self.lines.append(f"{indent_str}  lightningradius {node.lightningradius:.7g}")
        if node.lightningsubdiv != 0.0:
            self.lines.append(f"{indent_str}  lightningsubdiv {node.lightningsubdiv:.7g}")
        if node.lightningscale != 0.0:
            self.lines.append(f"{indent_str}  lightningscale {node.lightningscale:.7g}")
        if node.lightningzigzag != 0.0:
            self.lines.append(f"{indent_str}  lightningzigzag {node.lightningzigzag:.7g}")
        if node.percentstart != 0.0:
            self.lines.append(f"{indent_str}  percentstart {node.percentstart:.7g}")
        if node.percentmid != 0.0:
            self.lines.append(f"{indent_str}  percentmid {node.percentmid:.7g}")
        if node.percentend != 0.0:
            self.lines.append(f"{indent_str}  percentend {node.percentend:.7g}")
        if node.targetsize != 0.0:
            self.lines.append(f"{indent_str}  targetsize {node.targetsize:.7g}")
        if node.numcontrolpts != 0.0:
            self.lines.append(f"{indent_str}  numcontrolpts {node.numcontrolpts:.7g}")
        if node.controlptradius != 0.0:
            self.lines.append(f"{indent_str}  controlptradius {node.controlptradius:.7g}")
        if node.controlptdelay != 0.0:
            self.lines.append(f"{indent_str}  controlptdelay {node.controlptdelay:.7g}")
        if node.tangentspread != 0.0:
            self.lines.append(f"{indent_str}  tangentspread {node.tangentspread:.7g}")
        if node.tangentlength != 0.0:
            self.lines.append(f"{indent_str}  tangentlength {node.tangentlength:.7g}")
        if node.colorstart and node.colorstart != (0.0, 0.0, 0.0):
            self.lines.append(
                f"{indent_str}  colorstart {node.colorstart[0]:.7g} {node.colorstart[1]:.7g} {node.colorstart[2]:.7g}"
            )
        if node.colormid and node.colormid != (0.0, 0.0, 0.0):
            self.lines.append(
                f"{indent_str}  colormid {node.colormid[0]:.7g} {node.colormid[1]:.7g} {node.colormid[2]:.7g}"
            )
        if node.colorend and node.colorend != (0.0, 0.0, 0.0):
            self.lines.append(
                f"{indent_str}  colorend {node.colorend[0]:.7g} {node.colorend[1]:.7g} {node.colorend[2]:.7g}"
            )
        if node.detonate != 0.0:
            self.lines.append(f"{indent_str}  detonate {node.detonate:.7g}")

    def _write_light_properties(self, node: LightNode, indent: int) -> None:
        """Write light-specific properties."""
        indent_str = "  " * indent

        if node.radius != 5.0:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.RADIUS.value} {node.radius:.7g}")
        if node.multiplier != 1:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.MULTIPLIER.value} {node.multiplier:.7g}"
            )
        if node.color != (0.0, 0.0, 0.0):
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.COLOR.value} "
                f"{node.color[0]:.7g} {node.color[1]:.7g} {node.color[2]:.7g}"
            )
        if node.ambientonly != 1:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.AMBIENTONLY.value} {node.ambientonly}"
            )
        if node.dynamictype != 0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.NDYNAMICTYPE.value} {node.dynamictype}"
            )
        if node.affectdynamic != 1:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.AFFECTDYNAMIC.value} {node.affectdynamic}"
            )
        if node.lightpriority != 5:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.LIGHTPRIORITY.value} {node.lightpriority}"
            )
        if node.fadinglight != 1:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.FADINGLIGHT.value} {node.fadinglight}"
            )
        if node.lensflares != 0:
            self.lines.append(f"{indent_str}  {AsciiMdlKeyword.LENSFLARES.value} {node.lensflares}")
        if node.flareradius != 1.0:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.FLARERADIUS.value} {node.flareradius:.7g}"
            )
        if node.shadowradius != 0.0:
            self.lines.append(
                f"{indent_str}  shadowradius {node.shadowradius:.7g}"
            )
        if node.verticaldisplacement != 0.0:
            self.lines.append(
                f"{indent_str}  verticaldisplacement {node.verticaldisplacement:.7g}"
            )

        # Flare data
        if node.flare_list and node.flare_list.textures:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.TEXTURENAMES.value} {len(node.flare_list.textures)}"
            )
            for texture in node.flare_list.textures:
                self.lines.append(f"{indent_str}    {texture}")

            if node.flare_list.positions:
                self.lines.append(
                    f"{indent_str}  {AsciiMdlKeyword.FLAREPOSITIONS.value} {len(node.flare_list.positions)}"
                )
                for pos in node.flare_list.positions:
                    self.lines.append(f"{indent_str}    {pos:.7g}")

            if node.flare_list.sizes:
                self.lines.append(
                    f"{indent_str}  {AsciiMdlKeyword.FLARESIZES.value} {len(node.flare_list.sizes)}"
                )
                for size in node.flare_list.sizes:
                    self.lines.append(f"{indent_str}    {size:.7g}")

            if node.flare_list.colorshifts:
                self.lines.append(
                    f"{indent_str}  {AsciiMdlKeyword.FLARECOLORSHIFTS.value} {len(node.flare_list.colorshifts)}"
                )
                for color in node.flare_list.colorshifts:
                    self.lines.append(
                        f"{indent_str}    {color[0]:.7g} {color[1]:.7g} {color[2]:.7g}"
                    )

    def _write_aabb_properties(self, node: AabbNode, indent: int) -> None:
        """Write AABB-specific properties."""
        indent_str = "  " * indent

        # Write trimesh properties first
        self._write_trimesh_properties(node, indent)

        # AABB-specific (room links)
        if node.roomlinks:
            self.lines.append(
                f"{indent_str}  {AsciiMdlKeyword.ROOMLINKS.value} {len(node.roomlinks)}"
            )
            for edge_idx, room_id in sorted(node.roomlinks.items()):
                self.lines.append(f"{indent_str}    {edge_idx} {room_id}")

    def _write_reference_properties(self, node: ReferenceNode, indent: int) -> None:
        """Write reference node-specific properties."""
        indent_str = "  " * indent

        refmodel = node.refmodel if is_not_null(node.refmodel) else NULL
        self.lines.append(f"{indent_str}  {AsciiMdlKeyword.REFMODEL.value} {refmodel}")
        self.lines.append(
            f"{indent_str}  {AsciiMdlKeyword.REATTACHABLE.value} {1 if node.reattachable == 1 else 0}"
        )

    def _write_animations(self) -> None:
        """Write the animation section."""
        if not self.model.animations:
            return

        self.lines.append("")
        self.lines.append("# ANIM ASCII")

        for anim in self.model.animations:
            self._write_animation(anim)

    def _write_animation(self, anim: Animation) -> None:
        """Write a single animation."""
        model_name = self.name_map.get(self.model.name, self.model.name)
        self.lines.append(f"{AsciiMdlKeyword.NEWANIM.value} {anim.name} {model_name}")
        self.lines.append(f"  {AsciiMdlKeyword.LENGTH.value} {round(anim.length, 5)}")
        self.lines.append(f"  {AsciiMdlKeyword.TRANS_TIME.value} {round(anim.transtime, 3)}")

        animroot = anim.animroot if is_not_null(anim.animroot) else "undefined"
        self.lines.append(f"  {AsciiMdlKeyword.ANIMROOT.value} {animroot}")

        # Write events
        for event_time, event_name in anim.events:
            self.lines.append(
                f"  {AsciiMdlKeyword.EVENT.value} {round(event_time, 3)} {event_name}"
            )

        # Write animation nodes
        if anim.root_node:
            self._write_animation_node(anim.root_node, indent=1)

        self.lines.append(f"{AsciiMdlKeyword.DONEANIM.value} {anim.name} {model_name}")
        self.lines.append("")

    def _write_animation_node(self, anim_node: AnimationNode, indent: int) -> None:
        """Write an animation node and its children recursively."""
        indent_str = "  " * indent

        node_name = self.name_map.get(anim_node.name, anim_node.name)
        self.lines.append(f"{indent_str}{AsciiMdlKeyword.NODE.value} {node_name}")

        # Write keyframes for each controller
        # Format: keyframes[label] = [[time, value1, value2, ...], ...]
        for label, keyframes in anim_node.keyframes.items():
            if not keyframes:
                continue

            # Write controller header: label num_keys
            self.lines.append(f"{indent_str}  {label} {len(keyframes)}")

            # Write keyframe data
            for keyframe in keyframes:
                if not keyframe or len(keyframe) < 2:
                    continue

                time = keyframe[0]
                values = keyframe[1:]

                # Format based on number of values
                if len(values) == 1:
                    # Single value (scale, alpha, radius, etc.)
                    self.lines.append(f"{indent_str}    {time:.7g} {values[0]:.7g}")
                elif len(values) == 3:
                    # Position or color (3 values)
                    line = f"{indent_str}    {time:.7g} {values[0]:.7g} {values[1]:.7g} {values[2]:.7g}"
                    # Check for bezier (9 values total: 3 position + 3 in_tangent + 3 out_tangent)
                    if len(keyframe) >= 10:
                        in_tangent = keyframe[4:7]
                        out_tangent = keyframe[7:10]
                        line += f" {in_tangent[0]:.7g} {in_tangent[1]:.7g} {in_tangent[2]:.7g}"
                        line += f" {out_tangent[0]:.7g} {out_tangent[1]:.7g} {out_tangent[2]:.7g}"
                    self.lines.append(line)
                elif len(values) == 4:
                    # Orientation (quaternion: 4 values)
                    self.lines.append(
                        f"{indent_str}    {time:.7g} {values[0]:.7g} {values[1]:.7g} {values[2]:.7g} {values[3]:.7g}"
                    )
                else:
                    # Unknown format, write as-is
                    value_str = " ".join(f"{v:.7g}" for v in values)
                    self.lines.append(f"{indent_str}    {time:.7g} {value_str}")

        # Write children
        for child in anim_node.children:
            self._write_animation_node(child, indent + 1)

        self.lines.append(f"{indent_str}endnode")

    def _write_footer(self) -> None:
        """Write the model footer."""
        model_name = self.name_map.get(self.model.name, self.model.name)
        self.lines.append(f"{AsciiMdlKeyword.DONEMODEL.value} {model_name}")
        self.lines.append("")
