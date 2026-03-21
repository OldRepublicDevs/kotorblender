"""
test_scene_modelnode_skin_dangly_saber.py – Skinmesh / Danglymesh / Lightsaber node classes

Run with:
    blender --background --python test/blender/test_scene_modelnode_skin_dangly_saber.py
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

from io_scene_kotor.constants import MeshType, NodeType  # noqa: E402
from io_scene_kotor.scene.modelnode.danglymesh import DanglymeshNode  # noqa: E402
from io_scene_kotor.scene.modelnode.lightsaber import LightsaberNode  # noqa: E402
from io_scene_kotor.scene.modelnode.skinmesh import SkinmeshNode  # noqa: E402


def test_skinmesh_node_type() -> bool:
    n = SkinmeshNode("s")
    ok = n.nodetype == NodeType.SKIN and n.meshtype == MeshType.SKIN
    print("  PASS test_skinmesh_node_type" if ok else "  FAIL test_skinmesh_node_type")
    return ok


def test_danglymesh_node_defaults() -> bool:
    n = DanglymeshNode("d")
    ok = (
        n.nodetype == NodeType.DANGLYMESH
        and n.meshtype == MeshType.DANGLYMESH
        and n.period == 1.0
        and n.tightness == 1.0
        and n.displacement == 1.0
    )
    print("  PASS test_danglymesh_node_defaults" if ok else "  FAIL test_danglymesh_node_defaults")
    return ok


def test_lightsaber_node_type() -> bool:
    n = LightsaberNode("l")
    ok = n.nodetype == NodeType.LIGHTSABER and n.meshtype == MeshType.LIGHTSABER
    print("  PASS test_lightsaber_node_type" if ok else "  FAIL test_lightsaber_node_type")
    return ok


def run_tests() -> bool:
    print("\n=== test_scene_modelnode_skin_dangly_saber.py ===")
    results = [
        test_skinmesh_node_type(),
        test_danglymesh_node_defaults(),
        test_lightsaber_node_type(),
    ]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
