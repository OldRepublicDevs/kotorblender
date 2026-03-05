"""
test_registration.py – Blender background-mode test

Verifies that the KotorBlender extension loads correctly and registers all
expected operators, property groups, panels, and menus.

Run with:
    blender --background --python test/blender/test_registration.py
"""

import os
import sys

import bpy

# ---------------------------------------------------------------------------
# Extension setup
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

MODULE = "bl_ext.user_default.io_scene_kotor"
if MODULE not in bpy.context.preferences.addons:
    result = bpy.ops.preferences.addon_enable(module=MODULE)
    if "FINISHED" not in result:
        print(f"FATAL: Could not enable extension '{MODULE}': {result}")
        sys.exit(1)

# ---------------------------------------------------------------------------
# Expected registrations
# ---------------------------------------------------------------------------

EXPECTED_OPERATORS = [
    "kb.mdlimport",
    "kb.mdlexport",
    "kb.lytimport",
    "kb.lytexport",
    "kb.pthimport",
    "kb.pthexport",
    "kb.add_path_connection",
    "kb.delete_path_connection",
    "kb.add_animation",
    "kb.delete_animation",
    "kb.move_animation",
    "kb.play_animation",
    "kb.add_anim_event",
    "kb.delete_anim_event",
    "kb.move_anim_event",
    "kb.add_lens_flare",
    "kb.delete_lens_flare",
    "kb.move_lens_flare",
    "kb.bake_lightmaps_auto",
    "kb.bake_lightmaps_manual",
    "kb.render_minimap_auto",
    "kb.render_minimap_manual",
    "kb.rebuild_material",
    "kb.rebuild_all_materials",
    "kb.rebuild_armature",
    "kb.armature_apply_keyframes",
    "kb.armature_unapply_keyframes",
    "kb.show_walkmeshes",
    "kb.hide_walkmeshes",
    "kb.show_untextured",
    "kb.hide_untextured",
    "kb.show_unlightmapped",
    "kb.hide_unlightmapped",
    "kb.show_lights",
    "kb.hide_lights",
    "kb.show_emitters",
    "kb.hide_emitters",
    "kb.show_blockers",
    "kb.hide_blockers",
    "kb.show_char_bones",
    "kb.hide_char_bones",
    "kb.show_char_dummies",
    "kb.hide_char_dummies",
]

EXPECTED_PANELS = [
    "KB_PT_model",
    "KB_PT_animations",
    "KB_PT_animations_events",
    "KB_PT_animations_armature",
    "KB_PT_modelnode",
    "KB_PT_reference",
    "KB_PT_path_point",
    "KB_PT_mesh",
    "KB_PT_mesh_uv_anim",
    "KB_PT_mesh_dangly",
    "KB_PT_mesh_aabb",
    "KB_PT_light",
    "KB_PT_light_lens_flares",
    "KB_PT_emitter",
    "KB_PT_emitter_particles",
    "KB_PT_emitter_texture_anim",
    "KB_PT_emitter_control_points",
]

EXPECTED_MENUS = [
    "KB_MT_kotor",
    "KB_MT_kotor_lightmaps",
    "KB_MT_kotor_minimap",
    "KB_MT_kotor_showhide",
]

EXPECTED_LISTS = [
    "KB_UL_lens_flares",
    "KB_UL_path_points",
]

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def _clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def test_property_groups():
    """Object, Scene, and Image all gain a .kb property group."""
    missing = []
    if not hasattr(bpy.types.Object, "kb"):
        missing.append("Object.kb")
    if not hasattr(bpy.types.Scene, "kb"):
        missing.append("Scene.kb")
    if not hasattr(bpy.types.Image, "kb"):
        missing.append("Image.kb")
    if missing:
        print(f"  FAIL test_property_groups: missing {missing}")
        return False
    print("  PASS test_property_groups")
    return True


def test_operators_registered():
    """All 43 kb.* operators are accessible via bpy.ops."""
    failed = []
    for op_id in EXPECTED_OPERATORS:
        cat, name = op_id.split(".", 1)
        ops_cat = getattr(bpy.ops, cat, None)
        if ops_cat is None or not hasattr(ops_cat, name):
            failed.append(op_id)
    if failed:
        print(f"  FAIL test_operators_registered: missing {failed}")
        return False
    print(f"  PASS test_operators_registered ({len(EXPECTED_OPERATORS)} operators)")
    return True


def test_panels_registered():
    """All KB_PT_* panel types are registered in bpy.types."""
    failed = [p for p in EXPECTED_PANELS if not hasattr(bpy.types, p)]
    if failed:
        print(f"  FAIL test_panels_registered: missing {failed}")
        return False
    print(f"  PASS test_panels_registered ({len(EXPECTED_PANELS)} panels)")
    return True


def test_menus_registered():
    """All KB_MT_* menu types are registered in bpy.types."""
    failed = [m for m in EXPECTED_MENUS if not hasattr(bpy.types, m)]
    if failed:
        print(f"  FAIL test_menus_registered: missing {failed}")
        return False
    print(f"  PASS test_menus_registered ({len(EXPECTED_MENUS)} menus)")
    return True


def test_ui_lists_registered():
    """All KB_UL_* UIList types are registered in bpy.types."""
    failed = [u for u in EXPECTED_LISTS if not hasattr(bpy.types, u)]
    if failed:
        print(f"  FAIL test_ui_lists_registered: missing {failed}")
        return False
    print(f"  PASS test_ui_lists_registered ({len(EXPECTED_LISTS)} lists)")
    return True


def test_object_kb_property_defaults():
    """A newly created object exposes all core kb sub-properties."""
    _clear_scene()
    obj = bpy.data.objects.new("TestKbDefaults", None)
    bpy.context.scene.collection.objects.link(obj)
    try:
        # Core properties that must always exist
        _ = obj.kb.dummytype
        _ = obj.kb.meshtype
        _ = obj.kb.classification
        _ = obj.kb.animscale
        _ = obj.kb.node_number
        _ = obj.kb.export_order
        _ = obj.kb.selfillumcolor
        _ = obj.kb.alpha
        _ = obj.kb.supermodel
        _ = obj.kb.path_connection_list
        print("  PASS test_object_kb_property_defaults")
        return True
    except AttributeError as e:
        print(f"  FAIL test_object_kb_property_defaults: {e}")
        return False


def test_scene_kb_properties():
    """Scene.kb exposes expected properties."""
    try:
        scene = bpy.context.scene
        _ = scene.kb
        print("  PASS test_scene_kb_properties")
        return True
    except Exception as e:
        print(f"  FAIL test_scene_kb_properties: {e}")
        return False


def test_image_kb_properties():
    """Image.kb exposes expected properties for TXI metadata."""
    try:
        img = bpy.data.images.new("TestKbImage", 1, 1)
        _ = img.kb
        bpy.data.images.remove(img)
        print("  PASS test_image_kb_properties")
        return True
    except Exception as e:
        print(f"  FAIL test_image_kb_properties: {e}")
        return False


def test_addon_preferences():
    """Add-on preferences are accessible and have expected string fields."""
    try:
        prefs = bpy.context.preferences.addons.get(MODULE)
        if prefs is None:
            print("  FAIL test_addon_preferences: module not in addons")
            return False
        _ = prefs.preferences.texture_search_paths
        _ = prefs.preferences.lightmap_search_paths
        print("  PASS test_addon_preferences")
        return True
    except AttributeError as e:
        print(f"  FAIL test_addon_preferences: {e}")
        return False


def test_operator_poll_contexts():
    """Operators whose poll can run in background mode don't crash."""
    # These should not crash even in background mode (they may return CANCELLED)
    safe_ops = [
        ("kb", "hide_walkmeshes"),
        ("kb", "hide_lights"),
        ("kb", "hide_emitters"),
        ("kb", "show_walkmeshes"),
        ("kb", "show_lights"),
    ]
    failed = []
    for cat, name in safe_ops:
        try:
            op = getattr(getattr(bpy.ops, cat), name)
            op()  # result may be CANCELLED – that's fine
        except Exception as e:
            failed.append(f"{cat}.{name}: {e}")
    if failed:
        print(f"  FAIL test_operator_poll_contexts: {failed}")
        return False
    print(f"  PASS test_operator_poll_contexts ({len(safe_ops)} ops smoke-tested)")
    return True


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_tests():
    print("\n=== test_registration.py ===")
    tests = [
        test_property_groups,
        test_operators_registered,
        test_panels_registered,
        test_menus_registered,
        test_ui_lists_registered,
        test_object_kb_property_defaults,
        test_scene_kb_properties,
        test_image_kb_properties,
        test_addon_preferences,
        test_operator_poll_contexts,
    ]
    results = [t() for t in tests]
    passed = sum(results)
    total = len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_registration.py\n")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
