"""
test_ops_resource_helpers.py – ops.module.resource_helpers (LOOSE storage + IO helpers)

Run with:
    blender --background --python test/blender/test_ops_resource_helpers.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from types import SimpleNamespace

import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

MODULE = "bl_ext.user_default.io_scene_kotor"
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.constants import ResourceStorage  # noqa: E402
from io_scene_kotor.ops.module.resource_helpers import (  # noqa: E402
    add_resource_entry,
    clear_resource_list,
    resource_entry_bytes,
    temp_file_with_suffix,
    write_bytes_to_filepath,
)


class _FakeResourceList:
    def __init__(self) -> None:
        self._rows: list[SimpleNamespace] = []

    def add(self) -> SimpleNamespace:
        e = SimpleNamespace(
            label="",
            resref="",
            restype_ext="",
            storage="",
            erf_path="",
            loose_path="",
        )
        self._rows.append(e)
        return e

    def clear(self) -> None:
        self._rows.clear()


def test_add_clear_resource_entry() -> bool:
    kb = SimpleNamespace(resource_list=_FakeResourceList())
    add_resource_entry(
        kb,
        label="L",
        resref="test",
        restype_ext=".mdl",
        storage=ResourceStorage.LOOSE,
        loose_path="/tmp/x",
    )
    if len(kb.resource_list._rows) != 1:
        print("  FAIL test_add_clear_resource_entry: add")
        return False
    e = kb.resource_list._rows[0]
    if e.resref != "test" or e.restype_ext != "mdl":
        print("  FAIL test_add_clear_resource_entry: fields")
        return False
    clear_resource_list(kb)
    if kb.resource_list._rows:
        print("  FAIL test_add_clear_resource_entry: clear")
        return False
    print("  PASS test_add_clear_resource_entry")
    return True


def test_resource_entry_bytes_loose() -> bool:
    data = b"KOTOR\x00"
    path = temp_file_with_suffix(".bin", data)
    try:
        kb = SimpleNamespace(resource_list=_FakeResourceList())
        add_resource_entry(
            kb,
            label="f",
            resref="f",
            restype_ext="bin",
            storage=ResourceStorage.LOOSE,
            loose_path=path,
        )
        got = resource_entry_bytes(kb.resource_list._rows[0])
        if got != data:
            print(f"  FAIL test_resource_entry_bytes_loose: {got!r}")
            return False
    finally:
        if os.path.isfile(path):
            os.unlink(path)
    print("  PASS test_resource_entry_bytes_loose")
    return True


def test_write_bytes_to_filepath() -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        fp = os.path.join(tmp, "sub", "out.bin")
        write_bytes_to_filepath(b"abc", fp)
        if not os.path.isfile(fp) or open(fp, "rb").read() != b"abc":
            print("  FAIL test_write_bytes_to_filepath")
            return False
    print("  PASS test_write_bytes_to_filepath")
    return True


def run_tests() -> bool:
    print("\n=== test_ops_resource_helpers.py ===")
    results = [
        test_add_clear_resource_entry(),
        test_resource_entry_bytes_loose(),
        test_write_bytes_to_filepath(),
    ]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
