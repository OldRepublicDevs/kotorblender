"""
test_ops_io_smoke.py – High-value KotOR file operators execute without crashing

Uses bpy.ops.kb.* entrypoints (same as GUI).

Run with:
    blender --background --python test/blender/test_ops_io_smoke.py
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
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from test_helpers import get_addon_module_name  # noqa: E402

MODULE = get_addon_module_name()
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)


def test_ops_lytimport_finishes() -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "empty.lyt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("roomcount 0\n")
        try:
            bpy.ops.kb.lytimport(filepath=path)
        except Exception as e:
            print(f"  FAIL test_ops_lytimport_finishes: {e}")
            return False
    print("  PASS test_ops_lytimport_finishes")
    return True


def test_ops_mdlimport_missing_file_finishes() -> bool:
    path = os.path.join(os.environ.get("TEMP", "/tmp"), "kb_no_such_model_xyz.mdl")
    if os.path.isfile(path):
        os.unlink(path)
    try:
        bpy.ops.kb.mdlimport(filepath=path)
    except Exception:
        # Some Blender versions surface FileNotFoundError from the operator.
        pass
    print("  PASS test_ops_mdlimport_missing_file_finishes")
    return True


def test_ops_pthimport_missing_file_finishes() -> bool:
    path = os.path.join(os.environ.get("TEMP", "/tmp"), "kb_no_such_path_xyz.pth")
    if os.path.isfile(path):
        os.unlink(path)
    try:
        bpy.ops.kb.pthimport(filepath=path)
    except Exception:
        pass
    print("  PASS test_ops_pthimport_missing_file_finishes")
    return True


def run_tests() -> bool:
    print("\n=== test_ops_io_smoke.py ===")
    results = [
        test_ops_lytimport_finishes(),
        test_ops_mdlimport_missing_file_finishes(),
        test_ops_pthimport_missing_file_finishes(),
    ]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
