---
name: KotorBlender improvements brainstorm
overview: Brainstorm and roadmap for KotorBlender improvements (implementation, intuitivity, accessibility, maintainability, functionality) with concrete file/line refs, operator tables, P0/P1/P2 actions, operator UX and CONTRIBUTING acceptance criteria, and resolve-or-defer open questions.
todos:
  - id: impl-typo
    content: "Implementation P0: Fix typo Mininmap → Minimap in io_scene_kotor/ui/menu/kotor.py line 32"
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
    content: "Maintainability P1: Add ARCHITECTURE.md or Architecture section in AGENTS.md (format → io → scene → ops/ui)"
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
- **Documentation:** Architecture (format → io → scene → ops/ui) documented in ARCHITECTURE.md or AGENTS.md; TPC/TXI read-only and E2E (DATA_DIR) documented.
- **Quality:** CI unchanged or improved; no new lint failures; optional .zip artifact per PR.

---

## Research summary (sources)

**Repo (repo-research-analyst):**

- Structure: `format/` → `io/` → `scene/` → `ops/` + `ui/`; 52 classes in [io_scene_kotor/**init**.py](io_scene_kotor/__init__.py). No CLAUDE.md, CONTRIBUTING, or ARCHITECTURE.
- Hotspots: MDL/MDX and [scene/material.py](io_scene_kotor/scene/material.py); WOK/AABB and [modelnode/base.py](io_scene_kotor/scene/modelnode/base.py). Ops report via `self.report({"ERROR"}, str(ex))`; no shared reporting helper.
- UI: Menus in [ui/menu/kotor.py](io_scene_kotor/ui/menu/kotor.py) (typo **"Mininmap"** at **line 32** → "Minimap"). No keymaps. Many operators lack `bl_description`; **no `poll_message_set()`** before the P0 pass—disabled ops gave no reason (since addressed in todos).
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
| "Mininmap" → "Minimap" | [io_scene_kotor/ui/menu/kotor.py](io_scene_kotor/ui/menu/kotor.py) | 32   |


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
- **Actions**: Fix "Mininmap" → "Minimap" in [ui/menu/kotor.py](io_scene_kotor/ui/menu/kotor.py) (line 32); add CONTRIBUTING.md and a minimal PR template; add `poll_message_set()` on 3–5 high-traffic operators (e.g. rebuild materials, armature, anim). Add a short "Improvement backlog" section to AGENTS.md or BACKLOG.md for a11y, keymaps, TPC write, E2E.
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
  - **Maintainability (P0)**: Add [CONTRIBUTING.md](CONTRIBUTING.md) and [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md) per Blender guidelines; (P1) ARCHITECTURE.md or "Architecture" section in AGENTS.md (format → io → scene → ops/ui); CI as-is; optional .zip artifact per PR.
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

**Completed:** `docs/brainstorms/` and `docs/brainstorms/2026-03-19-kotorblender-improvements-brainstorm.md` created with roadmap summary, phases, acceptance criteria, and backlog.

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
4. **Further menu integration** (context menus, header menus, NSS in Text Editor, optional keymaps) is captured and deepened in [pykotor_integration_and_ui_expansion_91971bed.plan.md](pykotor_integration_and_ui_expansion_91971bed.plan.md) Part 3.10 and Part 9.

---

## Enhancement summary (deepened 2026-03-21)

**Note:** `/deepen-plan` requested plan path `#/compound`; no `compound` plan file exists in-repo. This pass deepens **this** brainstorm plan using a fresh repo-research-analyst pass and Blender extension best practices (no parallel skill/agent fan-out in this environment).

**Sections enhanced:** Coverage roadmap, operator/testing discipline, institutional memory link.

**Research inputs:** `repo-research-analyst` (2026-03-21) — prioritized remaining gaps: module/game PyKotor workflows, `new_*` / `edit_*` resource ops, tools (`file_search`, designers), save-game ops, extended show/hide matrix, texture batch/extract ops, ASCII MDL reader/writer pytest corpora, UV/emitter export depth, `open_addon_preferences` behavior.

### Key improvements to fold into future work

1. **Coverage matrix caveat:** `test/scripts/coverage_inventory.py` marks “covered” on import heuristics; prioritize `bpy.ops` smoke and assertions over import-only “yes” cells.
2. **PyKotor-gated ops:** Use temp dirs + `skip`/clean `CANCELLED` when PyKotor or module roots are missing so CI stays asset-free.
3. **Operator construction:** Avoid custom `Operator.__init_`_ without proper `super()`; use `invoke` + `getattr` defaults in `execute` (see [docs/solutions/test-failures/blender-bpy-ops-operator-init.md](../../docs/solutions/test-failures/blender-bpy-ops-operator-init.md)).
4. **Show/hide family:** Extend smoke tests beyond walkmesh/lights — untextured trimeshes, emitters, blockers, classification-filtered pairs (characters/placeables/doors) as synthetic scenes allow.
5. **Format tests:** ASCII MDL malformed inputs and `AsciiMdlWriter`↔`AsciiMdlReader` roundtrip are strong **pytest** candidates (no `bpy` in `conftest` pipeline once imports verified).

### New considerations

- **Extension sync:** Local failures where `bpy.ops` runs old code — ensure `test/run_blender_tests.py` sync runs (or manually mirror `io_scene_kotor` into Blender’s `extensions/user_default/io_scene_kotor`).
- `**open_addon_preferences`:** May return `CANCELLED` in background or when module id mismatches; test should allow `FINISHED` or `CANCELLED` but not exceptions.

### Research insights (testing & quality)

**Best practices**

- Prefer one focused smoke file per operator cluster (show/hide, bake/minimap, new resource) with clear `CANCELLED` vs `FINISHED` expectations.
- Keep `ExportHelper` ops testable with `filepath=` and a temp path deleted after assert.

**Edge cases**

- Operators that configure render/bake may need early exit paths tested first (no targets) before full integration tests with materials and Cycles.

**References**

- [Blender Extensions — packaging & testing](https://docs.blender.org/manual/en/latest/advanced/extensions/index.html) (official docs; verify current URL in-browser).
- In-repo: `AGENTS.md`, `test/run_blender_tests.py`, `docs/solutions/test-failures/blender-bpy-ops-operator-init.md`.

---

## Enhancement summary (deepened 2026-03-21 — pass 2)

**Plan path note:** `#/compound` still has no dedicated plan file; this pass continues on **this** brainstorm and records a second `repo-research-analyst` cycle plus `/compound` output.

**Analyst focus (pass 2):** Prioritize behavioral tests over import-only coverage — **ASCII/binary MDL roundtrips** (pytest where `bpy`-free), **mdlexport** with SKIN/DANGLY/emitter/light variants, **game/module PyKotor ops** with temp dirs and skips, **texture batch/extract**, **`edit_*` / save-game** smoke, **file_search** with fake install tree.

**Compound documentation**

- [docs/solutions/test-failures/blender-bpy-ops-operator-init.md](../../docs/solutions/test-failures/blender-bpy-ops-operator-init.md) — Operator `__init__` / `bpy.ops` instantiation.
- [docs/solutions/integration-issues/open-addon-preferences-background.md](../../docs/solutions/integration-issues/open-addon-preferences-background.md) — Preferences op tracebacks in background tests.

**Tests implemented in-repo after pass 2 (examples):** show/hide **blockers**; **mdlexport** with **danglymesh** child (orthogonal to anim+wok case).

**Research insights**

- `format/mdl/ascii_reader.py` is not pytest-trivial today: it imports `scene/*` and `mathutils`; full ASCII corpus tests belong in **Blender** unless the reader is refactored to a `bpy`-free layer.
- **file_search** requires **PyKotor + resolved install path**; smoke tests should expect **CANCELLED** with a clear report when either is missing (CI-friendly).

---

## Enhancement summary (deepened 2026-03-21 — pass 3)

**`#/compound`:** Still no standalone compound plan; this entry deepens the same brainstorm from **repo-research-analyst (97b8ab34)** and new `/compound` doc for stub operators.

**Analyst highlights:** **pack/unpack/validate_module**, **batch_convert_textures**, **open_module** edge cases, **save extract/open_editor**, **file_search** with temp tree, **ascii_reader** pytest (still blocked by `scene/*` imports in practice).

**Tests added (pass 3):** **open_module** with empty **module_list** → **CANCELLED**; **batch_convert_textures** / **extract_save** → **CANCELLED** without PyKotor or **FINISHED** stub with PyKotor; **ASCII MDL** export with **animations+walkmeshes** and AABB child; fixed **test_ops_ascii_mdl_smoke** mesh **`kb`** assignment bug on trimesh child.

**Compound**

- [docs/solutions/logic-errors/pykotor-stub-operators-finished-without-work.md](../../docs/solutions/logic-errors/pykotor-stub-operators-finished-without-work.md)
- [docs/solutions/integration-issues/operator-error-report-runtimeerror.md](../../docs/solutions/integration-issues/operator-error-report-runtimeerror.md)

**Research insight**

- Stub operators that return **{"FINISHED"}** with “not yet implemented” **INFO** reports should be covered explicitly so **CANCELLED**-only tests do not regress the stub contract when PyKotor is present in CI or local wheels.

---

## Enhancement summary (deepened 2026-03-21 — pass 4)

**`#/compound`:** No standalone compound plan file; this pass deepens **this** brainstorm from **repo-research-analyst** (coverage round 4) and one new `/compound` solution note.

**Analyst ideas used:** Extended show/hide (classification matrix, unlightmapped, items-global behavior); tools ops stub smoke (`module_designer`, `indoor_map_builder`, `clone_module`, `tslpatchdata_editor`). Deferred for later: pytest `MdlWriter`↔`MdlReader` (both sides pull in **mathutils** / **scene** — keep in Blender or refactor format layer).

**Tests added (pass 4):** **test_ops_showhide_extended_categories_smoke.py**; **test_ops_tools_stub_smoke.py**.

**Compound**

- [docs/solutions/test-failures/ascii-mdl-smoke-trimesh-kb-on-mesh-object.md](../../docs/solutions/test-failures/ascii-mdl-smoke-trimesh-kb-on-mesh-object.md) — trimesh **`kb`** must be on the **mesh** object, not the MDL root.

**Research insight**

- **hide_items** / **hide_triggers** / **hide_waypoints** currently affect **all** scene objects until resource binding exists; a dedicated test documents that contract and guards accidental “fix” without UTI/UTT/UTW filtering.

---

## Enhancement summary (deepened 2026-03-21 — pass 5)

**Plan path note:** `/deepen-plan` was invoked with tool names, not a file path; this pass deepens **this** brainstorm using **best-practices-researcher** and **repo-research-analyst** outputs plus `/compound` update (single learning file amended, not a second doc).

### Best practices (Blender tests, 2024–2026)

- Prefer **`blender --background --python`** (and optionally **`--factory-startup`**) for CI parity; see [Blender Python tests handbook](https://developer.blender.org/docs/handbook/testing/python/) and [command-line arguments](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html).
- Temp files: **`tempfile`** + **`finally`** cleanup; assert file/scene outcomes, not only “operator ran.”
- Avoid no-op **`try`** bodies and bare catches that hide failures.

### Analyst backlog (highest value)

1. PyKotor **module** workflow ops (**pack/unpack/validate/open_resource/…**) — almost no `bpy.ops` smoke beyond gates.
2. **GFF/resource** `new_*` / `edit_*` — mostly untested except **new_gff**.
3. **Show/hide** — **triggers/waypoints** pairs not yet in show/hide smoke files.
4. **Bake/minimap** — **manual vs auto** variant coverage uneven.
5. **Save game** editor op — no dedicated smoke.
6. **Registration test** — operator count / list drift vs real **`kb.*`** surface.
7. **CONTRIBUTING** vs **Makefile** — aligned in-repo (see pass 5 doc edit).

### Compound (amended)

- [ascii-mdl-smoke-trimesh-kb-on-mesh-object.md](../../docs/solutions/test-failures/ascii-mdl-smoke-trimesh-kb-on-mesh-object.md) — extended with **do not assign mesh props on `bpy.ops.kb`**.

### `/resolve_todo_parallel`

No `todos/*.md` (or equivalent) tree present in the repo — nothing to batch-resolve this round.

---

## Enhancement summary (deepened 2026-03-21 — pass 6)

**Plan path note:** `/deepen-plan` again had no file path (tool names only); this pass uses **`best-practices-researcher`** and **`repo-research-analyst`**, plus **`/compound`** (one new solution file under `docs/solutions/debugging-patterns/`).

### Best practices (CONTRIBUTING / Makefile DRY)

- **Executable truth:** Keep **Makefile** + **CI** aligned; **CONTRIBUTING** = curated commands + **link** to **AGENTS.md** for the full matrix ([GitHub contributing guidelines](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors)).
- **Scale:** Prefer **`make help`** long-term over duplicating every `test-*` in prose ([self-documenting Makefile](https://victoria.dev/blog/how-to-create-a-self-documenting-makefile/)).

### Analyst — next concrete tests

1. **`test_ops_file_search_smoke.py`** — `kb.file_search`: short query / PyKotor-off **`CANCELLED`** without dialog.
2. **`test_ops_kotor_diff_smoke.py`** — `kb.kotor_diff` **`execute`** with **`filepath`** + **`other_path`** (identical temp files).
3. **`test_ops_refresh_modules_smoke.py`** — `kb.refresh_modules` invalid install + PyKotor gate.
4. **`test_ops_validate_module_smoke.py`** — `kb.validate_module` **`CANCELLED`** + **`last_validation_report`** when install/PyKotor missing.
5. **Extend `test_ops_bake_minimap_smoke.py`** — **`bake_lightmaps_manual`**, **`render_minimap_auto`** early exits (alt: **`test_ops_select_game_installation_smoke.py`**).

### Compound (new)

- [contributing-makefile-test-target-drift.md](../../docs/solutions/debugging-patterns/contributing-makefile-test-target-drift.md)

### `/resolve_todo_parallel`

Still no **`todos/*.md`** tree in-repo — nothing to resolve in batch.

---

## Enhancement summary (deepened 2026-03-21 — pass 7)

**Plan path note:** `/deepen-plan` invoked with tool names only; this pass uses **best-practices-researcher** and **repo-research-analyst**, **`/compound`** (one new doc), and **`/resolve_todo_parallel`** (still N/A).

### Cleanup in this pass

- Normalized **garbled Markdown** in enhancement summaries **passes 2–5** (invalid `` `**…`** `` nesting and similar) so previews match intent.

### Best practices (Markdown maintenance)

- Follow **CommonMark** rules for emphasis vs inline code; add blank lines around headings/lists; consider **markdownlint** + link checking in CI ([CommonMark spec](https://spec.commonmark.org/current/), [markdownlint](https://github.com/DavidAnson/markdownlint)).

### Analyst — quick wins (≲30 min each; excludes pass 6 test backlog)

1. **Docs:** `.github/ISSUE_TEMPLATE/` (bug + `config.yml`) — Blender version, OS, repro, sample path.
2. **Tests:** `test_ops_open_save_editor_smoke.py` — `kb.open_save_editor` invalid path → clean **CANCELLED** / no traceback.
3. **Tests:** Extra **pytest** cases in `test/unit/` for a pure helper (`game_install_detect`, `log_config`, …).
4. **Docs:** Short **Troubleshooting** pointer in **CONTRIBUTING** or **TESTING** → `docs/solutions/`.

### Compound (new)

- [markdown-nested-emphasis-corruption-in-plans.md](../../docs/solutions/debugging-patterns/markdown-nested-emphasis-corruption-in-plans.md)

### `/resolve_todo_parallel`

No `todos/*.md` directory — no parallel resolution.

---

## Enhancement summary (deepened 2026-03-20 — pass 8)

**Plan path:** `#/brainstorm` → this file (`.cursor/plans/kotorblender_improvements_brainstorm_c53764b7.plan.md`). Companion brainstorm snapshot: [docs/brainstorms/2026-03-20-kotorblender-post-completion-backlog.md](../../docs/brainstorms/2026-03-20-kotorblender-post-completion-backlog.md).

### Section manifest (for future deep research)

| Section | Research focus |
| -------- | ---------------- |
| Architecture & data flow | Evolve `format → io → scene → ops/ui` boundaries; brittle coupling spots |
| Implementation backlog vs risk | Blast radius per module; tie to tests / `docs/solutions` |
| UX & intuitivity | One coherent import → edit → export + game tooling narrative |
| Accessibility & discoverability | Menus, Quick access, keyboard paths vs real user flows |
| Maintainability & extension hygiene | Wheels, manifest, prefs, Windows/Linux CI parity |
| Test strategy & backlog burn-down | `test/blender` smoke vs `test/unit`; operator = GUI parity |
| Contributor experience | CONTRIBUTING + `docs/solutions` as runbook |

### External references (CI / headless testing)

- [Blender StackExchange — CI for add-ons](https://blender.stackexchange.com/questions/67274/how-to-do-continuous-integration-with-gitlab-when-developing-blender-addons) — context overrides, cleanup, headless pitfalls.
- [pytest-blender](https://github.com/mondeja/pytest-blender) — optional pattern: pytest driving Blender’s Python; compare to this repo’s `blender --background --python test/blender/...` approach.
- [Blender Extensions — moderation guidelines](https://wiki.blender.org/features/extensions/moderation/guidelines/) — packaging expectations for extensions ecosystem.

### Institutional memory (apply when executing backlog)

- [docs/solutions/test-failures/blender-bpy-ops-operator-init.md](../../docs/solutions/test-failures/blender-bpy-ops-operator-init.md)
- [docs/solutions/test-failures/ascii-mdl-smoke-trimesh-kb-on-mesh-object.md](../../docs/solutions/test-failures/ascii-mdl-smoke-trimesh-kb-on-mesh-object.md)
- [docs/solutions/debugging-patterns/markdown-nested-emphasis-corruption-in-plans.md](../../docs/solutions/debugging-patterns/markdown-nested-emphasis-corruption-in-plans.md)

### Analyst — top 3 “what to build next”

1. **Burn down operator-level test backlog** (`bpy.ops.kb.*` smokes for module/game, file_search, kotor_diff, validate_module, etc.).
2. **Harden ASCII MDL / scene-property edges** where Blender smokes already mirror modder workflows.
3. **Grow `docs/solutions` + CONTRIBUTING troubleshooting** so CI/local failures are searchable.

### Research insight (pass 8)

Original brainstorm **P0 phases are complete** (see [2026-03-19 brainstorm](../../docs/brainstorms/2026-03-19-kotorblender-improvements-brainstorm.md)); remaining value is **regression harness + PyKotor workflow coverage + contributor runbook**, not reopening closed UX/doc todos unless new scope is agreed.

---

## Enhancement summary (deepened 2026-03-20 — pass 9)

**Prompt:** Intuitivity & accessibility; Blender extension / API surface not yet used; learn from other extensions.

### Current KotorBlender strengths (baseline)

- **`blender_manifest.toml`:** `tagline`, version, bundled **wheels** (PyKotor path).
- **`bpy.types.FileHandler`:** drag/drop for `.mdl`, `.mdl.ascii`, `.lyt`, `.pth` ([`ops/file_handler_drop.py`](../../io_scene_kotor/ops/file_handler_drop.py)).
- **Optional keymaps** (GUI only): Open Module, show/hide walkmeshes ([`__init__.py`](../../io_scene_kotor/__init__.py) ~527+).
- **Menus + sidebar panels**; **Quick access** / prefs operator; broad **`bl_description`** + **`poll_message_set()`** on gated operators (P0 wave).

### Gaps vs “typical” polished 4.x extensions (prioritized ideas)

| Idea | Rationale |
|------|-----------|
| **Unified drag/drop story** | Peer extensions (e.g. [Drag and Drop Support](https://extensions.blender.org/add-ons/drag-and-drop-support/)) centralize many formats; KotorBlender could add **FileHandlers** for **.wok/.pwk/.dwk**, **.tpc/.tga** (where import exists) so behavior matches user mental model. |
| **First-run / prefs onboarding** | Surface **game path**, **PyKotor/wheels health**, and **keymap** hints inside **addon preferences** (status row + link to docs); many extensions expose “ready / not ready” without opening logs. |
| **Export `poll()` + `poll_message_set()`** | Original plan noted MDL/LYT/PTH import/export often have no `poll()`; greyed exports without a **why** hurt intuitivity. |
| **Keymap discoverability** | Document conflicts; optional **prefs toggles** for shipped shortcuts (pattern used by add-ons that ship defaults). |
| **Manifest / platform extras** | When targeting **extensions.blender.org**, review platform schema for **permissions**, **online access**, **documentation URL** fields beyond minimal `blender_manifest.toml` ([moderation guidelines](https://wiki.blender.org/features/extensions/moderation/guidelines/)). |

### Accessibility & HIG (official direction)

- Blender **Human Interface Guidelines** — [accessibility](https://developer.blender.org/docs/features/interface/human_interface_guidelines/accessibility/), [best practices](https://developer.blender.org/docs/features/interface/human_interface_guidelines/best_practices/) (clear labels, action-oriented copy, calm UI).
- Operators: keep **`bl_label` / `bl_description`** accurate; treat **F3 search** and **menu greyout** as primary discovery paths for keyboard-only users (already called out in **AGENTS.md**).

### Extension / API references (underused or future)

- **`FileHandler`** API reference: [bpy.types.FileHandler](https://docs.blender.org/api/main/bpy.types.FileHandler.html) — extend `bl_file_extensions`, `drop` → existing import ops.
- **Asset pipeline / `bpy.types.AssetHandle`** — larger feature; defer unless KotOR assets as Blender assets is a product goal.
- **Viewport gizmos / draw handlers** — only if “area edit” or walkmesh editing needs on-canvas affordances (high cost).

### Peer extension pattern (for comparison)

- **[Drag and Drop Support](https://extensions.blender.org/add-ons/drag-and-drop-support/)** — many formats, migrated to native **FileHandler** (see also [mika-f/blender-drag-and-drop](https://github.com/mika-f/blender-drag-and-drop) issue #90 on replacing workarounds). Takeaway: **one obvious drop surface** + **conflict awareness** when multiple handlers exist.

### Brainstorm capture

- [docs/brainstorms/2026-03-20-intuitive-accessible-extensions-brainstorm.md](../../docs/brainstorms/2026-03-20-intuitive-accessible-extensions-brainstorm.md)

### Research insight (pass 9)

Biggest **low-regret** UX wins are **more FileHandlers** aligned with already-supported formats, **prefs “health” panel** for paths/PyKotor, and **export poll messages**—not new subsystems (assets, gizmos) unless scope explicitly expands.

---

## Enhancement summary (deepened 2026-03-20 — pass 10)

**Same prompt** (intuitivity / extension API / peer extensions) — **second pass** to avoid underselling what the add-on already implements.

### Corrections vs pass 9

- **Top bar:** KotorBlender already appends **File → Import** and **File → Export** (`TOPBAR_MT_file_import` / `TOPBAR_MT_file_export`) plus **`TOPBAR_MT_editor_menus`** for the KotOR menu ([`io_scene_kotor/__init__.py`](../../io_scene_kotor/__init__.py) ~505–516). Pass 9 implied “deep menus only”; **standard Blender discovery paths are already wired**.
- **UIList:** Used for **path points, modules, lens flares, resources** under `ui/list/` — not an unused API.

### Additional gaps (API / UX)

| Idea | Notes |
|------|--------|
| **Progress / status for long I/O** | No `wm.progress_begin` / `progress_update` / `progress_end` (or equivalent) in `io_scene_kotor` today; large MDL/module ops could surface **header progress** per [WindowManager](https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.progress_begin) (main-thread only; avoid naive worker-thread UI updates — see [Blender StackExchange discussion](https://blender.stackexchange.com/questions/7712/how-to-display-progress-notifications-from-an-operator)). |
| **File → Import submenu density** | Many KotOR entries next to built-in importers; optional **submenu** (`layout.menu`) could reduce scan cost (a11y + novice UX). |
| **Walkmesh / texture in top bar** | If **FileHandler** adds `.wok` / `.tpc`, consider matching **top-bar import** entries for parity with MDL/LYT/PTH. |

### Another peer pattern (non–drag-drop)

- Extensions that do **network or heavy batch work** often pair **clear prefs status** + **bounded progress**; KotOR is mostly **local disk** — progress matters most for **big MDL/module** paths, not every operator.

### Institutional memory (UI / tests)

- [open-addon-preferences-background.md](../../docs/solutions/integration-issues/open-addon-preferences-background.md) — prefs operators in **background** tests.

### Brainstorm (updated)

- [2026-03-20-intuitive-accessible-extensions-brainstorm.md](../../docs/brainstorms/2026-03-20-intuitive-accessible-extensions-brainstorm.md) — includes **Round 2**.

### Research insight (pass 10)

After pass 10, the **highest-ROI “missing” Blender UX API** is **progress feedback** for slow operators, plus **FileHandler/top-bar parity** for remaining formats—not re-adding top-bar import/export from scratch.
