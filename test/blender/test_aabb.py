"""
test_aabb.py – Blender background-mode test

Tests the AABB (Axis-Aligned Bounding Box) tree generator used for walkmesh
export.  Uses synthetic triangle data – no game assets required.

The face tuple format expected by generate_tree is:
    (face_index: int, vertices: list[Vector], center: Vector)

Run with:
    blender --background --python test/blender/test_aabb.py
"""

import os
import sys

# mathutils is supplied by Blender – must run inside Blender
from mathutils import Vector

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

from io_scene_kotor.aabb import (
    BoundingBox,
    compute_bounding_box,
    generate_tree,
    new_aabb_node,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tri(idx, a, b, c):
    """Create a face tuple with centroid auto-computed."""
    va, vb, vc = Vector(a), Vector(b), Vector(c)
    center = (va + vb + vc) / 3.0
    return (idx, [va, vb, vc], center)


def _float_eq(a, b, tol=1e-5):
    return abs(a - b) < tol


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_single_face_tree():
    """A tree built from one face produces exactly one leaf node."""
    faces = [_tri(0, (0, 0, 0), (1, 0, 0), (0, 1, 0))]
    tree = []
    generate_tree(tree, faces)
    ok = len(tree) == 1 and tree[0][8] == 0 and tree[0][6] == -1 and tree[0][7] == -1
    if ok:
        print("  PASS test_single_face_tree (1 node, face_idx=0)")
    else:
        print(f"  FAIL test_single_face_tree: tree={tree}")
    return ok


def test_two_face_tree():
    """A tree from 2 faces has exactly 3 nodes (1 interior + 2 leaves)."""
    faces = [
        _tri(0, (0, 0, 0), (1, 0, 0), (0, 1, 0)),
        _tri(1, (2, 0, 0), (3, 0, 0), (2, 1, 0)),
    ]
    tree = []
    generate_tree(tree, faces)
    ok = len(tree) == 3
    if ok:
        print(f"  PASS test_two_face_tree ({len(tree)} nodes)")
    else:
        print(f"  FAIL test_two_face_tree: expected 3 nodes, got {len(tree)}")
    return ok


def test_four_face_tree():
    """A perfectly-split 4-face grid produces 7 nodes (2n-1)."""
    faces = [
        _tri(0, (0, 0, 0), (1, 0, 0), (0, 1, 0)),
        _tri(1, (2, 0, 0), (3, 0, 0), (2, 1, 0)),
        _tri(2, (0, 2, 0), (1, 2, 0), (0, 3, 0)),
        _tri(3, (2, 2, 0), (3, 2, 0), (2, 3, 0)),
    ]
    tree = []
    generate_tree(tree, faces)
    ok = len(tree) == 7
    if ok:
        print(f"  PASS test_four_face_tree ({len(tree)} nodes)")
    else:
        print(f"  FAIL test_four_face_tree: expected 7 nodes, got {len(tree)}")
    return ok


def test_general_n_face_tree():
    """For n faces a valid AABB tree has exactly 2n-1 nodes."""
    n = 8
    faces = [_tri(i, (i * 2, 0, 0), (i * 2 + 1, 0, 0), (i * 2, 1, 0)) for i in range(n)]
    tree = []
    generate_tree(tree, faces)
    expected = 2 * n - 1
    ok = len(tree) == expected
    if ok:
        print(f"  PASS test_general_n_face_tree (n={n}, nodes={len(tree)})")
    else:
        print(f"  FAIL test_general_n_face_tree: expected {expected}, got {len(tree)}")
    return ok


def test_bounding_box_min_max():
    """compute_bounding_box returns correct min/max for a known triangle set."""
    faces = [
        _tri(0, (-1, -2, 0), (3, -2, 0), (-1, 4, 0)),
    ]
    bb = compute_bounding_box(faces)
    ok = (
        _float_eq(bb.min.x, -1.0)
        and _float_eq(bb.min.y, -2.0)
        and _float_eq(bb.max.x, 3.0)
        and _float_eq(bb.max.y, 4.0)
    )
    if ok:
        print("  PASS test_bounding_box_min_max")
    else:
        print(f"  FAIL test_bounding_box_min_max: min={bb.min}, max={bb.max}")
    return ok


def test_bounding_box_longest_axis_x():
    """Longest axis is X when the X extent dominates."""
    bb = BoundingBox(Vector((0, 0, 0)), Vector((10, 2, 1)), Vector((5, 1, 0.5)))
    ok = bb.longest_axis() == 0
    if ok:
        print("  PASS test_bounding_box_longest_axis_x")
    else:
        print(f"  FAIL test_bounding_box_longest_axis_x: got axis {bb.longest_axis()}")
    return ok


def test_bounding_box_longest_axis_y():
    """Longest axis is Y when the Y extent dominates."""
    bb = BoundingBox(Vector((0, 0, 0)), Vector((2, 10, 1)), Vector((1, 5, 0.5)))
    ok = bb.longest_axis() == 1
    if ok:
        print("  PASS test_bounding_box_longest_axis_y")
    else:
        print(f"  FAIL test_bounding_box_longest_axis_y: got axis {bb.longest_axis()}")
    return ok


def test_bounding_box_longest_axis_z():
    """Longest axis is Z when the Z extent dominates."""
    bb = BoundingBox(Vector((0, 0, 0)), Vector((1, 2, 15)), Vector((0.5, 1, 7.5)))
    ok = bb.longest_axis() == 2
    if ok:
        print("  PASS test_bounding_box_longest_axis_z")
    else:
        print(f"  FAIL test_bounding_box_longest_axis_z: got axis {bb.longest_axis()}")
    return ok


def test_leaf_node_face_index():
    """Leaf nodes store the correct original face index."""
    faces = [
        _tri(42, (0, 0, 0), (1, 0, 0), (0, 1, 0)),
    ]
    tree = []
    generate_tree(tree, faces)
    ok = tree[0][8] == 42
    if ok:
        print("  PASS test_leaf_node_face_index")
    else:
        print(f"  FAIL test_leaf_node_face_index: expected 42, got {tree[0][8]}")
    return ok


def test_interior_node_face_index_is_minus_one():
    """Interior nodes have face_idx == -1."""
    faces = [
        _tri(0, (0, 0, 0), (1, 0, 0), (0, 1, 0)),
        _tri(1, (5, 0, 0), (6, 0, 0), (5, 1, 0)),
    ]
    tree = []
    generate_tree(tree, faces)
    # Node 0 is the interior; nodes 1 and 2 are leaves
    ok = tree[0][8] == -1 and tree[1][8] != -1 and tree[2][8] != -1
    if ok:
        print("  PASS test_interior_node_face_index_is_minus_one")
    else:
        print(f"  FAIL test_interior_node_face_index_is_minus_one: tree[0][8]={tree[0][8]}")
    return ok


def test_interior_node_children_point_into_tree():
    """left_child and right_child indices of interior nodes are valid tree indices."""
    n = 4
    faces = [_tri(i, (i * 3, 0, 0), (i * 3 + 1, 0, 0), (i * 3, 1, 0)) for i in range(n)]
    tree = []
    generate_tree(tree, faces)
    failed = []
    for idx, node in enumerate(tree):
        left, right = node[6], node[7]
        face_idx = node[8]
        is_leaf = face_idx != -1
        if is_leaf:
            if left != -1 or right != -1:
                failed.append(f"leaf@{idx} has non-(-1) children: l={left}, r={right}")
        else:
            if not (0 <= left < len(tree) and 0 <= right < len(tree)):
                failed.append(f"interior@{idx} has bad children: l={left}, r={right}")
    ok = len(failed) == 0
    if ok:
        print("  PASS test_interior_node_children_point_into_tree")
    else:
        print(f"  FAIL test_interior_node_children_point_into_tree: {failed}")
    return ok


def test_degenerate_coplanar_faces():
    """Coplanar faces (degenerate split) are still partitioned without crashing."""
    # All faces at the same Y – the normal split axis will be degenerate
    faces = [_tri(i, (i, 0, 0), (i + 1, 0, 0), (i, 0.01, 0)) for i in range(4)]
    tree = []
    try:
        generate_tree(tree, faces)
        ok = len(tree) > 0
        if ok:
            print(f"  PASS test_degenerate_coplanar_faces ({len(tree)} nodes)")
        else:
            print("  FAIL test_degenerate_coplanar_faces: empty tree")
    except Exception as e:
        print(f"  FAIL test_degenerate_coplanar_faces: exception {e}")
        ok = False
    return ok


def test_aabb_node_structure():
    """new_aabb_node returns a 10-element list with the right layout."""
    bb = BoundingBox(Vector((1, 2, 3)), Vector((4, 5, 6)), Vector((2.5, 3.5, 4.5)))
    node = new_aabb_node(bb, 1, 2, -1, 1)
    ok = (
        len(node) == 10
        and _float_eq(node[0], 1.0) and _float_eq(node[1], 2.0) and _float_eq(node[2], 3.0)
        and _float_eq(node[3], 4.0) and _float_eq(node[4], 5.0) and _float_eq(node[5], 6.0)
        and node[6] == 1 and node[7] == 2
        and node[8] == -1 and node[9] == 1
    )
    if ok:
        print("  PASS test_aabb_node_structure")
    else:
        print(f"  FAIL test_aabb_node_structure: {node}")
    return ok


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_tests():
    print("\n=== test_aabb.py ===")
    tests = [
        test_single_face_tree,
        test_two_face_tree,
        test_four_face_tree,
        test_general_n_face_tree,
        test_bounding_box_min_max,
        test_bounding_box_longest_axis_x,
        test_bounding_box_longest_axis_y,
        test_bounding_box_longest_axis_z,
        test_leaf_node_face_index,
        test_interior_node_face_index_is_minus_one,
        test_interior_node_children_point_into_tree,
        test_degenerate_coplanar_faces,
        test_aabb_node_structure,
    ]
    results = [t() for t in tests]
    passed = sum(results)
    total = len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_aabb.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
