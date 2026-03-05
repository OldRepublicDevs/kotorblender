"""
test_mdl_validation.py – MDL export validation tests

Exercises the non-GUI export validation layer ported from KOTORMax-style
sanity checks.

Run with:
    blender --background --python test/blender/test_mdl_validation.py
"""

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


class _Op:
    def report(self, level, message):
        tag = next(iter(level)) if level else "INFO"
        print(f"    [{tag}] {message}")


_op = _Op()


def _clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
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


def _make_mesh(name, root, verts=None, faces=None, node_number=2):
    verts = verts if verts is not None else [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    faces = faces if faces is not None else [(0, 1, 2)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.parent = root
    obj.rotation_mode = "QUATERNION"
    obj.kb.meshtype = MeshType.TRIMESH
    obj.kb.node_number = node_number
    obj.kb.export_order = node_number - 1
    if "UVMap" not in mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    mat = bpy.data.materials.new(name=f"{name}_mat")
    mesh.materials.append(mat)
    bpy.context.collection.objects.link(obj)
    return obj


def _export(root):
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


def _cleanup_paths(*paths):
    for path in paths:
        if os.path.exists(path):
            os.unlink(path)


def _expect_export_failure(root, expected_substring):
    path = mdx_path = None
    try:
        path, mdx_path = _export(root)
    except RuntimeError as exc:
        ok = expected_substring.lower() in str(exc).lower()
        if ok:
            print(f"  PASS {expected_substring}")
        else:
            print(f"  FAIL wrong error: {exc}")
        return ok
    except Exception as exc:
        print(f"  FAIL unexpected exception type: {exc}")
        return False
    else:
        print("  FAIL export unexpectedly succeeded")
        return False
    finally:
        if path or mdx_path:
            _cleanup_paths(*(p for p in (path, mdx_path) if p))


def test_duplicate_name_validation():
    _clear_scene()
    root = _make_mdl_root("dup_root")
    child1 = bpy.data.objects.new("dup", None)
    child1.parent = root
    child1.kb.node_number = 2
    child1.kb.export_order = 1
    bpy.context.collection.objects.link(child1)
    child2 = bpy.data.objects.new("dup.001", None)
    child2.parent = root
    child2.kb.node_number = 3
    child2.kb.export_order = 2
    bpy.context.collection.objects.link(child2)
    return _expect_export_failure(root, "Duplicate exported node names")


def test_missing_animroot_validation():
    _clear_scene()
    root = _make_mdl_root("animroot_root")
    root.kb.animroot = "missing_node"
    _make_mesh("tri_01", root)
    return _expect_export_failure(root, "Anim Root")


def test_bitmap_length_validation():
    _clear_scene()
    root = _make_mdl_root("bitmap_root")
    mesh = _make_mesh("bitmap_mesh", root)
    mesh.kb.bitmap = "texture_name_too_long"
    return _expect_export_failure(root, "longer than 16 characters")


def test_zero_face_mesh_validation():
    _clear_scene()
    root = _make_mdl_root("zero_face_root")
    _make_mesh("zero_face_mesh", root, faces=[])
    return _expect_export_failure(root, "has no faces")


def run_tests():
    print("\n=== test_mdl_validation.py ===")
    tests = [
        test_duplicate_name_validation,
        test_missing_animroot_validation,
        test_bitmap_length_validation,
        test_zero_face_mesh_validation,
    ]
    results = [test() for test in tests]
    passed = sum(results)
    total = len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_mdl_validation.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
