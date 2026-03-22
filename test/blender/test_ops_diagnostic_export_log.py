"""
test_ops_diagnostic_export_log.py – Export operators emit structured diagnostic log lines

Run with:
    blender --background --python test/blender/test_ops_diagnostic_export_log.py
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile

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

from io_scene_kotor.constants import Classification, DummyType, MeshType  # noqa: E402


class _ListHandler(logging.Handler):
    def __init__(self, out: list[str]) -> None:
        super().__init__()
        self._out = out

    def emit(self, record: logging.LogRecord) -> None:
        self._out.append(self.format(record))


def _clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)


def _make_minimal_mdl_root_scene() -> None:
    root = bpy.data.objects.new("diag_exp_root", None)
    root.kb.dummytype = DummyType.MDLROOT
    root.kb.classification = Classification.OTHER
    root.kb.animscale = 1.0
    root.kb.node_number = 1
    root.kb.export_order = 0
    root.rotation_mode = "QUATERNION"
    bpy.context.collection.objects.link(root)

    mesh = bpy.data.meshes.new("diag_tri")
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    mesh.update()
    if "UVMap" not in mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    obj = bpy.data.objects.new("diag_tri", mesh)
    obj.parent = root
    obj.rotation_mode = "QUATERNION"
    obj.kb.meshtype = MeshType.TRIMESH
    obj.kb.node_number = 2
    obj.kb.export_order = 1
    mesh.materials.append(bpy.data.materials.new(name="diag_m"))
    bpy.context.collection.objects.link(obj)


def test_mdlexport_emits_op_start_op_end_ok() -> bool:
    _clear_scene()
    _make_minimal_mdl_root_scene()
    root = logging.getLogger("io_scene_kotor")
    messages: list[str] = []
    handler = _ListHandler(messages)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)
    prev_level = root.level
    root.setLevel(logging.INFO)
    path = ""
    mdx = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".mdl", delete=False) as f:
            path = f.name
        mdx = path[:-4] + ".mdx"
        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.kb.mdlexport(
            filepath=path,
            export_animations=False,
            export_walkmeshes=False,
        )
    except Exception as ex:
        print(f"  FAIL test_mdlexport_emits_op_start_op_end_ok: {ex!r}")
        return False
    finally:
        root.removeHandler(handler)
        root.setLevel(prev_level)
        for p in (path, mdx):
            if p and os.path.isfile(p):
                os.unlink(p)
        _clear_scene()

    joined = " ".join(messages)
    ok = "event=op_start" in joined and "event=op_end" in joined
    ok = ok and "operator_id=kb.mdlexport" in joined
    ok = ok and "entry=direct" in joined
    ok = ok and "reason_code=OK" in joined
    ok = ok and "work_done=True" in joined
    if ok:
        print("  PASS test_mdlexport_emits_op_start_op_end_ok")
    else:
        print(f"  FAIL test_mdlexport_emits_op_start_op_end_ok messages={messages!r}")
    return ok


def run_tests() -> bool:
    print("\n=== test_ops_diagnostic_export_log.py ===")
    ok = test_mdlexport_emits_op_start_op_end_ok()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_ops_diagnostic_export_log.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
