"""
test_mdl_structures.py – MDL structure parity tests

Covers model-header metadata, extended light properties, and emitter
controller/flag roundtrips that are important for KOTORMax parity.

Run with:
    blender --background --python test/blender/test_mdl_structures.py
"""

import math
import os
import sys
import tempfile

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

MODULE = "bl_ext.user_default.io_scene_kotor"
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.constants import Classification, DummyType, ExportOptions, MeshType
from io_scene_kotor.io.mdl import save_mdl
from io_scene_kotor.format.mdl.reader import MdlReader
from io_scene_kotor.scene.modelnode.emitter import EmitterNode
from io_scene_kotor.scene.modelnode.light import LightNode


class _Op:
    def report(self, level, message):
        tag = next(iter(level)) if level else "INFO"
        print(f"    [{tag}] {message}")


class _Options:
    build_materials = False


_op = _Op()


def _clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for light in list(bpy.data.lights):
        bpy.data.lights.remove(light)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)


def _make_mdl_root(name="testmodel"):
    root = bpy.data.objects.new(name, None)
    root.kb.dummytype = DummyType.MDLROOT
    root.kb.classification = Classification.OTHER
    root.kb.animscale = 1.0
    root.kb.node_number = 1
    root.kb.export_order = 0
    root.rotation_mode = "QUATERNION"
    bpy.context.collection.objects.link(root)
    return root


def _make_trimesh(name, root, verts, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    obj.parent = root
    obj.rotation_mode = "QUATERNION"
    obj.kb.meshtype = MeshType.TRIMESH
    obj.kb.node_number = 2
    obj.kb.export_order = 1
    if "UVMap" not in mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    mat = bpy.data.materials.new(name=f"{name}_mat")
    mesh.materials.append(mat)
    bpy.context.collection.objects.link(obj)
    return obj


def _make_light(name, root, node_number=2):
    light_node = LightNode(name)
    light_node.node_number = node_number
    light_node.export_order = node_number - 1
    obj = light_node.add_to_collection(bpy.context.collection, _Options())
    obj.parent = root
    return obj


def _make_emitter(name, root, node_number=2):
    emitter_node = EmitterNode(name)
    emitter_node.node_number = node_number
    emitter_node.export_order = node_number - 1
    obj = emitter_node.add_to_collection(bpy.context.collection, _Options())
    obj.parent = root
    return obj


def _export_model(root):
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    bpy.context.view_layer.objects.active = root

    with tempfile.NamedTemporaryFile(suffix=".mdl", delete=False) as f:
        path = f.name

    opts = ExportOptions()
    opts.export_animations = False
    opts.export_walkmeshes = False
    save_mdl(_op, path, opts)
    return path, path[:-4] + ".mdx"


def _load_model(path):
    reader = MdlReader(path)
    return reader.load()


def _cleanup_paths(*paths):
    for path in paths:
        if os.path.exists(path):
            os.unlink(path)


def test_model_header_preserves_custom_metadata():
    _clear_scene()
    root = _make_mdl_root("header_meta")
    root.kb.classification_unk1 = 7
    root.kb.bounding_box_min = (-2.0, -3.0, -4.0)
    root.kb.bounding_box_max = (5.0, 6.0, 7.0)
    root.kb.model_radius = 8.5

    path, mdx_path = _export_model(root)
    try:
        model = _load_model(path)
        ok = (
            model.classification_unk1 == 7
            and tuple(model.bounding_box_min) == (-2.0, -3.0, -4.0)
            and tuple(model.bounding_box_max) == (5.0, 6.0, 7.0)
            and math.isclose(model.model_radius, 8.5, rel_tol=0.0, abs_tol=1e-5)
        )
        if ok:
            print("  PASS test_model_header_preserves_custom_metadata")
        else:
            print(
                "  FAIL test_model_header_preserves_custom_metadata: "
                f"unk1={model.classification_unk1}, "
                f"bbmin={model.bounding_box_min}, "
                f"bbmax={model.bounding_box_max}, "
                f"radius={model.model_radius}"
            )
        return ok
    except Exception as exc:
        print(f"  FAIL test_model_header_preserves_custom_metadata: exception {exc}")
        return False
    finally:
        _cleanup_paths(path, mdx_path)


def test_model_header_computes_bounds_from_positive_mesh():
    _clear_scene()
    root = _make_mdl_root("bounds_mesh")
    _make_trimesh(
        "bounds_tri",
        root,
        verts=[(1.0, 2.0, 3.0), (4.0, 5.0, 6.0), (1.0, 5.0, 3.0)],
        faces=[(0, 1, 2)],
    )

    path, mdx_path = _export_model(root)
    try:
        model = _load_model(path)
        expected_radius = math.sqrt(6.75)
        ok = (
            tuple(round(v, 5) for v in model.bounding_box_min) == (1.0, 2.0, 3.0)
            and tuple(round(v, 5) for v in model.bounding_box_max) == (4.0, 5.0, 6.0)
            and math.isclose(
                model.model_radius, expected_radius, rel_tol=0.0, abs_tol=1e-5
            )
        )
        if ok:
            print("  PASS test_model_header_computes_bounds_from_positive_mesh")
        else:
            print(
                "  FAIL test_model_header_computes_bounds_from_positive_mesh: "
                f"bbmin={model.bounding_box_min}, "
                f"bbmax={model.bounding_box_max}, "
                f"radius={model.model_radius}"
            )
        return ok
    except Exception as exc:
        print(f"  FAIL test_model_header_computes_bounds_from_positive_mesh: {exc}")
        return False
    finally:
        _cleanup_paths(path, mdx_path)


def test_light_roundtrip_preserves_extended_properties():
    _clear_scene()
    root = _make_mdl_root("light_meta")
    light = _make_light("light_01", root)
    light.kb.radius = 14.0
    light.kb.multiplier = 2.0
    light.kb.shadowradius = 3.5
    light.kb.verticaldisplacement = -1.25

    path, mdx_path = _export_model(root)
    try:
        model = _load_model(path)
        light_node = model.find_node(lambda n: isinstance(n, LightNode))
        ok = (
            light_node is not None
            and math.isclose(light_node.radius, 14.0, rel_tol=0.0, abs_tol=1e-5)
            and math.isclose(light_node.multiplier, 2.0, rel_tol=0.0, abs_tol=1e-5)
            and math.isclose(light_node.shadowradius, 3.5, rel_tol=0.0, abs_tol=1e-5)
            and math.isclose(
                light_node.verticaldisplacement, -1.25, rel_tol=0.0, abs_tol=1e-5
            )
        )
        if ok:
            print("  PASS test_light_roundtrip_preserves_extended_properties")
        else:
            print(
                "  FAIL test_light_roundtrip_preserves_extended_properties: "
                f"node={light_node}"
            )
        return ok
    except Exception as exc:
        print(f"  FAIL test_light_roundtrip_preserves_extended_properties: {exc}")
        return False
    finally:
        _cleanup_paths(path, mdx_path)


def test_emitter_roundtrip_preserves_flags_and_detonate():
    _clear_scene()
    root = _make_mdl_root("emitter_meta")
    emitter = _make_emitter("emit_01", root)
    emitter.kb.update = "Explosion"
    emitter.kb.flag13 = True
    emitter.kb.emitter_unknown_flags = 0x2000
    emitter.kb.detonate = 4.25

    path, mdx_path = _export_model(root)
    try:
        model = _load_model(path)
        emitter_node = model.find_node(lambda n: isinstance(n, EmitterNode))
        ok = (
            emitter_node is not None
            and emitter_node.flag13
            and emitter_node.extra_flags == 0x2000
            and math.isclose(emitter_node.detonate, 4.25, rel_tol=0.0, abs_tol=1e-5)
        )
        if ok:
            print("  PASS test_emitter_roundtrip_preserves_flags_and_detonate")
        else:
            print(
                "  FAIL test_emitter_roundtrip_preserves_flags_and_detonate: "
                f"flag13={getattr(emitter_node, 'flag13', None)}, "
                f"extra={getattr(emitter_node, 'extra_flags', None)}, "
                f"detonate={getattr(emitter_node, 'detonate', None)}"
            )
        return ok
    except Exception as exc:
        print(f"  FAIL test_emitter_roundtrip_preserves_flags_and_detonate: {exc}")
        return False
    finally:
        _cleanup_paths(path, mdx_path)


def test_non_explosion_emitter_omits_detonate_controller():
    _clear_scene()
    root = _make_mdl_root("emit_no_det")
    emitter = _make_emitter("emit_02", root)
    emitter.kb.update = "Fountain"
    emitter.kb.detonate = 9.0

    path, mdx_path = _export_model(root)
    try:
        model = _load_model(path)
        emitter_node = model.find_node(lambda n: isinstance(n, EmitterNode))
        ok = emitter_node is not None and math.isclose(
            emitter_node.detonate, 0.0, rel_tol=0.0, abs_tol=1e-5
        )
        if ok:
            print("  PASS test_non_explosion_emitter_omits_detonate_controller")
        else:
            print(
                "  FAIL test_non_explosion_emitter_omits_detonate_controller: "
                f"detonate={getattr(emitter_node, 'detonate', None)}"
            )
        return ok
    except Exception as exc:
        print(f"  FAIL test_non_explosion_emitter_omits_detonate_controller: {exc}")
        return False
    finally:
        _cleanup_paths(path, mdx_path)


def run_tests():
    print("\n=== test_mdl_structures.py ===")
    tests = [
        test_model_header_preserves_custom_metadata,
        test_model_header_computes_bounds_from_positive_mesh,
        test_light_roundtrip_preserves_extended_properties,
        test_emitter_roundtrip_preserves_flags_and_detonate,
        test_non_explosion_emitter_omits_detonate_controller,
    ]
    results = [test() for test in tests]
    passed = sum(results)
    total = len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_mdl_structures.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
