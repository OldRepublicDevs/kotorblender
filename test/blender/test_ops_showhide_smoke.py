"""
test_ops_showhide_smoke.py – kb hide/show walkmeshes, untextured, blockers, emitters, lights

Run with:
    blender --background --python test/blender/test_ops_showhide_smoke.py
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

import io_scene_kotor.ops.showhideobjects as _kb_showhide  # noqa: F401, E402
from io_scene_kotor.constants import NULL, MeshType  # noqa: E402


def _make_aabb_walkmesh(name: str) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.kb.meshtype = MeshType.AABB
    bpy.context.collection.objects.link(obj)
    return obj


def test_hide_show_walkmeshes_roundtrip() -> bool:
    wok = _make_aabb_walkmesh("smoke_wok")
    wok.hide_viewport = False
    wok.hide_render = False
    try:
        r1 = bpy.ops.kb.hide_walkmeshes()
        if r1 != {"FINISHED"} or not wok.hide_viewport:
            print(f"  FAIL hide_walkmeshes {r1!r} vp={wok.hide_viewport}")
            return False
        r2 = bpy.ops.kb.show_walkmeshes()
        ok = r2 == {"FINISHED"} and not wok.hide_viewport and not wok.hide_render
        if ok:
            print("  PASS test_hide_show_walkmeshes_roundtrip")
        else:
            print(f"  FAIL show_walkmeshes {r2!r} vp={wok.hide_viewport} r={wok.hide_render}")
        return ok
    finally:
        bpy.data.objects.remove(wok, do_unlink=True)


def _make_trimesh(name: str, meshtype: MeshType) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.kb.meshtype = meshtype
    if "UVMap" not in mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    mesh.materials.append(bpy.data.materials.new(name=f"{name}_mat"))
    bpy.context.collection.objects.link(obj)
    return obj


def test_hide_show_untextured_roundtrip() -> bool:
    tri = _make_trimesh("untextured_tri", MeshType.TRIMESH)
    tri.kb.bitmap = NULL
    tri.kb.bitmap2 = NULL
    tri.hide_viewport = False
    tri.hide_render = False
    try:
        r1 = bpy.ops.kb.hide_untextured()
        if r1 != {"FINISHED"} or not tri.hide_viewport:
            print(f"  FAIL hide_untextured {r1!r} vp={tri.hide_viewport}")
            return False
        r2 = bpy.ops.kb.show_untextured()
        ok = r2 == {"FINISHED"} and not tri.hide_viewport and not tri.hide_render
        if ok:
            print("  PASS test_hide_show_untextured_roundtrip")
        else:
            print(f"  FAIL show_untextured {r2!r} vp={tri.hide_viewport} r={tri.hide_render}")
        return ok
    finally:
        bpy.data.objects.remove(tri, do_unlink=True)


def test_hide_show_blockers_roundtrip() -> bool:
    """Blocker = untextured trimesh with render enabled (see KB_OT_hide_blockers)."""
    blk = _make_trimesh("blocker_tri", MeshType.TRIMESH)
    blk.kb.bitmap = NULL
    blk.kb.bitmap2 = NULL
    blk.kb.render = True
    blk.hide_viewport = False
    blk.hide_render = False
    try:
        r1 = bpy.ops.kb.hide_blockers()
        if r1 != {"FINISHED"} or not blk.hide_viewport:
            print(f"  FAIL hide_blockers {r1!r} vp={blk.hide_viewport}")
            return False
        r2 = bpy.ops.kb.show_blockers()
        ok = r2 == {"FINISHED"} and not blk.hide_viewport and not blk.hide_render
        if ok:
            print("  PASS test_hide_show_blockers_roundtrip")
        else:
            print(f"  FAIL show_blockers {r2!r} vp={blk.hide_viewport} r={blk.hide_render}")
        return ok
    finally:
        bpy.data.objects.remove(blk, do_unlink=True)


def test_hide_show_emitters_roundtrip() -> bool:
    em = _make_trimesh("smoke_emit", MeshType.EMITTER)
    em.hide_viewport = False
    em.hide_render = False
    try:
        r1 = bpy.ops.kb.hide_emitters()
        if r1 != {"FINISHED"} or not em.hide_viewport:
            print(f"  FAIL hide_emitters {r1!r} vp={em.hide_viewport}")
            return False
        r2 = bpy.ops.kb.show_emitters()
        ok = r2 == {"FINISHED"} and not em.hide_viewport and not em.hide_render
        if ok:
            print("  PASS test_hide_show_emitters_roundtrip")
        else:
            print(f"  FAIL show_emitters {r2!r} vp={em.hide_viewport} r={em.hide_render}")
        return ok
    finally:
        bpy.data.objects.remove(em, do_unlink=True)


def test_hide_show_lights_roundtrip() -> bool:
    bpy.ops.object.light_add(type="POINT", location=(0, 0, 1))
    light = bpy.context.active_object
    if light is None:
        print("  FAIL no light")
        return False
    light.hide_viewport = False
    light.hide_render = False
    try:
        r1 = bpy.ops.kb.hide_lights()
        if r1 != {"FINISHED"} or not light.hide_viewport:
            print(f"  FAIL hide_lights {r1!r} vp={light.hide_viewport}")
            return False
        r2 = bpy.ops.kb.show_lights()
        ok = r2 == {"FINISHED"} and not light.hide_viewport and not light.hide_render
        if ok:
            print("  PASS test_hide_show_lights_roundtrip")
        else:
            print(f"  FAIL show_lights {r2!r} vp={light.hide_viewport} r={light.hide_render}")
        return ok
    finally:
        bpy.data.objects.remove(light, do_unlink=True)


def run_tests() -> bool:
    print("\n=== test_ops_showhide_smoke.py ===")
    results = [
        test_hide_show_walkmeshes_roundtrip(),
        test_hide_show_untextured_roundtrip(),
        test_hide_show_blockers_roundtrip(),
        test_hide_show_emitters_roundtrip(),
        test_hide_show_lights_roundtrip(),
    ]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed test_ops_showhide_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
