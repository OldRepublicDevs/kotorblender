"""
test_io_lyt_load.py – io.lyt.load_lyt smoke tests (no game MDL required)

Run with:
    blender --background --python test/blender/test_io_lyt_load.py
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

from io_scene_kotor.constants import ImportOptions  # noqa: E402
from io_scene_kotor.io.lyt import load_lyt  # noqa: E402


class _Op:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def report(self, level: set[str] | dict[str, str], message: str) -> None:
        tag = next(iter(level)) if level else "INFO"
        self.messages.append((tag, message))


def test_load_lyt_roomcount_zero() -> bool:
    """roomcount 0 loads without attempting MDL files."""
    op = _Op()
    opts = ImportOptions()
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "area.lyt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("roomcount 0\n")
        load_lyt(op, path, opts)
    print("  PASS test_load_lyt_roomcount_zero")
    return True


def test_load_lyt_missing_mdl_warns() -> bool:
    """Room entry with missing .mdl produces WARNING, does not raise."""
    op = _Op()
    opts = ImportOptions()
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "area.lyt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("roomcount 1\n")
            f.write("noroomfile 0 0 0\n")
        load_lyt(op, path, opts)
        warns = [m for m in op.messages if m[0] == "WARNING" and "not found" in m[1].lower()]
        if not warns:
            print("  FAIL test_load_lyt_missing_mdl_warns: expected WARNING")
            return False
    print("  PASS test_load_lyt_missing_mdl_warns")
    return True


def run_tests() -> bool:
    print("\n=== test_io_lyt_load.py ===")
    results = [test_load_lyt_roomcount_zero(), test_load_lyt_missing_mdl_warns()]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
