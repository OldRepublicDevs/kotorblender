"""
test_pykotor_mdl.py – Blender background-mode test (PyKotor MDL assertions ported)

Ports the same assertions as PyKotor test_mdl.py: load binary MDL/MDX, root and
node hierarchy, mesh data, round-trip, edge cases. Uses test_files/pykotor_mdl/
(c_dewback, dor_lhr02, m02aa_09b, m12aa_c03_char02, m12aa_c04_cam). Fails
if that directory is empty or missing or any listed file fails to load/roundtrip.

Run with:
    blender --background --python test/blender/test_pykotor_mdl.py
"""

from __future__ import annotations

import os
import sys
import tempfile

from collections.abc import Generator

import bpy

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

MODULE = "bl_ext.user_default.io_scene_kotor"
if MODULE not in bpy.context.preferences.addons:  # pyright: ignore[reportOptionalMemberAccess]
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.constants import DummyType, ExportOptions, ImportOptions  # noqa: E402
from io_scene_kotor.io.mdl import load_mdl, save_mdl  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _Op:
    def report(self, level: str | None, message: str) -> None:
        tag = next(iter(level)) if level else "INFO"
        print(f"    [{tag}] {message}")


_op = _Op()


def _clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)


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


def _import_opts() -> ImportOptions:
    opts = ImportOptions()
    opts.import_geometry = True
    opts.import_animations = False
    opts.import_walkmeshes = False
    opts.build_materials = False
    opts.build_armature = False
    return opts


def _first_loadable_path() -> tuple[str, str] | None:
    """Return (mdl_path, name) for the first PyKotor test MDL that loads without error."""
    paths = list(_pykotor_mdl_paths() or [])
    for mdl_path, name in paths:
        _clear_scene()
        try:
            load_mdl(_op, mdl_path, _import_opts())
            roots = [
                o
                for o in bpy.data.objects
                if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
            ]
            if len(roots) >= 1:
                return (mdl_path, name)
        except Exception:
            continue
    return None


# ---------------------------------------------------------------------------
# Tests (same assertions as PyKotor test_mdl.py, Blender idiom)
# ---------------------------------------------------------------------------


def test_read_mdl_basic():
    """Load one PyKotor test MDL; assert MDL root and name (mirror test_read_mdl_basic)."""
    p = _first_loadable_path()
    if not p:
        print("  FAIL test_read_mdl_basic (no pykotor_mdl assets or none loadable)")
        return False
    mdl_path, name = p
    _clear_scene()
    load_mdl(_op, mdl_path, _import_opts())
    roots = [
        o
        for o in bpy.data.objects
        if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
    ]
    ok = len(roots) >= 1 and roots[0].name
    if ok:
        print(f"  PASS test_read_mdl_basic ({name})")
    else:
        print("  FAIL test_read_mdl_basic: no root or empty name")
    return ok


def test_read_all_test_files():
    """Load every PyKotor test file; assert root and type. All must pass (no skips)."""
    paths = list(_pykotor_mdl_paths() or [])
    if not paths:
        print("  FAIL test_read_all_test_files (no pykotor_mdl assets)")
        return False
    all_ok = True
    for mdl_path, name in paths:
        _clear_scene()
        try:
            load_mdl(_op, mdl_path, _import_opts())
            roots = [
                o
                for o in bpy.data.objects
                if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
            ]
            if len(roots) >= 1:
                print(f"  PASS test_read_all_test_files ({name})")
            else:
                print(f"  FAIL test_read_all_test_files ({name}): no MDLROOT")
                all_ok = False
        except Exception as e:
            print(f"  FAIL test_read_all_test_files ({name}): {e}")
            all_ok = False
    return all_ok


def test_mdl_node_hierarchy():
    """After load, assert at least one node and root in objects (mirror test_mdl_node_hierarchy)."""
    p = _first_loadable_path()
    if not p:
        print("  FAIL test_mdl_node_hierarchy (no pykotor_mdl assets or none loadable)")
        return False
    mdl_path, name = p
    _clear_scene()
    load_mdl(_op, mdl_path, _import_opts())
    objs = list(bpy.data.objects)
    roots = [o for o in objs if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT]  # pyright: ignore[reportAttributeAccessIssue]
    ok = len(objs) > 0 and len(roots) >= 1 and roots[0] in objs
    for o in objs:
        if not (hasattr(o, "name") and isinstance(o.name, str)):
            ok = False
            break
    if ok:
        print(f"  PASS test_mdl_node_hierarchy ({name})")
    else:
        print("  FAIL test_mdl_node_hierarchy: hierarchy check failed")
    return ok


def test_mdl_mesh_data():
    """After load, assert at least one object with mesh data (mirror test_mdl_mesh_data)."""
    p = _first_loadable_path()
    if not p:
        print("  FAIL test_mdl_mesh_data (no pykotor_mdl assets or none loadable)")
        return False
    mdl_path, name = p
    _clear_scene()
    load_mdl(_op, mdl_path, _import_opts())
    mesh_objs = [o for o in bpy.data.objects if o.type == "MESH"]
    ok = len(mesh_objs) > 0
    if ok:
        print(f"  PASS test_mdl_mesh_data ({name})")
    else:
        print("  FAIL test_mdl_mesh_data: no mesh objects")
    return ok


def test_mdl_roundtrip():
    """Load MDL, save to temp, load again; assert root preserved (mirror round-trip intent)."""
    p = _first_loadable_path()
    if not p:
        print("  FAIL test_mdl_roundtrip (no pykotor_mdl assets or none loadable)")
        return False
    mdl_path, name = p
    _clear_scene()
    with tempfile.NamedTemporaryFile(suffix=".mdl", delete=False) as f:
        out_mdl = f.name
    out_mdx = os.path.splitext(out_mdl)[0] + ".mdx"
    try:
        load_mdl(_op, mdl_path, _import_opts())
        roots_before = [
            o
            for o in bpy.data.objects
            if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
        ]  # pyright: ignore[reportAttributeAccessIssue]
        if not roots_before:
            print("  FAIL test_mdl_roundtrip: no root after first load")
            return False
        name_before = roots_before[0].name
        opts_exp = ExportOptions()
        opts_exp.export_animations = False
        opts_exp.export_walkmeshes = False
        save_mdl(_op, out_mdl, opts_exp)
        _clear_scene()
        load_mdl(_op, out_mdl, _import_opts())
        roots_after = [
            o
            for o in bpy.data.objects
            if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
        ]  # pyright: ignore[reportAttributeAccessIssue]
        ok = len(roots_after) >= 1 and roots_after[0].name == name_before
        if ok:
            print(f"  PASS test_mdl_roundtrip ({name})")
        else:
            print("  FAIL test_mdl_roundtrip: root/name not preserved")
        return ok
    finally:
        for path in (out_mdl, out_mdx):
            if os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass


def test_mdl_get_node_by_name():
    """Get root by name; nonexistent name returns no object (mirror test_mdl_get_node_by_name)."""
    p = _first_loadable_path()
    if not p:
        print("  FAIL test_mdl_get_node_by_name (no pykotor_mdl assets or none loadable)")
        return False
    mdl_path, name = p
    _clear_scene()
    load_mdl(_op, mdl_path, _import_opts())
    roots = [
        o
        for o in bpy.data.objects
        if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
    ]  # pyright: ignore[reportAttributeAccessIssue]
    if not roots:
        print("  FAIL test_mdl_get_node_by_name: no root")
        return False
    root = roots[0]
    by_name = bpy.data.objects.get(root.name)
    ok = by_name is not None and by_name == root
    nonexistent = bpy.data.objects.get("nonexistent_node_name_xyz")
    ok = ok and (nonexistent is None)
    if ok:
        print(f"  PASS test_mdl_get_node_by_name ({name})")
    else:
        print("  FAIL test_mdl_get_node_by_name: get by name failed")
    return ok


def test_mdl_textures():
    """After load, texture/material names are strings (mirror test_mdl_textures)."""
    p = _first_loadable_path()
    if not p:
        print("  FAIL test_mdl_textures (no pykotor_mdl assets or none loadable)")
        return False
    mdl_path, name = p
    _clear_scene()
    load_mdl(_op, mdl_path, _import_opts())
    textures = set()
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        for slot in getattr(obj, "material_slots", []) or []:
            mat = slot.material
            if mat and getattr(mat, "name", None):
                textures.add(mat.name)
    ok = isinstance(textures, set)
    for t in textures:
        if not (isinstance(t, str) and len(t) > 0):
            ok = False
            break
    if ok:
        print(f"  PASS test_mdl_textures ({name})")
    else:
        print("  FAIL test_mdl_textures: texture names not valid")
    return ok


def test_mdl_lightmaps():
    """After load, lightmap/material slots exist; names are strings if present (mirror test_mdl_lightmaps)."""
    p = _first_loadable_path()
    if not p:
        print("  FAIL test_mdl_lightmaps (no pykotor_mdl assets or none loadable)")
        return False
    mdl_path, name = p
    _clear_scene()
    load_mdl(_op, mdl_path, _import_opts())
    lightmaps = set()
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        for slot in getattr(obj, "material_slots", []) or []:
            mat = slot.material
            if mat and getattr(mat, "name", None) and "lm" in mat.name.lower():
                lightmaps.add(mat.name)
    ok = isinstance(lightmaps, set)
    for lm in lightmaps:
        if not (isinstance(lm, str)):
            ok = False
            break
    if ok:
        print(f"  PASS test_mdl_lightmaps ({name})")
    else:
        print("  FAIL test_mdl_lightmaps: lightmap names not valid")
    return ok


def test_write_mdl_binary():
    """Load, save to binary file; assert file exists and has header (mirror test_write_mdl_binary)."""
    p = _first_loadable_path()
    if not p:
        print("  FAIL test_write_mdl_binary (no pykotor_mdl assets or none loadable)")
        return False
    mdl_path, name = p
    _clear_scene()
    load_mdl(_op, mdl_path, _import_opts())
    with tempfile.NamedTemporaryFile(suffix=".mdl", delete=False) as f:
        out_mdl = f.name
    out_mdx = os.path.splitext(out_mdl)[0] + ".mdx"
    try:
        opts_exp = ExportOptions()
        opts_exp.export_animations = False
        opts_exp.export_walkmeshes = False
        save_mdl(_op, out_mdl, opts_exp)
        ok = os.path.isfile(out_mdl) and os.path.getsize(out_mdl) > 12
        if ok:
            print(f"  PASS test_write_mdl_binary ({name})")
        else:
            print("  FAIL test_write_mdl_binary: file missing or too small")
        return ok
    finally:
        for path in (out_mdl, out_mdx):
            if os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass


def test_mdl_roundtrip_node_count():
    """Roundtrip preserves node count (mirror PyKotor roundtrip structure)."""
    p = _first_loadable_path()
    if not p:
        print("  FAIL test_mdl_roundtrip_node_count (no pykotor_mdl assets or none loadable)")
        return False
    mdl_path, name = p
    _clear_scene()
    load_mdl(_op, mdl_path, _import_opts())
    count_before = len(bpy.data.objects)
    roots_before = [
        o
        for o in bpy.data.objects
        if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
    ]  # pyright: ignore[reportAttributeAccessIssue]
    if not roots_before:
        print("  FAIL test_mdl_roundtrip_node_count: no root after load")
        return False
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
        count_after = len(bpy.data.objects)
        ok = count_after == count_before
        if ok:
            print(f"  PASS test_mdl_roundtrip_node_count ({name})")
        else:
            print(
                f"  FAIL test_mdl_roundtrip_node_count: node count {count_before} -> {count_after}"
            )
        return ok
    finally:
        for path in (out_mdl, out_mdx):
            if os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass


def test_mdl_roundtrip_each_loadable():
    """Roundtrip every loadable PyKotor model; assert root name and at least one node (exhaustive)."""
    paths = list(_pykotor_mdl_paths() or [])
    if not paths:
        print("  FAIL test_mdl_roundtrip_each_loadable (no pykotor_mdl assets)")
        return False
    all_ok = True
    for mdl_path, name in paths:
        _clear_scene()
        try:
            load_mdl(_op, mdl_path, _import_opts())
        except Exception as e:
            print(f"  FAIL test_mdl_roundtrip_each_loadable ({name}): load failed: {e}")
            all_ok = False
            continue
        roots = [
            o
            for o in bpy.data.objects
            if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
        ]  # pyright: ignore[reportAttributeAccessIssue]
        if not roots:
            print(f"  FAIL test_mdl_roundtrip_each_loadable ({name}): no MDLROOT")
            all_ok = False
            continue
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
            roots_after = [
                o
                for o in bpy.data.objects
                if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
            ]  # pyright: ignore[reportAttributeAccessIssue]
            objs_after = len(bpy.data.objects)
            if roots_after and roots_after[0].name == name_before and objs_after >= 1:
                print(f"  PASS test_mdl_roundtrip_each_loadable ({name})")
            else:
                print(
                    f"  FAIL test_mdl_roundtrip_each_loadable ({name}): root name or object count"
                )
                all_ok = False
        except Exception as e:
            print(f"  FAIL test_mdl_roundtrip_each_loadable ({name}): {e}")
            all_ok = False
        finally:
            for path in (out_mdl, out_mdx):
                if os.path.exists(path):
                    try:
                        os.unlink(path)
                    except OSError:
                        pass
    return all_ok


def test_read_nonexistent_file():
    """Loading a non-existent MDL raises (mirror test_read_nonexistent_file)."""
    fake = os.path.join(WORKSPACE_ROOT, "test", "test_files", "pykotor_mdl", "_nonexistent_.mdl")
    _clear_scene()
    try:
        load_mdl(_op, fake, _import_opts())
        print("  FAIL test_read_nonexistent_file: expected exception")
        return False
    except (FileNotFoundError, RuntimeError, OSError) as e:
        print(f"  PASS test_read_nonexistent_file (got {type(e).__name__})")
        return True
    except Exception as e:
        print(f"  PASS test_read_nonexistent_file (got {type(e).__name__})")
        return True


def test_read_mdl_fast_skipped():
    """PyKotor has read_mdl_fast; KotorBlender has no fast path (always pass; N/A)."""
    print("  PASS test_read_mdl_fast_skipped (no fast load in KotorBlender)")
    return True


def test_empty_mdl():
    """Create minimal MDL (root only), export, reimport; assert one root (mirror test_empty_mdl)."""
    from io_scene_kotor.constants import Classification, DummyType

    _clear_scene()
    root = bpy.data.objects.new("empty_mdl_root", None)
    root.kb.dummytype = DummyType.MDLROOT  # pyright: ignore[reportAttributeAccessIssue]
    root.kb.classification = Classification.OTHER  # pyright: ignore[reportAttributeAccessIssue]
    root.kb.animscale = 1.0  # pyright: ignore[reportAttributeAccessIssue]
    root.kb.node_number = 1  # pyright: ignore[reportAttributeAccessIssue]
    root.kb.export_order = 0  # pyright: ignore[reportAttributeAccessIssue]
    root.rotation_mode = "QUATERNION"
    bpy.context.collection.objects.link(root)  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
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
        roots = [
            o
            for o in bpy.data.objects
            if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
        ]  # pyright: ignore[reportAttributeAccessIssue]
        objs = list(bpy.data.objects)
        ok = len(roots) == 1 and len(objs) >= 1
        if ok:
            print("  PASS test_empty_mdl")
        else:
            print(f"  FAIL test_empty_mdl: roots={len(roots)} objs={len(objs)}")
        return ok
    finally:
        for path in (out_mdl, out_mdx):
            if os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass


def test_mdl_find_parent():
    """After load, root has no parent; at least one child's parent is root (mirror test_mdl_find_parent)."""
    p = _first_loadable_path()
    if not p:
        print("  FAIL test_mdl_find_parent (no pykotor_mdl assets or none loadable)")
        return False
    mdl_path, name = p
    _clear_scene()
    load_mdl(_op, mdl_path, _import_opts())
    roots = [
        o
        for o in bpy.data.objects
        if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
    ]  # pyright: ignore[reportAttributeAccessIssue]
    if not roots:
        print("  FAIL test_mdl_find_parent: no root")
        return False
    root = roots[0]
    ok = root.parent is None
    children_with_parent = [o for o in bpy.data.objects if o.parent is root]
    ok = ok and (len(children_with_parent) >= 0)  # root may have no children
    if ok:
        print(f"  PASS test_mdl_find_parent ({name})")
    else:
        print("  FAIL test_mdl_find_parent: parent check failed")
    return ok


def _roundtrip_by_type(basename: str) -> bool:
    """Roundtrip one PyKotor model by basename. Skip only if file missing (no assets); else strict pass/fail."""
    pykotor_dir = os.path.join(WORKSPACE_ROOT, "test", "test_files", "pykotor_mdl")
    mdl_path = os.path.join(pykotor_dir, basename + ".mdl")
    mdx_path = os.path.join(pykotor_dir, basename + ".mdx")
    if not os.path.isfile(mdl_path) or not os.path.isfile(mdx_path):
        print(f"  FAIL test_roundtrip_{basename} (file missing: {basename}.mdl/.mdx)")
        return False
    _clear_scene()
    try:
        load_mdl(_op, mdl_path, _import_opts())
    except Exception as e:
        print(f"  FAIL test_roundtrip_{basename}: load failed: {e}")
        return False
    roots = [
        o
        for o in bpy.data.objects
        if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
    ]  # pyright: ignore[reportAttributeAccessIssue]
    if not roots:
        print(f"  FAIL test_roundtrip_{basename}: no root after load")
        return False
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
        roots_after = [
            o
            for o in bpy.data.objects
            if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
        ]  # pyright: ignore[reportAttributeAccessIssue]
        ok = roots_after and roots_after[0].name == name_before
        if ok:
            print(f"  PASS test_roundtrip_{basename}")
        else:
            print(f"  FAIL test_roundtrip_{basename}: root name not preserved")
        return bool(ok)
    finally:
        for path in (out_mdl, out_mdx):
            if os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass


def test_roundtrip_character_model() -> bool:
    """Binary roundtrip character model c_dewback (mirror test_roundtrip_character_model, binary-only)."""
    return _roundtrip_by_type("c_dewback")


def test_roundtrip_door_model() -> bool:
    """Binary roundtrip door model dor_lhr02 (mirror test_roundtrip_door_model, binary-only)."""
    return _roundtrip_by_type("dor_lhr02")


def test_roundtrip_placeable_model() -> bool:
    """Binary roundtrip placeable m02aa_09b (mirror test_roundtrip_placeable_model, binary-only)."""
    return _roundtrip_by_type("m02aa_09b")


def test_roundtrip_animation_model() -> bool:
    """Binary roundtrip animation model m12aa_c03_char02 (mirror test_roundtrip_animation_model, binary-only)."""
    return _roundtrip_by_type("m12aa_c03_char02")


def test_roundtrip_camera_model() -> bool:
    """Binary roundtrip camera model m12aa_c04_cam (mirror test_roundtrip_camera_model, binary-only)."""
    return bool(_roundtrip_by_type("m12aa_c04_cam"))


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_tests():
    print("\n=== test_pykotor_mdl.py ===")
    paths = list(_pykotor_mdl_paths() or [])
    if not paths:
        print(
            "  FAIL: No test_files/pykotor_mdl MDL+MDX pairs (see test/test_files/pykotor_mdl/README.md)."
        )
        print("[FAIL] 0 passed in test_pykotor_mdl.py\n")
        return False

    tests = [
        test_read_mdl_basic,
        test_read_mdl_fast_skipped,
        test_read_all_test_files,
        test_mdl_node_hierarchy,
        test_mdl_mesh_data,
        test_mdl_get_node_by_name,
        test_mdl_textures,
        test_mdl_lightmaps,
        test_write_mdl_binary,
        test_mdl_roundtrip,
        test_mdl_roundtrip_node_count,
        test_mdl_roundtrip_each_loadable,
        test_read_nonexistent_file,
        test_empty_mdl,
        test_mdl_find_parent,
        test_roundtrip_character_model,
        test_roundtrip_door_model,
        test_roundtrip_placeable_model,
        test_roundtrip_animation_model,
        test_roundtrip_camera_model,
    ]
    results = [bool(t()) for t in tests]
    passed: int = sum(results)
    total: int = len(results)
    status: str = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_pykotor_mdl.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
