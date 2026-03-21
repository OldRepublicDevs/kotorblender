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

import math
from typing import TYPE_CHECKING, Sequence, cast

import bpy
from bpy_extras.io_utils import unpack_list
from mathutils import Vector

from ...constants import NULL, UV_MAP_LIGHTMAP, UV_MAP_MAIN, Compression, ExportOptions, ImportOptions, MeshType, NodeType, RootType
from ...utils import is_not_null
from .base import BaseNode

if TYPE_CHECKING:
    from bpy.types import Armature, Camera, Curve, Curves, GreasePencil, Lattice, Light, LightProbe, Mesh, MetaBall, PointCloud, Speaker, SurfaceCurve, TextCurve, Volume

    from ...ui.props.object import ObjectPropertyGroup


class FaceList:
    def __init__(self) -> None:
        self.vertices: list[tuple[int, int, int]] = []  # vertex indices
        self.uv: list[tuple[int, int, int]] = []  # UV indices
        self.materials: list[int] = []
        self.normals: list[tuple[float, float, float]] = []


class EdgeLoopMesh:
    def __init__(self) -> None:
        self.verts: list[tuple[float, float, float]] = []  # vertex coordinates
        self.weights: list[list[tuple[str, float]]] = []  # vertex bone weights
        self.constraints: list[float] = []  # vertex constraints (danglymesh)

        self.loop_verts: list[int] = []  # vertex indices
        self.loop_normals: list[tuple[float, float, float]] = []
        self.loop_uv1: list[tuple[float, float]] = []  # diffuse texture coordinates
        self.loop_uv2: list[tuple[float, float]] = []  # lightmap texture coordinates
        self.loop_tangents: list[tuple[float, float, float]] = []
        self.loop_bitangents: list[tuple[float, float, float]] = []

        self.face_materials: list[int] = []
        self.face_normals: list[tuple[float, float, float]] = []

    def num_faces(self) -> int:
        return self.num_loops() // 3

    def num_loops(self) -> int:
        return len(self.loop_verts)

    def num_verts(self) -> int:
        return len(self.verts)


def _quantize(val: float) -> int:
    """Quantize float for hashing; treat NaN as 0."""
    return 0 if math.isnan(val) else int(val * 10000)


class SimilarMdlVertex:
    def __init__(self, coords: tuple[float, float, float]) -> None:
        self.coords: tuple[float, float, float] = coords
        self.value: tuple[int, int, int] = cast("tuple[int, int, int]", tuple(_quantize(val) for val in self.coords))

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, rhs: object) -> bool:
        if not isinstance(rhs, SimilarMdlVertex):
            return NotImplemented
        return self.value == rhs.value


class SimilarEdgeLoopMeshVertex:
    def __init__(
        self,
        coords: tuple[float, float, float],
        normal: tuple[float, float, float],
        uv1: tuple[float, float],
        uv2: tuple[float, float],
    ) -> None:
        self.coords: tuple[float, float, float] = coords
        self.normal: tuple[float, float, float] = normal
        self.uv1: tuple[float, float] = uv1
        self.uv2: tuple[float, float] = uv2
        self.value: tuple[int, ...] = tuple(_quantize(val) for val in (*self.coords, *self.normal, *self.uv1, *self.uv2))

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, rhs: object) -> bool:
        if not isinstance(rhs, SimilarEdgeLoopMeshVertex):
            return NotImplemented
        return self.value == rhs.value


class TrimeshNode(BaseNode):
    def __init__(self, name: str = "UNNAMED") -> None:
        BaseNode.__init__(self, name)
        self.nodetype: NodeType = NodeType.TRIMESH
        self.compression: Compression = Compression.ENABLED

        # Properties
        self.meshtype: MeshType = MeshType.TRIMESH
        self.center: tuple[float, float, float] = (0.0, 0.0, 0.0)  # Unused ?
        self.lightmapped: int = 0
        self.render: int = 1
        self.shadow: int = 1
        self.beaming: int = 0
        self.background_geometry: int = 0
        self.dirt_enabled: int = 0
        self.dirt_texture: int = 1
        self.dirt_worldspace: int = 1
        self.hologram_donotdraw: int = 0
        self.animateuv: int = 0
        self.uvdirectionx: float = 1.0
        self.uvdirectiony: float = 1.0
        self.uvjitter: float = 0.0
        self.uvjitterspeed: float = 0.0
        self.alpha: float = 1.0
        self.transparencyhint: int = 0
        self.selfillumcolor: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.ambient: tuple[float, float, float] = (0.2, 0.2, 0.2)
        self.diffuse: tuple[float, float, float] = (0.8, 0.8, 0.8)
        self.bitmap: str = NULL
        self.bitmap2: str = NULL
        self.tangentspace: int = 0
        self.rotatetexture: int = 0

        # Mesh
        self.verts: list[tuple[float, float, float]] = []
        self.normals: list[tuple[float, float, float]] = []
        self.uv1: list[tuple[float, float]] = []
        self.uv2: list[tuple[float, float]] = []
        self.tangents: list[tuple[float, float, float]] = []
        self.bitangents: list[tuple[float, float, float]] = []
        self.tangentspacenormals: list[tuple[float, float, float]] = []
        self.weights: list[list[tuple[str, float]]] = []
        self.constraints: list[float] = []
        self.facelist: FaceList = FaceList()

    def add_to_collection(
        self,
        collection: bpy.types.Collection,
        options: ImportOptions,
    ) -> bpy.types.Object:
        mesh = self.mdl_to_edge_loop_mesh()
        bl_mesh = self.create_blender_mesh(self.name, mesh)
        obj = bpy.data.objects.new(self.name, bl_mesh)
        self.apply_edge_loop_mesh(mesh, obj)
        self.set_object_data(obj, options)
        if options.build_materials and self.roottype == RootType.MODEL:
            from .. import material

            material.rebuild_object_materials(
                obj,
                options.texture_search_paths,
                options.lightmap_search_paths,
            )
        collection.objects.link(obj)
        return obj

    def mdl_to_edge_loop_mesh(self) -> EdgeLoopMesh:
        num_faces: int = len(self.facelist.vertices)
        num_loops: int = 3 * num_faces
        mesh: EdgeLoopMesh = EdgeLoopMesh()
        mesh.loop_verts = [-1] * num_loops
        mesh.loop_normals = [(0, 0, 0)] * num_loops
        mesh.loop_uv1 = [(0, 0)] * num_loops if self.uv1 else []
        mesh.loop_uv2 = [(0, 0)] * num_loops if self.uv2 else []
        if self.compression != Compression.DISABLED:
            attrs_to_vert_idx: dict[SimilarMdlVertex, int] = cast("dict[SimilarMdlVertex, int]", dict())
            for face_idx in range(num_faces):
                face_verts: tuple[int, int, int] = self.facelist.vertices[face_idx]
                uniq_loop_verts: set[int] = set()
                for i in range(3):
                    loop_idx: int = 3 * face_idx + i
                    vert_idx: int = face_verts[i]
                    vert: tuple[float, float, float] = self.verts[vert_idx]
                    attrs = SimilarMdlVertex(vert)
                    if attrs in attrs_to_vert_idx and (attrs_to_vert_idx[attrs] not in uniq_loop_verts):
                        uniq_loop_verts.add(attrs_to_vert_idx[attrs])
                        mesh.loop_verts[loop_idx] = attrs_to_vert_idx[attrs]
                    else:
                        num_verts = len(mesh.verts)
                        mesh.verts.append(vert)
                        if self.weights:
                            mesh.weights.append(self.weights[vert_idx])
                        if self.constraints:
                            mesh.constraints.append(self.constraints[vert_idx])
                        if attrs not in attrs_to_vert_idx:
                            attrs_to_vert_idx[attrs] = num_verts
                        uniq_loop_verts.add(num_verts)
                        mesh.loop_verts[loop_idx] = num_verts
                    if self.normals:
                        mesh.loop_normals[loop_idx] = self.normals[vert_idx]
                    if self.uv1:
                        mesh.loop_uv1[loop_idx] = self.uv1[vert_idx]
                    if self.uv2:
                        mesh.loop_uv2[loop_idx] = self.uv2[vert_idx]
                    if self.tangents and self.bitangents:
                        mesh.loop_tangents[loop_idx] = self.tangents[vert_idx]
                        mesh.loop_bitangents[loop_idx] = self.bitangents[vert_idx]
        else:
            mesh.verts = self.verts
            mesh.weights = self.weights
            mesh.constraints = self.constraints
            for face_idx in range(num_faces):
                face_verts = self.facelist.vertices[face_idx]
                for i in range(3):
                    loop_idx = 3 * face_idx + i
                    vert_idx = face_verts[i]
                    mesh.loop_verts[loop_idx] = vert_idx
                    if self.normals:
                        mesh.loop_normals[loop_idx] = self.normals[vert_idx]
                    if self.uv1:
                        mesh.loop_uv1[loop_idx] = self.uv1[vert_idx]
                    if self.uv2:
                        mesh.loop_uv2[loop_idx] = self.uv2[vert_idx]
                    if self.tangents and self.bitangents:
                        mesh.loop_tangents[loop_idx] = self.tangents[vert_idx]
                        mesh.loop_bitangents[loop_idx] = self.bitangents[vert_idx]
        mesh.face_materials = self.facelist.materials
        mesh.face_normals = self.facelist.normals
        return mesh

    def create_blender_mesh(self, name: str, mesh: EdgeLoopMesh) -> bpy.types.Mesh:
        bl_mesh: bpy.types.Mesh = bpy.data.meshes.new(name)
        bl_mesh.vertices.add(mesh.num_verts())
        bl_mesh.vertices.foreach_set("co", unpack_list(mesh.verts))
        bl_mesh.loops.add(mesh.num_loops())
        bl_mesh.loops.foreach_set("vertex_index", mesh.loop_verts)
        bl_mesh.polygons.add(mesh.num_faces())
        bl_mesh.polygons.foreach_set("loop_start", range(0, mesh.num_loops(), 3))
        bl_mesh.polygons.foreach_set("loop_total", [3] * mesh.num_faces())
        bl_mesh.polygons.foreach_set("use_smooth", [True] * mesh.num_faces())
        bl_mesh.update()
        if mesh.loop_normals:
            bl_mesh.normals_split_custom_set(mesh.loop_normals)
            if bpy.app.version < (4, 1):
                bl_mesh.use_auto_smooth = True  # pyright: ignore[reportAttributeAccessIssue]
        if mesh.loop_uv1:
            uv_layer: bpy.types.MeshUVLoopLayer = bl_mesh.uv_layers.new(name=UV_MAP_MAIN, do_init=False)
            uv_layer.data.foreach_set("uv", unpack_list(mesh.loop_uv1))
        if mesh.loop_uv2:
            uv_layer = bl_mesh.uv_layers.new(name=UV_MAP_LIGHTMAP, do_init=False)
            uv_layer.data.foreach_set("uv", unpack_list(mesh.loop_uv2))
        return bl_mesh

    def apply_edge_loop_mesh(self, mesh: EdgeLoopMesh, obj: bpy.types.Object) -> None:
        pass

    def set_object_data(self, obj: bpy.types.Object, options: ImportOptions) -> None:
        BaseNode.set_object_data(self, obj, options)

        kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError(f"Object [{obj.name}] has no kb attribute")
        kb.meshtype = self.meshtype
        kb.bitmap = self.bitmap if is_not_null(self.bitmap) else ""
        kb.bitmap2 = self.bitmap2 if is_not_null(self.bitmap2) else ""
        kb.alpha = self.alpha
        kb.lightmapped = self.lightmapped == 1
        kb.render = self.render == 1
        kb.shadow = self.shadow == 1
        kb.beaming = self.beaming == 1
        kb.tangentspace = self.tangentspace == 1
        kb.rotatetexture = self.rotatetexture == 1
        kb.background_geometry = self.background_geometry == 1
        kb.dirt_enabled = self.dirt_enabled == 1
        kb.dirt_texture = self.dirt_texture
        kb.dirt_worldspace = self.dirt_worldspace
        kb.hologram_donotdraw = self.hologram_donotdraw == 1
        kb.animateuv = self.animateuv == 1
        kb.uvdirectionx = self.uvdirectionx
        kb.uvdirectiony = self.uvdirectiony
        kb.uvjitter = self.uvjitter
        kb.uvjitterspeed = self.uvjitterspeed
        kb.transparencyhint = self.transparencyhint
        kb.selfillumcolor = self.selfillumcolor
        kb.diffuse = self.diffuse
        kb.ambient = self.ambient

    def load_object_data(
        self,
        obj: bpy.types.Object,
        eval_obj: bpy.types.Object,
        options: ImportOptions | ExportOptions,
    ) -> None:
        BaseNode.load_object_data(self, obj, eval_obj, options)

        kb: ObjectPropertyGroup | None = getattr(obj, "kb", None)
        if kb is None:
            raise ValueError(f"Object [{obj.name}] has no kb attribute")
        self.meshtype = kb.meshtype
        self.bitmap = kb.bitmap if kb.bitmap else NULL
        self.bitmap2 = kb.bitmap2 if kb.bitmap2 else ""
        self.alpha = kb.alpha
        self.lightmapped = 1 if kb.lightmapped else 0
        self.render = 1 if kb.render else 0
        self.shadow = 1 if kb.shadow else 0
        self.beaming = 1 if kb.beaming else 0
        self.tangentspace = 1 if kb.tangentspace else 0
        self.rotatetexture = 1 if kb.rotatetexture else 0
        self.background_geometry = 1 if kb.background_geometry else 0
        self.dirt_enabled = 1 if kb.dirt_enabled else 0
        self.dirt_texture = kb.dirt_texture
        self.dirt_worldspace = kb.dirt_worldspace
        self.hologram_donotdraw = 1 if kb.hologram_donotdraw else 0
        self.animateuv = 1 if kb.animateuv else 0
        self.uvdirectionx = kb.uvdirectionx
        self.uvdirectiony = kb.uvdirectiony
        self.uvjitter = kb.uvjitter
        self.uvjitterspeed = kb.uvjitterspeed
        self.transparencyhint = kb.transparencyhint
        self.selfillumcolor = kb.selfillumcolor
        self.diffuse = kb.diffuse
        self.ambient = kb.ambient

        mesh = self.unapply_edge_loop_mesh(eval_obj)
        self.edge_loop_to_mdl_mesh(mesh)

    def unapply_edge_loop_mesh(self, obj: bpy.types.Object) -> EdgeLoopMesh:
        bl_mesh: (
            Armature
            | Camera
            | Curve
            | Curves
            | GreasePencil
            | Lattice
            | Light
            | LightProbe
            | Mesh
            | MetaBall
            | PointCloud
            | Speaker
            | SurfaceCurve
            | TextCurve
            | Volume
            | bpy.types.Mesh
            | None
        ) = obj.data
        assert bl_mesh is not None, "Object data is None"
        assert isinstance(bl_mesh, bpy.types.Mesh), "Object data is not a mesh"
        bl_mesh.calc_loop_triangles()
        if bpy.app.version < (4, 1):
            bl_mesh.calc_normals_split()  # pyright: ignore[reportAttributeAccessIssue]
        if self.tangentspace and bl_mesh.uv_layers:
            bl_mesh.calc_tangents(uvmap=bl_mesh.uv_layers[0].name)
        mesh = EdgeLoopMesh()
        for vert in bl_mesh.vertices:
            mesh.verts.append(cast("tuple[float, float, float]", vert.co[:3]))
        for face in bl_mesh.loop_triangles:
            for i in range(3):
                mesh.loop_verts.append(face.vertices[i])
                mesh.loop_normals.append(cast("tuple[float, float, float]", face.split_normals[i]))
                loop_idx = face.loops[i]
                if UV_MAP_MAIN in bl_mesh.uv_layers:
                    mesh.loop_uv1.append(cast("tuple[float, float]", bl_mesh.uv_layers[UV_MAP_MAIN].data[loop_idx].uv[:2]))
                if self.lightmapped:
                    if UV_MAP_LIGHTMAP not in bl_mesh.uv_layers:
                        raise RuntimeError(
                            f"Lightmapped object [{obj.name}] is missing UV map [${UV_MAP_LIGHTMAP}]",
                        )
                    mesh.loop_uv2.append(cast("tuple[float, float]", bl_mesh.uv_layers[UV_MAP_LIGHTMAP].data[loop_idx].uv[:2]))
                if self.tangentspace:
                    loop = bl_mesh.loops[loop_idx]
                    mesh.loop_tangents.append(cast("tuple[float, float, float]", loop.tangent[:3]))
                    mesh.loop_bitangents.append(cast("tuple[float, float, float]", loop.bitangent[:3]))
            mesh.face_materials.append(face.material_index)
            mesh.face_normals.append(cast("tuple[float, float, float]", face.normal[:3]))
        return mesh

    def edge_loop_to_mdl_mesh(self, mesh: EdgeLoopMesh) -> None:
        self.verts.clear()
        self.normals.clear()
        self.uv1.clear()
        self.uv2.clear()
        self.tangents.clear()
        self.bitangents.clear()
        self.tangentspacenormals.clear()
        self.weights.clear()
        self.constraints.clear()
        self.facelist = FaceList()

        if self.compression != Compression.DISABLED:
            attrs_to_vert_idx: dict[SimilarEdgeLoopMeshVertex, int] = {}
            for face_idx in range(mesh.num_faces()):
                vert_indices: Sequence[int] = [0, 0, 0]
                for i in range(3):
                    loop_idx: int = 3 * face_idx + i
                    vert_idx: int = mesh.loop_verts[loop_idx]
                    vert: tuple[float, float, float] = mesh.verts[vert_idx]
                    normal: tuple[float, float, float] = mesh.loop_normals[loop_idx]
                    uv1: tuple[float, float] = mesh.loop_uv1[loop_idx] if mesh.loop_uv1 else (0.0, 0.0)
                    uv2: tuple[float, float] = mesh.loop_uv2[loop_idx] if mesh.loop_uv2 else (0.0, 0.0)
                    attrs = SimilarEdgeLoopMeshVertex(vert, normal, uv1, uv2)
                    if attrs in attrs_to_vert_idx:
                        vert_indices[i] = attrs_to_vert_idx[attrs]
                    else:
                        num_verts = len(self.verts)
                        attrs_to_vert_idx[attrs] = num_verts
                        vert_indices[i] = num_verts
                        self.verts.append(vert)
                        self.normals.append(normal)
                        if mesh.loop_uv1:
                            self.uv1.append(uv1)
                        if mesh.loop_uv2:
                            self.uv2.append(uv2)
                        if mesh.loop_tangents and mesh.loop_bitangents:
                            self.tangents.append(mesh.loop_tangents[loop_idx])
                            self.bitangents.append(mesh.loop_bitangents[loop_idx])
                            self.tangentspacenormals.append(mesh.loop_normals[loop_idx])
                        if mesh.weights:
                            self.weights.append(mesh.weights[vert_idx])
                        if mesh.constraints:
                            self.constraints.append(mesh.constraints[vert_idx])
                self.facelist.vertices.append(cast("tuple[int, int, int]", tuple(vert_indices)))
                self.facelist.uv.append(cast("tuple[int, int, int]", tuple(vert_indices)))
        else:
            num_verts = len(mesh.verts)
            self.verts = mesh.verts
            self.weights = mesh.weights
            self.constraints = mesh.constraints
            normals = [Vector((0, 0, 0))] * num_verts
            tangents: list[Vector] = []
            bitangents: list[Vector] = []
            tanspacenormals: list[Vector] = []
            if mesh.loop_tangents and mesh.loop_bitangents:
                tangents = [Vector((0, 0, 0))] * num_verts
                bitangents = [Vector((0, 0, 0))] * num_verts
                tanspacenormals = [Vector((0, 0, 0))] * num_verts
            if mesh.loop_uv1:
                self.uv1 = [(0, 0)] * num_verts
            if mesh.loop_uv2:
                self.uv2 = [(0, 0)] * num_verts
            for face_idx in range(mesh.num_faces()):
                start_loop_idx = 3 * face_idx
                face_verts = mesh.loop_verts[start_loop_idx : (start_loop_idx + 3)]
                for i in range(3):
                    loop_idx = start_loop_idx + i
                    vert_idx = face_verts[i]
                    normals[vert_idx] += Vector(mesh.loop_normals[loop_idx])
                    if mesh.loop_uv1:
                        self.uv1[vert_idx] = mesh.loop_uv1[loop_idx]
                    if mesh.loop_uv2:
                        self.uv2[vert_idx] = mesh.loop_uv2[loop_idx]
                    if mesh.loop_tangents and mesh.loop_bitangents:
                        tangents[vert_idx] += Vector(cast("tuple[float, float, float]", mesh.loop_tangents[loop_idx]))
                        bitangents[vert_idx] += Vector(cast("tuple[float, float, float]", mesh.loop_bitangents[loop_idx]))
                        tanspacenormals[vert_idx] += Vector(cast("tuple[float, float, float]", mesh.loop_normals[loop_idx]))
                self.facelist.vertices.append(cast("tuple[int, int, int]", tuple(face_verts)))
                self.facelist.uv.append(cast("tuple[int, int, int]", tuple(face_verts)))
            normals = [normal.normalized() for normal in normals]
            self.normals = [cast("tuple[float, float, float]", normal[:3]) for normal in normals]
            if mesh.loop_tangents and mesh.loop_bitangents:
                tangents = [tangent.normalized() for tangent in tangents]
                bitangents = [bitangent.normalized() for bitangent in bitangents]
                tanspacenormals = [normal.normalized() for normal in tanspacenormals]
                self.tangents = [tangent.to_tuple() for tangent in tangents]
                self.bitangents = [bitangent.to_tuple() for bitangent in bitangents]
                self.tangentspacenormals = [normal.to_tuple() for normal in tanspacenormals]

        self.facelist.materials = mesh.face_materials
        self.facelist.normals = mesh.face_normals
