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

"""PyKotor adapter layer for io_scene_kotor.

This module wraps PyKotor APIs to match the existing io/ layer interface,
allowing gradual migration from custom format parsers to PyKotor equivalents.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from ..constants import NULL, USE_PYKOTOR_READERS, ExportOptions, GameType
from ..utils import logger

try:
    from pykotor.extract.installation import SearchLocation
    from pykotor.resource.formats.gff import GFF as PyKotorGFF
    from pykotor.resource.formats.gff import read_gff as pykotor_read_gff
    from pykotor.resource.formats.gff import write_gff as pykotor_write_gff
    from pykotor.resource.formats.mdl import MDL as PyKotorMDL
    from pykotor.resource.formats.mdl import read_mdl as pykotor_read_mdl
    from pykotor.resource.formats.mdl import write_mdl as pykotor_write_mdl
    from pykotor.resource.formats.tpc import TPC as PyKotorTPC
    from pykotor.resource.formats.tpc import read_tpc as pykotor_read_tpc
    from pykotor.resource.formats.tpc import write_tpc as pykotor_write_tpc

    PYKOTOR_AVAILABLE = True
except ImportError:
    PYKOTOR_AVAILABLE = False
    if not TYPE_CHECKING:
        PyKotorMDL = type("PyKotorMDL", (), {})
        PyKotorTPC = type("PyKotorTPC", (), {})
        PyKotorGFF = type("PyKotorGFF", (), {})
        SearchLocation = type("SearchLocation", (), {})

if TYPE_CHECKING:
    from ..format.tpc.reader import TpcImage
    from ..scene.animation import Animation
    from ..scene.animnode import AnimationNode
    from ..scene.model import Model
    from ..scene.modelnode.aabb import AabbNode
    from ..scene.modelnode.base import BaseNode
    from ..scene.modelnode.danglymesh import DanglymeshNode
    from ..scene.modelnode.emitter import EmitterNode
    from ..scene.modelnode.light import LightNode
    from ..scene.modelnode.lightsaber import LightsaberNode
    from ..scene.modelnode.skinmesh import SkinmeshNode
    from ..scene.modelnode.trimesh import TrimeshNode


def is_pykotor_available() -> bool:
    """Check if PyKotor is available for use."""
    return PYKOTOR_AVAILABLE


def get_use_pykotor_readers() -> bool:
    """Whether to use PyKotor for format read/write (TPC, GFF, etc.).

    Returns True only when USE_PYKOTOR_READERS is True and PyKotor is available.
    MDL is excluded: io_scene_kotor.io.mdl always uses MdlReader/MdlWriter and
    AsciiMdlReader/AsciiMdlWriter; it does not call this or any MDL adapter functions.
    """
    return PYKOTOR_AVAILABLE and USE_PYKOTOR_READERS


# ============================================================================
# MDL Conversion Functions
# ============================================================================
# NOTE: The following MDL-related functions (load_mdl_via_pykotor,
# save_mdl_via_pykotor, convert_pykotor_mdl_to_scene,
# convert_scene_model_to_pykotor, and their helper functions) are kept in
# this adapter for potential future use or external callers, but are NOT
# currently used by io_scene_kotor.io.mdl load/save operations. The MDL IO
# layer always uses the existing MdlReader/MdlWriter from
# io_scene_kotor.format.mdl.
# ============================================================================


def load_mdl_via_pykotor(filepath: str) -> PyKotorMDL | None:
    """Load an MDL file using PyKotor.

    PyKotor's read_mdl function automatically handles MDX companion files
    (geometry data) if they exist alongside the MDL file.

    NOTE: This function is not used by io_scene_kotor.io.mdl.load_mdl().
    It is kept for potential future use or external callers.

    Args:
        filepath: Path to the .mdl file

    Returns:
        PyKotor MDL object, or None if PyKotor is unavailable

    """
    if not PYKOTOR_AVAILABLE:
        return None

    try:
        # PyKotor's read_mdl automatically looks for and loads the corresponding .mdx file
        # if it exists (same base name, different extension)
        return pykotor_read_mdl(filepath)  # pyright: ignore[reportPossiblyUnboundVariable]
    except Exception as e:
        logger().debug(f"PyKotor MDL read failed for {filepath}: {e}", exc_info=True)
        return None


def save_mdl_via_pykotor(mdl: PyKotorMDL, filepath: str) -> bool:
    """Save an MDL file using PyKotor.

    NOTE: This function is not used by io_scene_kotor.io.mdl.save_mdl().
    It is kept for potential future use or external callers.

    Args:
        mdl: PyKotor MDL object
        filepath: Path to save the .mdl file

    Returns:
        True if successful, False otherwise

    """
    if not PYKOTOR_AVAILABLE:
        return False

    try:
        pykotor_write_mdl(mdl, filepath)  # pyright: ignore[reportPossiblyUnboundVariable]
        return True
    except Exception as e:
        logger().debug(f"PyKotor MDL write failed for {filepath}: {e}", exc_info=True)
        return False


def convert_pykotor_mdl_to_scene(pykotor_mdl: PyKotorMDL) -> Model | None:
    """Convert a PyKotor MDL object to io_scene_kotor scene.Model.

    Converts PyKotor's MDL structure to our scene representation, including:
    - Model header (name, classification, bounding box, etc.)
    - Node hierarchy (dummy, trimesh, skinmesh, reference, special nodes)
    - Animations
    - Materials and textures

    NOTE: This function is not used by io_scene_kotor.io.mdl.load_mdl().
    It is kept for potential future use or external callers.

    Args:
        pykotor_mdl: PyKotor MDL object

    Returns:
        io_scene_kotor Model object, or None if conversion fails

    """
    if not PYKOTOR_AVAILABLE or pykotor_mdl is None:
        return None

    try:
        from ..constants import NULL, Classification
        from ..scene.model import Model

        model = Model()

        # Convert MDL header properties
        model.name = (
            getattr(pykotor_mdl, "name", getattr(pykotor_mdl, "model_name", "UNNAMED")) or "UNNAMED"
        )
        if isinstance(model.name, bytes):
            model.name = model.name.decode("utf-8", errors="replace").rstrip("\0")

        model.supermodel = (
            getattr(pykotor_mdl, "supermodel", getattr(pykotor_mdl, "super_model", NULL)) or NULL
        )
        if isinstance(model.supermodel, bytes):
            model.supermodel = (
                model.supermodel.decode("utf-8", errors="replace").rstrip("\0") or NULL
            )

        # Convert classification
        classification_str = getattr(pykotor_mdl, "classification", None)
        if classification_str:
            if isinstance(classification_str, bytes):
                classification_str = classification_str.decode("utf-8", errors="replace")
            try:
                model.classification = Classification(classification_str.upper())
            except (ValueError, AttributeError):
                model.classification = Classification.OTHER

        model.subclassification = (
            getattr(pykotor_mdl, "subclassification", getattr(pykotor_mdl, "sub_classification", 0))
            or 0
        )
        model.classification_unk1 = getattr(pykotor_mdl, "classification_unk1", 0) or 0
        model.affected_by_fog = getattr(pykotor_mdl, "affected_by_fog", True)
        model.animroot = (
            getattr(pykotor_mdl, "animroot", getattr(pykotor_mdl, "anim_root", NULL)) or NULL
        )
        if isinstance(model.animroot, bytes):
            model.animroot = model.animroot.decode("utf-8", errors="replace").rstrip("\0") or NULL
        model.animscale = float(
            getattr(pykotor_mdl, "animscale", getattr(pykotor_mdl, "anim_scale", 1.0)) or 1.0
        )

        # Convert bounding box
        bbox_min = getattr(pykotor_mdl, "bounding_box_min", getattr(pykotor_mdl, "bbox_min", None))
        bbox_max = getattr(pykotor_mdl, "bounding_box_max", getattr(pykotor_mdl, "bbox_max", None))
        if bbox_min and len(bbox_min) >= 3:
            model.bounding_box_min = (float(bbox_min[0]), float(bbox_min[1]), float(bbox_min[2]))
        if bbox_max and len(bbox_max) >= 3:
            model.bounding_box_max = (float(bbox_max[0]), float(bbox_max[1]), float(bbox_max[2]))

        model.model_radius = float(
            getattr(pykotor_mdl, "model_radius", getattr(pykotor_mdl, "radius", 0.0)) or 0.0
        )

        # Convert root node
        root_node_pk = getattr(pykotor_mdl, "root", getattr(pykotor_mdl, "root_node", None))
        if root_node_pk:
            model.root_node = _convert_pykotor_node_to_scene_node(root_node_pk, None)
        else:
            # Create default root dummy node
            from ..scene.modelnode.dummy import DummyNode

            model.root_node = DummyNode("root")

        # Convert animations
        animations_pk = getattr(
            pykotor_mdl, "animations", getattr(pykotor_mdl, "animation_list", None)
        )
        if animations_pk:
            model.animations = _convert_pykotor_animations_to_scene(animations_pk, pykotor_mdl)

        return model
    except Exception as e:
        logger().debug(
            f"PyKotor MDL to scene conversion failed: {e.__class__.__name__}: {e}", exc_info=True
        )
        return None


def _convert_pykotor_node_to_scene_node(pk_node, parent) -> "BaseNode | None":
    """
    Convert a PyKotor node to io_scene_kotor BaseNode.

    Handles basic nodes: Dummy, Trimesh, Skinmesh, Reference.
    Special nodes are handled separately.

    Args:
        pk_node: PyKotor node object
        parent: Parent BaseNode or None

    Returns:
        BaseNode or subclass, or None if conversion fails
    """
    if not PYKOTOR_AVAILABLE or pk_node is None:
        return None

    try:
        from ..constants import NULL
        from ..scene.modelnode.base import BaseNode
        from ..scene.modelnode.dummy import DummyNode
        from ..scene.modelnode.reference import ReferenceNode

        # Extract node name
        node_name = getattr(pk_node, "name", getattr(pk_node, "node_name", "UNNAMED")) or "UNNAMED"
        if isinstance(node_name, bytes):
            node_name = node_name.decode("utf-8", errors="replace").rstrip("\0") or "UNNAMED"

        # Extract node type
        node_type_str = getattr(pk_node, "node_type", getattr(pk_node, "type", None))
        if isinstance(node_type_str, bytes):
            node_type_str = node_type_str.decode("utf-8", errors="replace")
        if isinstance(node_type_str, int):
            # Map integer type to string
            type_map = {0: "DUMMY", 1: "TRIMESH", 2: "SKIN", 3: "REFERENCE"}
            node_type_str = type_map.get(node_type_str, "DUMMY")

        # Extract position, rotation, scale
        position = (0.0, 0.0, 0.0)
        pos_attr = getattr(pk_node, "position", getattr(pk_node, "pos", None))
        if pos_attr:
            if hasattr(pos_attr, "__iter__") and len(pos_attr) >= 3:
                position = (float(pos_attr[0]), float(pos_attr[1]), float(pos_attr[2]))

        orientation = (1.0, 0.0, 0.0, 0.0)  # Quaternion (w, x, y, z)
        rot_attr = getattr(
            pk_node, "orientation", getattr(pk_node, "rotation", getattr(pk_node, "rot", None))
        )
        if rot_attr:
            if hasattr(rot_attr, "__iter__") and len(rot_attr) >= 4:
                orientation = (
                    float(rot_attr[0]),
                    float(rot_attr[1]),
                    float(rot_attr[2]),
                    float(rot_attr[3]),
                )
            elif hasattr(rot_attr, "__iter__") and len(rot_attr) >= 3:
                # Euler angles - convert to quaternion (simplified)
                orientation = (1.0, float(rot_attr[0]), float(rot_attr[1]), float(rot_attr[2]))

        scale = float(getattr(pk_node, "scale", getattr(pk_node, "scale_factor", 1.0)) or 1.0)

        # Determine node type and create appropriate node
        node_type_upper = (node_type_str or "").upper()
        scene_node: BaseNode | None = None

        if node_type_upper in ("REFERENCE", "REF"):
            scene_node = ReferenceNode(node_name)
            scene_node.refmodel = (
                getattr(pk_node, "refmodel", getattr(pk_node, "ref_model", NULL)) or NULL
            )
            if isinstance(scene_node.refmodel, bytes):
                scene_node.refmodel = (
                    scene_node.refmodel.decode("utf-8", errors="replace").rstrip("\0") or NULL
                )
            scene_node.reattachable = int(getattr(pk_node, "reattachable", 0) or 0)
        elif node_type_upper in ("EMITTER", "PARTICLE"):
            scene_node = _convert_pykotor_emitter_node(pk_node, node_name)
        elif node_type_upper in ("LIGHT", "LAMP"):
            scene_node = _convert_pykotor_light_node(pk_node, node_name)
        elif node_type_upper in ("LIGHTSABER", "SABER"):
            scene_node = _convert_pykotor_lightsaber_node(pk_node, node_name)
        elif node_type_upper in ("AABB", "BOUNDINGBOX"):
            scene_node = _convert_pykotor_aabb_node(pk_node, node_name)
        elif node_type_upper in ("DANGLYMESH", "DANGLY"):
            scene_node = _convert_pykotor_danglymesh_node(pk_node, node_name)
        elif node_type_upper in ("TRIMESH", "MESH"):
            scene_node = _convert_pykotor_trimesh_node(pk_node, node_name)
        elif node_type_upper in ("SKIN", "SKINMESH"):
            scene_node = _convert_pykotor_skinmesh_node(pk_node, node_name)
        else:
            # Default to DummyNode
            scene_node = DummyNode(node_name)

        if scene_node is None:
            return None

        # Set common properties
        scene_node.position = position
        scene_node.orientation = orientation
        scene_node.scale = scale
        scene_node.parent = parent
        scene_node.node_number = int(
            getattr(pk_node, "node_number", getattr(pk_node, "node_id", -1)) or -1
        )

        # Convert children
        children_pk = getattr(pk_node, "children", getattr(pk_node, "child_nodes", None))
        if children_pk and hasattr(children_pk, "__iter__"):
            for child_pk in children_pk:
                child_node = _convert_pykotor_node_to_scene_node(child_pk, scene_node)
                if child_node:
                    scene_node.children.append(child_node)

        return scene_node
    except Exception as e:
        logger().debug(f"PyKotor node conversion failed: {e}", exc_info=True)
        return None


def _convert_pykotor_trimesh_node(pk_node, name: str) -> "TrimeshNode | None":
    """Convert a PyKotor trimesh node to TrimeshNode."""
    try:
        from ..scene.modelnode.trimesh import EdgeLoopMesh, TrimeshNode

        node = TrimeshNode(name)

        # Extract geometry data
        mesh = EdgeLoopMesh()

        # Get vertices
        verts_pk = getattr(
            pk_node, "vertices", getattr(pk_node, "verts", getattr(pk_node, "vertex_data", None))
        )
        if verts_pk and hasattr(verts_pk, "__iter__"):
            for vert in verts_pk:
                if hasattr(vert, "__iter__") and len(vert) >= 3:
                    mesh.verts.append((float(vert[0]), float(vert[1]), float(vert[2])))

        # Get UV coordinates
        uv1_pk = getattr(
            pk_node, "uv1", getattr(pk_node, "uv", getattr(pk_node, "texture_coords", None))
        )
        uv2_pk = getattr(pk_node, "uv2", getattr(pk_node, "lightmap_uv", None))
        if uv1_pk and hasattr(uv1_pk, "__iter__"):
            for uv in uv1_pk:
                if hasattr(uv, "__iter__") and len(uv) >= 2:
                    mesh.loop_uv1.append((float(uv[0]), float(uv[1])))
        if uv2_pk and hasattr(uv2_pk, "__iter__"):
            for uv in uv2_pk:
                if hasattr(uv, "__iter__") and len(uv) >= 2:
                    mesh.loop_uv2.append((float(uv[0]), float(uv[1])))

        # Get faces/indices
        faces_pk = getattr(
            pk_node, "faces", getattr(pk_node, "indices", getattr(pk_node, "face_data", None))
        )
        if faces_pk and hasattr(faces_pk, "__iter__"):
            for face in faces_pk:
                if hasattr(face, "__iter__") and len(face) >= 3:
                    mesh.loop_verts.extend([int(face[0]), int(face[1]), int(face[2])])

        # Get normals
        normals_pk = getattr(pk_node, "normals", getattr(pk_node, "normal_data", None))
        if normals_pk and hasattr(normals_pk, "__iter__"):
            for norm in normals_pk:
                if hasattr(norm, "__iter__") and len(norm) >= 3:
                    mesh.loop_normals.append((float(norm[0]), float(norm[1]), float(norm[2])))

        # Get material/texture
        material_pk = getattr(pk_node, "material", getattr(pk_node, "texture", None))
        if material_pk:
            texture_name = getattr(material_pk, "name", getattr(material_pk, "texture_name", None))
            if texture_name:
                if isinstance(texture_name, bytes):
                    texture_name = texture_name.decode("utf-8", errors="replace").rstrip("\0")
                node.bitmap = texture_name or NULL

        return node
    except Exception as e:
        logger().debug(f"PyKotor trimesh conversion failed: {e}", exc_info=True)
        return None


def _convert_pykotor_skinmesh_node(pk_node: Any, name: str) -> "SkinmeshNode | None":
    """Convert a PyKotor skinmesh node to SkinmeshNode."""
    try:
        from ..scene.modelnode.skinmesh import SkinmeshNode

        node = SkinmeshNode(name)

        # Convert as trimesh first
        trimesh_node = _convert_pykotor_trimesh_node(pk_node, name)
        if trimesh_node:
            # Copy all trimesh attributes
            node.verts = trimesh_node.verts
            node.normals = trimesh_node.normals
            node.uv1 = trimesh_node.uv1
            node.uv2 = trimesh_node.uv2
            node.facelist = trimesh_node.facelist
            node.bitmap = trimesh_node.bitmap
            node.bitmap2 = trimesh_node.bitmap2

        # Extract bone weights
        weights_pk = getattr(pk_node, "weights", getattr(pk_node, "bone_weights", None))
        if weights_pk and hasattr(weights_pk, "__iter__"):
            node.weights = []
            for vert_idx, vert_weights in enumerate(weights_pk):
                if vert_idx < len(node.verts):
                    weight_list = []
                    if hasattr(vert_weights, "__iter__"):
                        for weight_data in vert_weights:
                            if hasattr(weight_data, "__iter__") and len(weight_data) >= 2:
                                bone_name = str(weight_data[0])
                                weight = float(weight_data[1])
                                weight_list.append((bone_name, weight))
                    if len(node.weights) <= vert_idx:
                        node.weights.extend([[]] * (vert_idx + 1 - len(node.weights)))
                    node.weights[vert_idx] = weight_list

        return node
    except Exception as e:
        logger().debug(f"PyKotor skinmesh conversion failed: {e}", exc_info=True)
        return None


def _convert_pykotor_emitter_node(pk_node, name: str) -> "EmitterNode | None":
    """Convert a PyKotor emitter node to EmitterNode."""
    try:
        from ..constants import NULL
        from ..scene.modelnode.emitter import EmitterNode

        node = EmitterNode(name)

        # Extract emitter properties (many attributes)
        for attr in EmitterNode.EMITTER_ATTRS:
            value = getattr(pk_node, attr, None)
            if value is not None:
                if isinstance(value, bytes) and attr in (
                    "texture",
                    "chunk_name",
                    "depth_texture_name",
                ):
                    value = value.decode("utf-8", errors="replace").rstrip("\0") or NULL
                setattr(node, attr, value)

        return node
    except Exception as e:
        logger().debug(f"PyKotor emitter conversion failed: {e}", exc_info=True)
        return None


def _convert_pykotor_light_node(pk_node, name: str) -> "LightNode | None":
    """Convert a PyKotor light node to LightNode."""
    try:
        from ..scene.modelnode.light import FlareList, LightNode

        node = LightNode(name)

        # Extract light properties
        node.shadow = int(getattr(pk_node, "shadow", 1) or 1)
        node.radius = float(getattr(pk_node, "radius", 5.0) or 5.0)
        node.shadowradius = float(getattr(pk_node, "shadowradius", 0.0) or 0.0)
        node.verticaldisplacement = float(getattr(pk_node, "verticaldisplacement", 0.0) or 0.0)
        node.multiplier = int(getattr(pk_node, "multiplier", 1) or 1)
        node.lightpriority = int(getattr(pk_node, "lightpriority", 5) or 5)

        color_attr = getattr(pk_node, "color", getattr(pk_node, "colour", None))
        if color_attr and hasattr(color_attr, "__iter__") and len(color_attr) >= 3:
            node.color = (float(color_attr[0]), float(color_attr[1]), float(color_attr[2]))

        node.ambientonly = int(getattr(pk_node, "ambientonly", 1) or 1)
        node.dynamictype = int(getattr(pk_node, "dynamictype", 0) or 0)
        node.affectdynamic = int(getattr(pk_node, "affectdynamic", 1) or 1)
        node.fadinglight = int(getattr(pk_node, "fadinglight", 1) or 1)
        node.lensflares = int(getattr(pk_node, "lensflares", 0) or 0)
        node.flareradius = float(getattr(pk_node, "flareradius", 1.0) or 1.0)

        # Convert flare list if present
        flares_pk = getattr(pk_node, "flares", getattr(pk_node, "flare_list", None))
        if flares_pk:
            node.flare_list = FlareList()
            # Extract flare data if available

        return node
    except Exception as e:
        logger().debug(f"PyKotor light conversion failed: {e}", exc_info=True)
        return None


def _convert_pykotor_lightsaber_node(pk_node, name: str) -> "LightsaberNode | None":
    """Convert a PyKotor lightsaber node to LightsaberNode."""
    try:
        from ..scene.modelnode.lightsaber import LightsaberNode

        node = LightsaberNode(name)

        # Convert as trimesh first (lightsaber has geometry)
        trimesh_node = _convert_pykotor_trimesh_node(pk_node, name)
        if trimesh_node:
            node.verts = trimesh_node.verts
            node.normals = trimesh_node.normals
            node.uv1 = trimesh_node.uv1
            node.uv2 = trimesh_node.uv2
            node.facelist = trimesh_node.facelist
            node.bitmap = trimesh_node.bitmap
            node.bitmap2 = trimesh_node.bitmap2

        # Extract lightsaber-specific properties
        # (LightsaberNode may have additional properties beyond TrimeshNode)

        return node
    except Exception as e:
        logger().debug(f"PyKotor lightsaber conversion failed: {e}", exc_info=True)
        return None


def _convert_pykotor_aabb_node(pk_node, name: str) -> "AabbNode | None":
    """Convert a PyKotor AABB node to AabbNode."""
    try:
        from ..scene.modelnode.aabb import AabbNode

        node = AabbNode(name)

        # Convert as trimesh first (AABB has geometry)
        trimesh_node = _convert_pykotor_trimesh_node(pk_node, name)
        if trimesh_node:
            node.edge_loop_mesh = trimesh_node.edge_loop_mesh
            node.diffuse_texture = trimesh_node.diffuse_texture

        # Extract AABB-specific properties
        lyt_pos = getattr(pk_node, "lytposition", getattr(pk_node, "lyt_position", None))
        if lyt_pos and hasattr(lyt_pos, "__iter__") and len(lyt_pos) >= 3:
            node.lytposition = (float(lyt_pos[0]), float(lyt_pos[1]), float(lyt_pos[2]))

        roomlinks_pk = getattr(pk_node, "roomlinks", getattr(pk_node, "room_links", None))
        if roomlinks_pk and isinstance(roomlinks_pk, dict):
            node.roomlinks = roomlinks_pk

        return node
    except Exception as e:
        logger().debug(f"PyKotor AABB conversion failed: {e}", exc_info=True)
        return None


def _convert_pykotor_danglymesh_node(pk_node, name: str) -> "DanglymeshNode | None":
    """Convert a PyKotor danglymesh node to DanglymeshNode."""
    try:
        from ..scene.modelnode.danglymesh import DanglymeshNode

        node = DanglymeshNode(name)

        # Convert as trimesh first
        trimesh_node = _convert_pykotor_trimesh_node(pk_node, name)
        if trimesh_node:
            node.verts = trimesh_node.verts
            node.normals = trimesh_node.normals
            node.uv1 = trimesh_node.uv1
            node.uv2 = trimesh_node.uv2
            node.facelist = trimesh_node.facelist
            node.bitmap = trimesh_node.bitmap
            node.bitmap2 = trimesh_node.bitmap2

            # Extract vertex constraints
            constraints_pk = getattr(
                pk_node, "constraints", getattr(pk_node, "vertex_constraints", None)
            )
            if constraints_pk and hasattr(constraints_pk, "__iter__"):
                node.constraints = []
                for vert_idx, constraint in enumerate(constraints_pk):
                    if vert_idx < len(node.verts):
                        if len(node.constraints) <= vert_idx:
                            node.constraints.extend([0] * (vert_idx + 1 - len(node.constraints)))
                        node.constraints[vert_idx] = (
                            int(constraint) if constraint is not None else 0
                        )

        # Extract danglymesh-specific properties
        node.period = float(getattr(pk_node, "period", 1.0) or 1.0)
        node.tightness = float(getattr(pk_node, "tightness", 1.0) or 1.0)
        node.displacement = float(getattr(pk_node, "displacement", 1.0) or 1.0)

        return node
    except Exception as e:
        logger().debug(f"PyKotor danglymesh conversion failed: {e}", exc_info=True)
        return None


def _convert_pykotor_animations_to_scene(animations_pk, pykotor_mdl) -> list["Animation"]:
    """Convert PyKotor animations to scene.Animation list."""
    try:
        from ..scene.animation import Animation

        animations: list[Animation] = []

        if not animations_pk or not hasattr(animations_pk, "__iter__"):
            return animations

        for anim_pk in animations_pk:
            anim_name = (
                getattr(anim_pk, "name", getattr(anim_pk, "anim_name", "UNNAMED")) or "UNNAMED"
            )
            if isinstance(anim_name, bytes):
                anim_name = anim_name.decode("utf-8", errors="replace").rstrip("\0") or "UNNAMED"

            anim = Animation(anim_name)
            anim.length = float(
                getattr(anim_pk, "length", getattr(anim_pk, "duration", 1.0)) or 1.0
            )
            anim.transtime = float(
                getattr(anim_pk, "transtime", getattr(anim_pk, "transition_time", 0.25)) or 0.25
            )
            anim.animroot = (
                getattr(anim_pk, "animroot", getattr(anim_pk, "anim_root", NULL)) or NULL
            )
            if isinstance(anim.animroot, bytes):
                anim.animroot = anim.animroot.decode("utf-8", errors="replace").rstrip("\0") or NULL

            # Convert animation events
            events_pk = getattr(anim_pk, "events", getattr(anim_pk, "event_list", None))
            if events_pk and hasattr(events_pk, "__iter__"):
                for event_pk in events_pk:
                    event_time = float(
                        getattr(event_pk, "time", getattr(event_pk, "timestamp", 0.0)) or 0.0
                    )
                    event_name = (
                        getattr(event_pk, "name", getattr(event_pk, "event_name", "")) or ""
                    )
                    if isinstance(event_name, bytes):
                        event_name = event_name.decode("utf-8", errors="replace")
                    if event_name:
                        anim.events.append((event_time, event_name))

            # Convert animation nodes/keyframes
            root_anim_node_pk = getattr(anim_pk, "root_node", getattr(anim_pk, "root", None))
            if root_anim_node_pk:
                anim.root_node = _convert_pykotor_animnode_to_scene(
                    root_anim_node_pk, None, pykotor_mdl
                )

            animations.append(anim)

        return animations
    except Exception as e:
        logger().debug(f"PyKotor animation conversion failed: {e}", exc_info=True)
        return []


def _convert_pykotor_animnode_to_scene(pk_animnode, parent, pykotor_mdl) -> "AnimationNode | None":
    """Convert a PyKotor animation node to AnimationNode.

    Args:
        pk_animnode: PyKotor animation node object
        parent: Parent AnimationNode or None
        pykotor_mdl: PyKotor MDL object (for accessing node numbers)

    Returns:
        AnimationNode or None if conversion fails
    """
    if not PYKOTOR_AVAILABLE or pk_animnode is None:
        return None

    try:
        from ..constants import NULL
        from ..scene.animnode import AnimationNode

        # Extract node name
        node_name = (
            getattr(pk_animnode, "name", getattr(pk_animnode, "node_name", "UNNAMED")) or "UNNAMED"
        )
        if isinstance(node_name, bytes):
            node_name = node_name.decode("utf-8", errors="replace").rstrip("\0") or "UNNAMED"

        anim_node = AnimationNode(node_name)

        # Extract node number
        node_number = getattr(pk_animnode, "node_number", getattr(pk_animnode, "node_id", -1))
        if node_number is None:
            node_number = -1
        anim_node.node_number = int(node_number)

        anim_node.parent = parent

        # Convert keyframes/controllers
        controllers_pk = getattr(
            pk_animnode, "controllers", getattr(pk_animnode, "keyframes", None)
        )
        if controllers_pk and hasattr(controllers_pk, "__iter__"):
            for ctrl_pk in controllers_pk:
                _convert_pykotor_controller_to_keyframes(ctrl_pk, anim_node)

        # Alternative: check for direct keyframe properties
        # PyKotor might store keyframes as attributes like position_key, orientation_key, etc.
        for prop_label in [
            "position",
            "orientation",
            "scale",
            "alpha",
            "selfillumcolor",
            "color",
            "radius",
        ]:
            key_data = getattr(pk_animnode, f"{prop_label}_key", None)
            bezier_key_data = getattr(pk_animnode, f"{prop_label}_bezierkey", None)
            if bezier_key_data:
                _convert_pykotor_keyframe_data(
                    bezier_key_data, prop_label, anim_node, is_bezier=True
                )
            elif key_data:
                _convert_pykotor_keyframe_data(key_data, prop_label, anim_node, is_bezier=False)
            else:
                # Check for unkeyed value
                unkeyed_value = getattr(pk_animnode, prop_label, None)
                if unkeyed_value is not None:
                    # Convert unkeyed to keyframe at time 0
                    if isinstance(unkeyed_value, (int, float)):
                        anim_node.keyframes[prop_label] = [[0.0, float(unkeyed_value)]]
                    elif hasattr(unkeyed_value, "__iter__"):
                        anim_node.keyframes[prop_label] = [
                            [0.0] + [float(v) for v in unkeyed_value]
                        ]

        # Convert children
        children_pk = getattr(pk_animnode, "children", getattr(pk_animnode, "child_nodes", None))
        if children_pk and hasattr(children_pk, "__iter__"):
            for child_pk in children_pk:
                child_node = _convert_pykotor_animnode_to_scene(child_pk, anim_node, pykotor_mdl)
                if child_node:
                    anim_node.children.append(child_node)
                    if child_node.animated:
                        anim_node.animated = True

        # Mark as animated if it has keyframes
        if anim_node.keyframes:
            anim_node.animated = True

        return anim_node
    except Exception as e:
        logger().debug(f"PyKotor animation node conversion failed: {e}", exc_info=True)
        return None


def _convert_pykotor_controller_to_keyframes(ctrl_pk, anim_node: "AnimationNode") -> None:
    """Convert a PyKotor controller to AnimationNode keyframes."""
    try:
        # Extract controller type/property
        ctrl_type = getattr(ctrl_pk, "type", getattr(ctrl_pk, "controller_type", None))
        if isinstance(ctrl_type, bytes):
            ctrl_type = ctrl_type.decode("utf-8", errors="replace")
        if isinstance(ctrl_type, int):
            # Map integer controller type to property label
            type_map = {
                0: "position",
                1: "orientation",
                2: "scale",
                3: "alpha",
                4: "selfillumcolor",
                5: "color",
                6: "radius",
            }
            ctrl_type = type_map.get(ctrl_type, None)

        if not ctrl_type:
            return

        # Extract keyframe data
        key_data = getattr(
            ctrl_pk, "keyframes", getattr(ctrl_pk, "keys", getattr(ctrl_pk, "data", None))
        )
        if not key_data or not hasattr(key_data, "__iter__"):
            return

        is_bezier = getattr(ctrl_pk, "bezier", getattr(ctrl_pk, "is_bezier", False))
        _convert_pykotor_keyframe_data(key_data, ctrl_type, anim_node, is_bezier=is_bezier)
    except Exception as e:
        logger().debug(f"PyKotor controller conversion failed: {e}", exc_info=True)


def _convert_pykotor_keyframe_data(
    key_data, prop_label: str, anim_node: "AnimationNode", is_bezier: bool = False
) -> None:
    """Convert PyKotor keyframe data to AnimationNode keyframes format."""
    try:
        if not key_data or not hasattr(key_data, "__iter__"):
            return

        keyframes_list = []
        for kf in key_data:
            if not hasattr(kf, "__iter__"):
                continue

            # Extract time (first element)
            time = float(kf[0]) if len(kf) > 0 else 0.0

            # Extract values
            if is_bezier:
                # Bezier: [time, p1_vals..., p0_vals..., p2_vals...]
                # PyKotor might store as [time, ...values] where values are 3x dimension
                values = [float(v) for v in kf[1:]] if len(kf) > 1 else []
                keyframes_list.append([time] + values)
            else:
                # Linear: [time, ...values]
                values = [float(v) for v in kf[1:]] if len(kf) > 1 else []
                keyframes_list.append([time] + values)

        if keyframes_list:
            anim_node.keyframes[prop_label] = keyframes_list
    except Exception as e:
        logger().debug(
            f"PyKotor keyframe data conversion failed for {prop_label}: {e}", exc_info=True
        )


def convert_scene_model_to_pykotor(model: Model, options: ExportOptions) -> PyKotorMDL | None:
    """Convert an io_scene_kotor scene.Model to PyKotor MDL object.

    Converts scene representation to PyKotor MDL format, including:
    - Model header (name, classification, bounding box, etc.)
    - Node hierarchy (all node types)
    - Animations with keyframes
    - Materials and textures

    NOTE: This function is not used by io_scene_kotor.io.mdl.save_mdl().
    It is kept for potential future use or external callers.

    Args:
        model: io_scene_kotor Model object
        options: Export options (TSL, Xbox, quaternion compression)

    Returns:
        PyKotor MDL object, or None if conversion fails

    """
    if not PYKOTOR_AVAILABLE or model is None:
        return None

    try:
        # Try to create PyKotor MDL object
        # Note: PyKotor's MDL API may not support creating objects from scratch.
        # If creation fails, this function returns None and the caller will
        # fall back to the existing MdlWriter.
        pykotor_mdl = None
        try:
            # Try direct instantiation (may not be supported)
            pykotor_mdl = PyKotorMDL()  # pyright: ignore[reportPossiblyUnboundVariable]
        except (TypeError, AttributeError, Exception) as e:
            logger().debug(f"PyKotor MDL direct instantiation failed: {e.__class__.__name__}")
            # PyKotor may require reading from a file or using a different API
            # For now, return None to trigger fallback to existing writer
            return None

        if pykotor_mdl is None:
            return None

        # Convert MDL header properties
        _set_pykotor_attr(pykotor_mdl, "name", model.name)
        _set_pykotor_attr(pykotor_mdl, "model_name", model.name)
        _set_pykotor_attr(pykotor_mdl, "supermodel", model.supermodel)
        _set_pykotor_attr(pykotor_mdl, "super_model", model.supermodel)
        _set_pykotor_attr(
            pykotor_mdl,
            "classification",
            model.classification.value
            if hasattr(model.classification, "value")
            else str(model.classification),
        )
        _set_pykotor_attr(pykotor_mdl, "subclassification", model.subclassification)
        _set_pykotor_attr(pykotor_mdl, "classification_unk1", model.classification_unk1)
        _set_pykotor_attr(pykotor_mdl, "affected_by_fog", model.affected_by_fog)
        _set_pykotor_attr(pykotor_mdl, "animroot", model.animroot)
        _set_pykotor_attr(pykotor_mdl, "anim_root", model.animroot)
        _set_pykotor_attr(pykotor_mdl, "animscale", model.animscale)
        _set_pykotor_attr(pykotor_mdl, "anim_scale", model.animscale)
        _set_pykotor_attr(pykotor_mdl, "bounding_box_min", list(model.bounding_box_min))
        _set_pykotor_attr(pykotor_mdl, "bbox_min", list(model.bounding_box_min))
        _set_pykotor_attr(pykotor_mdl, "bounding_box_max", list(model.bounding_box_max))
        _set_pykotor_attr(pykotor_mdl, "bbox_max", list(model.bounding_box_max))
        _set_pykotor_attr(pykotor_mdl, "model_radius", model.model_radius)
        _set_pykotor_attr(pykotor_mdl, "radius", model.model_radius)

        # Convert root node
        if model.root_node:
            root_node_pk = _convert_scene_node_to_pykotor(model.root_node, None, options)
            if root_node_pk:
                _set_pykotor_attr(pykotor_mdl, "root", root_node_pk)
                _set_pykotor_attr(pykotor_mdl, "root_node", root_node_pk)

        # Convert animations
        if model.animations:
            animations_pk = []
            for anim in model.animations:
                anim_pk = _convert_scene_animation_to_pykotor(anim, model, options)
                if anim_pk:
                    animations_pk.append(anim_pk)
            if animations_pk:
                _set_pykotor_attr(pykotor_mdl, "animations", animations_pk)
                _set_pykotor_attr(pykotor_mdl, "animation_list", animations_pk)

        return pykotor_mdl
    except Exception as e:
        logger().debug(f"Scene model to PyKotor MDL conversion failed: {e}", exc_info=True)
        return None


def _set_pykotor_attr(obj, attr_name: str, value) -> None:
    """Safely set an attribute on a PyKotor object, handling various attribute names."""
    try:
        if hasattr(obj, attr_name):
            setattr(obj, attr_name, value)
    except (AttributeError, TypeError):
        # Attribute might be read-only or have a setter - ignore
        pass


def _convert_scene_node_to_pykotor(scene_node, parent, options: ExportOptions) -> Any:
    """Convert a scene BaseNode to PyKotor node.

    Args:
        scene_node: scene BaseNode or subclass
        parent: Parent PyKotor node or None
        options: Export options

    Returns:
        PyKotor node object, or None if conversion fails
    """
    if not PYKOTOR_AVAILABLE or scene_node is None:
        return None

    try:
        # Try to create PyKotor node object
        # PyKotor might have node classes or use a generic structure
        pk_node = None
        try:
            # Try to get node type from PyKotor
            from pykotor.resource.formats.mdl import MDLNode

            pk_node = MDLNode()
        except (ImportError, AttributeError, TypeError):
            # Fallback: create a dict-like object or use setattr
            class _PyKotorNode:
                pass

            pk_node = _PyKotorNode()

        if pk_node is None:
            return None

        # Set common node properties
        _set_pykotor_attr(pk_node, "name", scene_node.name)
        _set_pykotor_attr(pk_node, "node_name", scene_node.name)
        _set_pykotor_attr(pk_node, "node_number", scene_node.node_number)
        _set_pykotor_attr(pk_node, "node_id", scene_node.node_number)
        _set_pykotor_attr(pk_node, "position", list(scene_node.position))
        _set_pykotor_attr(pk_node, "pos", list(scene_node.position))
        _set_pykotor_attr(pk_node, "orientation", list(scene_node.orientation))
        _set_pykotor_attr(pk_node, "rotation", list(scene_node.orientation))
        _set_pykotor_attr(pk_node, "rot", list(scene_node.orientation))
        _set_pykotor_attr(pk_node, "scale", scene_node.scale)
        _set_pykotor_attr(pk_node, "scale_factor", scene_node.scale)

        # Set node type
        node_type_str = scene_node.nodetype
        _set_pykotor_attr(pk_node, "node_type", node_type_str)
        _set_pykotor_attr(pk_node, "type", node_type_str)

        # Convert node-specific properties
        if hasattr(scene_node, "refmodel"):
            # ReferenceNode
            _set_pykotor_attr(pk_node, "refmodel", scene_node.refmodel)
            _set_pykotor_attr(pk_node, "ref_model", scene_node.refmodel)
            _set_pykotor_attr(pk_node, "reattachable", scene_node.reattachable)
        elif hasattr(scene_node, "verts"):
            # TrimeshNode or subclass
            _convert_scene_trimesh_to_pykotor(scene_node, pk_node)
        elif hasattr(scene_node, "dummytype"):
            # DummyNode - no additional properties needed
            pass

        # Convert children
        if scene_node.children:
            children_pk = []
            for child in scene_node.children:
                child_pk = _convert_scene_node_to_pykotor(child, pk_node, options)
                if child_pk:
                    children_pk.append(child_pk)
            if children_pk:
                _set_pykotor_attr(pk_node, "children", children_pk)
                _set_pykotor_attr(pk_node, "child_nodes", children_pk)

        return pk_node
    except Exception as e:
        logger().debug(f"Scene node to PyKotor conversion failed: {e}", exc_info=True)
        return None


def _convert_scene_trimesh_to_pykotor(scene_node, pk_node) -> None:
    """Convert scene TrimeshNode geometry to PyKotor node."""
    try:
        # Convert vertices
        if scene_node.verts:
            _set_pykotor_attr(pk_node, "vertices", [list(v) for v in scene_node.verts])
            _set_pykotor_attr(pk_node, "verts", [list(v) for v in scene_node.verts])
            _set_pykotor_attr(pk_node, "vertex_data", [list(v) for v in scene_node.verts])

        # Convert UVs
        if scene_node.uv1:
            _set_pykotor_attr(pk_node, "uv1", [list(uv) for uv in scene_node.uv1])
            _set_pykotor_attr(pk_node, "uv", [list(uv) for uv in scene_node.uv1])
            _set_pykotor_attr(pk_node, "texture_coords", [list(uv) for uv in scene_node.uv1])
        if scene_node.uv2:
            _set_pykotor_attr(pk_node, "uv2", [list(uv) for uv in scene_node.uv2])
            _set_pykotor_attr(pk_node, "lightmap_uv", [list(uv) for uv in scene_node.uv2])

        # Convert normals
        if scene_node.normals:
            _set_pykotor_attr(pk_node, "normals", [list(n) for n in scene_node.normals])
            _set_pykotor_attr(pk_node, "normal_data", [list(n) for n in scene_node.normals])

        # Convert faces
        if scene_node.facelist and scene_node.facelist.vertices:
            faces = [list(face) for face in scene_node.facelist.vertices]
            _set_pykotor_attr(pk_node, "faces", faces)
            _set_pykotor_attr(pk_node, "indices", faces)
            _set_pykotor_attr(pk_node, "face_data", faces)

        # Convert material/texture
        if hasattr(scene_node, "bitmap") and scene_node.bitmap:
            material_obj = type(
                "Material", (), {"name": scene_node.bitmap, "texture_name": scene_node.bitmap}
            )()
            _set_pykotor_attr(pk_node, "material", material_obj)
            _set_pykotor_attr(pk_node, "texture", material_obj)

        # Convert bone weights (for SkinmeshNode)
        if hasattr(scene_node, "weights") and scene_node.weights:
            weights_list = []
            for vert_weights in scene_node.weights:
                weight_data = [[w[0], w[1]] for w in vert_weights] if vert_weights else []
                weights_list.append(weight_data)
            _set_pykotor_attr(pk_node, "weights", weights_list)
            _set_pykotor_attr(pk_node, "bone_weights", weights_list)

        # Convert constraints (for DanglymeshNode)
        if hasattr(scene_node, "constraints") and scene_node.constraints:
            _set_pykotor_attr(pk_node, "constraints", list(scene_node.constraints))
            _set_pykotor_attr(pk_node, "vertex_constraints", list(scene_node.constraints))
    except Exception as e:
        logger().debug(f"Scene trimesh to PyKotor conversion failed: {e}", exc_info=True)


def _convert_scene_animation_to_pykotor(anim, model: Model, options: ExportOptions) -> Any:
    """Convert scene.Animation to PyKotor animation."""
    try:
        # Try to create PyKotor animation object
        anim_pk = None
        try:
            from pykotor.resource.formats.mdl import MDLAnimation

            anim_pk = MDLAnimation()
        except (ImportError, AttributeError, TypeError):

            class _PyKotorAnimation:
                pass

            anim_pk = _PyKotorAnimation()

        if anim_pk is None:
            return None

        # Set animation properties
        _set_pykotor_attr(anim_pk, "name", anim.name)
        _set_pykotor_attr(anim_pk, "anim_name", anim.name)
        _set_pykotor_attr(anim_pk, "length", anim.length)
        _set_pykotor_attr(anim_pk, "duration", anim.length)
        _set_pykotor_attr(anim_pk, "transtime", anim.transtime)
        _set_pykotor_attr(anim_pk, "transition_time", anim.transtime)
        _set_pykotor_attr(anim_pk, "animroot", anim.animroot)
        _set_pykotor_attr(anim_pk, "anim_root", anim.animroot)

        # Convert events
        if anim.events:
            events_pk = []
            for time, name in anim.events:
                event_pk = type(
                    "Event", (), {"time": time, "timestamp": time, "name": name, "event_name": name}
                )()
                events_pk.append(event_pk)
            _set_pykotor_attr(anim_pk, "events", events_pk)
            _set_pykotor_attr(anim_pk, "event_list", events_pk)

        # Convert animation nodes
        if anim.root_node:
            root_anim_node_pk = _convert_scene_animnode_to_pykotor(
                anim.root_node, None, model, options
            )
            if root_anim_node_pk:
                _set_pykotor_attr(anim_pk, "root_node", root_anim_node_pk)
                _set_pykotor_attr(anim_pk, "root", root_anim_node_pk)

        return anim_pk
    except Exception as e:
        logger().debug(f"Scene animation to PyKotor conversion failed: {e}", exc_info=True)
        return None


def _convert_scene_animnode_to_pykotor(
    anim_node, parent, model: Model, options: ExportOptions
) -> Any:
    """Convert scene.AnimationNode to PyKotor animation node."""
    try:
        anim_node_pk = None
        try:
            from pykotor.resource.formats.mdl import MDLAnimationNode

            anim_node_pk = MDLAnimationNode()
        except (ImportError, AttributeError, TypeError):

            class _PyKotorAnimationNode:
                pass

            anim_node_pk = _PyKotorAnimationNode()

        if anim_node_pk is None:
            return None

        # Set node properties
        _set_pykotor_attr(anim_node_pk, "name", anim_node.name)
        _set_pykotor_attr(anim_node_pk, "node_name", anim_node.name)
        _set_pykotor_attr(anim_node_pk, "node_number", anim_node.node_number)
        _set_pykotor_attr(anim_node_pk, "node_id", anim_node.node_number)

        # Convert keyframes/controllers
        if anim_node.keyframes:
            controllers_pk = []
            for prop_label, keyframe_data in anim_node.keyframes.items():
                if not keyframe_data:
                    continue
                # Determine if bezier (values are 3x dimension)
                is_bezier = any(
                    len(kf) > 2 and len(kf[1:]) % 3 == 0 for kf in keyframe_data if len(kf) > 1
                )
                ctrl_pk = type(
                    "Controller",
                    (),
                    {
                        "type": prop_label,
                        "controller_type": prop_label,
                        "keyframes": keyframe_data,
                        "keys": keyframe_data,
                        "data": keyframe_data,
                        "bezier": is_bezier,
                        "is_bezier": is_bezier,
                    },
                )()
                controllers_pk.append(ctrl_pk)
            if controllers_pk:
                _set_pykotor_attr(anim_node_pk, "controllers", controllers_pk)
                _set_pykotor_attr(anim_node_pk, "keyframes", controllers_pk)

        # Convert children
        if anim_node.children:
            children_pk = []
            for child in anim_node.children:
                child_pk = _convert_scene_animnode_to_pykotor(child, anim_node_pk, model, options)
                if child_pk:
                    children_pk.append(child_pk)
            if children_pk:
                _set_pykotor_attr(anim_node_pk, "children", children_pk)
                _set_pykotor_attr(anim_node_pk, "child_nodes", children_pk)

        return anim_node_pk
    except Exception as e:
        logger().debug(f"Scene animation node to PyKotor conversion failed: {e}", exc_info=True)
        return None


def load_tpc_via_pykotor(filepath: str) -> PyKotorTPC | None:
    """Load a TPC file using PyKotor.

    Args:
        filepath: Path to the .tpc file

    Returns:
        PyKotor TPC object, or None if PyKotor is unavailable

    """
    if not PYKOTOR_AVAILABLE:
        return None

    try:
        return pykotor_read_tpc(filepath)  # pyright: ignore[reportPossiblyUnboundVariable]
    except Exception as e:
        logger().debug(f"PyKotor TPC read failed for {filepath}: {e}", exc_info=True)
        return None


def convert_pykotor_tpc_to_tpcimage(pykotor_tpc: PyKotorTPC) -> TpcImage | None:
    """Convert a PyKotor TPC object to io_scene_kotor TpcImage.

    Extracts width, height, pixel data (normalized to 0-1 RGBA), and TXI lines.
    Handles GRAYSCALE, RGB, RGBA encodings and uses top-level mipmap.

    Args:
        pykotor_tpc: PyKotor TPC object

    Returns:
        TpcImage object matching current TpcReader.load() output, or None if conversion fails

    """
    if not PYKOTOR_AVAILABLE or pykotor_tpc is None:
        return None

    try:
        from ..format.tpc.reader import TpcImage

        # Extract width and height (try multiple API patterns)
        width = getattr(pykotor_tpc, "width", None)
        height = getattr(pykotor_tpc, "height", None)
        if width is None or height is None:
            dims = getattr(pykotor_tpc, "dimensions", None)
            if dims and len(dims) >= 2:
                width, height = dims[0], dims[1]
            else:
                # Try mipmaps[0] if available
                mipmaps = getattr(pykotor_tpc, "mipmaps", None)
                if mipmaps and len(mipmaps) > 0:
                    mip0 = mipmaps[0]
                    width = getattr(mip0, "width", getattr(mip0, "w", None))
                    height = getattr(mip0, "height", getattr(mip0, "h", None))

        if width is None or height is None or width <= 0 or height <= 0:
            logger().debug("PyKotor TPC conversion: unable to determine width/height")
            return None

        # Get top-level mipmap pixel data
        pixels_raw = None
        mipmaps = getattr(pykotor_tpc, "mipmaps", None)
        if mipmaps and len(mipmaps) > 0:
            mip0 = mipmaps[0]
            pixels_raw = getattr(mip0, "pixels", getattr(mip0, "data", None))
            if pixels_raw is None and hasattr(mip0, "get_pixels"):
                pixels_raw = mip0.get_pixels()
        else:
            # Try direct pixel access on TPC object
            pixels_raw = getattr(pykotor_tpc, "pixels", getattr(pykotor_tpc, "data", None))
            if pixels_raw is None and hasattr(pykotor_tpc, "get_pixels"):
                pixels_raw = pykotor_tpc.get_pixels()  # type: ignore[attr-defined]

        if pixels_raw is None:
            logger().debug("PyKotor TPC conversion: unable to extract pixel data")
            return None

        # Convert pixel data to normalized RGBA floats (0-1 range)
        # PyKotor likely provides decompressed RGBA bytes or floats
        pixels_normalized: list[float] = []
        if isinstance(pixels_raw, (list, tuple)):
            # Check if already normalized (0-1 range)
            if len(pixels_raw) > 0:
                sample = pixels_raw[0]
                if isinstance(sample, float) and 0.0 <= sample <= 1.0:
                    # Already normalized, ensure RGBA format
                    pixel_count = width * height
                    expected_len = pixel_count * 4
                    if len(pixels_raw) == expected_len:
                        pixels_normalized = list(pixels_raw)
                    elif len(pixels_raw) == pixel_count * 3:
                        # RGB -> RGBA
                        for i in range(pixel_count):
                            idx = i * 3
                            pixels_normalized.extend(
                                [
                                    pixels_raw[idx],
                                    pixels_raw[idx + 1],
                                    pixels_raw[idx + 2],
                                    1.0,
                                ]
                            )
                    elif len(pixels_raw) == pixel_count:
                        # GRAYSCALE -> RGBA
                        for val in pixels_raw:
                            pixels_normalized.extend([val, val, val, 1.0])
                else:
                    # Byte data (0-255), normalize to 0-1
                    pixel_count = width * height
                    if len(pixels_raw) == pixel_count * 4:
                        # RGBA bytes
                        pixels_normalized = [p / 255.0 for p in pixels_raw]
                    elif len(pixels_raw) == pixel_count * 3:
                        # RGB bytes -> RGBA
                        for i in range(pixel_count):
                            idx = i * 3
                            pixels_normalized.extend(
                                [
                                    pixels_raw[idx] / 255.0,
                                    pixels_raw[idx + 1] / 255.0,
                                    pixels_raw[idx + 2] / 255.0,
                                    1.0,
                                ]
                            )
                    elif len(pixels_raw) == pixel_count:
                        # GRAYSCALE bytes -> RGBA
                        for val in pixels_raw:
                            norm = val / 255.0 if isinstance(val, (int, float)) else 0.0
                            pixels_normalized.extend([norm, norm, norm, 1.0])
        elif hasattr(pixels_raw, "__iter__"):
            # Try to convert iterable
            pixels_list = list(pixels_raw)
            if len(pixels_list) > 0:
                sample = pixels_list[0]
                if isinstance(sample, float) and 0.0 <= sample <= 1.0:
                    pixels_normalized = pixels_list
                else:
                    pixels_normalized = [
                        p / 255.0 if isinstance(p, (int, float)) else 0.0 for p in pixels_list
                    ]

        if not pixels_normalized:
            logger().debug("PyKotor TPC conversion: unable to normalize pixel data")
            return None

        # Extract TXI lines if present
        txi_lines: list[str] = []
        txi_data = getattr(pykotor_tpc, "txi", getattr(pykotor_tpc, "txi_data", None))
        if txi_data:
            if isinstance(txi_data, str):
                txi_lines = txi_data.splitlines()
            elif isinstance(txi_data, (list, tuple)):
                txi_lines = [str(line) for line in txi_data]
            elif isinstance(txi_data, bytes):
                txi_lines = txi_data.decode("utf-8", errors="replace").splitlines()

        tpc_image = TpcImage(width, height, pixels_normalized)
        tpc_image.txi_lines = txi_lines
        return tpc_image
    except Exception as e:
        logger().debug(f"PyKotor TPC conversion failed: {e}", exc_info=True)
        return None


def load_gff_via_pykotor(filepath: str) -> PyKotorGFF | None:
    """Load a GFF file using PyKotor.

    Args:
        filepath: Path to the GFF file

    Returns:
        PyKotor GFF object, or None if PyKotor is unavailable

    """
    if not PYKOTOR_AVAILABLE:
        return None

    try:
        return pykotor_read_gff(filepath)  # pyright: ignore[reportPossiblyUnboundVariable]
    except Exception as e:
        logger().debug(f"PyKotor GFF read failed for {filepath}: {e}", exc_info=True)
        return None


def save_gff_via_pykotor(gff: PyKotorGFF, filepath: str) -> bool:
    """Save a GFF file using PyKotor.

    Args:
        gff: PyKotor GFF object
        filepath: Path to save the GFF file

    Returns:
        True if successful, False otherwise

    """
    if not PYKOTOR_AVAILABLE:
        return False

    try:
        pykotor_write_gff(gff, filepath)  # pyright: ignore[reportPossiblyUnboundVariable]
        return True
    except Exception as e:
        logger().debug(f"PyKotor GFF write failed for {filepath}: {e}", exc_info=True)
        return False


def convert_pykotor_gff_to_tree(pykotor_gff: PyKotorGFF) -> dict | None:
    """
    Convert a PyKotor GFF object to io_scene_kotor dict tree format.

    Converts PyKotor's GFF structure to the dict format used by GffReader.load():
    - Root dict has `_type` (struct type) and `_fields` (field name -> type mapping)
    - Field values are keys in the dict
    - Nested structs are dicts with `_type` and `_fields`
    - Lists are Python lists of dict structs

    Args:
        pykotor_gff: PyKotor GFF object

    Returns:
        Dict tree matching GffReader.load() output, or None if conversion fails
    """
    if not PYKOTOR_AVAILABLE or pykotor_gff is None:
        return None

    try:
        from ..format.gff.types import FIELD_TYPE_DWORD, FIELD_TYPE_FLOAT, FIELD_TYPE_LIST, FIELD_TYPE_STRUCT

        def convert_struct(pk_struct) -> dict:
            """Convert a PyKotor struct to dict format."""
            tree: dict = {}
            struct_type = getattr(
                pk_struct,
                "struct_id",
                getattr(pk_struct, "type_id", getattr(pk_struct, "type", 0xFFFFFFFF)),
            )
            fields_dict: dict[str, int] = {}
            tree["_type"] = struct_type

            # Get fields from PyKotor struct
            fields = getattr(pk_struct, "fields", getattr(pk_struct, "field_list", None))
            if fields is None:
                # Try accessing fields as attributes or dict
                if hasattr(pk_struct, "__dict__"):
                    fields = pk_struct.__dict__
                elif hasattr(pk_struct, "get_fields"):
                    fields = pk_struct.get_fields()  # type: ignore[attr-defined]
                else:
                    fields = []

            if isinstance(fields, dict):
                # Fields are a dict: field_name -> field_value
                for field_name, field_value in fields.items():
                    if field_name.startswith("_"):
                        continue
                    field_type = _infer_gff_field_type(field_value)
                    fields_dict[field_name] = field_type
                    tree[field_name] = _convert_field_value(field_value, field_type)
            elif hasattr(fields, "__iter__"):
                # Fields are iterable (list or similar)
                for field in fields:
                    field_name = getattr(
                        field, "label", getattr(field, "name", getattr(field, "key", None))
                    )
                    field_value = getattr(field, "value", getattr(field, "data", field))
                    field_type = getattr(
                        field,
                        "type",
                        getattr(field, "field_type", _infer_gff_field_type(field_value)),
                    )
                    if field_name:
                        fields_dict[field_name] = field_type
                        tree[field_name] = _convert_field_value(field_value, field_type)

            tree["_fields"] = fields_dict
            return tree

        def _infer_gff_field_type(value) -> int:
            """Infer GFF field type from Python value."""
            if isinstance(value, int):
                return FIELD_TYPE_DWORD
            elif isinstance(value, float):
                return FIELD_TYPE_FLOAT
            elif isinstance(value, dict):
                return FIELD_TYPE_STRUCT
            elif isinstance(value, list):
                return FIELD_TYPE_LIST
            elif isinstance(value, str):
                # String fields - PyKotor may use different type constants
                return FIELD_TYPE_DWORD  # Default fallback
            return FIELD_TYPE_DWORD

        def _convert_field_value(value, field_type: int):
            """Convert a field value based on its type."""
            if field_type == FIELD_TYPE_DWORD:
                return int(value) if value is not None else 0
            elif field_type == FIELD_TYPE_FLOAT:
                return float(value) if value is not None else 0.0
            elif field_type == FIELD_TYPE_STRUCT:
                if isinstance(value, dict):
                    # Already a dict, ensure it has _type and _fields
                    if "_type" not in value:
                        value["_type"] = 0xFFFFFFFF
                    if "_fields" not in value:
                        value["_fields"] = {}
                    return value
                else:
                    # PyKotor struct object
                    return convert_struct(value)
            elif field_type == FIELD_TYPE_LIST:
                if isinstance(value, list):
                    return [
                        convert_struct(item) if not isinstance(item, dict) else item
                        for item in value
                    ]
                return []
            return value

        # Get root struct from PyKotor GFF
        root = getattr(pykotor_gff, "root", getattr(pykotor_gff, "root_struct", None))
        if root is None:
            # Try accessing as dict or direct struct
            if isinstance(pykotor_gff, dict):
                root = pykotor_gff
            else:
                logger().debug("PyKotor GFF conversion: unable to find root struct")
                return None

        return convert_struct(root) if not isinstance(root, dict) else root
    except Exception as e:
        logger().debug(f"PyKotor GFF conversion failed: {e}", exc_info=True)
        return None


def convert_tree_to_pykotor_gff(tree: dict, file_type: str) -> PyKotorGFF | None:
    """
    Convert an io_scene_kotor dict tree to PyKotor GFF object.

    Converts the dict format from GffReader.load() to PyKotor's GFF structure.
    Callers (e.g. io/pth.py save_pth, ops/resource/new_gff.py) fall back to the
    native GFF writer when this returns None.

    Args:
        tree: Dict tree matching GffReader.load() output
        file_type: GFF file type (e.g., "PTH")

    Returns:
        PyKotor GFF object, or None to use native writer fallback
    """
    if not PYKOTOR_AVAILABLE or tree is None:
        return None

    try:
        # PyKotor GFF build from dict would require: root struct creation,
        # dict fields -> PyKotor field objects, nested structs/lists, file_type.
        # Until then, return None so callers use the native format/gff writer.
        return None
    except Exception as e:
        logger().debug(f"PyKotor GFF tree conversion failed: {e}", exc_info=True)
        return None


def find_kotor_paths_from_default() -> dict[str, str]:
    """Discover KotOR 1 and KotOR 2 install dirs: PyKotor APIs, then registry/Steam heuristics.

    Logs extensively at INFO/DEBUG under logger ``io_scene_kotor.game_install`` — set
    **Add-on Preferences → Logging verbosity** to **Debug** for full candidate traces.
    """
    from ..game_install_detect import (
        first_valid_k1,
        first_valid_k2,
        is_probable_kotor1_install,
        is_probable_kotor2_install,
        log_install_discovery_summary,
    )
    from ..log_config import get_kb_logger

    log = get_kb_logger("game_install")
    result: dict[str, str] = {GameType.KOTOR1: "", GameType.KOTOR2: ""}

    if PYKOTOR_AVAILABLE:
        try:
            from pykotor.extract import installation as inst_mod

            log.debug("PyKotor installation module: %s", getattr(inst_mod, "__file__", inst_mod))
            finder = getattr(inst_mod, "find_kotor_paths_from_default", None)
            log.debug("find_kotor_paths_from_default present: %s", callable(finder))
            if callable(finder):
                paths = finder()
                log.info("PyKotor find_kotor_paths_from_default() returned: %r", paths)
                if isinstance(paths, dict):
                    result[GameType.KOTOR1] = (
                        str(
                            paths.get(GameType.KOTOR1)
                            or paths.get("KOTOR1")
                            or paths.get("kotor1")
                            or ""
                        ).strip()
                    )
                    result[GameType.KOTOR2] = (
                        str(
                            paths.get(GameType.KOTOR2)
                            or paths.get("KOTOR2")
                            or paths.get("kotor2")
                            or ""
                        ).strip()
                    )
                elif isinstance(paths, (list, tuple)):
                    if len(paths) >= 1 and paths[0]:
                        result[GameType.KOTOR1] = str(paths[0]).strip()
                    if len(paths) >= 2 and paths[1]:
                        result[GameType.KOTOR2] = str(paths[1]).strip()
            if not result[GameType.KOTOR1] or not result[GameType.KOTOR2]:
                find_alt = getattr(inst_mod, "find_paths", None) or getattr(
                    inst_mod,
                    "find_installations",
                    None,
                )
                if callable(find_alt):
                    log.debug("Trying PyKotor alternate: %s", find_alt.__name__)
                    found = find_alt()
                    log.info("PyKotor %s() -> %r", find_alt.__name__, found)
                    if isinstance(found, dict):
                        if not result[GameType.KOTOR1]:
                            result[GameType.KOTOR1] = str(
                                found.get(GameType.KOTOR1) or found.get("kotor1") or ""
                            ).strip()
                        if not result[GameType.KOTOR2]:
                            result[GameType.KOTOR2] = str(
                                found.get(GameType.KOTOR2) or found.get("kotor2") or ""
                            ).strip()
        except Exception:
            log.exception("PyKotor installation discovery raised")

    for gt, path in list(result.items()):
        if not path:
            continue
        if not os.path.isdir(path):
            log.warning("Discarding non-directory path for %s: %s", gt, path)
            result[gt] = ""
            continue
        if gt == GameType.KOTOR1 and not is_probable_kotor1_install(path):
            log.warning("PyKotor K1 path failed validation (trying native fallbacks): %s", path)
            result[gt] = ""
        elif gt == GameType.KOTOR2 and not is_probable_kotor2_install(path):
            log.warning("PyKotor K2 path failed validation (trying native fallbacks): %s", path)
            result[gt] = ""

    if not result[GameType.KOTOR1]:
        n1 = first_valid_k1(log)
        if n1:
            result[GameType.KOTOR1] = os.path.normpath(n1)
            log.info("Native heuristic selected KOTOR1: %s", result[GameType.KOTOR1])
        else:
            log.warning("No KotOR 1 installation found (PyKotor + registry/Steam scan)")

    if not result[GameType.KOTOR2]:
        n2 = first_valid_k2(log)
        if n2:
            result[GameType.KOTOR2] = os.path.normpath(n2)
            log.info("Native heuristic selected KOTOR2: %s", result[GameType.KOTOR2])
        else:
            log.warning("No KotOR 2 installation found (PyKotor + registry/Steam scan)")

    if not result[GameType.KOTOR1] or not result[GameType.KOTOR2]:
        log_install_discovery_summary(
            log,
            k1_found=bool(result[GameType.KOTOR1]),
            k2_found=bool(result[GameType.KOTOR2]),
        )

    return result


def resolve_game_install_path(kb: Any) -> str | None:
    """Resolve KotOR installation directory from scene ``kb`` (ScenePropertyGroup)."""
    if kb is None:
        return None
    if kb.game_type == GameType.CUSTOM:
        install_path = kb.game_installation_path or ""
    else:
        install_path = kb.game_installation_path or ""
        if not install_path or not os.path.exists(install_path):
            paths = find_kotor_paths_from_default()
            install_path = paths.get(kb.game_type, "") or ""
    if install_path and os.path.isdir(install_path):
        return os.path.normpath(install_path)
    return None


def _restype_extension(restype: Any) -> str:
    try:
        ext = getattr(restype, "extension", None)
        if ext:
            return str(ext).lstrip(".").lower()
    except Exception:
        pass
    name = getattr(restype, "name", None)
    if name is not None:
        return str(name).lower()
    return "dat"


def list_erf_mod_resources(mod_path: str) -> list[tuple[str, str, bytes]]:
    """List resources inside a .mod/.erf file: (resref, extension, data)."""
    if not PYKOTOR_AVAILABLE:
        return []
    try:
        from pykotor.resource.formats.erf import read_erf

        erf = read_erf(mod_path)
        out: list[tuple[str, str, bytes]] = []
        for res in erf:
            rr = str(res.resref)
            ext = _restype_extension(res.restype)
            out.append((rr, ext, bytes(res.data)))
        return out
    except Exception as e:
        logger().debug(f"list_erf_mod_resources failed: {e}", exc_info=True)
        return []


def get_erf_resource_bytes(erf_path: str, resref: str, restype_ext: str) -> bytes | None:
    """Read one resource from an ERF/MOD by resref and extension (e.g. ``mdl``)."""
    if not PYKOTOR_AVAILABLE:
        return None
    try:
        from pykotor.resource.formats.erf import read_erf
        from pykotor.resource.type import ResourceType

        erf = read_erf(erf_path)
        ext = restype_ext.strip().lower().lstrip(".")
        dot = "." + ext if ext else ".mdl"
        rt = ResourceType.from_extension(dot)
        return erf.get(resref, rt)
    except Exception as e:
        logger().debug(f"get_erf_resource_bytes failed: {e}", exc_info=True)
        return None


def try_list_bif_resources(bif_path: str) -> list[tuple[str, str]]:
    """Return ``(resref, ext)`` entries if PyKotor can read the BIF."""
    if not PYKOTOR_AVAILABLE:
        return []
    try:
        from pykotor.resource.formats.bif import read_bif

        bif = read_bif(bif_path)
        return [(str(r.resref), _restype_extension(r.restype)) for r in bif]
    except Exception as e:
        logger().debug(f"try_list_bif_resources failed: {e}", exc_info=True)
        return []


def get_bif_resource_bytes(bif_path: str, resref: str, restype_ext: str) -> bytes | None:
    """Read one resource from a BIF by resref and extension (e.g. ``tpc``)."""
    if not PYKOTOR_AVAILABLE:
        return None
    try:
        from pykotor.resource.formats.bif import read_bif
        from pykotor.resource.type import ResourceType

        bif = read_bif(bif_path)
        ext = restype_ext.strip().lower().lstrip(".")
        dot = "." + ext if ext else ".mdl"
        rt = ResourceType.from_extension(dot)
        data = bif.get(resref, rt)
        return bytes(data) if data is not None else None
    except Exception as e:
        logger().debug(f"get_bif_resource_bytes failed: {e}", exc_info=True)
        return None


def twoda_to_tsv_string(twoda: Any) -> str:
    """Serialize PyKotor TwoDA to tab-separated text (row label in first column)."""
    headers = twoda.get_headers()
    lines: list[str] = ["\t".join([""] + list(headers))]
    for i in range(twoda.get_height()):
        row = twoda.get_row(i)
        lab = row.label()
        cells = [row.get_string(h) for h in headers]
        lines.append("\t".join([lab] + cells))
    return "\n".join(lines)


def twoda_from_tsv_string(text: str) -> Any | None:
    """Build PyKotor TwoDA from TSV (first column = row labels, header row = column names)."""
    if not PYKOTOR_AVAILABLE:
        return None
    try:
        from pykotor.resource.formats.twoda import TwoDA

        lines = [ln for ln in text.replace("\r\n", "\n").split("\n") if ln.strip()]
        if not lines:
            return None
        parts0 = lines[0].split("\t")
        if len(parts0) < 2:
            return None
        headers = [h.strip() for h in parts0[1:] if h.strip()]
        if not headers:
            return None
        td = TwoDA(headers)
        for ln in lines[1:]:
            cols = ln.split("\t")
            lab = (cols[0] or "").strip() if cols else ""
            cells: dict[str, str] = {}
            for hi, h in enumerate(headers):
                idx = hi + 1
                cells[h] = cols[idx].strip() if idx < len(cols) else ""
            td.add_row(lab or None, cells)
        return td
    except Exception as e:
        logger().debug(f"twoda_from_tsv_string failed: {e}", exc_info=True)
        return None


def load_twoda_file(path: str) -> Any | None:
    if not PYKOTOR_AVAILABLE:
        return None
    try:
        from pykotor.resource.formats.twoda import read_2da

        return read_2da(path)
    except Exception as e:
        logger().debug(f"load_twoda_file failed: {e}", exc_info=True)
        return None


def save_twoda_file(twoda: Any, path: str) -> bool:
    if not PYKOTOR_AVAILABLE or twoda is None:
        return False
    try:
        from pykotor.resource.formats.twoda import write_2da

        write_2da(twoda, path)
        return True
    except Exception as e:
        logger().debug(f"save_twoda_file failed: {e}", exc_info=True)
        return False


def load_vis_visibility_pairs(path: str) -> list[tuple[str, str]]:
    """Load VIS as (observer_room, visible_room) pairs using PyKotor."""
    if not PYKOTOR_AVAILABLE:
        return []
    try:
        from pykotor.resource.formats.vis import read_vis

        vis = read_vis(path)
        pairs: list[tuple[str, str]] = []
        for observer, observed_set in vis:
            for show in observed_set:
                pairs.append((observer, show))
        return pairs
    except Exception as e:
        logger().debug(f"load_vis_visibility_pairs failed: {e}", exc_info=True)
        return []


def save_vis_visibility_pairs(pairs: list[tuple[str, str]], path: str) -> bool:
    """Write VIS from (observer, visible) pairs using PyKotor."""
    if not PYKOTOR_AVAILABLE or not pairs:
        return False
    try:
        from pykotor.resource.formats.vis import write_vis
        from pykotor.resource.formats.vis.vis_data import VIS

        vis = VIS()
        for a, b in pairs:
            aa, bb = a.lower(), b.lower()
            vis.add_room(aa)
            vis.add_room(bb)
        for a, b in pairs:
            vis.set_visible(a, b, visible=True)
        write_vis(vis, path)
        return True
    except Exception as e:
        logger().debug(f"save_vis_visibility_pairs failed: {e}", exc_info=True)
        return False


def discover_game_installation(path: str) -> SearchLocation | None:
    """Discover a KotOR game installation using PyKotor.

    Args:
        path: Path to the game installation directory

    Returns:
        PyKotor SearchLocation, or None if not found or PyKotor unavailable

    """
    if not PYKOTOR_AVAILABLE:
        return None

    try:
        # Optional: use PyKotor installation discovery (chitin.key, dialog.tlk, etc.)
        # to return a SearchLocation. Until then, return None.
        if os.path.exists(os.path.join(path, "chitin.key")):
            # Return appropriate SearchLocation when PyKotor API is wired
            pass
        return None
    except Exception as e:
        logger().debug(f"PyKotor discover_game_installation failed for {path}: {e}", exc_info=True)
        return None
