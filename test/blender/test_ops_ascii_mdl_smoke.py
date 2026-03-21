"""
test_ops_ascii_mdl_smoke.py – bpy.ops.kb.asciimdlexport / asciimdlimport

Run with:
    blender --background --python test/blender/test_ops_ascii_mdl_smoke.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from typing import TYPE_CHECKING

import bpy

if TYPE_CHECKING:
    from io_scene_kotor.ui.props.object import ObjectPropertyGroup

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

MODULE = "bl_ext.user_default.io_scene_kotor"
if MODULE not in bpy.context.preferences.addons:  # pyright: ignore[reportOptionalMemberAccess]
    bpy.ops.preferences.addon_enable(module=MODULE)

import io_scene_kotor.ops.mdl.ascii_export as _kb_ascii_export  # noqa: F401, E402
import io_scene_kotor.ops.mdl.ascii_importop as _kb_ascii_import  # noqa: F401, E402
from io_scene_kotor.constants import Classification, DummyType, MeshType  # noqa: E402


def _clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)


def _make_root_and_trimesh() -> bpy.types.Object:
    root = bpy.data.objects.new("ascii_ops_root", None)
    kb_r = getattr(root, "kb", None)
    if kb_r is None:
        print("  FAIL: root.kb is None")
        return None  # pyright: ignore[reportReturnType]
    kb_r.dummytype = DummyType.MDLROOT
    kb_r.classification = Classification.OTHER
    kb_r.animscale = 1.0
    kb_r.node_number = 1
    kb_r.export_order = 0
    root.rotation_mode = "QUATERNION"
    bpy.context.collection.objects.link(root)  # pyright: ignore[reportOptionalMemberAccess]

    mesh = bpy.data.meshes.new("tri_ops")
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    mesh.update()
    if "UVMap" not in mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    obj = bpy.data.objects.new("tri_ops", mesh)
    obj.parent = root
    obj.rotation_mode = "QUATERNION"
    kb_o: ObjectPropertyGroup | None = getattr(obj, "kb", None)
    if kb_o is None:
        print("  FAIL: obj.kb is None")
        return None  # pyright: ignore[reportReturnType]
    kb_o.meshtype = MeshType.TRIMESH
    kb_o.node_number = 2
    kb_o.export_order = 1
    mesh.materials.append(bpy.data.materials.new(name="m_ascii_ops"))
    assert bpy.context.collection is not None, "bpy.context.collection is None"
    bpy.context.collection.objects.link(obj)
    return root


def _add_walkmesh_child(root: bpy.types.Object) -> None:
    mesh = bpy.data.meshes.new("ascii_walk")
    mesh.from_pydata([(2, 0, 0), (3, 0, 0), (2, 1, 0)], [], [(0, 1, 2)])
    mesh.update()
    if "UVMap" not in mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    wok = bpy.data.objects.new("ascii_walk", mesh)
    wok.parent = root
    wok.rotation_mode = "QUATERNION"
    kb: ObjectPropertyGroup | None = getattr(wok, "kb", None)
    if kb is None:
        print("  FAIL: wok.kb is None")
        return
    kb.meshtype = MeshType.AABB
    kb.node_number = 3
    kb.export_order = 2
    mesh.materials.append(bpy.data.materials.new(name="wm_ascii_ops"))
    bpy.context.collection.objects.link(wok)  # pyright: ignore[reportOptionalMemberAccess]


def test_ops_ascii_mdl_export_import_roundtrip() -> bool:
    _clear_scene()
    _make_root_and_trimesh()
    with tempfile.NamedTemporaryFile(suffix=".mdl.ascii", delete=False) as f:
        path = f.name
    try:
        try:
            bpy.ops.kb.asciimdlexport(  # pyright: ignore[reportAttributeAccessIssue]
                filepath=path,
                check_existing=False,
                export_animations=False,
                export_walkmeshes=False,
            )
        except Exception as e:
            print(f"  FAIL asciimdlexport: {e}")
            return False
        if not os.path.isfile(path) or os.path.getsize(path) < 50:
            print("  FAIL: export file missing or too small")
            return False
        text = open(path, encoding="utf-8", errors="replace").read()
        if "newmodel" not in text.lower():
            print("  FAIL: export missing newmodel")
            return False

        _clear_scene()
        try:
            bpy.ops.kb.asciimdlimport(  # pyright: ignore[reportAttributeAccessIssue]
                filepath=path,
                import_geometry=True,
                import_animations=False,
                import_walkmeshes=False,
                build_materials=False,
                build_armature=False,
            )
        except Exception as e:
            print(f"  FAIL asciimdlimport: {e.__class__.__name__}: {e}")
            return False

        roots = [
            o
            for o in bpy.data.objects
            if getattr(o, "kb", None) and o.kb.dummytype == DummyType.MDLROOT  # pyright: ignore[reportAttributeAccessIssue]
        ]
        meshes = [o for o in bpy.data.objects if o.type == "MESH"]
        ok = len(roots) >= 1 and len(meshes) >= 1
        _clear_scene()
        if ok:
            print("  PASS test_ops_ascii_mdl_export_import_roundtrip")
        else:
            print(f"  FAIL: roots={len(roots)} meshes={len(meshes)}")
        return ok
    finally:
        if os.path.isfile(path):
            os.unlink(path)


def test_ops_ascii_mdl_export_animations_walkmeshes_writes_aabb() -> bool:
    """Exercise asciimdlexport with export_animations and export_walkmeshes True."""
    _clear_scene()
    root = _make_root_and_trimesh()
    _add_walkmesh_child(root)
    with tempfile.NamedTemporaryFile(suffix=".mdl.ascii", delete=False) as f:
        path = f.name
    try:
        bpy.ops.object.select_all(action="DESELECT")
        root.select_set(True)
        bpy.context.view_layer.objects.active = root  # pyright: ignore[reportOptionalMemberAccess]
        try:
            bpy.ops.kb.asciimdlexport(  # pyright: ignore[reportAttributeAccessIssue]
                filepath=path,
                check_existing=False,
                export_animations=True,
                export_walkmeshes=True,
            )
        except Exception as e:
            print(f"  FAIL asciimdlexport (anim+walk): {e}")
            return False
        if not os.path.isfile(path) or os.path.getsize(path) < 80:
            print("  FAIL: ascii export missing or too small")
            return False
        text = open(path, encoding="utf-8", errors="replace").read().lower()
        if "aabb" not in text and "ascii_walk" not in text:
            print("  FAIL: expected AABB/walkmesh-related content in ASCII export")
            return False
    finally:
        if os.path.isfile(path):
            os.unlink(path)
        _clear_scene()
    print("  PASS test_ops_ascii_mdl_export_animations_walkmeshes_writes_aabb")
    return True


def run_tests() -> bool:
    print("\n=== test_ops_ascii_mdl_smoke.py ===")
    results = [
        test_ops_ascii_mdl_export_import_roundtrip(),
        test_ops_ascii_mdl_export_animations_walkmeshes_writes_aabb(),
    ]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed test_ops_ascii_mdl_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
