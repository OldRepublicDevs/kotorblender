# KotorBlender Improvements Brainstorm (2026-03-19)

Improvements to the KotorBlender (io_scene_kotor) extension across five dimensions:

- **Implementation** — Code quality, patterns, error handling, duplication.
- **Intuitivity** — Discoverability, feedback (why an operator is disabled), clarity of UI.
- **Accessibility** — Keyboard reachability, descriptions for screen readers, theme-friendly UI.
- **Maintainability** — Contributor experience, tests, CI, docs, architecture.
- **Functionality** — Format support, E2E/asset testing, known gaps.

No large new features; small, high-impact fixes (e.g. operator descriptions, `poll_message_set`) are in scope.

---

## Vision & objectives

- **Operator feedback:** All operators that use `poll()` show a clear, user-facing reason when disabled (via `poll_message_set()`).
- **Discoverability:** Every operator has a one-sentence `bl_description` (tooltip and screen readers).
- **Contributor experience:** CONTRIBUTING.md and PR template in place; README and TESTING point to them and to test commands.
- **Documentation:** Architecture (format → io → scene → ops/ui) documented in ARCHITECTURE.md or AGENTS.md; TPC/TXI read-only and E2E (DATA_DIR) documented.
- **Quality:** CI unchanged or improved; no new lint failures.

---

## Implementation phases (execution order)

1. **Phase 1 — Maintainability P0:** Create CONTRIBUTING.md and .github/PULL_REQUEST_TEMPLATE.md.
2. **Phase 2 — Implementation P0:** Fix typo "Mininmap" → "Minimap" in ui/menu/kotor.py; add `poll_message_set()` to 17 operators (armature, rebuild, anim, anim/event, lensflare, pth add/remove).
3. **Phase 3 — Intuitivity P0:** Add `bl_description` to all operators lacking it (anim, lensflare, lyt, mdl, pth, rebuildmaterial, rebuildallmaterials).
4. **Phase 4 — Doc updates:** README Contributing/Testing links; TESTING.md asset-free vs E2E.
5. **Phase 5 — Maintainability P1 / Intuitivity P1 / Accessibility / Functionality:** ARCHITECTURE section in AGENTS.md, addonprefs audit, a11y audit, TPC/TXI and E2E docs.
6. **Phase 6 — Verification:** Operator UX checklist and Docs checklist.

---

## Operator UX checklist (acceptance criteria)

- **poll_message_set()** (Blender 4.x) wherever `poll()` can return False; short user-facing sentence (e.g. "Select a KotOR model object").
- **bl_description** on every operator (one sentence: what it does, when to use it).
- All actions **keyboard reachable** via menus; no custom keymaps unless necessary.

---

## Docs: CONTRIBUTING & PR template (acceptance criteria)

- **CONTRIBUTING.md** contains: contact before large changes, one logical change per PR, tests/docs for new behavior, how to run tests (`make test`, test/blender/, run_blender_tests.py), code style (ruff, AGENTS.md), extension name `bl_ext.user_default.io_scene_kotor` (4.2+).
- **PR template** contains: description of problem, proposed solution, alternatives considered, limitations, checklist (e.g. `make test`, no new lint, docs/CHANGELOG if needed).

---

## Backlog (deferred)

- **Golden files in CI** — Use existing test_files when present; do not add new golden MDL/MDX set for CI until E2E-in-CI is required.
- **Show/hide refactor** — Keep 18 operator classes; only ensure bl_description. Revisit when adding new show/hide types.

---

## Status

All phases above have been implemented. CONTRIBUTING.md, PR template, typo fix, poll_message_set on gated operators, bl_description on operators, README/TESTING links, ARCHITECTURE in AGENTS.md, addonprefs and a11y audits, and TPC/TXI/E2E documentation are in place. Verification checklists have been run.

This document is the canonical brainstorm and improvement roadmap; the implementation plan lives in `.cursor/plans/`.
