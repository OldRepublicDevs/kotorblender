---
title: "open_addon_preferences: Blender stderr tracebacks in background mode"
category: integration-issues
tags: [blender, background-mode, preferences, extensions, bpy.ops, testing]
module: io_scene_kotor.ops.misc.open_addon_preferences
symptom: "Tests pass but console shows Python tracebacks from userpref_show / addon_show"
root_cause: "bpy.ops.preferences.addon_show triggers UI operators that poll() fail without a valid screen context; Blender logs the error before our try/except returns CANCELLED."
date: 2026-03-21
---

## Problem

`KB_OT_open_addon_preferences` loops over `ADDON_PREFERENCE_MODULE_KEYS` and calls `bpy.ops.preferences.addon_show(module=...)`, catching `RuntimeError` per key. In **`blender --background`**, internal code still invokes `screen.userpref_show`, which **fails `poll()`** and prints tracebacks to stderr.

The operator may correctly end with **`{"CANCELLED"}`** and a **`WARNING`** report after all keys fail.

## What to do

- **Tests:** Assert **return set** (`FINISHED` or `CANCELLED`) and **no uncaught exception** — do not require a clean stderr.
- **Optional product fix:** Detect background or invalid context and **skip** `addon_show`, or use a non-UI API if Blender exposes one for the active extension module only (version-dependent).

## Related

- `test/blender/test_ops_open_preferences_smoke.py`
- `docs/solutions/test-failures/blender-bpy-ops-operator-init.md` (operator instantiation patterns)
