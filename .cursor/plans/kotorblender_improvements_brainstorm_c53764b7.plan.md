---
name: KotorBlender improvements brainstorm
overview: Brainstorm and roadmap for KotorBlender improvements (implementation, intuitivity, accessibility, maintainability, functionality) with concrete file/line refs, operator tables, P0/P1/P2 actions, operator UX and CONTRIBUTING acceptance criteria, and resolve-or-defer open questions.
todos:
  - id: impl-typo
    content: "Implementation P0: Fix typo Mininmap -> Minimap in io_scene_kotor/ui/menu/kotor.py line 32"
    status: completed
  - id: impl-poll
    content: "Implementation P0: Add poll_message_set() to 17 operators with poll() (armature, rebuild, anim, anim/event, lensflare, pth add/remove)"
    status: completed
  - id: intuit-desc
    content: "Intuitivity P0: Add bl_description to all operators lacking it (anim, lensflare, lyt, mdl, pth, rebuildmaterial, rebuildallmaterials)"
    status: completed
  - id: intuit-prefs
    content: "Intuitivity P1: Audit addonprefs.py texture/lightmap path descriptions (props already have description; add draw() tooltips if needed)"
    status: completed
  - id: a11y-audit
    content: "Accessibility P1: Confirm all actions keyboard-reachable via menus; audit panel/operator labels for clarity"
    status: completed
  - id: maint-contrib
    content: "Maintainability P0: Create CONTRIBUTING.md (contact before large changes, one PR per topic, tests/docs, how to run tests, ruff, extension name)"
    status: completed
  - id: maint-pr
    content: "Maintainability P0: Create .github/PULL_REQUEST_TEMPLATE.md (problem, solution, alternatives, limitations, checklist)"
    status: completed
  - id: maint-arch
    content: "Maintainability P1: Add ARCHITECTURE.md or Architecture section in AGENTS.md (format -> io -> scene -> ops/ui)"
    status: completed
  - id: doc-readme
    content: "Doc updates: Add Contributing and Testing links to README.md (CONTRIBUTING.md, TESTING.md or AGENTS.md)"
    status: completed
  - id: doc-testing
    content: "Doc updates: Update TESTING.md with asset-free vs E2E, test targets or pointer to AGENTS.md/Makefile"
    status: completed
  - id: func-doc
    content: "Functionality P1: Document TPC/TXI read-only and E2E (DATA_DIR) in README and/or TESTING.md"
    status: completed
  - id: verify-ux
    content: "Verification: Run Operator UX checklist (poll_message_set where poll fails, bl_description on all ops, keyboard reachable)"
    status: completed
  - id: verify-docs
    content: "Verification: Run Docs CONTRIBUTING & PR template acceptance criteria"
    status: completed
isProject: false
---

# KotorBlender Extension Improvements — Brainstorm

## What we're building

Improvements to the KotorBlender (io_scene_kotor) extension across five dimensions:

- **Implementation**: Code quality, patterns, error handling, duplication.
- **Intuitivity**: Discoverability, feedback (why an operator is disabled), clarity of UI.
- **Accessibility**: Keyboard reachability, descriptions for screen readers, theme-friendly UI.
- **Maintainability**: Contributor experience, tests, CI, docs, architecture.
- **Functionality**: Format support, E2E/asset testing, known gaps.

No new features are in scope unless they are small, high-impact fixes (e.g. operator descriptions).

---

## Vision & objectives (measurable goals)

- **Operator feedback:** All operators that use `poll()` show a clear, user-facing reason when disabled (via `poll_message_set()`).
- **Discoverability:** Every operator has a one-sentence `bl_description` (tooltip and screen readers).
- **Contributor experience:** CONTRIBUTING.md and PR template in place; README and TESTING point to them and to test commands.
- **Documentation:** Architecture (format -> io -> scene -> ops/ui) documented in ARCHITECTURE.md or AGENTS.md; TPC/TXI read-only and E2E (DATA_DIR) documented.
- **Quality:** CI unchanged or improved; no new lint failures; optional .zip artifact per PR.

---

## Research summary (sources)

**Repo (repo-research-analyst):**

- Structure: `format/` -> `io/` -> `scene/` -> `ops/` + `ui/`; 52 classes in [io_scene_kotor/**init**.py](io_scene_kotor/__init__.py). No CLAUDE.md, CONTRIBUTING, or ARCHITECTURE.
- Hotspots: MDL/MDX and [scene/material.py](io_scene_kotor/scene/material.py); WOK/AABB and [modelnode/base.py](io_scene_kotor/scene/modelnode/base.py). Ops report via `self.report({"ERROR"}, str(ex))`; no shared reporting helper.
- UI: Menus in [ui/menu/kotor.py](io_scene_kotor/ui/menu/kotor.py) (typo **"Mininmap"** at **line 32** -> "Minimap"). No keymaps. Many operators lack `bl_description`; **no `poll_message`** anywhere—disabled ops give no reason.
- Maintainability: [test/blender/](test/blender/) + Makefile + [test/run_blender_tests.py](test/run_blender_tests.py); CI lint (E9,F821,F823) and test-and-build; 400+ F401/F403 accepted.
- Gaps: TPC/TXI read-only; E2E needs `DATA_DIR` (not in CI).

**Best practices (best-practices-researcher):**

- Blender 4.x: Single register/unregister, thin `__init__.py`; extensions use `blender_manifest.toml`; allow online access, self-contained, read-only install dir.
- Accessibility: All actions keyboard-reachable; descriptive labels; WCAG 2.2 focus visibility; theme-aware UI.
- Format I/O: Roundtrip tests, golden files, versioned headers, clear exceptions; separate format vs scene layer.
- OSS quality: README quick start, CONTRIBUTING (one change per PR, tests/docs for new behavior), CI lint + Blender tests, optional build artifact.

**Current state (confirmed):** No CONTRIBUTING.md or ARCHITECTURE; no .github/PULL_REQUEST_TEMPLATE.md (only .github/workflows exist). README has Installation/Usage/Compatibility but no Contributing or Testing links. TESTING.md describes E2E only (DATA_DIR, TSL, OFFSET, LIMIT); asset-free tests and Makefile targets are in AGENTS.md. addonprefs.py already has StringProperty description on texture/lightmap paths (lines 35, 40). No poll_message_set in codebase.

---

## Plan structure (roadmap template)

- **Vision & objectives** — Measurable goals (e.g. all high-traffic operators show a clear reason when disabled).
- **Current state / gaps** — Above research summary.
- **Phases / scope** — By dimension (Implementation, Intuitivity, Accessibility, Maintainability, Functionality) with P0/P1/P2.
- **Priority levels** — P0 (must), P1 (should), P2 (nice); applied per action.
- **Dependencies & sequencing** — CONTRIBUTING/docs before contributor-facing work; operator UX (poll_message_set, bl_description) unblocked.
- **Acceptance criteria** — Per item or phase ("Done when X"); see Operator UX checklist and Docs checklist below.
- **Success metrics** — No operator without `bl_description`; all gated operators have `poll_message_set()`; CONTRIBUTING.md and PR template in repo; CI unchanged or improved.

---

## Concrete references (from repo research)

**Typo / UI**


| Change                 | File                                                               | Line |
| ---------------------- | ------------------------------------------------------------------ | ---- |
| "Mininmap" -> "Minimap" | [io_scene_kotor/ui/menu/kotor.py](io_scene_kotor/ui/menu/kotor.py) | 32   |


**Operators with `poll()` but no `poll_message` (add `poll_message_set(context, "…")` with user-facing reason)**


| File                            | Operator ID                   | poll() at |
| ------------------------------- | ----------------------------- | --------- |
| ops/armatureapplykeyframes.py   | kb.armature_apply_keyframes   | ~32       |
| ops/armatureunapplykeyframes.py | kb.armature_unapply_keyframes | ~32       |
| ops/rebuildarmature.py          | kb.rebuild_armature           | ~32       |
| ops/rebuildallmaterials.py      | kb.rebuild_all_materials      | ~31       |
| ops/rebuildmaterial.py          | kb.rebuild_material           | ~30       |
| ops/anim/add.py                 | kb.add_animation              | ~30       |
| ops/anim/delete.py              | kb.delete_animation           | ~29       |
| ops/anim/move.py                | kb.move_animation             | ~32       |
| ops/anim/play.py                | kb.play_animation             | ~29       |
| ops/anim/event/add.py           | kb.add_anim_event             | ~31       |
| ops/anim/event/delete.py        | kb.delete_anim_event          | ~30       |
| ops/anim/event/move.py          | kb.move_anim_event            | ~32       |
| ops/lensflare/add.py            | kb.add_lens_flare             | ~29       |
| ops/lensflare/delete.py         | kb.delete_lens_flare          | ~27       |
| ops/lensflare/move.py           | kb.move_lens_flare            | ~30       |
| ops/pth/addconnection.py        | kb.add_path_connection        | ~29       |
| ops/pth/removeconnection.py     | kb.remove_path_connection     | ~29       |


*Note:* MDL/LYT/PTH import/export have no `poll()` (always available). To give "why disabled" feedback for export, add `poll()` that can return False (e.g. no valid selection) then add `poll_message_set()`.

**Operators lacking `bl_description` (add one-sentence tooltip)**

- ops/anim/ (add, delete, move, play) and ops/anim/event/ (add, delete, move)
- ops/lensflare/ (add, delete, move)
- ops/lyt/ (importop, export) — kb.lytimport, kb.lytexport
- ops/mdl/ (importop, export) — kb.mdlimport, kb.mdlexport
- ops/pth/ (importop, export, addconnection, removeconnection)
- ops/rebuildallmaterials.py, ops/rebuildmaterial.py

**Docs to add**

- **Create** [CONTRIBUTING.md](CONTRIBUTING.md) (root).
- **Create** [ARCHITECTURE.md](ARCHITECTURE.md) or add "Architecture" section to [AGENTS.md](AGENTS.md).
- **Optional:** [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md), .github/ISSUE_TEMPLATE/.

**Doc updates**

- [README.md](README.md) — Contributing + Testing links (CONTRIBUTING.md, TESTING.md or AGENTS.md).
- [TESTING.md](TESTING.md) — Asset-free vs E2E, test targets or pointer to AGENTS.md/Makefile.

---

## Operator UX checklist (acceptance criteria)

- **poll_message_set()** (Blender 4.x) wherever `poll()` can return False; short user-facing sentence (e.g. "Select a KotOR model object").
- **bl_description** on every operator (one sentence: what it does, when to use it).
- All actions **keyboard reachable** via menus (document as baseline); no custom keymaps unless necessary.

---

## Docs: CONTRIBUTING & PR template (acceptance criteria)

- **CONTRIBUTING.md** contains: contact before large changes, one logical change per PR, tests/docs for new behavior, how to run tests (`make test`, test/blender/, run_blender_tests.py), code style (ruff, AGENTS.md), extension name `bl_ext.user_default.io_scene_kotor` (4.2+).
- **PR template** contains: description of problem, proposed solution, alternatives considered, limitations, checklist (e.g. `make test`, no new lint, docs/CHANGELOG if needed).

---

## Approaches

### Approach A — Quick wins + backlog (minimal)

- **What**: Fix the known low-hanging fruit and document the rest.
- **Actions**: Fix "Mininmap" -> "Minimap" in [ui/menu/kotor.py](io_scene_kotor/ui/menu/kotor.py) (line 32); add CONTRIBUTING.md and a minimal PR template; add `poll_message_set()` on 3–5 high-traffic operators (e.g. rebuild materials, armature, anim). Add a short "Improvement backlog" section to AGENTS.md or BACKLOG.md for a11y, keymaps, TPC write, E2E.
- **Pros**: Fast, low risk, immediate value for users and contributors.
- **Cons**: No structured roadmap; backlog can stay vague.

**Best for:** Getting something shippable quickly without a big process.

---

### Approach B — Dimension-by-dimension roadmap (recommended)

- **What**: One structured plan per dimension, each with 3–5 concrete, prioritized actions. Single brainstorm doc that doubles as the improvement roadmap.
- **Actions** (summary; concrete refs in tables below):
  - **Implementation (P0)**: Fix typo at [ui/menu/kotor.py:32](io_scene_kotor/ui/menu/kotor.py); add `poll_message_set()` where `poll()` fails (see operator table); optional shared report helper; (P2) reduce duplication in [ops/showhideobjects.py](io_scene_kotor/ops/showhideobjects.py) (base class or shared helper; 18 classes, ~lines 33–311).
  - **Intuitivity (P0)**: Every operator has `bl_description` (see operators lacking list); (P1) tooltips/descriptions for texture/lightmap path prefs in [addonprefs.py](io_scene_kotor/addonprefs.py) (props ~31–41, draw ~43–46).
  - **Accessibility (P1)**: All actions keyboard-reachable via menus (no custom keymaps unless needed); audit labels/operator names; keep custom UI minimal and theme-aware.
  - **Maintainability (P0)**: Add [CONTRIBUTING.md](CONTRIBUTING.md) and [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md) per Blender guidelines; (P1) ARCHITECTURE.md or "Architecture" section in AGENTS.md (format -> io -> scene -> ops/ui); CI as-is; optional .zip artifact per PR.
  - **Functionality (P1)**: Document TPC/TXI read-only and E2E (DATA_DIR) in README/TESTING; (P2) optional golden MDL/MDX in repo for roundtrip tests.
- **Pros**: Clear priorities, one doc to drive planning and execution, covers all five dimensions.
- **Cons**: More upfront thinking; some items (e.g. shared show/hide base) need design.

**Best for:** Aligning contributors and maintaining a single improvement plan.

---

### Approach C — User- and contributor-facing first

- **What**: Prioritize what a new user and first-time contributor see, then extend.
- **Actions**: (1) README quick start (enable extension, import one MDL, export). (2) CONTRIBUTING.md + PR template. (3) Operator descriptions and `poll_message` for import/export and rebuild. (4) Then a11y audit (labels, keyboard), then format/architecture docs.
- **Pros**: Improves adoption and first contributions quickly.
- **Cons**: Less explicit structure for "implementation" or "functionality" gaps; those become follow-up.

**Best for:** Growing the user and contributor base before deep refactors.

---

## Recommendation

**Approach B (dimension-by-dimension roadmap)** is recommended because:

- You chose to cover **all** areas; B is the only one that explicitly structures all five.
- The repo already has solid CI and tests; the main gaps are docs (CONTRIBUTING, architecture), UX (poll_message_set, bl_description), and a few code cleanups—B captures these in one place.
- It produces a single brainstorm document that can be turned into an implementation plan (e.g. via `/workflows:plan`) or used as a living roadmap.

---

## Key decisions

- **Scope**: Improvements only; no large new features. Small, high-impact additions (e.g. operator descriptions, poll_message_set) are in scope.
- **Docs**: Add CONTRIBUTING.md and PR template; optional ARCHITECTURE.md or AGENTS.md section; keep AGENTS.md the single entry for agents/automation.
- **Tests**: Keep asset-free CI; tests that need [test_files/](test/test_files/) continue to skip when missing. Optional: golden MDL/MDX for roundtrip tests (see Open questions).
- **Accessibility**: Keyboard reachability via menus; clear labels/descriptions; avoid custom keymaps unless needed; theme-aware UI.
- **Dependencies & sequencing**: CONTRIBUTING and PR template first (unblocks contributor-facing work); operator UX (poll_message_set, bl_description) can run in parallel; doc cross-links (README, TESTING) after new docs exist.

---

## Open questions (all resolved or deferred)

**Process:** Each open question is either **Resolved** (becomes a planned item with acceptance criteria and priority) or **Deferred** (moved to Backlog with reason and optional revisit trigger). No question stays open without a target resolution.

1. **Golden files** — **Decision:** Deferred. Use existing test_files when present; no new golden set for CI until E2E-in-CI is required. Revisit when adding CI E2E.
2. **Show/hide operators** — **Decision:** Deferred. Add bl_description only (already present on show/hide ops); leave structure as-is. Revisit when adding new show/hide types.

---

## Resolved questions

1. **Extension vs add-on** — Project **already** has both [io_scene_kotor/blender_manifest.toml](io_scene_kotor/blender_manifest.toml) (extension) and `bl_info` in [io_scene_kotor/**init**.py](io_scene_kotor/__init__.py) (lines 109–116) for backward compatibility. No "migrate to extension layout" step needed. Optional P2: document dual extension/addon support or drop `bl_info` when dropping Blender 3.6.

---

## Backlog (deferred)

*Items moved here when an open question is deferred; include reason and optional revisit trigger.*

- **Golden files in CI** — Deferred. Use existing test_files when present; do not add new golden MDL/MDX set for CI until E2E-in-CI is required. Revisit when adding CI E2E.
- **Show/hide refactor** — Deferred. Keep 18 operator classes; only ensure bl_description (already present). Revisit when adding new show/hide types.

---

## Deliverable

- **Document**: Create [docs/brainstorms/2026-03-19-kotorblender-improvements-brainstorm.md](docs/brainstorms/2026-03-19-kotorblender-improvements-brainstorm.md) with the content above (and expand the dimension-by-dimension action lists when implementing the plan).
- **Directory**: Create `docs/brainstorms/` if it does not exist (repo currently has no `docs/`).

---

## Implementation phases (execution order)

1. **Phase 1 — Maintainability P0:** Create CONTRIBUTING.md and .github/PULL_REQUEST_TEMPLATE.md (todos: maint-contrib, maint-pr).
2. **Phase 2 — Implementation P0:** Fix typo in kotor.py; add poll_message_set() to 17 operators (todos: impl-typo, impl-poll).
3. **Phase 3 — Intuitivity P0:** Add bl_description to all operators lacking it (todo: intuit-desc).
4. **Phase 4 — Doc updates:** README Contributing/Testing links; TESTING.md asset-free vs E2E (todos: doc-readme, doc-testing).
5. **Phase 5 — Maintainability P1 / Intuitivity P1 / Accessibility / Functionality:** ARCHITECTURE section, addonprefs audit, a11y audit, TPC/TXI and E2E docs (todos: maint-arch, intuit-prefs, a11y-audit, func-doc).
6. **Phase 6 — Verification:** Operator UX checklist and Docs checklist (todos: verify-ux, verify-docs).

---

## Next steps

1. Execute the todo steps above in phase order (see Implementation phases).
2. Optionally create [docs/brainstorms/2026-03-19-kotorblender-improvements-brainstorm.md](docs/brainstorms/2026-03-19-kotorblender-improvements-brainstorm.md) from this plan for sharing.
3. Use this plan as the implementation roadmap or run `/workflows:plan` to produce a phase-by-phase implementation plan.

