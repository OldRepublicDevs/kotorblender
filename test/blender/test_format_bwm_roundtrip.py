"""
test_format_bwm_roundtrip.py – BWM writer → reader roundtrip (Blender context)

Requires Blender: format/bwm pulls in scene nodes (bpy / mathutils).

Run with:
    blender --background --python test/blender/test_format_bwm_roundtrip.py
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

from io_scene_kotor.format.bwm.reader import BwmReader  # noqa: E402
from io_scene_kotor.format.bwm.writer import BwmWriter  # noqa: E402
from io_scene_kotor.scene.modelnode.aabb import AabbNode  # noqa: E402
from io_scene_kotor.scene.modelnode.trimesh import FaceList  # noqa: E402
from io_scene_kotor.scene.walkmesh import Walkmesh  # noqa: E402


def test_bwm_write_read_roundtrip() -> bool:
    """Single-triangle WOK survives BwmWriter.save() → BwmReader.load()."""
    aabb = AabbNode("wg")
    aabb.verts = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    fl = FaceList()
    fl.vertices.append((0, 1, 2))
    fl.materials.append(0)
    fl.normals.append((0.0, 0.0, 1.0))
    aabb.facelist = fl

    wm = Walkmesh.from_aabb_node(aabb)
    path = os.path.join(os.environ.get("TEMP", "/tmp"), "kb_test_roundtrip.wok")
    try:
        BwmWriter(path, wm).save()
        loaded = BwmReader(path, "mdlroot").load()
        geom = loaded.root_node.find_node(lambda n: isinstance(n, AabbNode))
        if geom is None:
            print("  FAIL test_bwm_write_read_roundtrip: no AabbNode")
            return False
        if len(geom.verts) != 3:
            print(f"  FAIL test_bwm_write_read_roundtrip: vert count {len(geom.verts)}")
            return False
        if len(geom.facelist.vertices) != 1:
            print("  FAIL test_bwm_write_read_roundtrip: face count")
            return False
        exp = sorted(tuple(round(x, 5) for x in v) for v in aabb.verts)
        got = sorted(tuple(round(x, 5) for x in v) for v in geom.verts)
        if exp != got:
            print(f"  FAIL test_bwm_write_read_roundtrip: verts {got} != {exp}")
            return False
        print("  PASS test_bwm_write_read_roundtrip")
        return True
    finally:
        if os.path.isfile(path):
            os.unlink(path)


def run_tests() -> bool:
    print("\n=== test_format_bwm_roundtrip.py ===")
    ok = test_bwm_write_read_roundtrip()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_format_bwm_roundtrip.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
