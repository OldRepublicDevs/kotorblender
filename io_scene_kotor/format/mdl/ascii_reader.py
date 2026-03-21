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
from typing import TYPE_CHECKING

from mathutils import Quaternion, Vector

from ...constants import NULL, AsciiMdlKeyword, BlendType, Classification, EmitterRenderType, NodeType, SpawnType, UpdateType
from ...scene.animation import Animation
from ...scene.animnode import AnimationNode
from ...scene.model import Model
from ...scene.modelnode.aabb import AabbNode
from ...scene.modelnode.base import BaseNode
from ...scene.modelnode.danglymesh import DanglymeshNode
from ...scene.modelnode.dummy import DummyNode
from ...scene.modelnode.emitter import EmitterNode
from ...scene.modelnode.light import FlareList, LightNode
from ...scene.modelnode.lightsaber import LightsaberNode
from ...scene.modelnode.reference import ReferenceNode
from ...scene.modelnode.skinmesh import SkinmeshNode
from ...scene.modelnode.trimesh import FaceList, TrimeshNode
from ...utils import logger

if TYPE_CHECKING:
    pass

# Emitter animation keyframe controller keywords (must match loop in _parse_animation_node_tree)
_EMITTER_KEYFRAME_CONTROLLER_KEYWORDS: frozenset[str] = frozenset(
    {
        "alphastart",
        "alphamid",
        "alphaend",
        "birthrate",
        "m_frandombirthrate",
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
        "colorstart",
        "colormid",
        "colorend",
        "detonate",
    }
)


def _parse_ascii_enum(enum_cls: type, token: str, default: str | int):  # noqa: ANN401
    """Parse enum from ASCII: try by name (e.g. FOUNTAIN) then by value (e.g. Fountain)."""
    try:
        return enum_cls[token.upper()].value  # pyright: ignore[reportIndexIssue]
    except (KeyError, AttributeError):
        try:
            return enum_cls(token).value
        except (ValueError, TypeError):
            return default


class AsciiMdlReader:
    """Reader for ASCII MDL format files (.mdl.ascii)."""

    def __init__(self, path: str):
        self.path: str = path
        self.model: Model | None = None
        self.lines: list[str] = []
        self.current_line: int = 0

    def load(self) -> Model:
        """Load an ASCII MDL file and return a Model object."""
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"ASCII MDL file not found: {self.path}")

        with open(self.path, "r", encoding="utf-8") as f:
            content = f.read()

        self.model = Model()
        self.lines = content.splitlines()
        self.current_line = 0

        # Find sections
        geom_start = self._find_line_containing(AsciiMdlKeyword.NODE.value + " ")
        anim_start = self._find_line_containing(AsciiMdlKeyword.NEWANIM.value + " ")
        geom_end = self._find_line_containing(AsciiMdlKeyword.ENDMODELGEOM.value + " ")

        if geom_start < 0:
            raise ValueError("Unable to find geometry section (no 'node' keyword found)")

        if anim_start > 0 and geom_start > anim_start:
            raise ValueError("Animations found before geometry section")

        # Parse header
        self._parse_header(geom_start)

        # Parse geometry
        self._parse_geometry(geom_start, geom_end if geom_end > 0 else len(self.lines))

        # Parse animations
        if anim_start > 0:
            self._parse_animations(anim_start)

        assert self.model is not None
        return self.model

    def _find_line_containing(self, text: str) -> int:
        """Find the first line index containing the given text. Returns -1 if not found."""
        for i, line in enumerate(self.lines):
            if text in line:
                return i
        return -1

    def _parse_header(self, geom_start: int) -> None:
        """Parse the model header section (before geometry)."""
        assert self.model is not None

        for i in range(geom_start):
            line = self.lines[i].strip()
            if not line or line.startswith("#"):
                continue

            tokens = line.split()
            if not tokens:
                continue

            keyword = tokens[0].lower()

            if keyword == AsciiMdlKeyword.NEWMODEL.value:
                if len(tokens) >= 2:
                    self.model.name = tokens[1]
            elif keyword == AsciiMdlKeyword.SETSUPERMODEL.value:
                if len(tokens) >= 3:
                    self.model.supermodel = tokens[2]
            elif keyword == AsciiMdlKeyword.CLASSIFICATION.value:
                if len(tokens) >= 2:
                    try:
                        # Map ASCII classification to enum
                        class_str = tokens[1].upper()
                        self.model.classification = Classification[class_str]
                    except KeyError:
                        logger().warning(f"Unknown classification: {tokens[1]}, using OTHER")
                        self.model.classification = Classification.OTHER
            elif keyword == AsciiMdlKeyword.CLASSIFICATION_UNK1.value:
                if len(tokens) >= 2:
                    try:
                        self.model.classification_unk1 = int(tokens[1])
                    except ValueError:
                        logger().warning(f"Invalid classification_unk1: {tokens[1]}")
            elif keyword == AsciiMdlKeyword.IGNOREFOG.value:
                if len(tokens) >= 2:
                    self.model.affected_by_fog = tokens[1] == "0"
            elif keyword == AsciiMdlKeyword.SETANIMATIONSCALE.value:
                if len(tokens) >= 2:
                    try:
                        self.model.animscale = float(tokens[1])
                    except ValueError:
                        logger().warning(f"Invalid animscale: {tokens[1]}")
            elif keyword == AsciiMdlKeyword.LAYOUTPOSITION.value:
                if len(tokens) >= 4:
                    try:
                        # Store for AABB nodes
                        self.model.lytposition = (
                            float(tokens[1]),
                            float(tokens[2]),
                            float(tokens[3]),
                        )
                    except ValueError:
                        logger().warning(f"Invalid layoutposition: {tokens[1:4]}")

    def _parse_geometry(self, start_line: int, end_line: int) -> None:
        """Parse the geometry section (nodes)."""
        assert self.model is not None

        # First pass: parse all nodes
        nodes: list[BaseNode] = []
        node_parent_map: dict[BaseNode, str | None] = {}

        i = start_line
        while i < end_line:
            line = self.lines[i].strip()
            if not line:
                i += 1
                continue

            tokens = line.split()
            if not tokens:
                i += 1
                continue

            keyword = tokens[0].lower()

            if keyword == AsciiMdlKeyword.NODE.value:
                # Parse a node block
                node_end = self._find_node_end(i)
                if node_end < 0:
                    raise ValueError(f"Node starting at line {i + 1} has no matching endnode")

                node = self._parse_node(i, node_end)
                if node:
                    # Store parent name for later resolution
                    parent_name = getattr(node, "_parent_name", None)
                    node_parent_map[node] = parent_name
                    nodes.append(node)

                i = node_end + 1
            else:
                i += 1

        # Second pass: build hierarchy
        for node in nodes:
            parent_name = node_parent_map.get(node)

            if parent_name is None or parent_name.upper() == NULL:
                # Root node
                if self.model.root_node is None:
                    if isinstance(node, DummyNode):
                        self.model.root_node = node
                    else:
                        raise ValueError("First node must be a dummy without a parent")
                else:
                    logger().warning(f"Multiple root nodes found, ignoring '{node.name}'")
            else:
                # Find parent node
                parent = None
                for candidate in nodes:
                    if candidate.name == parent_name:
                        parent = candidate
                        break

                if parent:
                    parent.children.append(node)
                    node.parent = parent
                else:
                    logger().warning(f"Parent '{parent_name}' not found for node '{node.name}'")

    def _find_node_end(self, start_line: int) -> int:
        """Find the matching 'endnode' for a node starting at start_line."""
        depth = 1
        i = start_line + 1
        while i < len(self.lines):
            line = self.lines[i].strip()
            tokens = line.split()
            if tokens:
                keyword = tokens[0].lower()
                if keyword == AsciiMdlKeyword.NODE.value:
                    depth += 1
                elif keyword == AsciiMdlKeyword.ENDNODE.value:
                    depth -= 1
                    if depth == 0:
                        return i
            i += 1
        return -1

    def _parse_node(self, start_line: int, end_line: int) -> BaseNode | None:
        """Parse a single node block."""
        # Get node type and name from first line
        first_line = self.lines[start_line].strip()
        tokens = first_line.split()
        if len(tokens) < 3:
            raise ValueError(f"Invalid node declaration at line {start_line + 1}: {first_line}")

        node_type_str = tokens[1].lower()
        node_name = tokens[2]

        # Map node type string to class
        node_type_map: dict[str, type[BaseNode]] = {
            NodeType.DUMMY.value.lower(): DummyNode,
            NodeType.REFERENCE.value.lower(): ReferenceNode,
            NodeType.TRIMESH.value.lower(): TrimeshNode,
            NodeType.DANGLYMESH.value.lower(): DanglymeshNode,
            NodeType.SKIN.value.lower(): SkinmeshNode,
            NodeType.EMITTER.value.lower(): EmitterNode,
            NodeType.LIGHT.value.lower(): LightNode,
            NodeType.AABB.value.lower(): AabbNode,
            NodeType.LIGHTSABER.value.lower(): LightsaberNode,
        }

        node_class = node_type_map.get(node_type_str)
        if not node_class:
            raise ValueError(f"Unknown node type: {node_type_str}")

        node = node_class()
        node.name = node_name

        # Parse node properties
        i = start_line + 1
        while i < end_line:
            line = self.lines[i].strip()
            if not line:
                i += 1
                continue

            tokens = line.split()
            if not tokens:
                i += 1
                continue

            keyword = tokens[0].lower()
            i = self._parse_node_property(node, keyword, tokens, i, end_line)
            i += 1

        return node

    def _parse_node_property(self, node: BaseNode, keyword: str, tokens: list[str], line_num: int, end_line: int) -> int:
        """Parse a single node property. Returns the new line number after parsing."""
        try:
            if keyword == AsciiMdlKeyword.PARENT.value:
                if len(tokens) >= 2:
                    parent_name = tokens[1]
                    if parent_name.upper() != NULL:
                        setattr(node, "_parent_name", parent_name)
            elif keyword == AsciiMdlKeyword.POSITION.value:
                if len(tokens) >= 4:
                    node.position = (
                        float(tokens[1]),
                        float(tokens[2]),
                        float(tokens[3]),
                    )
            elif keyword == AsciiMdlKeyword.ORIENTATION.value:
                if len(tokens) >= 5:
                    # Axis-angle format: x y z angle
                    axis = Vector((float(tokens[1]), float(tokens[2]), float(tokens[3])))
                    angle = float(tokens[4])
                    quat = Quaternion(axis, angle)
                    # Convert to tuple (w, x, y, z)
                    node.orientation = (quat.w, quat.x, quat.y, quat.z)
            elif keyword == AsciiMdlKeyword.SCALE.value:
                if len(tokens) >= 2:
                    scale_val = float(tokens[1])
                    node.scale = scale_val

            # Node-type specific parsing
            if isinstance(node, TrimeshNode):
                return self._parse_trimesh_property(node, keyword, tokens, line_num, end_line)
            elif isinstance(node, DanglymeshNode):
                return self._parse_danglymesh_property(node, keyword, tokens, line_num, end_line)
            elif isinstance(node, SkinmeshNode):
                return self._parse_skinmesh_property(node, keyword, tokens, line_num, end_line)
            elif isinstance(node, EmitterNode):
                return self._parse_emitter_property(node, keyword, tokens, line_num, end_line)
            elif isinstance(node, LightNode):
                return self._parse_light_property(node, keyword, tokens, line_num, end_line)
            elif isinstance(node, AabbNode):
                return self._parse_aabb_property(node, keyword, tokens, line_num, end_line)
            elif isinstance(node, ReferenceNode):
                return self._parse_reference_property(node, keyword, tokens, line_num, end_line)

        except (ValueError, IndexError) as e:
            logger().warning(f"Error parsing property '{keyword}' at line {line_num + 1}: {e}")

        return line_num

    def _parse_trimesh_property(self, node: TrimeshNode, keyword: str, tokens: list[str], line_num: int, end_line: int) -> int:
        """Parse trimesh-specific properties."""
        if keyword == AsciiMdlKeyword.BITMAP.value:
            if len(tokens) >= 2:
                node.bitmap = tokens[1] if tokens[1].upper() != NULL else NULL
        elif keyword == AsciiMdlKeyword.BITMAP2.value:
            if len(tokens) >= 2:
                node.bitmap2 = tokens[1] if tokens[1].upper() != NULL else NULL
        elif keyword == AsciiMdlKeyword.ALPHA.value:
            if len(tokens) >= 2:
                node.alpha = float(tokens[1])
        elif keyword == AsciiMdlKeyword.RENDER.value:
            if len(tokens) >= 2:
                node.render = 1 if tokens[1] == "1" else 0
        elif keyword == AsciiMdlKeyword.SHADOW.value:
            if len(tokens) >= 2:
                node.shadow = 1 if tokens[1] == "1" else 0
        elif keyword == AsciiMdlKeyword.LIGHTMAPPED.value:
            if len(tokens) >= 2:
                node.lightmapped = 1 if tokens[1] == "1" else 0
        elif keyword == AsciiMdlKeyword.BEAMING.value:
            if len(tokens) >= 2:
                node.beaming = 1 if tokens[1] == "1" else 0
        elif keyword == AsciiMdlKeyword.TANGENTSPACE.value:
            if len(tokens) >= 2:
                node.tangentspace = 1 if tokens[1] == "1" else 0
        elif keyword == AsciiMdlKeyword.ROTATETEXTURE.value:
            if len(tokens) >= 2:
                node.rotatetexture = 1 if tokens[1] == "1" else 0
        elif keyword == AsciiMdlKeyword.BACKGROUND_GEOMETRY.value:
            if len(tokens) >= 2:
                node.background_geometry = 1 if tokens[1] == "1" else 0
        elif keyword == AsciiMdlKeyword.DIRT_ENABLED.value:
            if len(tokens) >= 2:
                node.dirt_enabled = 1 if tokens[1] == "1" else 0
        elif keyword == AsciiMdlKeyword.DIRT_TEXTURE.value:
            if len(tokens) >= 2:
                node.dirt_texture = int(tokens[1])
        elif keyword == AsciiMdlKeyword.DIRT_WORLDSPACE.value:
            if len(tokens) >= 2:
                node.dirt_worldspace = 1 if tokens[1] == "1" else 0
        elif keyword == AsciiMdlKeyword.HOLOGRAM_DONOTDRAW.value:
            if len(tokens) >= 2:
                node.hologram_donotdraw = 1 if tokens[1] == "1" else 0
        elif keyword == AsciiMdlKeyword.ANIMATEUV.value:
            if len(tokens) >= 2:
                node.animateuv = 1 if tokens[1] == "1" else 0
        elif keyword == AsciiMdlKeyword.UVDIRECTIONX.value:
            if len(tokens) >= 2:
                node.uvdirectionx = float(tokens[1])
        elif keyword == AsciiMdlKeyword.UVDIRECTIONY.value:
            if len(tokens) >= 2:
                node.uvdirectiony = float(tokens[1])
        elif keyword == AsciiMdlKeyword.UVJITTER.value:
            if len(tokens) >= 2:
                node.uvjitter = float(tokens[1])
        elif keyword == AsciiMdlKeyword.UVJITTERSPEED.value:
            if len(tokens) >= 2:
                node.uvjitterspeed = float(tokens[1])
        elif keyword == AsciiMdlKeyword.TRANSPARENCYHINT.value:
            if len(tokens) >= 2:
                node.transparencyhint = int(tokens[1])
        elif keyword == AsciiMdlKeyword.SELFILLUMCOLOR.value:
            if len(tokens) >= 4:
                node.selfillumcolor = (
                    float(tokens[1]),
                    float(tokens[2]),
                    float(tokens[3]),
                )
        elif keyword == AsciiMdlKeyword.AMBIENT.value:
            if len(tokens) >= 4:
                node.ambient = (
                    float(tokens[1]),
                    float(tokens[2]),
                    float(tokens[3]),
                )
        elif keyword == AsciiMdlKeyword.DIFFUSE.value:
            if len(tokens) >= 4:
                node.diffuse = (
                    float(tokens[1]),
                    float(tokens[2]),
                    float(tokens[3]),
                )
        elif keyword == AsciiMdlKeyword.CENTER.value:
            if len(tokens) >= 4:
                try:
                    node.center = (
                        float(tokens[1]),
                        float(tokens[2]),
                        float(tokens[3]),
                    )
                except ValueError:
                    pass  # Sometimes "undefined" string
        elif keyword == AsciiMdlKeyword.VERTS.value:
            # Parse vertex list
            if len(tokens) >= 2:
                num_verts = int(tokens[1])
                node.verts = []
                for j in range(num_verts):
                    line_num += 1
                    if line_num < len(self.lines) and line_num < end_line:
                        vert_tokens = self.lines[line_num].strip().split()
                        if len(vert_tokens) >= 3:
                            node.verts.append(
                                (
                                    float(vert_tokens[0]),
                                    float(vert_tokens[1]),
                                    float(vert_tokens[2]),
                                )
                            )
                return line_num
        elif keyword == AsciiMdlKeyword.FACES.value:
            # Parse face list
            if len(tokens) >= 2:
                num_faces = int(tokens[1])
                node.facelist = FaceList()
                for j in range(num_faces):
                    line_num += 1
                    if line_num < len(self.lines) and line_num < end_line:
                        face_tokens = self.lines[line_num].strip().split()
                        if len(face_tokens) >= 3:
                            # Format: v1 v2 v3 smooth_group uv1 uv2 uv3 mat_id
                            v1, v2, v3 = (
                                int(face_tokens[0]),
                                int(face_tokens[1]),
                                int(face_tokens[2]),
                            )
                            node.facelist.vertices.append((v1, v2, v3))
                            if len(face_tokens) >= 4:
                                smooth_group = int(face_tokens[3])
                                # Store smooth group in normals list (temporary)
                                node.facelist.normals.append(smooth_group)  # pyright: ignore[reportArgumentType]
                            if len(face_tokens) >= 7:
                                uv1, uv2, uv3 = (
                                    int(face_tokens[4]),
                                    int(face_tokens[5]),
                                    int(face_tokens[6]),
                                )
                                node.facelist.uv.append((uv1, uv2, uv3))
                            if len(face_tokens) >= 8:
                                mat_id = int(face_tokens[7])
                                node.facelist.materials.append(mat_id)
                return line_num
        elif keyword == AsciiMdlKeyword.TVERTS.value:
            # Parse texture coordinates
            if len(tokens) >= 2:
                num_tverts = int(tokens[1])
                node.uv1 = []
                for j in range(num_tverts):
                    line_num += 1
                    if line_num < len(self.lines) and line_num < end_line:
                        uv_tokens = self.lines[line_num].strip().split()
                        if len(uv_tokens) >= 2:
                            node.uv1.append(
                                (
                                    float(uv_tokens[0]),
                                    float(uv_tokens[1]),
                                )
                            )
                return line_num
        elif keyword == AsciiMdlKeyword.TVERTS1.value:
            # Parse lightmap texture coordinates
            if len(tokens) >= 2:
                num_tverts = int(tokens[1])
                node.uv2 = []
                for j in range(num_tverts):
                    line_num += 1
                    if line_num < len(self.lines) and line_num < end_line:
                        uv_tokens = self.lines[line_num].strip().split()
                        if len(uv_tokens) >= 2:
                            node.uv2.append(
                                (
                                    float(uv_tokens[0]),
                                    float(uv_tokens[1]),
                                )
                            )
                return line_num
        elif keyword == AsciiMdlKeyword.TEXINDICES1.value:
            # Parse lightmap texture indices
            if len(tokens) >= 2:
                num_indices = int(tokens[1])
                # This is stored per-face, but we'll parse it
                for j in range(num_indices):
                    line_num += 1
                    if line_num < len(self.lines) and line_num < end_line:
                        idx_tokens = self.lines[line_num].strip().split()
                        # Format: idx1 idx2 idx3 per face
                        pass  # Store if needed
                return line_num
        elif keyword == AsciiMdlKeyword.ROOMLINKS.value:
            # Parse room links (for AABB/walkmesh)
            if len(tokens) >= 2:
                num_links = int(tokens[1])
                if isinstance(node, AabbNode):
                    node.roomlinks = {}
                    for j in range(num_links):
                        line_num += 1
                        if line_num < len(self.lines) and line_num < end_line:
                            link_tokens = self.lines[line_num].strip().split()
                            if len(link_tokens) >= 2:
                                edge_idx = int(link_tokens[0])
                                room_id = int(link_tokens[1])
                                node.roomlinks[edge_idx] = room_id
                return line_num

        return line_num

    def _parse_danglymesh_property(self, node: DanglymeshNode, keyword: str, tokens: list[str], line_num: int, end_line: int) -> int:
        """Parse danglymesh-specific properties."""
        # First parse as trimesh
        line_num = self._parse_trimesh_property(node, keyword, tokens, line_num, end_line)

        if keyword == AsciiMdlKeyword.PERIOD.value:
            if len(tokens) >= 2:
                node.period = float(tokens[1])
        elif keyword == AsciiMdlKeyword.TIGHTNESS.value:
            if len(tokens) >= 2:
                node.tightness = float(tokens[1])
        elif keyword == AsciiMdlKeyword.DISPLACEMENT.value:
            if len(tokens) >= 2:
                node.displacement = float(tokens[1])
        elif keyword == AsciiMdlKeyword.CONSTRAINTS.value:
            # Parse vertex constraints
            if len(tokens) >= 2:
                num_constraints = int(tokens[1])
                node.constraints = []
                for j in range(num_constraints):
                    line_num += 1
                    if line_num < len(self.lines) and line_num < end_line:
                        constraint_tokens = self.lines[line_num].strip().split()
                        if len(constraint_tokens) >= 1:
                            # Weight 0-255
                            weight = int(constraint_tokens[0])
                            node.constraints.append(weight)
                return line_num

        return line_num

    def _parse_skinmesh_property(self, node: SkinmeshNode, keyword: str, tokens: list[str], line_num: int, end_line: int) -> int:
        """Parse skinmesh-specific properties."""
        # First parse as trimesh
        line_num = self._parse_trimesh_property(node, keyword, tokens, line_num, end_line)

        if keyword == AsciiMdlKeyword.WEIGHTS.value:
            # Parse bone weights
            if len(tokens) >= 2:
                num_weights = int(tokens[1])
                node.weights = []
                for j in range(num_weights):
                    line_num += 1
                    if line_num < len(self.lines) and line_num < end_line:
                        weight_tokens = self.lines[line_num].strip().split()
                        # Format: bone_name weight [bone_name weight ...] (max 4 bones per vertex)
                        vertex_weights = []
                        i = 0
                        while i < len(weight_tokens) and len(vertex_weights) < 4:
                            if i + 1 < len(weight_tokens):
                                bone_name = weight_tokens[i]
                                weight = float(weight_tokens[i + 1])
                                vertex_weights.append((bone_name, weight))
                                i += 2
                            else:
                                break
                        node.weights.append(vertex_weights)
                return line_num

        return line_num

    def _parse_emitter_property(self, node: EmitterNode, keyword: str, tokens: list[str], line_num: int, end_line: int) -> int:
        """Parse emitter-specific properties."""
        # Basic properties
        if keyword == AsciiMdlKeyword.DEADSPACE.value:
            if len(tokens) >= 2:
                node.deadspace = float(tokens[1])
        elif keyword == AsciiMdlKeyword.BLASTRADIUS.value:
            if len(tokens) >= 2:
                node.blastradius = float(tokens[1])
        elif keyword == AsciiMdlKeyword.BLASTLENGTH.value:
            if len(tokens) >= 2:
                node.blastlength = float(tokens[1])
        elif keyword == AsciiMdlKeyword.NUMBRANCHES.value:
            if len(tokens) >= 2:
                node.num_branches = int(tokens[1])
        elif keyword == AsciiMdlKeyword.CONTROLPTMOOTHING.value:
            if len(tokens) >= 2:
                node.controlptsmoothing = int(tokens[1])
        elif keyword == AsciiMdlKeyword.XGRID.value:
            if len(tokens) >= 2:
                node.xgrid = int(tokens[1])
        elif keyword == AsciiMdlKeyword.YGRID.value:
            if len(tokens) >= 2:
                node.ygrid = int(tokens[1])
        elif keyword == AsciiMdlKeyword.SPAWNTYPE.value:
            if len(tokens) >= 2:
                node.spawntype = _parse_ascii_enum(SpawnType, tokens[1], 0)  # pyright: ignore[reportAttributeAccessIssue]
        elif keyword == AsciiMdlKeyword.UPDATE.value:
            if len(tokens) >= 2:
                node.update = _parse_ascii_enum(UpdateType, tokens[1], "")  # pyright: ignore[reportAttributeAccessIssue]
        elif keyword == AsciiMdlKeyword.EMITTER_RENDER.value:
            if len(tokens) >= 2:
                node.emitter_render = _parse_ascii_enum(EmitterRenderType, tokens[1], "")  # pyright: ignore[reportAttributeAccessIssue]
        elif keyword == AsciiMdlKeyword.BLEND.value:
            if len(tokens) >= 2:
                node.blend = _parse_ascii_enum(BlendType, tokens[1], "")  # pyright: ignore[reportAttributeAccessIssue]
        elif keyword == AsciiMdlKeyword.TEXTURE.value:
            if len(tokens) >= 2:
                node.texture = tokens[1]
        elif keyword == AsciiMdlKeyword.CHUNKNAME.value:
            if len(tokens) >= 2:
                node.chunk_name = tokens[1]
        elif keyword == AsciiMdlKeyword.TWOSIDEDTEX.value:
            if len(tokens) >= 2:
                node.twosidedtex = tokens[1] == "1"
        elif keyword == AsciiMdlKeyword.LOOP.value:
            if len(tokens) >= 2:
                node.loop = tokens[1] == "1"
        elif keyword == AsciiMdlKeyword.RENDERORDER.value:
            if len(tokens) >= 2:
                node.renderorder = int(tokens[1])
        elif keyword == AsciiMdlKeyword.FRAME_BLENDING.value:
            if len(tokens) >= 2:
                node.frame_blending = tokens[1] == "1"
        elif keyword == AsciiMdlKeyword.DEPTH_TEXTURE_NAME.value:
            if len(tokens) >= 2:
                node.depth_texture_name = tokens[1] if tokens[1].upper() != NULL else NULL
        # Flags
        elif keyword == AsciiMdlKeyword.P2P.value:
            if len(tokens) >= 2:
                node.p2p = tokens[1] == "1"
        elif keyword == AsciiMdlKeyword.P2P_SEL.value:
            if len(tokens) >= 2:
                node.p2p_sel = tokens[1] == "1"
        elif keyword == AsciiMdlKeyword.AFFECTEDBYWIND.value:
            if len(tokens) >= 2:
                node.affected_by_wind = tokens[1] == "1"
        elif keyword == AsciiMdlKeyword.TINTED.value:
            if len(tokens) >= 2:
                node.tinted = tokens[1] == "1"
        elif keyword == AsciiMdlKeyword.BOUNCE.value:
            if len(tokens) >= 2:
                node.bounce = tokens[1] == "1"
        elif keyword == AsciiMdlKeyword.RANDOM.value:
            if len(tokens) >= 2:
                node.random = tokens[1] == "1"
        elif keyword == AsciiMdlKeyword.INHERIT.value:
            if len(tokens) >= 2:
                node.inherit = tokens[1] == "1"
        elif keyword == AsciiMdlKeyword.INHERITVEL.value:
            if len(tokens) >= 2:
                node.inheritvel = tokens[1] == "1"
        elif keyword == AsciiMdlKeyword.INHERIT_LOCAL.value:
            if len(tokens) >= 2:
                node.inherit_local = tokens[1] == "1"
        elif keyword == AsciiMdlKeyword.SPLAT.value:
            if len(tokens) >= 2:
                node.splat = tokens[1] == "1"
        elif keyword == AsciiMdlKeyword.INHERIT_PART.value:
            if len(tokens) >= 2:
                node.inherit_part = tokens[1] == "1"
        elif keyword == AsciiMdlKeyword.DEPTH_TEXTURE.value:
            if len(tokens) >= 2:
                node.depth_texture = tokens[1] == "1"
        # Controllers (can be keyed)
        elif keyword == "alphastart":
            if len(tokens) >= 2:
                node.alphastart = float(tokens[1])
        elif keyword == "alphamid":
            if len(tokens) >= 2:
                node.alphamid = float(tokens[1])
        elif keyword == "alphaend":
            if len(tokens) >= 2:
                node.alphaend = float(tokens[1])
        elif keyword == "birthrate":
            if len(tokens) >= 2:
                node.birthrate = float(tokens[1])
        elif keyword == "m_frandombirthrate" or keyword == "randombirthrate":
            if len(tokens) >= 2:
                node.randombirthrate = float(tokens[1])
        elif keyword == "bounce_co":
            if len(tokens) >= 2:
                node.bounce_co = float(tokens[1])
        elif keyword == "combinetime":
            if len(tokens) >= 2:
                node.combinetime = float(tokens[1])
        elif keyword == "drag":
            if len(tokens) >= 2:
                node.drag = float(tokens[1])
        elif keyword == "fps":
            if len(tokens) >= 2:
                node.fps = float(tokens[1])
        elif keyword == "frameend":
            if len(tokens) >= 2:
                node.frameend = float(tokens[1])
        elif keyword == "framestart":
            if len(tokens) >= 2:
                node.framestart = float(tokens[1])
        elif keyword == "grav":
            if len(tokens) >= 2:
                node.grav = float(tokens[1])
        elif keyword == "lifeexp":
            if len(tokens) >= 2:
                node.lifeexp = float(tokens[1])
        elif keyword == "mass":
            if len(tokens) >= 2:
                node.mass = float(tokens[1])
        elif keyword == "p2p_bezier2":
            if len(tokens) >= 2:
                node.p2p_bezier2 = float(tokens[1])
        elif keyword == "p2p_bezier3":
            if len(tokens) >= 2:
                node.p2p_bezier3 = float(tokens[1])
        elif keyword == "particlerot":
            if len(tokens) >= 2:
                node.particlerot = float(tokens[1])
        elif keyword == "randvel":
            if len(tokens) >= 2:
                node.randvel = float(tokens[1])
        elif keyword == "sizestart":
            if len(tokens) >= 2:
                node.sizestart = float(tokens[1])
        elif keyword == "sizemid":
            if len(tokens) >= 2:
                node.sizemid = float(tokens[1])
        elif keyword == "sizeend":
            if len(tokens) >= 2:
                node.sizeend = float(tokens[1])
        elif keyword == "sizestart_y":
            if len(tokens) >= 2:
                node.sizestart_y = float(tokens[1])
        elif keyword == "sizemid_y":
            if len(tokens) >= 2:
                node.sizemid_y = float(tokens[1])
        elif keyword == "sizeend_y":
            if len(tokens) >= 2:
                node.sizeend_y = float(tokens[1])
        elif keyword == "spread":
            if len(tokens) >= 2:
                node.spread = float(tokens[1])
        elif keyword == "threshold":
            if len(tokens) >= 2:
                node.threshold = float(tokens[1])
        elif keyword == "velocity":
            if len(tokens) >= 2:
                node.velocity = float(tokens[1])
        elif keyword == "xsize":
            if len(tokens) >= 2:
                node.xsize = float(tokens[1])
        elif keyword == "ysize":
            if len(tokens) >= 2:
                node.ysize = float(tokens[1])
        elif keyword == "blurlength":
            if len(tokens) >= 2:
                node.blurlength = float(tokens[1])
        elif keyword == "lightningdelay":
            if len(tokens) >= 2:
                node.lightningdelay = float(tokens[1])
        elif keyword == "lightningradius":
            if len(tokens) >= 2:
                node.lightningradius = float(tokens[1])
        elif keyword == "lightningsubdiv":
            if len(tokens) >= 2:
                node.lightningsubdiv = float(tokens[1])
        elif keyword == "lightningscale":
            if len(tokens) >= 2:
                node.lightningscale = float(tokens[1])
        elif keyword == "lightningzigzag":
            if len(tokens) >= 2:
                node.lightningzigzag = float(tokens[1])
        elif keyword == "percentstart":
            if len(tokens) >= 2:
                node.percentstart = float(tokens[1])
        elif keyword == "percentmid":
            if len(tokens) >= 2:
                node.percentmid = float(tokens[1])
        elif keyword == "percentend":
            if len(tokens) >= 2:
                node.percentend = float(tokens[1])
        elif keyword == "targetsize":
            if len(tokens) >= 2:
                node.targetsize = float(tokens[1])
        elif keyword == "numcontrolpts":
            if len(tokens) >= 2:
                node.numcontrolpts = float(tokens[1])
        elif keyword == "controlptradius":
            if len(tokens) >= 2:
                node.controlptradius = float(tokens[1])
        elif keyword == "controlptdelay":
            if len(tokens) >= 2:
                node.controlptdelay = float(tokens[1])
        elif keyword == "tangentspread":
            if len(tokens) >= 2:
                node.tangentspread = float(tokens[1])
        elif keyword == "tangentlength":
            if len(tokens) >= 2:
                node.tangentlength = float(tokens[1])
        elif keyword == "colorstart":
            if len(tokens) >= 4:
                node.colorstart = (
                    float(tokens[1]),
                    float(tokens[2]),
                    float(tokens[3]),
                )
        elif keyword == "colormid":
            if len(tokens) >= 4:
                node.colormid = (
                    float(tokens[1]),
                    float(tokens[2]),
                    float(tokens[3]),
                )
        elif keyword == "colorend":
            if len(tokens) >= 4:
                node.colorend = (
                    float(tokens[1]),
                    float(tokens[2]),
                    float(tokens[3]),
                )
        elif keyword == "detonate":
            if len(tokens) >= 2:
                node.detonate = float(tokens[1])

        return line_num

    def _parse_light_property(self, node: LightNode, keyword: str, tokens: list[str], line_num: int, end_line: int) -> int:
        """Parse light-specific properties."""
        if keyword == AsciiMdlKeyword.RADIUS.value:
            if len(tokens) >= 2:
                node.radius = float(tokens[1])
        elif keyword == AsciiMdlKeyword.MULTIPLIER.value:
            if len(tokens) >= 2:
                node.multiplier = float(tokens[1])
        elif keyword == AsciiMdlKeyword.COLOR.value:
            if len(tokens) >= 4:
                node.color = (
                    float(tokens[1]),
                    float(tokens[2]),
                    float(tokens[3]),
                )
        elif keyword == AsciiMdlKeyword.AMBIENTONLY.value:
            if len(tokens) >= 2:
                node.ambientonly = 1 if tokens[1] == "1" else 0  # pyright: ignore[reportAttributeAccessIssue]
        elif keyword == AsciiMdlKeyword.NDYNAMICTYPE.value:
            if len(tokens) >= 2:
                node.dynamictype = int(tokens[1])
        elif keyword == AsciiMdlKeyword.ISDYNAMIC.value:
            # Not directly stored, but affects dynamictype
            pass
        elif keyword == AsciiMdlKeyword.AFFECTDYNAMIC.value:
            if len(tokens) >= 2:
                node.affectdynamic = 1 if tokens[1] == "1" else 0
        elif keyword == AsciiMdlKeyword.NEGATIVELIGHT.value:
            # Handled via color values
            pass
        elif keyword == AsciiMdlKeyword.LIGHTPRIORITY.value:
            if len(tokens) >= 2:
                node.lightpriority = int(tokens[1])
        elif keyword == AsciiMdlKeyword.FADINGLIGHT.value:
            if len(tokens) >= 2:
                node.fadinglight = 1 if tokens[1] == "1" else 0  # pyright: ignore[reportAttributeAccessIssue]
        elif keyword == AsciiMdlKeyword.LENSFLARES.value:
            if len(tokens) >= 2:
                node.lensflares = int(tokens[1])  # pyright: ignore[reportAttributeAccessIssue]
        elif keyword == AsciiMdlKeyword.FLARERADIUS.value:
            if len(tokens) >= 2:
                node.flareradius = float(tokens[1])
        elif keyword == "shadowradius":
            if len(tokens) >= 2:
                node.shadowradius = float(tokens[1])
        elif keyword == "verticaldisplacement":
            if len(tokens) >= 2:
                node.verticaldisplacement = float(tokens[1])
        elif keyword == AsciiMdlKeyword.TEXTURENAMES.value:
            # Parse flare texture names
            if len(tokens) >= 2:
                num_flares = int(tokens[1])
                node.flare_list = FlareList()
                for j in range(num_flares):
                    line_num += 1
                    if line_num < len(self.lines) and line_num < end_line:
                        texture_name = self.lines[line_num].strip()
                        node.flare_list.textures.append(texture_name)
                return line_num
        elif keyword == AsciiMdlKeyword.FLAREPOSITIONS.value:
            # Parse flare positions
            if len(tokens) >= 2:
                num_flares = int(tokens[1])
                if node.flare_list is None:
                    node.flare_list = FlareList()
                for j in range(num_flares):
                    line_num += 1
                    if line_num < len(self.lines) and line_num < end_line:
                        pos_tokens = self.lines[line_num].strip().split()
                        if len(pos_tokens) >= 1:
                            node.flare_list.positions.append(float(pos_tokens[0]))
                return line_num
        elif keyword == AsciiMdlKeyword.FLARESIZES.value:
            # Parse flare sizes
            if len(tokens) >= 2:
                num_flares = int(tokens[1])
                if node.flare_list is None:
                    node.flare_list = FlareList()
                for j in range(num_flares):
                    line_num += 1
                    if line_num < len(self.lines) and line_num < end_line:
                        size_tokens = self.lines[line_num].strip().split()
                        if len(size_tokens) >= 1:
                            node.flare_list.sizes.append(float(size_tokens[0]))
                return line_num
        elif keyword == AsciiMdlKeyword.FLARECOLORSHIFTS.value:
            # Parse flare color shifts
            if len(tokens) >= 2:
                num_flares = int(tokens[1])
                if node.flare_list is None:
                    node.flare_list = FlareList()
                for j in range(num_flares):
                    line_num += 1
                    if line_num < len(self.lines) and line_num < end_line:
                        color_tokens = self.lines[line_num].strip().split()
                        if len(color_tokens) >= 3:
                            node.flare_list.colorshifts.append(
                                (
                                    float(color_tokens[0]),
                                    float(color_tokens[1]),
                                    float(color_tokens[2]),
                                )
                            )
                return line_num

        return line_num

    def _parse_aabb_property(self, node: AabbNode, keyword: str, tokens: list[str], line_num: int, end_line: int) -> int:
        """Parse AABB-specific properties."""
        # AABB nodes share trimesh properties
        line_num = self._parse_trimesh_property(node, keyword, tokens, line_num, end_line)

        if keyword == AsciiMdlKeyword.AABB.value:
            # Parse AABB tree structure
            # Format: aabb min_x min_y min_z max_x max_y max_z child_count
            if len(tokens) >= 8:
                # AABB bounding box
                min_x, min_y, min_z = float(tokens[1]), float(tokens[2]), float(tokens[3])
                max_x, max_y, max_z = float(tokens[4]), float(tokens[5]), float(tokens[6])
                child_count = int(tokens[7])
                # Store AABB data if needed
                # Then parse child nodes recursively
                for j in range(child_count):
                    line_num += 1
                    if line_num < len(self.lines) and line_num < end_line:
                        # Parse child AABB entry
                        child_tokens = self.lines[line_num].strip().split()
                        if child_tokens and child_tokens[0].lower() == AsciiMdlKeyword.AABB.value:
                            # Recursive AABB child
                            pass
                return line_num

        return line_num

    def _parse_reference_property(self, node: ReferenceNode, keyword: str, tokens: list[str], line_num: int, end_line: int) -> int:
        """Parse reference node-specific properties."""
        if keyword == AsciiMdlKeyword.REFMODEL.value:
            if len(tokens) >= 2:
                node.refmodel = tokens[1] if tokens[1].upper() != NULL else NULL
        elif keyword == AsciiMdlKeyword.REATTACHABLE.value:
            if len(tokens) >= 2:
                node.reattachable = 1 if tokens[1] == "1" else 0

        return line_num

    def _parse_animations(self, start_line: int) -> None:
        """Parse animation section."""
        assert self.model is not None

        # Split animations by "newanim" keyword
        i = start_line
        while i < len(self.lines):
            line = self.lines[i].strip()
            if not line:
                i += 1
                continue

            tokens = line.split()
            if tokens and tokens[0].lower() == AsciiMdlKeyword.NEWANIM.value:
                # Find the end of this animation
                anim_end = self._find_animation_end(i)
                if anim_end < 0:
                    logger().warning(f"Animation starting at line {i + 1} has no matching doneanim")
                    break

                # Parse animation
                anim = self._parse_animation(i, anim_end)
                if anim:
                    self.model.animations.append(anim)

                i = anim_end + 1
            else:
                i += 1

    def _find_animation_end(self, start_line: int) -> int:
        """Find the matching 'doneanim' for an animation starting at start_line."""
        i = start_line + 1
        while i < len(self.lines):
            line = self.lines[i].strip()
            tokens = line.split()
            if tokens and tokens[0].lower() == AsciiMdlKeyword.DONEANIM.value:
                return i
            i += 1
        return -1

    def _parse_animation(self, start_line: int, end_line: int) -> Animation | None:
        """Parse a single animation block."""
        # Get animation name from first line
        first_line = self.lines[start_line].strip()
        tokens = first_line.split()
        if len(tokens) < 2:
            return None

        anim_name = tokens[1] if len(tokens) >= 2 else "UNNAMED"
        anim = Animation()
        anim.name = anim_name

        # Parse animation properties
        i = start_line + 1
        anim_node_start = -1
        while i < end_line:
            line = self.lines[i].strip()
            if not line:
                i += 1
                continue

            tokens = line.split()
            if not tokens:
                i += 1
                continue

            keyword = tokens[0].lower()

            if keyword == AsciiMdlKeyword.LENGTH.value:
                if len(tokens) >= 2:
                    anim.length = float(tokens[1])
            elif keyword == AsciiMdlKeyword.TRANS_TIME.value:
                if len(tokens) >= 2:
                    anim.transtime = float(tokens[1])
            elif keyword == AsciiMdlKeyword.ANIMROOT.value:
                if len(tokens) >= 2:
                    anim.animroot = tokens[1]
            elif keyword == AsciiMdlKeyword.EVENT.value:
                if len(tokens) >= 3:
                    event_time = float(tokens[1])
                    event_name = tokens[2]
                    anim.events.append((event_time, event_name))
            elif keyword == AsciiMdlKeyword.EVENTLIST.value:
                # Parse event list
                if len(tokens) >= 2:
                    num_events = int(tokens[1])
                    for j in range(num_events):
                        i += 1
                        if i < len(self.lines) and i < end_line:
                            event_tokens = self.lines[i].strip().split()
                            if len(event_tokens) >= 2:
                                event_time = float(event_tokens[0])
                                event_name = event_tokens[1]
                                anim.events.append((event_time, event_name))
            elif keyword == AsciiMdlKeyword.NODE.value:
                # Start of animation node tree
                anim_node_start = i
                break

            i += 1

        # Parse animation nodes if present
        if anim_node_start >= 0:
            anim.root_node = self._parse_animation_node_tree(anim_node_start, end_line)

        return anim

    def _parse_animation_node_tree(self, start_line: int, end_line: int) -> AnimationNode | None:
        """Parse animation node tree recursively."""
        # Find the node name
        first_line = self.lines[start_line].strip()
        tokens = first_line.split()
        if len(tokens) < 3:
            return None

        node_name = tokens[2]
        anim_node = AnimationNode(node_name)

        # Find end of this animation node
        node_end = self._find_animation_node_end(start_line, end_line)
        if node_end < 0:
            node_end = end_line

        # Parse keyframes and child nodes
        i = start_line + 1
        while i < node_end and i < end_line:
            line = self.lines[i].strip()
            if not line:
                i += 1
                continue

            tokens = line.split()
            if not tokens:
                i += 1
                continue

            keyword = tokens[0].lower()

            # Parse keyframe controllers
            # Base controllers
            base_controllers = [
                "position",
                "orientation",
                "scale",
                "alpha",
                "selfillumcolor",
                "color",
                "radius",
                "shadowradius",
                "verticaldisplacement",
            ]
            if keyword in base_controllers or keyword in _EMITTER_KEYFRAME_CONTROLLER_KEYWORDS:
                i = self._parse_keyframe_controller(anim_node, keyword, tokens, i, node_end)
            elif keyword == AsciiMdlKeyword.NODE.value:
                # Child animation node
                child_node = self._parse_animation_node_tree(i, node_end)
                if child_node:
                    child_node.parent = anim_node
                    anim_node.children.append(child_node)
                    # Find end of child node
                    child_end = self._find_animation_node_end(i, node_end)
                    if child_end >= 0:
                        i = child_end + 1
                    else:
                        i += 1
                else:
                    i += 1
            elif keyword == "endnode":
                # End of this node
                break
            else:
                i += 1

        # Mark as animated if it has keyframes
        anim_node.animated = bool(anim_node.keyframes) or any(child.animated for child in anim_node.children)

        return anim_node

    def _find_animation_node_end(self, start_line: int, end_line: int) -> int:
        """Find the end of an animation node (next node or end of parent)."""
        depth = 1
        i = start_line + 1
        while i < end_line:
            line = self.lines[i].strip()
            tokens = line.split()
            if tokens:
                keyword = tokens[0].lower()
                if keyword == AsciiMdlKeyword.NODE.value:
                    depth += 1
                elif keyword == "endnode":
                    depth -= 1
                    if depth == 0:
                        return i
            i += 1
        return end_line

    def _parse_keyframe_controller(
        self,
        anim_node: AnimationNode,
        keyword: str,
        tokens: list[str],
        line_num: int,
        end_line: int,
    ) -> int:
        """Parse a keyframe controller."""
        # Format: controller_name num_keys [keyframe_data...]
        if len(tokens) < 2:
            return line_num

        num_keys = int(tokens[1])
        keyframes = []

        for j in range(num_keys):
            line_num += 1
            if line_num >= len(self.lines) or line_num >= end_line:
                break

            key_tokens = self.lines[line_num].strip().split()
            if not key_tokens:
                continue

            # Parse keyframe: time value1 [value2 value3] [bezier_data]
            time = float(key_tokens[0])

            # Determine number of values based on controller type
            if keyword == "position":
                values = (float(key_tokens[1]), float(key_tokens[2]), float(key_tokens[3]))
                # Check for bezier (9 values total)
                if len(key_tokens) >= 10:
                    # Bezier keyframe
                    in_tangent = (float(key_tokens[4]), float(key_tokens[5]), float(key_tokens[6]))
                    out_tangent = (float(key_tokens[7]), float(key_tokens[8]), float(key_tokens[9]))
                    keyframes.append((time, values, in_tangent, out_tangent))
                else:
                    keyframes.append((time, values))
            elif keyword == "orientation":
                values = (
                    float(key_tokens[1]),
                    float(key_tokens[2]),
                    float(key_tokens[3]),
                    float(key_tokens[4]),
                )
                keyframes.append((time, values))
            elif keyword in ["alpha", "radius", "scale", "shadowradius", "verticaldisplacement"]:
                # Single float value
                if len(key_tokens) >= 2:
                    values = float(key_tokens[1])
                    keyframes.append((time, values))
            elif keyword == "selfillumcolor" or keyword == "color":
                # 3 float values (RGB)
                if len(key_tokens) >= 4:
                    values = (
                        float(key_tokens[1]),
                        float(key_tokens[2]),
                        float(key_tokens[3]),
                    )
                    keyframes.append((time, values))
            elif keyword in _EMITTER_KEYFRAME_CONTROLLER_KEYWORDS:
                # Emitter controllers - most are single float, some are RGB
                if keyword in ["colorstart", "colormid", "colorend"]:
                    # RGB color controllers
                    if len(key_tokens) >= 4:
                        values = (
                            float(key_tokens[1]),
                            float(key_tokens[2]),
                            float(key_tokens[3]),
                        )
                        keyframes.append((time, values))
                else:
                    # Single float controllers
                    if len(key_tokens) >= 2:
                        values = float(key_tokens[1])
                        keyframes.append((time, values))

        # Store keyframes in animation node's keyframes dict
        # Format: keyframes[label] = [[time, value1, value2, ...], ...]
        formatted_keyframes = []
        for keyframe in keyframes:
            time = keyframe[0]
            values = keyframe[1] if len(keyframe) > 1 else None
            if values is None:
                continue

            # Format as [time, value1, value2, ...]
            if isinstance(values, tuple):
                formatted_keyframes.append([time] + list(values))
            elif isinstance(values, (int, float)):
                formatted_keyframes.append([time, values])
            elif len(keyframe) >= 4:
                # Bezier keyframe: [time, values, in_tangent, out_tangent]
                in_tangent = keyframe[2]
                out_tangent = keyframe[3]
                if isinstance(values, tuple):
                    # For position: combine values with tangents
                    formatted_keyframes.append([time] + list(values) + list(in_tangent) + list(out_tangent))
                else:
                    formatted_keyframes.append([time, values])
            else:
                formatted_keyframes.append([time, values])

        if formatted_keyframes:
            anim_node.keyframes[keyword] = formatted_keyframes

        return line_num
