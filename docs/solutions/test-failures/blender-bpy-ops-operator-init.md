---
title: "Blender bpy.ops fails: could not create instance (Operator __init__)"
category: test-failures
tags: [blender, bpy, operators, extensions, python, pytest, background-mode]
module: io_scene_kotor.ops.bakelightmaps, io_scene_kotor.ops.renderminimap
symptom: "RuntimeError: could not create instance of KB_OT_* to call callback function 'execute'"
root_cause: "Operator subclasses used broken __init__ (no super()), typo _init__, or non-RNA class attributes on bpy.types.Operator; Blender 4.4 refuses to instantiate."
date: 2026-03-21
---

## Problem

Calling `bpy.ops.kb.bake_lightmaps_auto()` or `kb.render_minimap_manual()` raised:

`RuntimeError: could not create instance of KB_OT_* to call callback function 'execute'`

Background-mode tests that expect `CANCELLED` never reached `execute`.

## Investigation

- Direct `SomeOperator()` is invalid for RNA types (`TypeError: bpy_struct.__new__`), so use `bpy.ops` for integration tests.
- The extension copy under Blender’s `extensions/user_default/io_scene_kotor` must match the repo; stale copies can hide fixes. `python test/run_blender_tests.py` syncs before tests; verify the synced tree if CI/local disagree.
- **BakeLightmapsOperator** defined `def _init__(self):` (never called) instead of initializing state correctly.
- Subclasses used `def __init__(self): self.foo = …` **without** `super().__init__(...)`, which breaks operator instantiation on Blender 4.4+.
- Placing arbitrary Python class attributes on `Operator` subclasses (e.g. `hide_non_lightmapped = False`) can interfere with RNA registration/instantiation.

## Working solution

1. **Avoid invalid `Operator.__init__` overrides.** Do not define `__init__` on `bpy.types.Operator` subclasses unless you call `super().__init__(*args, **kwargs)` in a way Blender supports; prefer **`invoke()`** to set per-run instance state, then call `return self.execute(context)`.

2. **Safe defaults when `execute` runs without `invoke`:** At the start of `execute`, use `getattr(self, "flag_name", default)` so `bpy.ops` execution contexts that call `execute` directly still work.

3. **Concrete pattern (this repo):**
   - `BakeLightmapsOperator.execute` uses `hide_nm = bool(getattr(self, "hide_non_lightmapped", True))`.
   - `KB_OT_bake_lightmaps_auto` / `_manual` implement `invoke` to set `self.hide_non_lightmapped` then delegate to `execute`.
   - `RenderMinimapOperator.execute` reads `hide_untextured` / `reset_render` via `getattr`; `KB_OT_render_minimap_auto` sets them in `invoke`.

## Prevention

- Add **smoke tests** that call `bpy.ops.kb.<operator>()` for operators with non-default configuration (even expecting `CANCELLED`).
- **Code review:** Flag `Operator` subclasses with custom `__init__` or typo `_init__`.
- **CI:** Run `test/run_blender_tests.py` so the addon is synced and extension behavior matches the branch.

## Related tests

- `test/blender/test_ops_bake_minimap_smoke.py` — no-target / no-AABB paths return `CANCELLED` without raising.

## Note: `open_addon_preferences` in background mode

`bpy.ops.preferences.addon_show` may invoke UI (`screen.userpref_show`) and log tracebacks when `poll()` fails, even if a wrapping operator catches `RuntimeError` and returns `CANCELLED`. Tests should assert return codes, not a clean console.

See also: [open-addon-preferences-background.md](../integration-issues/open-addon-preferences-background.md).

## References

- Blender Python API: `bpy.types.Operator`, `invoke`, `execute`
- Repository: `io_scene_kotor/ops/bakelightmaps.py`, `io_scene_kotor/ops/renderminimap.py`
