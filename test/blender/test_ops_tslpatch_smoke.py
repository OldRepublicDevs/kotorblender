"""
test_ops_tslpatch_smoke.py – TSLPatchData load/save operators (no PyKotor)

Run with:
    blender --background --python test/blender/test_ops_tslpatch_smoke.py
"""

from __future__ import annotations

import os
import shutil
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

_OP_FINISHED = frozenset(("FINISHED",))


def test_tslpatch_save_and_load_roundtrip() -> bool:
    d = tempfile.mkdtemp(prefix="kb_tslpatch_")
    try:
        kb = bpy.context.scene.kb
        kb.tslpatchdata_folder = d
        kb.tslpatchdata_ini_body = "[settings]\nmodname=RoundTripMod\nauthor=Tester\n"
        r_save = bpy.ops.kb.tslpatchdata_save_changes_ini()
        ini = os.path.join(d, "changes.ini")
        if r_save != _OP_FINISHED or not os.path.isfile(ini):
            print(f"  FAIL save: {r_save!r} file_exists={os.path.isfile(ini)}")
            return False
        kb.tslpatchdata_ini_body = ""
        r_load = bpy.ops.kb.tslpatchdata_load_changes_ini()
        body = kb.tslpatchdata_ini_body or ""
        ok = r_load == _OP_FINISHED and "RoundTripMod" in body
        print(f"  {'PASS' if ok else 'FAIL'} test_tslpatch_save_and_load_roundtrip")
        return ok
    finally:
        shutil.rmtree(d, ignore_errors=True)


def run_tests() -> bool:
    print("\n=== test_ops_tslpatch_smoke.py ===")
    ok = test_tslpatch_save_and_load_roundtrip()
    status = "OK" if ok else "FAIL"
    print(f"\n[{status}] 1/1 passed in test_ops_tslpatch_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
