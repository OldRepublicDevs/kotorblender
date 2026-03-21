"""
test_ops_anim_smoke.py – kb.add_animation operator (real bpy context)

Run with:
    blender --background --python test/blender/test_ops_anim_smoke.py
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
if MODULE not in bpy.context.preferences.addons:  # pyright: ignore[reportOptionalMemberAccess]
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.constants import Classification, Direction, DummyType  # noqa: E402
import io_scene_kotor.ops.anim.delete as _kb_anim_delete  # noqa: F401, E402
import io_scene_kotor.ops.anim.move as _kb_anim_move  # noqa: F401, E402
import io_scene_kotor.ops.anim.play as _kb_anim_play  # noqa: F401, E402
import io_scene_kotor.ops.anim.event.add as _kb_anim_ev_add  # noqa: F401, E402
import io_scene_kotor.ops.anim.event.delete as _kb_anim_ev_del  # noqa: F401, E402
import io_scene_kotor.ops.anim.event.move as _kb_anim_ev_move  # noqa: F401, E402


def _make_mdl_root(name: str = "mdl_anim") -> bpy.types.Object:
    root = bpy.data.objects.new(name, None)
    root.kb.dummytype = DummyType.MDLROOT
    root.kb.classification = Classification.OTHER
    root.kb.animscale = 1.0
    root.kb.node_number = 1
    root.kb.export_order = 0
    root.rotation_mode = "QUATERNION"
    bpy.context.collection.objects.link(root)
    return root


def test_ops_add_animation_finishes() -> bool:
    root = _make_mdl_root()
    try:
        kb = getattr(root, "kb", None)
        if kb is None:
            print("  FAIL test_ops_add_animation_finishes: kb")
            return False
        seed = kb.anim_list.add()
        seed.name = "__seed"
        seed.frame_start = 0
        seed.frame_end = 0
        before = len(kb.anim_list)
        bpy.ops.object.select_all(action="DESELECT")
        root.select_set(True)
        bpy.context.view_layer.objects.active = root
        try:
            bpy.ops.kb.add_animation()
        except Exception as e:
            print(f"  FAIL test_ops_add_animation_finishes: {e}")
            return False
        if len(kb.anim_list) != before + 1:
            print("  FAIL test_ops_add_animation_finishes: anim count")
            return False
    finally:
        bpy.data.objects.remove(root, do_unlink=True)
    print("  PASS test_ops_add_animation_finishes")
    return True


def test_ops_delete_animation_removes_entry() -> bool:
    root = _make_mdl_root("mdl_anim_del")
    try:
        kb = getattr(root, "kb", None)
        if kb is None:
            print("  FAIL test_ops_delete_animation_removes_entry: kb")
            return False
        kb.anim_list.clear()
        for i in range(2):
            e = kb.anim_list.add()
            e.name = f"anim_{i}"
            e.frame_start = 0
            e.frame_end = 1
        kb.anim_list_idx = 0
        bpy.ops.object.select_all(action="DESELECT")
        root.select_set(True)
        bpy.context.view_layer.objects.active = root
        if not bpy.ops.kb.delete_animation.poll():
            print("  FAIL test_ops_delete_animation_removes_entry: poll")
            return False
        r = bpy.ops.kb.delete_animation()
        ok = r == {"FINISHED"} and len(kb.anim_list) == 1 and kb.anim_list[0].name == "anim_1"
        if ok:
            print("  PASS test_ops_delete_animation_removes_entry")
        else:
            print(f"  FAIL result={r!r} len={len(kb.anim_list)}")
        return ok
    finally:
        bpy.data.objects.remove(root, do_unlink=True)


def test_ops_move_and_play_animation() -> bool:
    root = _make_mdl_root("mdl_anim_move")
    try:
        kb = root.kb
        kb.anim_list.clear()
        for i, (fs, fe) in enumerate([(0, 5), (10, 20)]):
            a = kb.anim_list.add()
            a.name = f"a{i}"
            a.frame_start = fs
            a.frame_end = fe
        kb.anim_list_idx = 1
        bpy.ops.object.select_all(action="DESELECT")
        root.select_set(True)
        bpy.context.view_layer.objects.active = root
        r1 = bpy.ops.kb.move_animation(direction=Direction.UP)
        if r1 != {"FINISHED"} or kb.anim_list_idx != 0 or kb.anim_list[0].name != "a1":
            print(f"  FAIL move_animation: {r1!r} idx={kb.anim_list_idx} names={[x.name for x in kb.anim_list]}")
            return False
        kb.anim_list_idx = 0
        r2 = bpy.ops.kb.play_animation()
        sc = bpy.context.scene
        ok = (
            r2 == {"FINISHED"}
            and sc.frame_start == 10
            and sc.frame_end == 20
            and sc.frame_current == 10
        )
        if ok:
            print("  PASS test_ops_move_and_play_animation")
        else:
            print(f"  FAIL play: {r2!r} frames {sc.frame_start}-{sc.frame_end} cur={sc.frame_current}")
        return ok
    finally:
        bpy.data.objects.remove(root, do_unlink=True)


def test_ops_anim_event_add_delete_move() -> bool:
    root = _make_mdl_root("mdl_anim_ev")
    try:
        kb = root.kb
        kb.anim_list.clear()
        anim = kb.anim_list.add()
        anim.name = "solo"
        anim.frame_start = 0
        anim.frame_end = 30
        kb.anim_list_idx = 0
        bpy.ops.object.select_all(action="DESELECT")
        root.select_set(True)
        bpy.context.view_layer.objects.active = root
        if bpy.ops.kb.add_anim_event() != {"FINISHED"}:
            print("  FAIL add_anim_event")
            return False
        bpy.ops.kb.add_anim_event()
        if len(anim.event_list) != 2:
            print(f"  FAIL event count {len(anim.event_list)}")
            return False
        anim.event_list_idx = 0
        if bpy.ops.kb.move_anim_event(direction=Direction.DOWN) != {"FINISHED"}:
            print("  FAIL move_anim_event")
            return False
        anim.event_list_idx = 0
        if bpy.ops.kb.delete_anim_event() != {"FINISHED"} or len(anim.event_list) != 1:
            print("  FAIL delete_anim_event")
            return False
        print("  PASS test_ops_anim_event_add_delete_move")
        return True
    finally:
        bpy.data.objects.remove(root, do_unlink=True)


def run_tests() -> bool:
    print("\n=== test_ops_anim_smoke.py ===")
    results = [
        test_ops_add_animation_finishes(),
        test_ops_delete_animation_removes_entry(),
        test_ops_move_and_play_animation(),
        test_ops_anim_event_add_delete_move(),
    ]
    ok = all(results)
    print(f"\n[{'OK' if ok else 'FAIL'}] {sum(results)}/{len(results)} passed in test_ops_anim_smoke.py\n")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
