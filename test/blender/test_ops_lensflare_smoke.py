"""
test_ops_lensflare_smoke.py – bpy.ops.kb.add_lens_flare

Run with:
    blender --background --python test/blender/test_ops_lensflare_smoke.py
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

import io_scene_kotor.ops.lensflare.add as _kb_lensflare_add  # noqa: F401, E402
import io_scene_kotor.ops.lensflare.delete as _kb_lensflare_del  # noqa: F401, E402
import io_scene_kotor.ops.lensflare.move as _kb_lensflare_move  # noqa: F401, E402

from io_scene_kotor.constants import Direction  # noqa: E402


def test_ops_add_lens_flare_finishes() -> bool:
    bpy.ops.object.light_add(type="POINT", location=(0, 0, 0))
    light = bpy.context.active_object
    if light is None or light.type != "LIGHT":
        print("  FAIL: no light")
        return False
    light.kb.lensflares = True
    before = len(light.kb.flare_list)
    bpy.context.view_layer.objects.active = light
    light.select_set(True)
    if not bpy.ops.kb.add_lens_flare.poll():
        print("  FAIL add_lens_flare poll() False")
        bpy.data.objects.remove(light, do_unlink=True)
        return False
    r = bpy.ops.kb.add_lens_flare()
    n_after = len(light.kb.flare_list)
    ok = r == {"FINISHED"} and n_after == before + 1
    bpy.data.objects.remove(light, do_unlink=True)
    if ok:
        print("  PASS test_ops_add_lens_flare_finishes")
    else:
        print(f"  FAIL result={r!r} flares={n_after} (was {before})")
    return ok


def _light_with_flares() -> bpy.types.Object:
    bpy.ops.object.light_add(type="POINT", location=(0, 0, 0))
    light = bpy.context.active_object
    assert light is not None and light.type == "LIGHT"
    light.kb.lensflares = True
    bpy.context.view_layer.objects.active = light
    light.select_set(True)
    bpy.ops.kb.add_lens_flare()
    bpy.ops.kb.add_lens_flare()
    return light


def test_ops_lens_flare_move_and_delete() -> bool:
    light = _light_with_flares()
    try:
        kb = light.kb
        if len(kb.flare_list) != 2:
            print("  FAIL lensflare move/delete: need 2 flares")
            return False
        kb.flare_list_idx = 0
        r1 = bpy.ops.kb.move_lens_flare(direction=Direction.DOWN)
        if r1 != {"FINISHED"}:
            print(f"  FAIL move_lens_flare: {r1!r}")
            return False
        kb.flare_list_idx = 0
        r2 = bpy.ops.kb.delete_lens_flare()
        ok = r2 == {"FINISHED"} and len(kb.flare_list) == 1
        if ok:
            print("  PASS test_ops_lens_flare_move_and_delete")
        else:
            print(f"  FAIL delete: {r2!r} len={len(kb.flare_list)}")
        return ok
    finally:
        bpy.data.objects.remove(light, do_unlink=True)


def run_tests() -> bool:
    print("\n=== test_ops_lensflare_smoke.py ===")
    results = [test_ops_add_lens_flare_finishes(), test_ops_lens_flare_move_and_delete()]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed in test_ops_lensflare_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
