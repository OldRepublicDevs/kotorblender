"""
test_ops_bwm_import_smoke.py – bpy.ops.kb.bwmimport on a minimal .wok

Run with:
    blender --background --python test/blender/test_ops_bwm_import_smoke.py
"""

from __future__ import annotations

import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from test_helpers import enable_addon  # noqa: E402

if not enable_addon():
    print("FATAL: could not enable KotorBlender addon")
    sys.exit(1)

from io_scene_kotor.format.bwm.reader import BwmReader  # noqa: E402
from io_scene_kotor.format.bwm.writer import BwmWriter  # noqa: E402
from io_scene_kotor.scene.modelnode.aabb import AabbNode  # noqa: E402
from io_scene_kotor.scene.modelnode.trimesh import FaceList  # noqa: E402
from io_scene_kotor.scene.walkmesh import Walkmesh  # noqa: E402


def _clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def test_ops_bwmimport_minimal_wok() -> bool:
    _clear_scene()
    aabb = AabbNode("wg")
    aabb.verts = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    fl = FaceList()
    fl.vertices.append((0, 1, 2))
    fl.materials.append(0)
    fl.normals.append((0.0, 0.0, 1.0))
    aabb.facelist = fl
    wm = Walkmesh.from_aabb_node(aabb)

    stem = "kb_test_bwm_smoke"
    path = os.path.join(os.environ.get("TEMP", "/tmp"), f"{stem}.wok")
    try:
        BwmWriter(path, wm).save()
        if not os.path.isfile(path):
            print("  FAIL test_ops_bwmimport_minimal_wok: writer did not create file")
            return False

        try:
            bpy.ops.kb.bwmimport(filepath=path)
        except Exception as e:
            print(f"  FAIL test_ops_bwmimport_minimal_wok: operator raised {e!r}")
            return False

        root_name = f"{stem}_wok"
        geom_name = f"{stem}_wok_wg"
        if root_name not in bpy.data.objects:
            print(f"  FAIL test_ops_bwmimport_minimal_wok: missing root {root_name!r}")
            return False
        if geom_name not in bpy.data.objects:
            print(f"  FAIL test_ops_bwmimport_minimal_wok: missing geom {geom_name!r}")
            return False
        root = bpy.data.objects[root_name]
        geom = bpy.data.objects[geom_name]
        if geom.parent != root:
            print("  FAIL test_ops_bwmimport_minimal_wok: geom not parented to root")
            return False
        if root.parent is not None:
            print("  FAIL test_ops_bwmimport_minimal_wok: expected world-root walkmesh root")
            return False

        # Pipeline matches reader naming (same as BwmReader roundtrip test)
        loaded = BwmReader(path, stem).load()
        g2 = loaded.root_node.find_node(lambda n: isinstance(n, AabbNode))
        if g2 is None or len(g2.verts) != 3:
            print("  FAIL test_ops_bwmimport_minimal_wok: reader sanity check failed")
            return False
    finally:
        if os.path.isfile(path):
            os.unlink(path)
        _clear_scene()

    print("  PASS test_ops_bwmimport_minimal_wok")
    return True


def run_tests() -> bool:
    print("\n=== test_ops_bwm_import_smoke.py ===")
    ok = test_ops_bwmimport_minimal_wok()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_ops_bwm_import_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
