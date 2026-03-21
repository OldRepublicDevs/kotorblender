"""
test_pykotor_adapter_smoke.py – PyKotor adapter availability flags

Run with:
    blender --background --python test/blender/test_pykotor_adapter_smoke.py
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

from io_scene_kotor.constants import USE_PYKOTOR_READERS  # noqa: E402
from io_scene_kotor.vendor.pykotor_adapter import (  # noqa: E402
    PYKOTOR_AVAILABLE,
    get_use_pykotor_readers,
    is_pykotor_available,
)


def test_adapter_flags_consistent() -> bool:
    if is_pykotor_available() is not PYKOTOR_AVAILABLE:
        print("  FAIL is_pykotor_available() != PYKOTOR_AVAILABLE")
        return False
    expect_readers = bool(PYKOTOR_AVAILABLE and USE_PYKOTOR_READERS)
    if get_use_pykotor_readers() is not expect_readers:
        print(
            f"  FAIL get_use_pykotor_readers()={get_use_pykotor_readers()!r} "
            f"expected {expect_readers!r} (PYKOTOR_AVAILABLE={PYKOTOR_AVAILABLE}, "
            f"USE_PYKOTOR_READERS={USE_PYKOTOR_READERS})",
        )
        return False
    print("  PASS test_adapter_flags_consistent")
    return True


def run_tests() -> bool:
    print("\n=== test_pykotor_adapter_smoke.py ===")
    ok = test_adapter_flags_consistent()
    print(f"\n[{'OK' if ok else 'FAIL'}] test_pykotor_adapter_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
