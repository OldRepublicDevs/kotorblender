"""
test_lyt_export.py – Blender background-mode test

Tests the LYT (area layout) export pipeline using a synthetic Blender scene.
No game assets required.

The flow:
  1. Create MDLROOT empty objects at known positions.
  2. Call save_lyt() to write a plain-text LYT file.
  3. Parse the produced file and assert its structure is correct.

Run with:
    blender --background --python test/blender/test_lyt_export.py
"""

import os
import sys
import tempfile

import bpy

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

MODULE = "bl_ext.user_default.io_scene_kotor"
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

from io_scene_kotor.constants import DummyType
from io_scene_kotor.io.lyt import save_lyt

# ---------------------------------------------------------------------------
# Mock operator & helpers
# ---------------------------------------------------------------------------


class _Op:
    def report(self, level, message):
        tag = next(iter(level)) if level else "INFO"
        print(f"    [{tag}] {message}")


_op = _Op()


def _clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def _make_mdl_root(name, x=0.0, y=0.0, z=0.0):
    obj = bpy.data.objects.new(name, None)
    obj.kb.dummytype = DummyType.MDLROOT
    obj.location = (x, y, z)
    # save_lyt reads from bpy.context.collection, not the scene master collection
    bpy.context.collection.objects.link(obj)
    return obj


def _read_lyt(path):
    with open(path, "r") as f:
        return f.read()


def _parse_lyt_rooms(content):
    """Return list of (name, x, y, z) tuples from a LYT file."""
    rooms = []
    lines = [l.strip() for l in content.splitlines()]
    reading = False
    count = 0
    for line in lines:
        tokens = line.split()
        if not tokens:
            continue
        if tokens[0].startswith("roomcount"):
            count = int(tokens[1])
            reading = count > 0
            continue
        if reading and len(tokens) >= 4:
            rooms.append((tokens[0], float(tokens[1]), float(tokens[2]), float(tokens[3])))
            count -= 1
            if count == 0:
                reading = False
    return rooms


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_lyt_has_begin_done_layout():
    """Exported LYT file starts with 'beginlayout' and ends with 'donelayout'."""
    _clear_scene()
    _make_mdl_root("room_a")
    with tempfile.NamedTemporaryFile(suffix=".lyt", mode="w", delete=False) as f:
        path = f.name
    try:
        save_lyt(_op, path)
        content = _read_lyt(path)
        ok = "beginlayout" in content and "donelayout" in content
        if ok:
            print("  PASS test_lyt_has_begin_done_layout")
        else:
            print(f"  FAIL test_lyt_has_begin_done_layout: content=\n{content}")
        return ok
    finally:
        os.unlink(path)


def test_lyt_roomcount_matches():
    """roomcount in the LYT file equals the number of MDLROOT objects."""
    _clear_scene()
    _make_mdl_root("room_a")
    _make_mdl_root("room_b")
    _make_mdl_root("room_c")
    with tempfile.NamedTemporaryFile(suffix=".lyt", mode="w", delete=False) as f:
        path = f.name
    try:
        save_lyt(_op, path)
        content = _read_lyt(path)
        rooms = _parse_lyt_rooms(content)
        ok = len(rooms) == 3
        if ok:
            print(f"  PASS test_lyt_roomcount_matches ({len(rooms)} rooms)")
        else:
            print(f"  FAIL test_lyt_roomcount_matches: expected 3, got {len(rooms)}\n{content}")
        return ok
    finally:
        os.unlink(path)


def test_lyt_room_positions():
    """Room positions written to the LYT file match the object locations."""
    _clear_scene()
    _make_mdl_root("room_a", x=0.0, y=0.0, z=0.0)
    _make_mdl_root("room_b", x=10.0, y=5.5, z=0.0)
    with tempfile.NamedTemporaryFile(suffix=".lyt", mode="w", delete=False) as f:
        path = f.name
    try:
        save_lyt(_op, path)
        content = _read_lyt(path)
        rooms = {r[0]: r[1:] for r in _parse_lyt_rooms(content)}
        tol = 1e-3
        ok = (
            "room_a" in rooms
            and "room_b" in rooms
            and abs(rooms["room_a"][0] - 0.0) < tol
            and abs(rooms["room_b"][0] - 10.0) < tol
            and abs(rooms["room_b"][1] - 5.5) < tol
        )
        if ok:
            print("  PASS test_lyt_room_positions")
        else:
            print(f"  FAIL test_lyt_room_positions: rooms={rooms}")
        return ok
    finally:
        os.unlink(path)


def test_lyt_empty_scene():
    """An empty scene produces a valid LYT with roomcount 0."""
    _clear_scene()
    with tempfile.NamedTemporaryFile(suffix=".lyt", mode="w", delete=False) as f:
        path = f.name
    try:
        save_lyt(_op, path)
        content = _read_lyt(path)
        rooms = _parse_lyt_rooms(content)
        ok = len(rooms) == 0 and "beginlayout" in content
        if ok:
            print("  PASS test_lyt_empty_scene")
        else:
            print(f"  FAIL test_lyt_empty_scene: rooms={rooms}")
        return ok
    finally:
        os.unlink(path)


def test_lyt_non_mdlroot_objects_excluded():
    """Non-MDLROOT empties are not written as rooms."""
    _clear_scene()
    _make_mdl_root("real_room")
    # A plain empty (no dummytype = MDLROOT)
    plain = bpy.data.objects.new("SomeDoor", None)
    bpy.context.collection.objects.link(plain)
    with tempfile.NamedTemporaryFile(suffix=".lyt", mode="w", delete=False) as f:
        path = f.name
    try:
        save_lyt(_op, path)
        content = _read_lyt(path)
        rooms = _parse_lyt_rooms(content)
        ok = len(rooms) == 1 and rooms[0][0] == "real_room"
        if ok:
            print("  PASS test_lyt_non_mdlroot_objects_excluded")
        else:
            print(f"  FAIL test_lyt_non_mdlroot_objects_excluded: rooms={rooms}")
        return ok
    finally:
        os.unlink(path)


def test_lyt_contains_fixed_sections():
    """LYT output always contains trackcount and obstaclecount sections."""
    _clear_scene()
    _make_mdl_root("room_x")
    with tempfile.NamedTemporaryFile(suffix=".lyt", mode="w", delete=False) as f:
        path = f.name
    try:
        save_lyt(_op, path)
        content = _read_lyt(path)
        ok = "trackcount" in content and "obstaclecount" in content
        if ok:
            print("  PASS test_lyt_contains_fixed_sections")
        else:
            print(f"  FAIL test_lyt_contains_fixed_sections:\n{content}")
        return ok
    finally:
        os.unlink(path)


def test_lyt_single_room_name():
    """The room name in the LYT matches the Blender object name."""
    _clear_scene()
    _make_mdl_root("dantooine_m05aa")
    with tempfile.NamedTemporaryFile(suffix=".lyt", mode="w", delete=False) as f:
        path = f.name
    try:
        save_lyt(_op, path)
        content = _read_lyt(path)
        ok = "dantooine_m05aa" in content
        if ok:
            print("  PASS test_lyt_single_room_name")
        else:
            print(f"  FAIL test_lyt_single_room_name: room name not found\n{content}")
        return ok
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_tests():
    print("\n=== test_lyt_export.py ===")
    tests = [
        test_lyt_has_begin_done_layout,
        test_lyt_roomcount_matches,
        test_lyt_room_positions,
        test_lyt_empty_scene,
        test_lyt_non_mdlroot_objects_excluded,
        test_lyt_contains_fixed_sections,
        test_lyt_single_room_name,
    ]
    results = [t() for t in tests]
    passed = sum(results)
    total = len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_lyt_export.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
