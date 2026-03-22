"""
test_ops_diagnostic_import_log.py – Import operators emit structured diagnostic log lines

Run with:
    blender --background --python test/blender/test_ops_diagnostic_import_log.py
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


class _ListHandler(logging.Handler):
    def __init__(self, out: list[str]) -> None:
        super().__init__()
        self._out = out

    def emit(self, record: logging.LogRecord) -> None:
        self._out.append(self.format(record))


def test_mdlimport_emits_op_start_op_end() -> bool:
    root = logging.getLogger("io_scene_kotor")
    messages: list[str] = []
    handler = _ListHandler(messages)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    try:
        path = os.path.join(os.environ.get("TEMP", "/tmp"), "kb_diag_missing_xyz.mdl")
        if os.path.isfile(path):
            os.unlink(path)
        try:
            bpy.ops.kb.mdlimport(filepath=path)
        except Exception:
            pass
    finally:
        root.removeHandler(handler)

    joined = " ".join(messages)
    ok = "event=op_start" in joined and "event=op_end" in joined
    ok = ok and "operator_id=kb.mdlimport" in joined
    ok = ok and "entry=direct" in joined
    ok = ok and "reason_code=MISSING_FILE" in joined
    if ok:
        print("  PASS test_mdlimport_emits_op_start_op_end")
    else:
        print(f"  FAIL test_mdlimport_emits_op_start_op_end messages={messages!r}")
    return ok


def run_tests() -> bool:
    print("\n=== test_ops_diagnostic_import_log.py ===")
    ok = test_mdlimport_emits_op_start_op_end()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_ops_diagnostic_import_log.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
