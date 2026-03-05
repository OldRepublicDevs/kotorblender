"""
test_pth_io.py – Blender background-mode test

Tests the PTH (path / navigation-graph) import and export pipeline end-to-end
using synthetic data generated inside Blender – no game assets required.

The flow for each sub-test:
  1. Build path-point objects in the current Blender scene.
  2. Call save_pth() to write a binary GFF PTH file.
  3. Clear the scene.
  4. Call load_pth() to re-create path-point objects from the file.
  5. Assert that positions, connectivity, and counts match.

Run with:
    blender --background --python test/blender/test_pth_io.py
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
from io_scene_kotor.io.pth import load_pth, save_pth

# ---------------------------------------------------------------------------
# Mock operator
# ---------------------------------------------------------------------------


class _Op:
    """Minimal mock of a Blender operator (only needs .report())."""

    def report(self, level, message):
        tag = next(iter(level)) if level else "INFO"
        print(f"    [{tag}] {message}")


_op = _Op()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clear_scene():
    """Remove all objects from the scene data-block."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def _make_path_root(name="TestPath"):
    obj = bpy.data.objects.new(name, None)
    obj.kb.dummytype = DummyType.PTHROOT
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _make_path_point(name, x, y, parent=None):
    obj = bpy.data.objects.new(name, None)
    obj.kb.dummytype = DummyType.PATHPOINT
    obj.location = (x, y, 0.0)
    if parent:
        obj.parent = parent
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _add_connection(src_obj, dst_name):
    conn = src_obj.kb.path_connection_list.add()
    conn.point = dst_name


def _float_eq(a, b, tol=1e-4):
    return abs(a - b) < tol


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_empty_path_roundtrip():
    """Exporting zero path points produces a valid (empty) PTH file."""
    _clear_scene()
    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        path = f.name
    try:
        save_pth(_op, path)
        assert os.path.getsize(path) > 0, "PTH file must not be empty"
        _clear_scene()
        load_pth(_op, path)
        path_points = [o for o in bpy.data.objects if o.kb.dummytype == DummyType.PATHPOINT]
        ok = len(path_points) == 0
        if ok:
            print("  PASS test_empty_path_roundtrip")
        else:
            print(f"  FAIL test_empty_path_roundtrip: expected 0 points, got {len(path_points)}")
        return ok
    finally:
        os.unlink(path)


def test_single_point_roundtrip():
    """A single isolated path point round-trips with correct coordinates."""
    _clear_scene()
    root = _make_path_root()
    _make_path_point("PathPoint000", 5.0, 7.5, parent=root)

    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        path = f.name
    try:
        save_pth(_op, path)
        _clear_scene()
        load_pth(_op, path)
        points = [o for o in bpy.data.objects if o.kb.dummytype == DummyType.PATHPOINT]
        ok = (
            len(points) == 1
            and _float_eq(points[0].location.x, 5.0)
            and _float_eq(points[0].location.y, 7.5)
        )
        if ok:
            print("  PASS test_single_point_roundtrip")
        else:
            locs = [(o.location.x, o.location.y) for o in points]
            print(f"  FAIL test_single_point_roundtrip: points={locs}")
        return ok
    finally:
        os.unlink(path)


def test_multiple_points_positions():
    """Three path points all round-trip with correct positions."""
    _clear_scene()
    coords = [(1.0, 2.0), (3.5, -4.0), (0.0, 0.0)]
    root = _make_path_root()
    for i, (x, y) in enumerate(coords):
        _make_path_point(f"PathPoint{i:03d}", x, y, parent=root)

    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        path = f.name
    try:
        save_pth(_op, path)
        _clear_scene()
        load_pth(_op, path)
        points = sorted(
            [o for o in bpy.data.objects if o.kb.dummytype == DummyType.PATHPOINT],
            key=lambda o: o.name,
        )
        if len(points) != 3:
            print(f"  FAIL test_multiple_points_positions: expected 3, got {len(points)}")
            return False
        ok = all(
            _float_eq(points[i].location.x, coords[i][0])
            and _float_eq(points[i].location.y, coords[i][1])
            for i in range(3)
        )
        if ok:
            print("  PASS test_multiple_points_positions")
        else:
            print("  FAIL test_multiple_points_positions: positions mismatch")
        return ok
    finally:
        os.unlink(path)


def test_connectivity_roundtrip():
    """Point-to-point connections survive the save/load cycle."""
    _clear_scene()
    root = _make_path_root()
    p0 = _make_path_point("PathPoint000", 0.0, 0.0, parent=root)
    p1 = _make_path_point("PathPoint001", 1.0, 0.0, parent=root)
    _make_path_point("PathPoint002", 0.0, 1.0, parent=root)
    _add_connection(p0, "PathPoint001")
    _add_connection(p0, "PathPoint002")
    _add_connection(p1, "PathPoint000")

    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        path = f.name
    try:
        save_pth(_op, path)
        _clear_scene()
        load_pth(_op, path)
        points = {o.name: o for o in bpy.data.objects if o.kb.dummytype == DummyType.PATHPOINT}
        if len(points) != 3:
            print(f"  FAIL test_connectivity_roundtrip: expected 3 points, got {len(points)}")
            return False
        # Point 0 should have 2 connections, point 1 should have 1, point 2 should have 0
        counts = {name: len(obj.kb.path_connection_list) for name, obj in points.items()}
        total_connections = sum(counts.values())
        ok = total_connections == 3
        if ok:
            print(f"  PASS test_connectivity_roundtrip (total connections={total_connections})")
        else:
            print(f"  FAIL test_connectivity_roundtrip: connection counts={counts}")
        return ok
    finally:
        os.unlink(path)


def test_large_path_roundtrip():
    """20 path points in a chain all survive the roundtrip."""
    _clear_scene()
    n = 20
    root = _make_path_root()
    pts = []
    for i in range(n):
        pts.append(_make_path_point(f"PathPoint{i:03d}", float(i), float(i * 2), parent=root))
    # Chain: 0→1→2→...→(n-1)
    for i in range(n - 1):
        _add_connection(pts[i], f"PathPoint{i+1:03d}")

    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        path = f.name
    try:
        save_pth(_op, path)
        _clear_scene()
        load_pth(_op, path)
        points = [o for o in bpy.data.objects if o.kb.dummytype == DummyType.PATHPOINT]
        total_conn = sum(len(o.kb.path_connection_list) for o in points)
        ok = len(points) == n and total_conn == n - 1
        if ok:
            print(f"  PASS test_large_path_roundtrip ({n} points, {n-1} connections)")
        else:
            print(f"  FAIL test_large_path_roundtrip: points={len(points)}, conns={total_conn}")
        return ok
    finally:
        os.unlink(path)


def test_pth_file_size_sanity():
    """A PTH file for 5 points has a plausible minimum size (> 56 bytes header)."""
    _clear_scene()
    root = _make_path_root()
    for i in range(5):
        _make_path_point(f"PathPoint{i:03d}", float(i), 0.0, parent=root)

    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        path = f.name
    try:
        save_pth(_op, path)
        size = os.path.getsize(path)
        ok = size > 56  # GFF header alone is 56 bytes
        if ok:
            print(f"  PASS test_pth_file_size_sanity (size={size} bytes)")
        else:
            print(f"  FAIL test_pth_file_size_sanity: file too small ({size} bytes)")
        return ok
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_tests():
    print("\n=== test_pth_io.py ===")
    tests = [
        test_empty_path_roundtrip,
        test_single_point_roundtrip,
        test_multiple_points_positions,
        test_connectivity_roundtrip,
        test_large_path_roundtrip,
        test_pth_file_size_sanity,
    ]
    results = [t() for t in tests]
    passed = sum(results)
    total = len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_pth_io.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
