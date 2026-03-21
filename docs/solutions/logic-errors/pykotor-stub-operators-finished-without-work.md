---
title: "PyKotor-gated operators that FINISHED without implementing work"
category: logic-errors
tags: [blender, pykotor, operators, stubs, testing, batch_convert, save-game]
module: io_scene_kotor.ops.texture.batch_convert_textures, io_scene_kotor.ops.save.extract
symptom: "Operator returns FINISHED and INFO says not yet implemented"
root_cause: "Placeholder execute() paths: gate on is_pykotor_available() then report INFO stub instead of doing I/O."
date: 2026-03-21
---

## Relationship to integration audit

[Integration audit plan](../../plans/2026-02-19-feat-integration-gaps-stubs-audit-plan.md) **Section A** defines a **target** policy: operators that perform no durable work should prefer **`{"CANCELLED"}`** (and honest severity) over **`{"FINISHED"}`**. **This document** describes **current as-built behavior and smoke expectations** for the two operators named below **until** that policy is implemented in code.

When changing return values, update **this file and the related smokes in the same PR** as the operators. **False-success `new_*` resource operators** (INFO “Created” with no disk write) are inventoried separately in the plan (**Section A.2**), not here.

---

## Context

`KB_OT_batch_convert_textures` and `KB_OT_extract_save` intentionally **do not** perform batch conversion or save extraction yet. They still return **`{"FINISHED"}`** when PyKotor is available, after an **INFO** report with the chosen path.

Without PyKotor they return **`{"CANCELLED"}`** with an **ERROR** report.

## Testing contract

Smoke tests should branch on **`is_pykotor_available()`**:

- **No PyKotor:** operators **`report({"ERROR"}, ...)`**; Blender may raise **`RuntimeError`** to the Python caller even when the operator would return **`CANCELLED`** — catch and assert the message contains **`PyKotor`**, or accept **`CANCELLED`** if no exception.
- **PyKotor present:** expect **`FINISHED`** (stub), no uncaught exception.

Do not assert filesystem side effects until the operators are implemented.

## Related

- `test/blender/test_ops_pykotor_stub_texture_save_smoke.py`
- `io_scene_kotor/ops/texture/batch_convert_textures.py`
- `io_scene_kotor/ops/save/extract.py`
