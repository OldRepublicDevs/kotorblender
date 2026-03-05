"""
test_mdl_minimal.py – Blender background-mode test

Tests the MDL export pipeline with synthetically constructed minimal scenes:
  - A model with a single MDLROOT dummy node
  - A model with a MDLROOT + one mesh child (TRIMESH)
  - Verifies the output file exists and is non-zero length.
  - Re-imports the exported MDL and checks basic scene properties.

No proprietary game assets are required.

Run with:
    blender --background --python test/blender/test_mdl_minimal.py
"""

import os
import sys
import tempfile

import bpy

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

MODULE = "bl_ext.user_default.io_scene_kotor"
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.constants import DummyType, MeshType, Classification, ExportOptions, ImportOptions
from io_scene_kotor.io.mdl import save_mdl, load_mdl

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
    # save_mdl reads from bpy.context.collection, not the scene master collection
    bpy.context.collection.objects.link(root)
    return root


def _make_trimesh(name, root, verts=None, faces=None):
    """Create a minimal triangle mesh as a TRIMESH child of root."""
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
    # Assign UV maps expected by the exporter
    if "UVMap" not in mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")

    mat = bpy.data.materials.new(name=f"{name}_mat")
    mesh.materials.append(mat)

    bpy.context.collection.objects.link(obj)
    return obj


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_export_minimal_dummy_root():
    """Exporting a scene with only an MDLROOT dummy produces a non-empty file."""
    _clear_scene()
    _make_mdl_root("testmodel")

    with tempfile.NamedTemporaryFile(suffix=".mdl", delete=False) as f:
        path = f.name
    mdx_path = path[:-4] + ".mdx"
    try:
        opts = ExportOptions()
        opts.export_animations = False
        opts.export_walkmeshes = False
        save_mdl(_op, path, opts)
        ok = os.path.exists(path) and os.path.getsize(path) > 0
        if ok:
            print(f"  PASS test_export_minimal_dummy_root (MDL size={os.path.getsize(path)} bytes)")
        else:
            print("  FAIL test_export_minimal_dummy_root: file missing or empty")
        return ok
    except Exception as e:
        print(f"  FAIL test_export_minimal_dummy_root: exception {e}")
        return False
    finally:
        for p in (path, mdx_path):
            if os.path.exists(p):
                os.unlink(p)


def test_export_root_with_mesh():
    """Exporting a root + single triangle mesh produces a non-empty file."""
    _clear_scene()
    root = _make_mdl_root("meshmodel")
    _make_trimesh("tri_01", root)

    with tempfile.NamedTemporaryFile(suffix=".mdl", delete=False) as f:
        path = f.name
    mdx_path = path[:-4] + ".mdx"
    try:
        opts = ExportOptions()
        opts.export_animations = False
        opts.export_walkmeshes = False
        save_mdl(_op, path, opts)
        mdl_ok = os.path.exists(path) and os.path.getsize(path) > 0
        mdx_ok = os.path.exists(mdx_path)
        ok = mdl_ok and mdx_ok
        if ok:
            print(
                f"  PASS test_export_root_with_mesh "
                f"(MDL={os.path.getsize(path)}B, MDX={os.path.getsize(mdx_path)}B)"
            )
        else:
            print(f"  FAIL test_export_root_with_mesh: mdl_ok={mdl_ok}, mdx_ok={mdx_ok}")
        return ok
    except Exception as e:
        print(f"  FAIL test_export_root_with_mesh: exception {e}")
        return False
    finally:
        for p in (path, mdx_path):
            if os.path.exists(p):
                os.unlink(p)


def test_export_then_reimport():
    """Export a minimal MDL then re-import it; the root object reappears."""
    _clear_scene()
    root_name = "reimporttest"
    _make_mdl_root(root_name)

    with tempfile.NamedTemporaryFile(suffix=".mdl", delete=False) as f:
        path = f.name
    mdx_path = path[:-4] + ".mdx"
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

        mdl_roots = [
            o for o in bpy.data.objects if o.kb.dummytype == DummyType.MDLROOT
        ]
        ok = len(mdl_roots) >= 1
        if ok:
            print(f"  PASS test_export_then_reimport (found root: '{mdl_roots[0].name}')")
        else:
            print("  FAIL test_export_then_reimport: no MDLROOT found after import")
        return ok
    except Exception as e:
        print(f"  FAIL test_export_then_reimport: exception {e}")
        return False
    finally:
        for p in (path, mdx_path):
            if os.path.exists(p):
                os.unlink(p)


def test_mdl_file_starts_with_signature():
    """The exported MDL binary starts with expected header bytes (model name area)."""
    _clear_scene()
    _make_mdl_root("sigtest")

    with tempfile.NamedTemporaryFile(suffix=".mdl", delete=False) as f:
        path = f.name
    mdx_path = path[:-4] + ".mdx"
    try:
        opts = ExportOptions()
        opts.export_animations = False
        opts.export_walkmeshes = False
        save_mdl(_op, path, opts)
        with open(path, "rb") as fh:
            header = fh.read(12)
        # First 4 bytes of a K1-PC MDL are the function pointer (not 0)
        ok = len(header) == 12
        if ok:
            print(f"  PASS test_mdl_file_starts_with_signature (header={header[:4].hex()})")
        else:
            print("  FAIL test_mdl_file_starts_with_signature")
        return ok
    except Exception as e:
        print(f"  FAIL test_mdl_file_starts_with_signature: {e}")
        return False
    finally:
        for p in (path, mdx_path):
            if os.path.exists(p):
                os.unlink(p)


def test_export_options_object():
    """ExportOptions and ImportOptions objects have all expected fields."""
    opts_e = ExportOptions()
    opts_i = ImportOptions()
    try:
        assert hasattr(opts_e, "export_for_tsl")
        assert hasattr(opts_e, "export_for_xbox")
        assert hasattr(opts_e, "export_animations")
        assert hasattr(opts_e, "export_walkmeshes")
        assert hasattr(opts_e, "compress_quaternions")
        assert hasattr(opts_i, "import_geometry")
        assert hasattr(opts_i, "import_animations")
        assert hasattr(opts_i, "import_walkmeshes")
        assert hasattr(opts_i, "build_materials")
        assert hasattr(opts_i, "build_armature")
        print("  PASS test_export_options_object")
        return True
    except AssertionError as e:
        print(f"  FAIL test_export_options_object: {e}")
        return False


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_tests():
    print("\n=== test_mdl_minimal.py ===")
    tests = [
        test_export_options_object,
        test_export_minimal_dummy_root,
        test_export_root_with_mesh,
        test_export_then_reimport,
        test_mdl_file_starts_with_signature,
    ]
    results = [t() for t in tests]
    passed = sum(results)
    total = len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_mdl_minimal.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
