"""
test_helpers.py – Shared utilities for Blender background-mode tests

Provides helper functions for test setup, including version-aware addon loading.
"""

import os
import sys

import bpy


def get_addon_module_name() -> str:
    """
    Returns the correct module name for the addon based on Blender version.
    
    - Blender 3.6: uses 'io_scene_kotor' (addon in scripts/addons)
    - Blender 4.2+: uses 'bl_ext.user_default.io_scene_kotor' (extension)
    
    Returns:
        The module name string to use with bpy.ops.preferences.addon_enable()
    """
    version = bpy.app.version
    if version >= (4, 2):
        return "bl_ext.user_default.io_scene_kotor"
    else:
        return "io_scene_kotor"


def enable_addon() -> bool:
    """
    Enables the KotorBlender addon, trying both modern and legacy module names.
    Works across Blender 3.6+ by automatically detecting the correct name.
    
    Returns:
        True if the addon was successfully enabled, False otherwise.
    """
    # Try version-appropriate name first
    module = get_addon_module_name()
    modules_to_try = [module]
    
    # Also try the other name as fallback (handles edge cases)
    if module == "bl_ext.user_default.io_scene_kotor":
        modules_to_try.append("io_scene_kotor")
    else:
        modules_to_try.append("bl_ext.user_default.io_scene_kotor")
    
    for mod in modules_to_try:
        # Disable first so a reload picks up synced extension files (stale enable would skip updates).
        if mod in bpy.context.preferences.addons:
            try:
                bpy.ops.preferences.addon_disable(module=mod)
            except RuntimeError:
                pass
        result = bpy.ops.preferences.addon_enable(module=mod)
        if "FINISHED" in result:
            return True

    print(f"ERROR: Could not enable addon. Tried: {modules_to_try}")
    return False


def setup_test_environment() -> None:
    """
    Sets up the test environment by adding the workspace to sys.path.
    This should be called at the start of each test file.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(os.path.dirname(script_dir))
    if workspace_root not in sys.path:
        sys.path.insert(0, workspace_root)
