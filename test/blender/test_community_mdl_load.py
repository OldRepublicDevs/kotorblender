"""
test_community_mdl_load.py – Blender background-mode test

Ensures KotorBlender supports both:
- Unfixed community models (BINS.zip) in test/test_files/unfixed/
- Fixed community models (converted.rar) in test/test_files/fixed/converted/

All listed MDLs must load. Fails if test_files/fixed or test_files/unfixed have no MDL+MDX pairs.

Run with:
    blender --background --python test/blender/test_community_mdl_load.py
"""

from __future__ import annotations

import os
import sys

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

from io_scene_kotor.constants import DummyType, ImportOptions
from io_scene_kotor.io.mdl import load_mdl

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


def _fixed_mdl_paths() -> Generator[tuple[str, str], None, None]:
    """Yield (mdl_path, name) for each .mdl in test_files/fixed that has a sibling .mdx."""
    fixed_base = os.path.join(WORKSPACE_ROOT, "test", "test_files", "fixed")
    if not os.path.isdir(fixed_base):
        return
    # RAR extracts into fixed/converted/
    for subdir in ("", "converted"):
        search_dir = os.path.join(fixed_base, subdir) if subdir else fixed_base
        if not os.path.isdir(search_dir):
            continue
        for entry in os.listdir(search_dir):
            if not entry.lower().endswith(".mdl"):
                continue
            mdl_path = os.path.join(search_dir, entry)
            if not os.path.isfile(mdl_path):
                continue
            mdx_path = os.path.splitext(mdl_path)[0] + ".mdx"
            if not os.path.isfile(mdx_path):
                continue
            name = os.path.splitext(entry)[0]
            yield mdl_path, name


def _unfixed_mdl_paths() -> Generator[tuple[str, str], None, None]:
    """Yield (mdl_path, name) for each .mdl in test_files/unfixed (BINS.zip) with sibling .mdx."""
    unfixed_base = os.path.join(WORKSPACE_ROOT, "test", "test_files", "unfixed")
    if not os.path.isdir(unfixed_base):
        return
    for entry in os.listdir(unfixed_base):
        if not entry.lower().endswith(".mdl"):
            continue
        mdl_path = os.path.join(unfixed_base, entry)
        if not os.path.isfile(mdl_path):
            continue
        mdx_path = os.path.splitext(mdl_path)[0] + ".mdx"
        if not os.path.isfile(mdx_path):
            continue
        name = os.path.splitext(entry)[0]
        yield mdl_path, name


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_load_all_fixed_mdls() -> bool:
    """Load each fixed community MDL; assert at least one MDLROOT, node count > 0, and root name."""
    paths = list(_fixed_mdl_paths())
    if not paths:
        print(
            "  FAIL test_load_all_fixed_mdls (no test_files/fixed MDL+MDX pairs; add fixed/converted assets)"
        )
        return False

    all_ok = True
    for mdl_path, name in paths:
        _clear_scene()
        try:
            opts = ImportOptions()
            opts.import_geometry = True
            opts.import_animations = False
            opts.import_walkmeshes = False
            opts.build_materials = False
            opts.build_armature = False
            load_mdl(_op, mdl_path, opts)
            roots = [
                o
                for o in bpy.data.objects
                if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
            ]  # pyright: ignore[reportAttributeAccessIssue]
            objs = list(bpy.data.objects)
            if len(roots) < 1:
                print(f"  FAIL test_load_all_fixed_mdls ({name}): no MDLROOT after load")
                all_ok = False
            elif len(objs) < 1:
                print(f"  FAIL test_load_all_fixed_mdls ({name}): no objects after load")
                all_ok = False
            elif not (roots[0].name and isinstance(roots[0].name, str)):
                print(f"  FAIL test_load_all_fixed_mdls ({name}): root has no valid name")
                all_ok = False
            else:
                print(f"  PASS test_load_all_fixed_mdls ({name})")
        except Exception as e:
            print(f"  FAIL test_load_all_fixed_mdls ({name}): {e}")
            all_ok = False
    return all_ok


def test_fixed_mdls_have_mesh_or_dummy() -> bool:
    """Each fixed MDL load yields at least one MESH or multiple objects (geometry or hierarchy)."""
    paths = list(_fixed_mdl_paths())
    if not paths:
        print("  FAIL test_fixed_mdls_have_mesh_or_dummy (no test_files/fixed MDL+MDX pairs)")
        return False

    all_ok = True
    for mdl_path, name in paths:
        _clear_scene()
        try:
            opts = ImportOptions()
            opts.import_geometry = True
            opts.import_animations = False
            opts.import_walkmeshes = False
            opts.build_materials = False
            opts.build_armature = False
            load_mdl(_op, mdl_path, opts)
            mesh_objs = [o for o in bpy.data.objects if o.type == "MESH"]
            total = len(bpy.data.objects)
            if total >= 1 and (len(mesh_objs) >= 1 or total >= 2):
                print(f"  PASS test_fixed_mdls_have_mesh_or_dummy ({name})")
            else:
                print(
                    f"  FAIL test_fixed_mdls_have_mesh_or_dummy ({name}): no mesh and single object"
                )
                all_ok = False
        except Exception as e:
            print(f"  FAIL test_fixed_mdls_have_mesh_or_dummy ({name}): {e}")
            all_ok = False
    return all_ok


def test_fixed_mdl_roundtrip_each() -> bool:
    """Roundtrip each fixed community MDL: load, save to temp, load again; assert root name preserved."""
    import tempfile

    from io_scene_kotor.constants import ExportOptions
    from io_scene_kotor.io.mdl import save_mdl

    paths = list(_fixed_mdl_paths())
    if not paths:
        print("  FAIL test_fixed_mdl_roundtrip_each (no test_files/fixed MDL+MDX pairs)")
        return False

    all_ok = True
    for mdl_path, name in paths:
        _clear_scene()
        try:
            opts = ImportOptions()
            opts.import_geometry = True
            opts.import_animations = False
            opts.import_walkmeshes = False
            opts.build_materials = False
            opts.build_armature = False
            load_mdl(_op, mdl_path, opts)
            roots = [
                o
                for o in bpy.data.objects
                if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
            ]  # pyright: ignore[reportAttributeAccessIssue]
            if not roots:
                print(f"  FAIL test_fixed_mdl_roundtrip_each ({name}): no root after load")
                all_ok = False
                continue
            name_before = roots[0].name
            with tempfile.NamedTemporaryFile(suffix=".mdl", delete=False) as f:
                out_mdl = f.name
            out_mdx = os.path.splitext(out_mdl)[0] + ".mdx"
            try:
                exp_opts = ExportOptions()
                exp_opts.export_animations = False
                exp_opts.export_walkmeshes = False
                save_mdl(_op, out_mdl, exp_opts)
                _clear_scene()
                load_mdl(_op, out_mdl, opts)
                roots_after = [
                    o
                    for o in bpy.data.objects
                    if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
                ]  # pyright: ignore[reportAttributeAccessIssue]
                if roots_after and roots_after[0].name == name_before:
                    print(f"  PASS test_fixed_mdl_roundtrip_each ({name})")
                else:
                    print(f"  FAIL test_fixed_mdl_roundtrip_each ({name}): root name not preserved")
                    all_ok = False
            finally:
                for path in (out_mdl, out_mdx):
                    if os.path.exists(path):
                        try:
                            os.unlink(path)
                        except OSError:
                            pass
        except Exception as e:
            print(f"  FAIL test_fixed_mdl_roundtrip_each ({name}): {e}")
            all_ok = False
    return all_ok


def test_load_all_unfixed_mdls() -> bool:
    """Load each unfixed (BINS.zip) community MDL; same assertions as fixed (root, nodes, name).
    Goal: KotorBlender supports both BINS and converted. If unfixed fail to load (e.g. reader
    expects K2 layout), test fails so we extend the reader; no silent skip."""
    paths = list(_unfixed_mdl_paths())
    if not paths:
        print(
            "  FAIL test_load_all_unfixed_mdls (no test_files/unfixed MDL+MDX pairs; add unfixed assets)"
        )
        return False

    all_ok = True
    for mdl_path, name in paths:
        _clear_scene()
        try:
            opts = ImportOptions()
            opts.import_geometry = True
            opts.import_animations = False
            opts.import_walkmeshes = False
            opts.build_materials = False
            opts.build_armature = False
            load_mdl(_op, mdl_path, opts)
            roots = [
                o
                for o in bpy.data.objects
                if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT
            ]  # pyright: ignore[reportAttributeAccessIssue]
            objs = list(bpy.data.objects)
            if len(roots) < 1:
                print(f"  FAIL test_load_all_unfixed_mdls ({name}): no MDLROOT after load")
                all_ok = False
            elif len(objs) < 1:
                print(f"  FAIL test_load_all_unfixed_mdls ({name}): no objects after load")
                all_ok = False
            elif not (roots[0].name and isinstance(roots[0].name, str)):
                print(f"  FAIL test_load_all_unfixed_mdls ({name}): root has no valid name")
                all_ok = False
            else:
                print(f"  PASS test_load_all_unfixed_mdls ({name})")
        except Exception as e:
            print(f"  FAIL test_load_all_unfixed_mdls ({name}): {e}")
            all_ok = False
    return all_ok


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_tests() -> bool:
    print("\n=== test_community_mdl_load.py ===")
    fixed_paths = list(_fixed_mdl_paths())
    unfixed_paths = list(_unfixed_mdl_paths())
    if not fixed_paths and not unfixed_paths:
        print("  FAIL: No test_files/fixed or unfixed MDL+MDX pairs found.")
        print(
            "  Add test_files/fixed/converted/ and test_files/unfixed/ (see test/test_files/README.md)."
        )
        print("[FAIL] 0/4 passed in test_community_mdl_load.py\n")
        return False

    results: list[bool] = [
        test_load_all_fixed_mdls(),
        test_fixed_mdls_have_mesh_or_dummy(),
        test_fixed_mdl_roundtrip_each(),
        test_load_all_unfixed_mdls(),
    ]
    passed: int = sum(results)
    total: int = len(results)
    status: str = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_community_mdl_load.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
