---
title: "ASCII MDL smoke tests must set trimesh kb on the mesh object"
category: test-failures
tags: [blender, mdl, ascii, object.kb, trimesh, tests]
module: io_scene_kotor
symptom: "ASCII MDL export/import smoke fails or wrong node types; trimesh treated as dummy; or spurious assignments on bpy.ops.kb"
root_cause: "KotOR props live on each object's kb (ObjectPropertyGroup). They are not on bpy.ops.kb (the operator submodule); conflating the two corrupts operator state or silently does nothing useful"
---

## Problem

Synthetic scenes for `kb.asciimdlexport` / `kb.asciimdlimport` tests build an MDL root empty plus a triangle mesh child. If test code assigns trimesh-related fields on **`root.kb`** only (or reuses the same `ObjectPropertyGroup` reference), the **mesh object** may still have default `meshtype`, so export produces the wrong graph or assertions on ASCII content fail.

## Working pattern

- Create the mesh object with **`obj.kb.meshtype = MeshType.TRIMESH`** (and node numbers, UVs, materials) on **`obj`**, not on the root.
- Use separate variables for root vs mesh `kb` state; never assume child inherits root KotOR props.
- Call operators as **`bpy.ops.kb.asciimdlexport(...)`** only; do not treat **`bpy.ops.kb`** as a stand-in for object **`kb`**.

## Prevention

- When adding MDL pipeline tests, follow `test/blender/test_mdl_minimal.py` / `test_ops_ascii_mdl_smoke.py`: parent is `DummyType.MDLROOT`; child mesh gets its own `kb` configuration.
- If a test fails with missing `trimesh` / `verts` in ASCII output, first verify **`bpy.data.objects['mesh_name'].kb.meshtype`**.

## Related

- [blender-bpy-ops-operator-init.md](./blender-bpy-ops-operator-init.md) — `bpy.ops` instantiation
- [operator-error-report-runtimeerror.md](../integration-issues/operator-error-report-runtimeerror.md) — `report({'ERROR'})` in tests
