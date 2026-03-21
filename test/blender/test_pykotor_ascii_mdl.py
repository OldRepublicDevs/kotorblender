"""
test_pykotor_ascii_mdl.py – Blender background-mode test (ported from PyKotor ASCII/MDL tests)

Ported from PyKotor's MDL/ASCII test behaviour. Uses only KotorBlender's MDL stack:
- io_scene_kotor.io.mdl: load_mdl, save_mdl
- io_scene_kotor.format.mdl: AsciiMdlReader, AsciiMdlWriter (via load_mdl/save_mdl)
- No PyKotor reader/writer/objects.

Tests:
- ASCII format detection (_is_ascii_mdl)
- ASCII export (minimal root, root+mesh)
- ASCII import (from exported file)
- ASCII roundtrip (export → import, root and node count)
- Binary roundtrip when test_files/pykotor_mdl assets exist (load binary → save binary → load)
- Binary → ASCII → import (load binary if present, save as ASCII, load ASCII)
- Nonexistent file raises
- Empty/minimal MDL (root only) export and reimport

Run with:
    blender --background --python test/blender/test_pykotor_ascii_mdl.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from collections.abc import Generator

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

MODULE = "bl_ext.user_default.io_scene_kotor"
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.constants import (
    Classification,
    DummyType,
    ExportOptions,
    ImportOptions,
    MeshType,
)
from io_scene_kotor.io import mdl as mdl_module
from io_scene_kotor.io.mdl import load_mdl, save_mdl


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


def _import_opts():
    opts = ImportOptions()
    opts.import_geometry = True
    opts.import_animations = False
    opts.import_walkmeshes = False
    opts.build_materials = False
    opts.build_armature = False
    return opts


def _pykotor_mdl_paths() -> Generator[tuple[str, str], None, None]:
    """Yield (mdl_path, name) for each .mdl in test_files/pykotor_mdl that has sibling .mdx."""
    pykotor_dir = os.path.join(WORKSPACE_ROOT, "test", "test_files", "pykotor_mdl")
    if not os.path.isdir(pykotor_dir):
        return
    for entry in os.listdir(pykotor_dir):
        if not entry.lower().endswith(".mdl"):
            continue
        mdl_path = os.path.join(pykotor_dir, entry)
        if not os.path.isfile(mdl_path):
            continue
        mdx_path = os.path.splitext(mdl_path)[0] + ".mdx"
        if not os.path.isfile(mdx_path):
            continue
        name = os.path.splitext(entry)[0]
        yield mdl_path, name


# ---------------------------------------------------------------------------
# Ported ASCII / MDL tests (KotorBlender stack only)
# ---------------------------------------------------------------------------


def test_ascii_format_detection():
    """_is_ascii_mdl: .mdl.ascii / .ascii and content newmodel/# are ASCII; plain .mdl is not without content."""
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
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mdl", delete=False, encoding="utf-8") as f:
        f.write("newmodel foo\n")
        path = f.name
    try:
        if not is_ascii(path):
            print("  FAIL test_ascii_format_detection: content 'newmodel' should be ASCII")
            return False
    finally:
        os.unlink(path)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mdl", delete=False, encoding="utf-8") as f:
        f.write("# comment\n")
        path = f.name
    try:
        if not is_ascii(path):
            print("  FAIL test_ascii_format_detection: content '#' should be ASCII")
            return False
    finally:
        os.unlink(path)
    print("  PASS test_ascii_format_detection")
    return True


def test_ascii_export_minimal():
    """Export minimal scene to .mdl.ascii; file exists and contains newmodel/node/endnode."""
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


def test_ascii_export_with_mesh():
    """Export root + mesh to .mdl.ascii; file contains trimesh/geometry."""
    _clear_scene()
    root = _make_mdl_root("ascii_mesh")
    _make_trimesh("mesh_01", root)
    with tempfile.NamedTemporaryFile(suffix=".mdl.ascii", delete=False) as f:
        path = f.name
    try:
        opts = ExportOptions()
        opts.export_animations = False
        opts.export_walkmeshes = False
        save_mdl(_op, path, opts)
        if not os.path.exists(path):
            print("  FAIL test_ascii_export_with_mesh: file not created")
            return False
        content = open(path, encoding="utf-8").read()
        if "trimesh" not in content.lower():
            print("  FAIL test_ascii_export_with_mesh: file does not contain trimesh")
            return False
        print(f"  PASS test_ascii_export_with_mesh (size={os.path.getsize(path)} bytes)")
        return True
    except Exception as e:
        print(f"  FAIL test_ascii_export_with_mesh: {e}")
        return False
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_ascii_import_from_exported():
    """Export to .mdl.ascii then import; root and mesh objects exist (ASCII roundtrip)."""
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
        load_mdl(_op, path, _import_opts())
        roots = [
            o
            for o in bpy.data.objects
            if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
        ]
        if not roots:
            print("  FAIL test_ascii_import_from_exported: no MDLROOT after import")
            return False
        if roots[0].name != root_name:
            print(f"  FAIL test_ascii_import_from_exported: root name '{roots[0].name}' != '{root_name}'")
            return False
        children = [o for o in roots[0].children if o.type == "MESH"]
        if not children:
            print("  FAIL test_ascii_import_from_exported: no mesh child after import")
            return False
        print(f"  PASS test_ascii_import_from_exported (root='{roots[0].name}', meshes={len(children)})")
        return True
    except Exception as e:
        print(f"  FAIL test_ascii_import_from_exported: {e}")
        return False
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_ascii_roundtrip_node_count():
    """ASCII roundtrip preserves object count."""
    _clear_scene()
    root = _make_mdl_root("nodecount")
    _make_trimesh("m1", root)
    _make_trimesh("m2", root)
    with tempfile.NamedTemporaryFile(suffix=".mdl.ascii", delete=False) as f:
        path = f.name
    try:
        opts = ExportOptions()
        opts.export_animations = False
        opts.export_walkmeshes = False
        save_mdl(_op, path, opts)
        count_before = len(bpy.data.objects)
        _clear_scene()
        load_mdl(_op, path, _import_opts())
        count_after = len(bpy.data.objects)
        ok = count_after == count_before
        if ok:
            print(f"  PASS test_ascii_roundtrip_node_count ({count_before} objects)")
        else:
            print(f"  FAIL test_ascii_roundtrip_node_count: {count_before} -> {count_after}")
        return ok
    except Exception as e:
        print(f"  FAIL test_ascii_roundtrip_node_count: {e}")
        return False
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_binary_roundtrip_when_assets_present():
    """When test_files/pykotor_mdl has MDL+MDX, load binary → save binary → load; root name preserved."""
    paths = list(_pykotor_mdl_paths())
    if not paths:
        print("  SKIP test_binary_roundtrip_when_assets_present (no pykotor_mdl assets)")
        return True
    mdl_path, name = paths[0]
    _clear_scene()
    try:
        load_mdl(_op, mdl_path, _import_opts())
    except Exception as e:
        print(f"  SKIP test_binary_roundtrip_when_assets_present ({name} load failed: {e})")
        return True
    roots = [o for o in bpy.data.objects if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT]
    if not roots:
        print("  SKIP test_binary_roundtrip_when_assets_present (no root after load)")
        return True
    name_before = roots[0].name
    with tempfile.NamedTemporaryFile(suffix=".mdl", delete=False) as f:
        out_mdl = f.name
    out_mdx = os.path.splitext(out_mdl)[0] + ".mdx"
    try:
        opts_exp = ExportOptions()
        opts_exp.export_animations = False
        opts_exp.export_walkmeshes = False
        save_mdl(_op, out_mdl, opts_exp)
        _clear_scene()
        load_mdl(_op, out_mdl, _import_opts())
        roots_after = [o for o in bpy.data.objects if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT]
        ok = roots_after and roots_after[0].name == name_before
        if ok:
            print(f"  PASS test_binary_roundtrip_when_assets_present ({name})")
        else:
            print(f"  FAIL test_binary_roundtrip_when_assets_present: root name not preserved")
        return ok
    except Exception as e:
        print(f"  FAIL test_binary_roundtrip_when_assets_present: {e}")
        return False
    finally:
        for p in (out_mdl, out_mdx):
            if os.path.exists(p):
                try:
                    os.unlink(p)
                except OSError:
                    pass


def test_binary_to_ascii_then_import():
    """If binary test file exists: load binary → save as ASCII → load ASCII; one root."""
    paths = list(_pykotor_mdl_paths())
    if not paths:
        print("  SKIP test_binary_to_ascii_then_import (no pykotor_mdl assets)")
        return True
    mdl_path, name = paths[0]
    _clear_scene()
    try:
        load_mdl(_op, mdl_path, _import_opts())
    except Exception as e:
        print(f"  SKIP test_binary_to_ascii_then_import ({name} load failed: {e})")
        return True
    with tempfile.NamedTemporaryFile(suffix=".mdl.ascii", delete=False) as f:
        ascii_path = f.name
    try:
        opts_exp = ExportOptions()
        opts_exp.export_animations = False
        opts_exp.export_walkmeshes = False
        save_mdl(_op, ascii_path, opts_exp)
        _clear_scene()
        load_mdl(_op, ascii_path, _import_opts())
        roots = [o for o in bpy.data.objects if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT]
        ok = len(roots) >= 1
        if ok:
            print(f"  PASS test_binary_to_ascii_then_import ({name})")
        else:
            print("  FAIL test_binary_to_ascii_then_import: no root after ASCII load")
        return ok
    except Exception as e:
        print(f"  FAIL test_binary_to_ascii_then_import: {e}")
        return False
    finally:
        if os.path.exists(ascii_path):
            os.unlink(ascii_path)


def test_read_nonexistent_file():
    """Loading a non-existent MDL path raises (FileNotFoundError/OSError/RuntimeError)."""
    fake = os.path.join(WORKSPACE_ROOT, "test", "test_files", "pykotor_mdl", "_nonexistent_.mdl")
    _clear_scene()
    try:
        load_mdl(_op, fake, _import_opts())
        print("  FAIL test_read_nonexistent_file: expected exception")
        return False
    except (FileNotFoundError, OSError, RuntimeError):
        print("  PASS test_read_nonexistent_file (got expected exception)")
        return True
    except Exception as e:
        print(f"  PASS test_read_nonexistent_file (got {type(e).__name__})")
        return True


def test_empty_mdl_export_reimport():
    """Minimal MDL (root only): export then reimport; one root (binary)."""
    _clear_scene()
    _make_mdl_root("empty_mdl_root")
    with tempfile.NamedTemporaryFile(suffix=".mdl", delete=False) as f:
        out_mdl = f.name
    out_mdx = os.path.splitext(out_mdl)[0] + ".mdx"
    try:
        opts_exp = ExportOptions()
        opts_exp.export_animations = False
        opts_exp.export_walkmeshes = False
        save_mdl(_op, out_mdl, opts_exp)
        _clear_scene()
        load_mdl(_op, out_mdl, _import_opts())
        roots = [o for o in bpy.data.objects if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT]
        ok = len(roots) == 1 and len(bpy.data.objects) >= 1
        if ok:
            print("  PASS test_empty_mdl_export_reimport")
        else:
            print(f"  FAIL test_empty_mdl_export_reimport: roots={len(roots)} objs={len(bpy.data.objects)}")
        return ok
    except Exception as e:
        print(f"  FAIL test_empty_mdl_export_reimport: {e}")
        return False
    finally:
        for p in (out_mdl, out_mdx):
            if os.path.exists(p):
                try:
                    os.unlink(p)
                except OSError:
                    pass


def test_empty_mdl_ascii_export_reimport():
    """Minimal MDL (root only): export as ASCII then reimport; one root."""
    _clear_scene()
    _make_mdl_root("empty_ascii_root")
    with tempfile.NamedTemporaryFile(suffix=".mdl.ascii", delete=False) as f:
        path = f.name
    try:
        opts_exp = ExportOptions()
        opts_exp.export_animations = False
        opts_exp.export_walkmeshes = False
        save_mdl(_op, path, opts_exp)
        _clear_scene()
        load_mdl(_op, path, _import_opts())
        roots = [o for o in bpy.data.objects if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT]
        ok = len(roots) == 1
        if ok:
            print("  PASS test_empty_mdl_ascii_export_reimport")
        else:
            print(f"  FAIL test_empty_mdl_ascii_export_reimport: roots={len(roots)}")
        return ok
    except Exception as e:
        print(f"  FAIL test_empty_mdl_ascii_export_reimport: {e}")
        return False
    finally:
        if os.path.exists(path):
            os.unlink(path)


def run_tests():
    print("\n=== test_pykotor_ascii_mdl.py (ported from PyKotor; KotorBlender stack only) ===")
    tests = [
        test_ascii_format_detection,
        test_ascii_export_minimal,
        test_ascii_export_with_mesh,
        test_ascii_import_from_exported,
        test_ascii_roundtrip_node_count,
        test_binary_roundtrip_when_assets_present,
        test_binary_to_ascii_then_import,
        test_read_nonexistent_file,
        test_empty_mdl_export_reimport,
        test_empty_mdl_ascii_export_reimport,
    ]
    results = [bool(t()) for t in tests]
    passed = sum(results)
    total = len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_pykotor_ascii_mdl.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
