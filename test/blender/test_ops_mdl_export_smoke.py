"""
test_ops_mdl_export_smoke.py – bpy.ops.kb.mdlexport matches save_mdl pipeline

Run with:
    blender --background --python test/blender/test_ops_mdl_export_smoke.py
"""

from __future__ import annotations

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

from io_scene_kotor.constants import Classification, DummyType, MeshType  # noqa: E402
from io_scene_kotor.scene.modelnode.danglymesh import CONSTRAINTS  # noqa: E402


def _clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)


def _make_scene() -> bpy.types.Object:
    root = bpy.data.objects.new("exp_root", None)
    root.kb.dummytype = DummyType.MDLROOT
    root.kb.classification = Classification.OTHER
    root.kb.animscale = 1.0
    root.kb.node_number = 1
    root.kb.export_order = 0
    root.rotation_mode = "QUATERNION"
    bpy.context.collection.objects.link(root)

    mesh = bpy.data.meshes.new("tri")
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    mesh.update()
    if "UVMap" not in mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    obj = bpy.data.objects.new("tri", mesh)
    obj.parent = root
    obj.rotation_mode = "QUATERNION"
    obj.kb.meshtype = MeshType.TRIMESH
    obj.kb.node_number = 2
    obj.kb.export_order = 1
    mesh.materials.append(bpy.data.materials.new(name="m"))
    bpy.context.collection.objects.link(obj)
    return root


def _make_scene_with_walkmesh() -> bpy.types.Object:
    """Single trimesh plus one AABB walkmesh (permits .wok export when walkmeshes enabled)."""
    root = _make_scene()
    mesh = bpy.data.meshes.new("walk")
    mesh.from_pydata([(2, 0, 0), (3, 0, 0), (2, 1, 0)], [], [(0, 1, 2)])
    mesh.update()
    if "UVMap" not in mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    wok = bpy.data.objects.new("walk", mesh)
    wok.parent = root
    wok.rotation_mode = "QUATERNION"
    wok.kb.meshtype = MeshType.AABB
    wok.kb.node_number = 3
    wok.kb.export_order = 2
    mesh.materials.append(bpy.data.materials.new(name="wm"))
    bpy.context.collection.objects.link(wok)
    return root


def _make_scene_with_dangly() -> bpy.types.Object:
    """MDL root with a single danglymesh (exercises DanglymeshNode export path)."""
    root = bpy.data.objects.new("dangly_root", None)
    root.kb.dummytype = DummyType.MDLROOT
    root.kb.classification = Classification.OTHER
    root.kb.animscale = 1.0
    root.kb.node_number = 1
    root.kb.export_order = 0
    root.rotation_mode = "QUATERNION"
    bpy.context.collection.objects.link(root)

    mesh = bpy.data.meshes.new("dangly")
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    mesh.update()
    if "UVMap" not in mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    obj = bpy.data.objects.new("dangly", mesh)
    obj.parent = root
    obj.rotation_mode = "QUATERNION"
    obj.kb.meshtype = MeshType.DANGLYMESH
    obj.kb.node_number = 2
    obj.kb.export_order = 1
    obj.kb.period = 1.0
    obj.kb.tightness = 1.0
    obj.kb.displacement = 1.0
    vg = obj.vertex_groups.new(name=CONSTRAINTS)
    vg.add([0, 1, 2], 0.5, "REPLACE")
    obj.kb.constraints = CONSTRAINTS
    mesh.materials.append(bpy.data.materials.new(name="dm"))
    bpy.context.collection.objects.link(obj)
    return root


def test_ops_mdlexport_writes_file() -> bool:
    _clear_scene()
    _make_scene()
    with tempfile.NamedTemporaryFile(suffix=".mdl", delete=False) as f:
        path = f.name
    mdx = path[:-4] + ".mdx"
    try:
        bpy.ops.object.select_all(action="DESELECT")
        ok_run = True
        try:
            bpy.ops.kb.mdlexport(
                filepath=path,
                export_animations=False,
                export_walkmeshes=False,
            )
        except Exception as e:
            print(f"  FAIL test_ops_mdlexport_writes_file: {e}")
            ok_run = False
        if not ok_run:
            return False
        if not (os.path.isfile(path) and os.path.getsize(path) > 0):
            print("  FAIL test_ops_mdlexport_writes_file: mdl missing")
            return False
    finally:
        for p in (path, mdx):
            if os.path.isfile(p):
                os.unlink(p)
        _clear_scene()
    print("  PASS test_ops_mdlexport_writes_file")
    return True


def test_ops_mdlexport_animations_and_walkmeshes() -> bool:
    """Exercise save_mdl with export_animations and export_walkmeshes both True (analyst gap)."""
    _clear_scene()
    _make_scene_with_walkmesh()
    with tempfile.NamedTemporaryFile(suffix=".mdl", delete=False) as f:
        path = f.name
    mdx = path[:-4] + ".mdx"
    wok = path[:-4] + ".wok"
    try:
        bpy.ops.object.select_all(action="DESELECT")
        root = next(o for o in bpy.context.collection.objects if getattr(o.kb, "dummytype", None) == DummyType.MDLROOT)
        root.select_set(True)
        bpy.context.view_layer.objects.active = root
        try:
            bpy.ops.kb.mdlexport(
                filepath=path,
                export_animations=True,
                export_walkmeshes=True,
            )
        except Exception as e:
            print(f"  FAIL test_ops_mdlexport_animations_and_walkmeshes: {e}")
            return False
        if not (os.path.isfile(path) and os.path.getsize(path) > 0):
            print("  FAIL test_ops_mdlexport_animations_and_walkmeshes: mdl missing")
            return False
        if not (os.path.isfile(mdx) and os.path.getsize(mdx) > 0):
            print("  FAIL test_ops_mdlexport_animations_and_walkmeshes: mdx missing")
            return False
        if not (os.path.isfile(wok) and os.path.getsize(wok) > 0):
            print("  FAIL test_ops_mdlexport_animations_and_walkmeshes: wok missing")
            return False
    finally:
        for p in (path, mdx, wok):
            if os.path.isfile(p):
                os.unlink(p)
        _clear_scene()
    print("  PASS test_ops_mdlexport_animations_and_walkmeshes")
    return True


def test_ops_mdlexport_danglymesh() -> bool:
    _clear_scene()
    _make_scene_with_dangly()
    with tempfile.NamedTemporaryFile(suffix=".mdl", delete=False) as f:
        path = f.name
    mdx = path[:-4] + ".mdx"
    try:
        bpy.ops.object.select_all(action="DESELECT")
        root = next(o for o in bpy.context.collection.objects if getattr(o.kb, "dummytype", None) == DummyType.MDLROOT)
        root.select_set(True)
        bpy.context.view_layer.objects.active = root
        try:
            bpy.ops.kb.mdlexport(
                filepath=path,
                export_animations=False,
                export_walkmeshes=False,
            )
        except Exception as e:
            print(f"  FAIL test_ops_mdlexport_danglymesh: {e}")
            return False
        if not (os.path.isfile(path) and os.path.getsize(path) > 0):
            print("  FAIL test_ops_mdlexport_danglymesh: mdl missing")
            return False
        if not (os.path.isfile(mdx) and os.path.getsize(mdx) > 0):
            print("  FAIL test_ops_mdlexport_danglymesh: mdx missing")
            return False
    finally:
        for p in (path, mdx):
            if os.path.isfile(p):
                os.unlink(p)
        _clear_scene()
    print("  PASS test_ops_mdlexport_danglymesh")
    return True


def run_tests() -> bool:
    print("\n=== test_ops_mdl_export_smoke.py ===")
    results = [
        test_ops_mdlexport_writes_file(),
        test_ops_mdlexport_animations_and_walkmeshes(),
        test_ops_mdlexport_danglymesh(),
    ]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed test_ops_mdl_export_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
