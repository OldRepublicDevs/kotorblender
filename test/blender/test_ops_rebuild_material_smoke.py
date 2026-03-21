"""
test_ops_rebuild_material_smoke.py – bpy.ops.kb.rebuild_material

Run with:
    blender --background --python test/blender/test_ops_rebuild_material_smoke.py
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

from io_scene_kotor.constants import MeshType  # noqa: E402
import io_scene_kotor.ops.rebuildmaterial as _kb_rebuild_mat  # noqa: F401, E402


def test_ops_rebuild_material_trimesh_finishes() -> bool:
    mesh = bpy.data.meshes.new("rb_mat_mesh")
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    mesh.update()
    if "UVMap" not in mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    obj = bpy.data.objects.new("rb_mat_obj", mesh)
    obj.kb.meshtype = MeshType.TRIMESH
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        if not bpy.ops.kb.rebuild_material.poll():
            print("  FAIL rebuild_material poll() False")
            return False
        r = bpy.ops.kb.rebuild_material()
        ok = r == {"FINISHED"}
        if ok:
            print("  PASS test_ops_rebuild_material_trimesh_finishes")
        else:
            print(f"  FAIL result={r!r}")
        return ok
    finally:
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(mesh)


def run_tests() -> bool:
    print("\n=== test_ops_rebuild_material_smoke.py ===")
    ok = test_ops_rebuild_material_trimesh_finishes()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_ops_rebuild_material_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
