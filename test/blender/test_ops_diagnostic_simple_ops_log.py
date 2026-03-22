"""
test_ops_diagnostic_simple_ops_log.py – run_simple_operator_logged operators

Run with:
    blender --background --python test/blender/test_ops_diagnostic_simple_ops_log.py
"""

from __future__ import annotations

import logging
import os
import sys

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from test_helpers import get_addon_module_name  # noqa: E402

MODULE = get_addon_module_name()
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.constants import MeshType  # noqa: E402


class _ListHandler(logging.Handler):
    def __init__(self, out: list[str]) -> None:
        super().__init__()
        self._out = out

    def emit(self, record: logging.LogRecord) -> None:
        self._out.append(self.format(record))


def test_open_addon_preferences_emits_op_start_op_end() -> bool:
    root = logging.getLogger("io_scene_kotor")
    messages: list[str] = []
    handler = _ListHandler(messages)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)
    prev_level = root.level
    root.setLevel(logging.INFO)
    try:
        bpy.ops.kb.open_addon_preferences()
    finally:
        root.removeHandler(handler)
        root.setLevel(prev_level)

    joined = " ".join(messages)
    ok = "event=op_start" in joined and "event=op_end" in joined
    ok = ok and "operator_id=kb.open_addon_preferences" in joined
    if ok:
        print("  PASS test_open_addon_preferences_emits_op_start_op_end")
    else:
        print(f"  FAIL test_open_addon_preferences_emits_op_start_op_end messages={messages!r}")
    return ok


def test_rebuild_material_emits_op_start_op_end() -> bool:
    mesh = bpy.data.meshes.new("diag_simple_rb_mesh")
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    mesh.update()
    if "UVMap" not in mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    obj = bpy.data.objects.new("diag_simple_rb_obj", mesh)
    obj.kb.meshtype = MeshType.TRIMESH
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    root = logging.getLogger("io_scene_kotor")
    messages: list[str] = []
    handler = _ListHandler(messages)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)
    prev_level = root.level
    root.setLevel(logging.INFO)
    try:
        if not bpy.ops.kb.rebuild_material.poll():
            print("  FAIL rebuild_material poll() False")
            return False
        bpy.ops.kb.rebuild_material()
    finally:
        root.removeHandler(handler)
        root.setLevel(prev_level)
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(mesh)

    joined = " ".join(messages)
    ok = "event=op_start" in joined and "event=op_end" in joined
    ok = ok and "operator_id=kb.rebuild_material" in joined
    ok = ok and "reason_code=OK" in joined and "work_done=True" in joined
    if ok:
        print("  PASS test_rebuild_material_emits_op_start_op_end")
    else:
        print(f"  FAIL test_rebuild_material_emits_op_start_op_end messages={messages!r}")
    return ok


def run_tests() -> bool:
    print("\n=== test_ops_diagnostic_simple_ops_log.py ===")
    results = [
        test_open_addon_preferences_emits_op_start_op_end(),
        test_rebuild_material_emits_op_start_op_end(),
    ]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
