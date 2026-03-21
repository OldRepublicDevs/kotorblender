"""
test_ascii_mdl.py – Blender background-mode test

Tests ASCII MDL format:
  - Format detection (_is_ascii_mdl)
  - Export to .mdl.ascii and file content
  - Export then re-import roundtrip (root + mesh)

No proprietary game assets required.

Run with:
    blender --background --python test/blender/test_ascii_mdl.py
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

from io_scene_kotor.constants import (
    DummyType,
    MeshType,
    Classification,
    ExportOptions,
    ImportOptions,
)
from io_scene_kotor.io.mdl import load_mdl, save_mdl

# Import for format detection test (private function)
import io_scene_kotor.io.mdl as mdl_module


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


def _make_trimesh(name, root, verts=None, faces=None):
    if verts is None:
        verts = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    if faces is None:
        faces = [(0, 1, 2)]
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


def test_ascii_format_detection():
    """_is_ascii_mdl returns True for .mdl.ascii extension and for content starting with newmodel/#."""
    is_ascii = getattr(mdl_module, "_is_ascii_mdl", None)
    if not is_ascii:
        print("  FAIL test_ascii_format_detection: _is_ascii_mdl not found")
        return False
    if not is_ascii("/some/path/model.mdl.ascii"):
        print("  FAIL test_ascii_format_detection: .mdl.ascii should be ASCII")
        return False
    if not is_ascii("/some/path/model.ascii"):
        print("  FAIL test_ascii_format_detection: .ascii should be ASCII")
        return False
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".mdl", delete=False, encoding="utf-8"
    ) as f:
        f.write("newmodel foo\n")
        path = f.name
    try:
        if not is_ascii(path):
            print("  FAIL test_ascii_format_detection: content 'newmodel' should be ASCII")
            return False
    finally:
        os.unlink(path)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".mdl", delete=False, encoding="utf-8"
    ) as f:
        f.write("# comment\n")
        path = f.name
    try:
        if not is_ascii(path):
            print("  FAIL test_ascii_format_detection: content '#' should be ASCII")
            return False
    finally:
        os.unlink(path)
    if is_ascii("/some/binary.mdl"):
        print("  FAIL test_ascii_format_detection: .mdl without content check might be binary")
    print("  PASS test_ascii_format_detection")
    return True


def test_ascii_export_minimal():
    """Export minimal scene to .mdl.ascii; file exists and contains newmodel."""
    _clear_scene()
    _make_mdl_root("asciitest")
    with tempfile.NamedTemporaryFile(suffix=".mdl.ascii", delete=False) as f:
        path = f.name
    try:
        opts = ExportOptions()
        opts.export_animations = False
        opts.export_walkmeshes = False
        save_mdl(_op, path, opts)
        if not os.path.exists(path):
            print("  FAIL test_ascii_export_minimal: file not created")
            return False
        content = open(path, encoding="utf-8").read()
        if "newmodel" not in content.lower():
            print("  FAIL test_ascii_export_minimal: file does not contain newmodel")
            return False
        if "node " not in content.lower() or "endnode" not in content.lower():
            print("  FAIL test_ascii_export_minimal: file missing node/endnode")
            return False
        print(f"  PASS test_ascii_export_minimal (size={os.path.getsize(path)} bytes)")
        return True
    except Exception as e:
        print(f"  FAIL test_ascii_export_minimal: {e}")
        return False
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_ascii_export_then_import():
    """Export to .mdl.ascii then re-import; root and mesh objects exist."""
    _clear_scene()
    root_name = "ascii_roundtrip"
    root = _make_mdl_root(root_name)
    _make_trimesh("mesh_01", root)
    with tempfile.NamedTemporaryFile(suffix=".mdl.ascii", delete=False) as f:
        path = f.name
    try:
        opts_exp = ExportOptions()
        opts_exp.export_animations = False
        opts_exp.export_walkmeshes = False
        save_mdl(_op, path, opts_exp)
        _clear_scene()
        opts_imp = ImportOptions()
        opts_imp.import_geometry = True
        opts_imp.import_animations = False
        opts_imp.import_walkmeshes = False
        opts_imp.build_materials = False
        opts_imp.build_armature = False
        load_mdl(_op, path, opts_imp)
        roots = [
            o
            for o in bpy.data.objects
            if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
        ]
        if not roots:
            print("  FAIL test_ascii_export_then_import: no MDLROOT after import")
            return False
        children = [o for o in roots[0].children if o.type == "MESH"]
        if not children:
            print("  FAIL test_ascii_export_then_import: no mesh child after import")
            return False
        print(
            f"  PASS test_ascii_export_then_import (root='{roots[0].name}', "
            f"meshes={len(children)})"
        )
        return True
    except Exception as e:
        print(f"  FAIL test_ascii_export_then_import: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        if os.path.exists(path):
            os.unlink(path)


def run_tests():
    print("\n=== test_ascii_mdl.py ===")
    results = [
        test_ascii_format_detection(),
        test_ascii_export_minimal(),
        test_ascii_export_then_import(),
    ]
    passed = sum(results)
    total = len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_ascii_mdl.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
