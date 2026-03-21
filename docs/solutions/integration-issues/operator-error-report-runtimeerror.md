---
title: "bpy.ops: ERROR report surfaces as RuntimeError to Python"
category: integration-issues
tags: [blender, bpy.ops, operators, testing, background-mode]
module: general Blender operator API
symptom: "bpy.ops.kb.*() raises RuntimeError with the operator's English error string"
root_cause: "Blender propagates operator failure to the script caller when the operator uses self.report({'ERROR'}, ...) in some execution contexts."
date: 2026-03-21
---

## Problem

Tests that call `bpy.ops.kb.open_module()` or other operators expecting a **return set** may instead receive:

`RuntimeError: Error: …` (message matches `self.report` text).

## Mitigation in tests

Use **`try` / `except RuntimeError`** and assert on the message substring, **or** use lower-level APIs if available.

## Examples in-repo

- `test/blender/test_ops_open_module_stub_smoke.py` — **"No module selected"**
- `test/blender/test_ops_pykotor_stub_texture_save_smoke.py` — **"PyKotor is not available"**

## Related

- [pykotor-stub-operators-finished-without-work.md](../logic-errors/pykotor-stub-operators-finished-without-work.md)

