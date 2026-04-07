"""
test_mdl_types.py – Blender background-mode test

Tests MDL types and constants: CLASS_BY_VALUE mapping, function pointer
distinctness, EMITTER_CONTROLLER_KEYS structure, and NODE_* / MDX_FLAG_*
consistency. No file I/O; data consistency only.

Run with:
    blender --background --python test/blender/test_mdl_types.py
"""

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
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

from io_scene_kotor.constants import Classification
from io_scene_kotor.format.mdl.types import (
    CLASS_BY_VALUE,
    EMITTER_CONTROLLER_KEYS,
    MDX_FLAG_COLOR,
    MDX_FLAG_NORMAL,
    MDX_FLAG_TANGENT1,
    MDX_FLAG_UV1,
    MDX_FLAG_VERTEX,
    MODEL_FN_PTR_1_K1_PC,
    MODEL_FN_PTR_1_K1_XBOX,
    MODEL_FN_PTR_1_K2_PC,
    MODEL_FN_PTR_1_K2_XBOX,
    NODE_AABB,
    NODE_DANGLY,
    NODE_EMITTER,
    NODE_LIGHT,
    NODE_MESH,
    NODE_REFERENCE,
    NODE_SABER,
    NODE_SKIN,
)

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_class_by_value_maps_to_classification():
    """Every CLASS_BY_VALUE entry maps to a distinct Classification member."""
    expected = {
        Classification.OTHER,
        Classification.EFFECT,
        Classification.TILE,
        Classification.CHARACTER,
        Classification.DOOR,
        Classification.LIGHTSABER,
        Classification.PLACEABLE,
        Classification.FLYER,
    }
    actual = set(CLASS_BY_VALUE.values())
    ok = actual == expected and len(CLASS_BY_VALUE) == len(actual)
    if ok:
        print("  PASS test_class_by_value_maps_to_classification")
    else:
        print(
            f"  FAIL test_class_by_value_maps_to_classification: expected={expected}, actual={actual}"
        )
    return ok


def test_function_pointer_constants_distinct():
    """K1/K2 and PC/Xbox model fn ptrs are distinct where expected."""
    ok = (
        MODEL_FN_PTR_1_K1_PC != MODEL_FN_PTR_1_K2_PC
        and MODEL_FN_PTR_1_K1_PC != MODEL_FN_PTR_1_K1_XBOX
        and MODEL_FN_PTR_1_K2_PC != MODEL_FN_PTR_1_K2_XBOX
    )
    if ok:
        print("  PASS test_function_pointer_constants_distinct")
    else:
        print("  FAIL test_function_pointer_constants_distinct")
    return ok


def test_emitter_controller_keys_structure():
    """EMITTER_CONTROLLER_KEYS entries are (ctrl_type, name, num_columns); no duplicate ctrl_type."""
    ctrl_types = []
    ok = True
    for entry in EMITTER_CONTROLLER_KEYS:
        if len(entry) != 3:
            ok = False
            break
        ctrl_type, name, num_columns = entry
        if (
            not isinstance(ctrl_type, int)
            or not isinstance(name, str)
            or not isinstance(num_columns, int)
        ):
            ok = False
            break
        ctrl_types.append(ctrl_type)
    if ok:
        ok = len(ctrl_types) == len(set(ctrl_types))
    if ok:
        print("  PASS test_emitter_controller_keys_structure")
    else:
        print("  FAIL test_emitter_controller_keys_structure")
    return ok


def test_node_and_mdx_flags_distinct_within_sets():
    """NODE_* values are distinct; MDX_FLAG_* values are distinct (used in different contexts)."""
    node_vals = [
        NODE_LIGHT,
        NODE_EMITTER,
        NODE_REFERENCE,
        NODE_MESH,
        NODE_SKIN,
        NODE_DANGLY,
        NODE_AABB,
        NODE_SABER,
    ]
    mdx_vals = [
        MDX_FLAG_VERTEX,
        MDX_FLAG_UV1,
        MDX_FLAG_NORMAL,
        MDX_FLAG_COLOR,
        MDX_FLAG_TANGENT1,
    ]
    ok = len(node_vals) == len(set(node_vals)) and len(mdx_vals) == len(set(mdx_vals))
    if ok:
        print("  PASS test_node_and_mdx_flags_distinct_within_sets")
    else:
        print("  FAIL test_node_and_mdx_flags_distinct_within_sets")
    return ok


def run_tests():
    print("\n=== test_mdl_types.py ===")
    tests = [
        test_class_by_value_maps_to_classification,
        test_function_pointer_constants_distinct,
        test_emitter_controller_keys_structure,
        test_node_and_mdx_flags_distinct_within_sets,
    ]
    results = [t() for t in tests]
    passed = sum(results)
    total = len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_mdl_types.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
