"""
test_ops_rebuild_all_materials_smoke.py – bpy.ops.kb.rebuild_all_materials

Run with:
    blender --background --python test/blender/test_ops_rebuild_all_materials_smoke.py
"""

from __future__ import annotations

import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

MODULE = "bl_ext.user_default.io_scene_kotor"
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.constants import Classification, DummyType, MeshType  # noqa: E402
import io_scene_kotor.ops.rebuildallmaterials as _kb_rebuild_all  # noqa: F401, E402


def _tri(name: str, parent: bpy.types.Object) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    mesh.update()
    if "UVMap" not in mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    obj = bpy.data.objects.new(name, mesh)
    obj.parent = parent
    obj.kb.meshtype = MeshType.TRIMESH
    mesh.materials.append(bpy.data.materials.new(name=f"{name}_m"))
    bpy.context.collection.objects.link(obj)
    return obj


def test_ops_rebuild_all_materials_finishes() -> bool:
    root = bpy.data.objects.new("mdl_all_mat", None)
    root.kb.dummytype = DummyType.MDLROOT
    root.kb.classification = Classification.OTHER
    bpy.context.collection.objects.link(root)
    _tri("t1", root)
    _tri("t2", root)
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    bpy.context.view_layer.objects.active = root
    try:
        if not bpy.ops.kb.rebuild_all_materials.poll():
            print("  FAIL rebuild_all_materials poll() False")
            return False
        r = bpy.ops.kb.rebuild_all_materials()
        ok = r == {"FINISHED"}
        if ok:
            print("  PASS test_ops_rebuild_all_materials_finishes")
        else:
            print(f"  FAIL {r!r}")
        return ok
    finally:
        for o in list(bpy.data.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        for m in list(bpy.data.meshes):
            bpy.data.meshes.remove(m)
        for mat in list(bpy.data.materials):
            bpy.data.materials.remove(mat)


def run_tests() -> bool:
    print("\n=== test_ops_rebuild_all_materials_smoke.py ===")
    ok = test_ops_rebuild_all_materials_finishes()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_ops_rebuild_all_materials_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
