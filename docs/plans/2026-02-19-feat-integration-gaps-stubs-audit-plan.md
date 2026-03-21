---
title: "Integration surface audit — gaps, stubs, and Blender extension parity"
type: feat
status: active
date: 2026-02-19
---

# Integration surface audit — gaps, stubs, and Blender extension parity

## Overview

This plan consolidates **what KotorBlender already wires into Blender** (menus, operators, FileHandlers, prefs, panels) versus **placeholders, simplified paths, and missing behavior**, so follow-up work can prioritize **full integration “everywhere”** without duplicating effort across brainstorms.

**Inputs:**

- Repo scan: `TODO` / `FIXME` / `not yet implemented` / `pass` hotspots / `NotImplementedError`
- [AGENTS.md](../../AGENTS.md) Gotchas (**Operator stubs**)
- Brainstorms: [2026-03-20 intuitive & accessible extensions](../../docs/brainstorms/2026-03-20-intuitive-accessible-extensions-brainstorm.md), [2026-03-20 post-completion backlog](../../docs/brainstorms/2026-03-20-kotorblender-post-completion-backlog.md), [2026-03-19 improvements](../../docs/brainstorms/2026-03-19-kotorblender-improvements-brainstorm.md)
- Learnings: [pykotor-stub-operators-finished-without-work](../../docs/solutions/logic-errors/pykotor-stub-operators-finished-without-work.md)

**Non-goals here:** Implementing fixes (use focused PRs per theme); editing `.cursor/plans/*` copies.

**Canonical doc:** This file under `docs/plans/` is authoritative for the integration audit. Older copies under `.cursor/plans/` may contradict it—ignore them for inventory truth. **Section K** covers **mechanical** integration (registration, menus, FileHandler strings, manifest) in addition to **stub honesty** (A–I, J).

---

## Problem statement / motivation

Users discover features through **File**, **Editor**, **sidebar**, **F3**, and **drag-and-drop**. When an operator **returns FINISHED** but only logs a stub message, or when a format is supported in code but **not** in FileHandler/menus, integration feels incomplete. Contributors need a **single inventory** to align tests, docs, and UI copy.

---

## Current integration map (high level)

| Surface | KotorBlender usage | Gaps |
|--------|---------------------|------|
| **File → Import / Export** | MDL, ASCII MDL, LYT, PTH, walkmesh (BWM), module, save | Some entries open flows that immediately defer to “sidebar” or “future UI” |
| **FileHandler (drop)** | `.mdl`, `.mdl.ascii`, `.lyt`, `.pth`, `.wok`, `.pwk`, `.dwk` | TPC/TGA not dropped (by design today); conflict with other drop add-ons undocumented in UI |
| **Editor → KotOR** | Large tree: game, module, resources, tools, editors, quick access | Stub tools/editors mixed with full implementations |
| **Sidebar panels** | Model, animations, game install, module browser, designer, save, resources | WIP labels (e.g. area edit flag) |
| **Preferences** | Textures, lightmaps, diff tool, logging, runtime status | Optional: progress/keymap/docs links expansion per brainstorm |
| **Keymaps** | Open module, show/hide walkmeshes | Optional defaults / prefs documentation |
| **Agent-native parity** | Menus + `bl_description` + F3 | Any action only in undocumented shortcuts should gain menu or doc link |

---

## Taxonomy (single classification)

Use **one bucket per operator** so sections A/B do not duplicate mentally:

| Class | Meaning | Typical fix |
|-------|---------|-------------|
| **I/O stub** | Advertises file work; does nothing durable | Implement via `io/` + `format/`, or `poll` + `poll_message_set`, or honest `CANCELLED` |
| **UI-deferred** | File picked or loaded; no panel/tree | Epic per type; align `bl_description` with reality |
| **PyKotor-gated** | Needs wheels; must `CANCELLED` + ERROR when absent | Already OK in many editors; extend to all module flows |
| **Format limitation** | `NotImplementedError` / `NotImplemented` in library | Document + translate in `ops/` to user `report`, not menu lies |
| **Intentional no-op** | Placeholder for future gizmo/flag | WIP copy in UI; optional `poll` false |

**Section A.1** = **I/O stubs** (explicit “not yet implemented”). **Section A.2** = **false-success creators** (claim file written, no I/O). **Section B** = **UI-deferred** and related. **Section C** = **format limitation** (do not “fix” in menus by pretending support).

---

## A. Explicit “not yet implemented” operators (INFO stub, often FINISHED)

These **register and run** but **do not perform** the advertised I/O (verify before changing tests — see learning doc above). **Class:** I/O stub.

| Operator area | `bl_idname` | File | User-visible behavior |
|---------------|-------------|------|------------------------|
| New UTC | `kb.new_utc` | `ops/resource/new_utc.py` | INFO: not yet implemented |
| MDL texture extract | `kb.extract_mdl_textures` | `ops/module/extract_mdl_textures.py` | INFO: not yet implemented |
| Module TPC extract | `kb.extract_tpc` | `ops/module/extract_tpc.py` | INFO: not yet implemented |
| TGA → TPC | `kb.convert_tga_to_tpc` | `ops/texture/convert_tga_to_tpc.py` | INFO: not yet implemented |
| Batch texture convert | `kb.batch_convert_textures` | `ops/texture/batch_convert_textures.py` | INFO: not yet implemented |
| Save extract | `kb.extract_save` | `ops/save/extract.py` | INFO: not yet implemented |

**Recommendation:** For each stub, either (1) implement minimal real path through **`io/`**, (2) `poll()` false + **`poll_message_set`**, or (3) return **`{"CANCELLED"}`** (and optionally WARNING) instead of FINISHED when no work runs—then document in **CONTRIBUTING** and extend [pykotor-stub-operators-finished-without-work](../../docs/solutions/logic-errors/pykotor-stub-operators-finished-without-work.md).

**Return-value policy (decide once, apply everywhere):**

- **Default for no-work paths:** `{"CANCELLED"}` so scripts/agents that only inspect the return set do not treat a stub as success.
- **When to keep FINISHED:** Only if a durable, observable effect occurred (file written, object created, data loaded into Blender state).
- **Severity:** Prefer **WARNING** over **INFO** for “invoked but did nothing” if the operator remains callable from menus (helps headless logs and tests).
- **Test impact:** Changing FINISHED → CANCELLED or adding `poll` false breaks any smoke test that asserts `FINISHED`; update `test_registration.py` / smokes in the same PR as the behavior change.

### A.2 New resource operators — false “Created” (FINISHED, no disk write)

**2026-03-20 audit:** Several `ops/resource/new_*.py` operators report **`INFO` “Created new … file”** and return **`{"FINISHED"}`** but **never call `open()` / `GffWriter` / PyKotor save** — higher severity than section A text stubs because users and **scripts assume `FINISHED` ⇒ file exists** (silent “data loss” perception).

| Status | `bl_idname` | File | Actual behavior |
|--------|-------------|------|-----------------|
| **False success** | `kb.new_utp` | `new_utp.py` | INFO only |
| **False success** | `kb.new_uti` | `new_uti.py` | INFO only |
| **False success** | `kb.new_utd` | `new_utd.py` | INFO only |
| **False success** | `kb.new_utm` | `new_utm.py` | INFO only |
| **False success** | `kb.new_utt` | `new_utt.py` | INFO only |
| **False success** | `kb.new_uts` | `new_uts.py` | INFO only |
| **False success** | `kb.new_utw` | `new_utw.py` | INFO only |
| **False success** | `kb.new_ute` | `new_ute.py` | INFO only |
| **False success** | `kb.new_erf` | `new_erf.py` | INFO only |
| **False success** | `kb.new_dlg` | `new_dlg.py` | INFO only |
| **False success** | `kb.new_tlk` | `new_tlk.py` | INFO only |
| **Explicit stub** | `kb.new_utc` | `new_utc.py` | Says “not yet implemented” but still returns **FINISHED** (contradictory) |
| **Writes disk** | `kb.new_gff` | `new_gff.py` | Uses `GffWriter` / PyKotor — model for GFF family |
| **Writes disk** | `kb.new_nss` | `new_nss.py` | Plain text; no PyKotor |

**Recommendation:** (1) Short term: **CANCELLED + WARNING** and honest copy until write exists; align **`new_utc`** return set with its message. (2) Medium term: one **`io/` helper** for “minimal empty GFF” parameterized by **fourcc** (reuse `new_gff` logic); separate paths later for **TLK** / **ERF** when formats are defined. (3) Tests: temp dir + `os.path.isfile` + size &gt; 0 for operators that claim creation (pattern: [`test/blender/test_ops_new_gff_smoke.py`](../../test/blender/test_ops_new_gff_smoke.py)).

**Learning doc:** Extend or companion to [pykotor-stub-operators-finished-without-work](../../docs/solutions/logic-errors/pykotor-stub-operators-finished-without-work.md) for this **false-success** class.

### A.3 Module “open resource” — TPC branch

`ops/module/open_resource.py`: for extension **`tpc`**, reports INFO directing user to texture conversion and returns **`{"FINISHED"}`** without opening the resource — document as **guidance-only** path (not a crash; easy to mistake for “opened”). Consider **`{"CANCELLED"}`** + clearer copy if policy in A applies to “no durable effect.”

---

## B. “Future release” / minimal UI operators

### B.1 Explicit “future release” copy

| Item | `bl_idname` | File | Notes |
|------|-------------|------|--------|
| Save game editor | `kb.open_save_editor` | `ops/save/open_editor.py` | INFO: editor UI coming |
| TLK | `kb.edit_tlk` | `ops/editor/edit_tlk.py` | States future UI in message |
| UTC (edit) | `kb.edit_utc` | `ops/editor/edit_utc.py` | Same |
| JRL | `kb.edit_jrl` | `ops/editor/edit_jrl.py` | Same |
| TSLPatchData | `kb.tslpatchdata_editor` | `ops/tools/tslpatchdata_editor.py` | Picks `.ini`, no structured UI |
| Indoor Map Builder | `kb.indoor_map_builder` | `ops/tools/indoor_map_builder.py` | INFO + tooltip; PyKotor ERROR path returns CANCELLED |

### B.2 GFF generic editor (loads data, no tree UI)

| Item | `bl_idname` | File | Notes |
|------|-------------|------|--------|
| Edit GFF | `kb.edit_gff` | `ops/editor/edit_gff.py` | Loads tree via PyKotor or `GffReader`; **no** property panel; comment: tree view planned |

### B.3 “Edit …” operators — **misleading labels** (INFO only, no editor UI)

`bl_description` claims editing; **execute** only reports path after PyKotor check. **Class:** UI-deferred / honesty gap.

| `bl_idname` | File |
|-------------|------|
| `kb.edit_utp` | `ops/editor/edit_utp.py` |
| `kb.edit_utd` | `ops/editor/edit_utd.py` |
| `kb.edit_uti` | `ops/editor/edit_uti.py` |
| `kb.edit_utm` | `ops/editor/edit_utm.py` |
| `kb.edit_utt` | `ops/editor/edit_utt.py` |
| `kb.edit_uts` | `ops/editor/edit_uts.py` |
| `kb.edit_utw` | `ops/editor/edit_utw.py` |
| `kb.edit_ute` | `ops/editor/edit_ute.py` |
| `kb.edit_dlg` | `ops/editor/edit_dlg.py` |
| `kb.edit_erf` | `ops/editor/edit_erf.py` |

### B.4 Partial / different pattern

| Item | File | Notes |
|------|------|--------|
| Edit NSS | `ops/editor/edit_nss.py` | Opens file in **Text Editor** — closer to a real workflow; verify completeness vs. HolocronToolset |

**Recommendation:** Track **B.3** as one epic with **shared pattern** (e.g. open externally, or first vertical slice in P4). First milestone = **`bl_description` first sentence states placeholder** + optional “Open in Text Editor” parity with NSS, or **`poll` + message** until a panel exists.

---

## C. Format / library gaps (not menu stubs)

Tag each by **impact** so QA and tests are not lumped into one bucket:

| Location | Issue | Impact |
|----------|-------|--------|
| `format/gff/reader.py` / `writer.py` | `NotImplementedError` on unsupported GFF field types | **Crash / load failure** on exotic templates; `ops/` should catch and `report` + CANCELLED where user-facing |
| `scene/modelnode/trimesh.py` | `NotImplemented` on ordering protocol | **Niche**; unlikely normal UI path |
| `ascii_reader.py` / `ascii_writer.py` | Empty `pass` in enum/skip paths | **Silent skip** vs intentional — audit per branch |
| `vendor/pykotor_adapter.py` | Multiple `pass` in adapter | **Optional path** / dead branches — cleanup PR only |

**Architecture note:** Do not “fix” **format/** limitations by changing **menu** copy to imply support; keep **two inventories** (library vs operator honesty).

---

## D. UI / copy placeholders

| Location | Text |
|----------|------|
| `ui/panel/game_installation.py` | “Area edit flag (WIP)” |

Tie resolution to **Indoor Map Builder** epic or remove until behavior exists.

---

## E. Integration ideas (Blender extension & UX API)

Aligned with [2026-03-20 intuitive & accessible extensions brainstorm](../../docs/brainstorms/2026-03-20-intuitive-accessible-extensions-brainstorm.md):

1. **Export `poll` + `poll_message_set`** — Grey out export/actions when selection/context wrong; reduces “nothing happens” reports.
2. **`wm.progress_begin` / `progress_update` / `progress_end`** — Scope to **main thread**, start with MDL import or module unpack (document threading constraints).
3. **Asset Library / Browser** — Defer unless product scope explicitly includes it (YAGNI).
4. **Manifest / extensions.blender.org** — Permissions, `doc_url`, changelog parity if publishing officially.
5. **FileHandler ordering** — Document conflicts with other drop add-ons in README or prefs.
6. **TPC drag-and-drop** — Only if a **single** import operator owns texture-in (avoid duplicate handlers).

**Peer pattern:** One FileHandler per format, official [FileHandler API](https://docs.blender.org/api/current/bpy.types.FileHandler.html), consistent with walkmesh/MDL drop.

---

## F. Test & documentation integration

From [post-completion backlog brainstorm](../../docs/brainstorms/2026-03-20-kotorblender-post-completion-backlog.md):

- Extend **operator smokes** for PyKotor-gated and stub operators (branch on `is_pykotor_available()` per learning doc). When a stub’s return value changes (FINISHED → CANCELLED) or `poll` goes false, **update the same PR** that changes behavior (registration tests, smokes that assert return sets).
- Optional **generated** `kb.*` list vs `test_registration.py` curated list — defer until stub drift pain is recurring; until then, **this plan + periodic grep** is the source of truth.
- **GitHub issue templates** (Blender version, OS, repro).
- **CONTRIBUTING:** add a prominent **“Known limitations & stubs”** link → this plan and [docs/solutions/](../../docs/solutions/).
- More **pytest** coverage for pure helpers (`game_install_detect`, `log_config`, etc.).
- **CI (optional hardening):** consider a job that runs tests with **wheels empty / minimal manifest** so optional-PyKotor degradation stays honest (aligns with “degrade clearly” in Dependencies & risks).

---

## G. Agent-native / accessibility checklist (for future PRs)

- Every **user-visible** action: reachable from **menu** or documented **F3** string; `bl_description` complete.
- **Stub registry (single table):** columns `bl_idname`, class (taxonomy), implemented?, `poll` behavior, deps (PyKotor/prefs), safe for automation? — humans and agents share this list.
- **`bl_description` contract:** first sentence states **Placeholder** / **Requires PyKotor** / **Loads file only** where applicable (F3 hover, screen readers, agent tooltips).
- **`bl_label`:** avoid sounding like a finished product for stubs; stable `bl_idname` for scripts; naming convention in CONTRIBUTING.
- Stubs: apply **Return-value policy** (section A); agents that only check return sets must not see `FINISHED` on no-ops.
- **F3 keywords:** align labels/descriptions with user search terms (walkmesh vs BWM, ASCII MDL, module, KotOR).
- Screen reader: meaningful **labels** on panels/lists; avoid icon-only critical actions.
- **Changelog / AGENTS.md** supported-formats table must match **actual** operator behavior, not aspirational menus.

---

## H. Repo scan: `TODO` / `FIXME` / `HACK`

**2026-03-21:** `rg 'TODO|FIXME|HACK' io_scene_kotor --glob '*.py'` returned **no matches**. Ongoing gaps are tracked via **user-visible strings** (`not yet implemented`, `future release`) and **taxonomy** above, not comment markers.

**Related copy:** `ui/menu/kotor.py` describes creating **“resource stubs on disk”** — today **A.2** operators often create **nothing**; update menu copy when behavior is fixed or honest-stubbed.

---

## I. `pass` / empty-body hotspots (code audit, not necessarily bugs)

**2026-03-20** `rg '^\s+pass\s*$' io_scene_kotor --glob '*.py'` (deduped by logical path):

| Area | File(s) | Note |
|------|---------|------|
| MDL I/O | `io/mdl.py` | After `UnicodeDecodeError` / unreadable peek — intentional “not ASCII MDL” |
| Binary framing | `format/binreader.py`, `format/binwriter.py` | Likely skip/align no-ops — verify in context |
| ASCII MDL | `format/mdl/ascii_reader.py`, `ascii_writer.py` | Multiple `pass` — audit skip branches vs missing work |
| Scene | `scene/modelnode/trimesh.py` | One `pass` in protocol/helper — cross-check with `NotImplemented` ordering |
| Ops | `ops/tools/kotor_diff.py` | `pass` in branch — verify |
| Ops | `ops/module/open_resource.py` | `pass` on `OSError` unlink cleanup — idiomatic |
| Adapter | `vendor/pykotor_adapter.py` | Cluster of `pass` — optional stubs / fallbacks; partition in cleanup PR |
| Types | `game_install_detect.py` | Empty body or protocol — verify |

Use this table for **follow-up PRs** only; do not conflate with menu stubs without reading each site.

---

## Proposed implementation phases (pick one theme per PR)

**P1 priority order (recommended):** (0) **A.2 false-success `new_*`** and **`new_utc` return/message** (highest trust impact), (1) CONTRIBUTING **Known limitations** link + stub table, (2) **return value + severity** honesty for **A.1** operators, (3) `poll` / `poll_message_set` where menus should grey out, (4) implement **`io/` shared minimal GFF create** or other real I/O only after (0)–(2).

| Phase | Theme | Deliverable |
|-------|--------|-------------|
| **P1** | Stub honesty | CONTRIBUTING stub table + link here; **A.2 + A.1** return/copy fixes; then optional `poll_message_set` or **`io/` minimal GFF create** for GFF-family `new_*` |
| **P2** | Export discoverability | `poll`/`poll_message_set` pass on MDL/LYT/PTH/BWM exports |
| **P3** | Long I/O feedback | Progress API on one heavy operator + docs |
| **P4** | Editor epics | **One vertical slice:** e.g. `kb.edit_utp` (or GFF panel) with **minimal acceptance test** — load → show/edit one field → write roundtrip or explicit “open in Text Editor” smoke |
| **P5** | CI/docs | Issue templates + solutions index links; optional no-wheel CI job |

**Invariant (architecture):** every format entry point (menu, FileHandler, batch) delegates to **one `io.load_*` / `io.save_*` family** per format — no parallel parsing in `ops/`.

---

## Acceptance criteria (for this audit plan as a living doc)

- [ ] Stakeholders agree **P1–P5** ordering or reprioritize (owner + target milestone optional but closes “active forever” risk).
- [ ] Each item in **section A.1** and **A.2** has a GitHub issue, label (e.g. `stub-operator`), or “won’t fix / intentional” note.
- [ ] **A.3** (`open_resource` TPC) decided: keep guidance FINISHED vs CANCELLED + copy.
- [ ] **Section K.1** wiring risks reviewed after major UI/registration changes (or automated when feasible).
- [ ] **Section B.3** editors either have honest `bl_description` + return semantics or a single epic issue.
- [ ] Brainstorm **open questions** (FileHandler priority, keymaps defaults, extensions.blender.org) answered or tracked in GitHub issues.
- [ ] After major releases, re-run grep for `not yet implemented` / `future release` and update this file (inventory is **not** closed by section A alone).

---

## Success metrics

- Fewer “I clicked X and nothing happened” reports (measurable via issue template tags).
- Test suite explicitly encodes **stub vs real** behavior for PyKotor-gated ops and **on-disk proof** for any operator that claims file creation (`new_*`, exports).
- CONTRIBUTING lists **known limitations** linking here or to `docs/solutions/`.

---

## Dependencies & risks

- **PyKotor optional:** Module/resource features must degrade clearly when wheels absent; keep checks in **`vendor/pykotor_adapter.py`** / `io/` rather than duplicating across every `ops/` stub.
- **Proprietary assets:** Golden tests remain policy-limited; prefer synthetic fixtures.
- **Blender version drift:** 4.2+ extension module name vs 3.6 legacy — tests already dual-path; keep in mind for new operators.
- **FileHandler / drop:** never the only path to a format — **File → Import** + **`io/`** remain canonical (ordering vs other add-ons is undefined).

---

## Research insights (deepen — 2026-03-21)

Synthesized from **code-reviewer**, **architecture-strategist**, and **agent-native-reviewer** passes on this plan (read-only).

### Plan quality

- **FINISHED vs CANCELLED** is now specified under section A (**Return-value policy**); implementers should not infer from scattered docs alone.
- **Taxonomy** (new) reduces duplication between old sections A and B.
- **Test/CI consequences** called out in section F and section A (same PR as behavior change).
- **P1 priority order** makes documentation + honesty precede optional new features.
- **P4** now includes a **minimal acceptance test** bound.
- **Canonical path** called out at top; **CONTRIBUTING** link pattern named in F.
- **Format vs operator** failure modes separated in section C (**Impact** column).

### Architecture

- Guard against **duplicate I/O** in `ops/` — always delegate to **`io/`** + **`format/`** via established paths.
- **Manifest / extensions.blender.org:** capabilities must match stub inventory.
- **Defer (YAGNI):** Asset Library, generated operator registries, broad keymap work, TPC drop until one owning import path exists.

### Agent-native / automation

- **Return set** is the automation signal: no `FINISHED` without durable effect; prefer **stub registry** table in G.
- **Severity** (WARNING) aids headless logs for no-op invocations.
- **Menu vs script parity:** document any intentional differences; avoid menu-only “success” paths.

### Second pass — 2026-03-20 (`new_*` false success + `pass` map)

- **False-success `new_*`:** Treat as **critical** for automation: `FINISHED` + “Created” without write is worse than explicit “not yet implemented.” **`new_utc`** must not pair “not implemented” with `FINISHED`.
- **CONTRIBUTING:** Forbid success wording + `FINISHED` without persistence; point contributors to **A.2** and `new_gff` / `new_nss` patterns.
- **Architecture:** Centralize **minimal GFF resource creation** in **`io/`** (path + fourcc + empty tree); **TLK/ERF** get their own single delegations when implemented — avoid N copies of PyKotor branching in `ops/resource/`.
- **`bl_description`:** Until write exists, state that **no file is written** or mark placeholder in the first sentence.
- **Section I:** `pass` sites are **technical debt candidates**, not automatic stubs — review per file.

### Third pass — 2026-03-20 (solutions index, normative vs as-built, registry)

- **Plan vs [pykotor-stub-operators-finished-without-work](../../docs/solutions/logic-errors/pykotor-stub-operators-finished-without-work.md):** Plan = **target** return policy; learning doc + smokes = **current** contract for listed operators until one PR changes all three.
- **CONTRIBUTING** should surface [docs/solutions/](../../docs/solutions/) with a small table (implemented).
- **Optional `test_expectation_*` columns** on the stub registry; version or date stamp when contract changes; drift check vs smokes.
- **A.2** may warrant a **new** solutions article when P1 step 0 ships.

### Fourth pass — 2026-03-20 (mechanical integration, DoD, agent checklist)

- **Registration / menu / string drift:** `classes` tuple vs menus vs `layout.operator("kb.*")` vs FileHandler `bl_idname` strings can diverge (orphan ops or broken drop). Optional future: grep/CI guard that every `bpy.ops.kb.` reference matches a registered `bl_idname`.
- **Duplicate menu entries:** Same operator surfaced twice in **Editor → KotOR** after refactors — separate audit from stub honesty.
- **AGENTS.md + manifest:** Beyond the formats table, refresh operator counts, Makefile targets, **`bl_info` / `blender_manifest.toml` version**, `wheels`, **permissions** vs real behavior when shipping or adding ops.
- **Wiring tests:** Strengthen “File menu op == FileHandler target” for each format; extend `test_ops_file_handlers` / IO smokes where gaps exist.
- **Definition of done (architecture):** Single **`io/`** path per format, PyKotor boundary in adapter/`io/`, honest UI copy, **`FINISHED` only with durable effect**, manifest parity, drop + File menu not forked.
- **External agents:** Never trust **`FINISHED`** alone for **A.1/A.2**; verify disk/scene; use **J** + solutions for *current* vs *target* contract; enable `bl_ext.user_default.io_scene_kotor`; handle **`RuntimeError`** on `report(ERROR)`.

---

## J. `docs/solutions` alignment & contract drift

**Problem:** This plan is **normative** (target: no durable work → prefer `CANCELLED` / WARNING). [pykotor-stub-operators-finished-without-work](../../docs/solutions/logic-errors/pykotor-stub-operators-finished-without-work.md) documents **as-built** behavior for **`kb.batch_convert_textures`** and **`kb.extract_save`**: with PyKotor present, smokes still expect **`FINISHED`** after INFO stub. Until code changes land, **tests + that learning doc are the live contract** for those two operators.

**Reconciliation rule:** When changing any stub’s return set, update **operator + smoke tests + learning doc(s)** in the **same PR**. Optionally add a one-line “Planned” note in the learning doc only during an in-flight branch—not on `main` alone without code.

**False-success `new_*` (A.2):** Distinct from PyKotor INFO stubs: claims **file created** with no write. Either extend the stub learning doc with an **A.2** subsection or add sibling [`docs/solutions/logic-errors/new-resource-operators-false-success.md`](../../docs/solutions/logic-errors/new-resource-operators-false-success.md) (recommended when implementing P1 step 0).

**CONTRIBUTING:** [CONTRIBUTING.md](../../CONTRIBUTING.md) includes a **Solutions library** table (Troubleshooting) linking this plan, stub-contract learnings, and operator `RuntimeError` behavior.

**Registry (future):** Add optional columns `test_expectation_pykotor_yes`, `test_expectation_pykotor_no`, `durable_side_effect` so agents, tests, and prose don’t diverge (see Research insights → Third pass).

**Grep when implementing policy:** `test/blender/test_ops_pykotor_stub_texture_save_smoke.py`, `test_registration.py`, `test_ops_*smoke*.py` for `FINISHED` / `CANCELLED` / `batch_convert` / `extract_save` / `new_`.

---

## K. Mechanical integration, “done,” and external automation

### K.1 Wiring & drift (orthogonal to stub tables)

| Risk | Mitigation |
|------|------------|
| Operator in **`ui/`** menu but missing from **`__init__.py` `classes`** (or reverse) | After adding ops: diff `classes` vs `grep layout.operator\("kb\.` in `ui/` |
| **`bpy.ops.kb.*` string typos** in panels, keymaps, FileHandler | Grep `kb\.\w+` in `io_scene_kotor`; compare to `bl_idname` definitions |
| **FileHandler** invokes different op than **File → Import** | Keep one target id per format; extend [`test/blender/test_ops_file_handlers.py`](../../test/blender/test_ops_file_handlers.py) when adding handlers |
| **Duplicate `layout.operator`** for same `bl_idname` | Occasional pass over `ui/menu/kotor.py` and panel files |
| **`bl_info` vs `blender_manifest.toml`** version, **wheels**, **permissions** | Release checklist; align with real capabilities (no extra scope vs stub inventory) |
| **AGENTS.md** structure (counts, targets, extension name) | Update when operator/panel/test surface changes materially |

### K.2 Definition of done — “full integration” (architecture)

1. One **`io/`** entry family per format from every entry point (menu, drop, batch).
2. PyKotor optional behavior centralized (**`vendor/pykotor_adapter.py`** / **`io/`**), not re-scattered in `ops/`.
3. UI only invokes ops/helpers — no parallel byte I/O; **`bl_description`** matches **Taxonomy** classes.
4. **Return contract:** no **`FINISHED`** without durable effect (**section A** policy).
5. **Manifest / publish** fields match behavior.
6. **FileHandler** is additive, not the only path; documented conflicts with other add-ons (**section E**).
7. CONTRIBUTING + solutions + smokes reflect stub vs real (**sections F, J**).

### K.3 External agent checklist (`bpy.ops.kb.*`)

1. Read **this plan A.1 / A.2 / J** before scripting; treat **J** for normative vs as-built.
2. After invoke: verify **disk** (`os.path.isfile`) or **scene** changes — not return set alone for resource/create/export ops.
3. **`bl_ext.user_default.io_scene_kotor`** enablement (Blender 4.2+).
4. PyKotor absence → expect **ERROR/CANCELLED** on gated workflows.
5. Prefs: absolute paths; Blender 5.x prefs may need **`str()`** coercion (see AGENTS.md).
6. **`report({"ERROR"}, …)`** → possible **`RuntimeError`** — see [operator-error-report-runtimeerror](../../docs/solutions/integration-issues/operator-error-report-runtimeerror.md).
7. F3 / discovery: use **`bl_idname`** when known; search “KotOR”, “walkmesh”, “module”, etc.
8. On add-on upgrade, re-run verification; return semantics may change in one PR (**J**).

---

## References & research

- [AGENTS.md](../../AGENTS.md) — structure, tests, extension module name
- [docs/solutions/logic-errors/pykotor-stub-operators-finished-without-work.md](../../docs/solutions/logic-errors/pykotor-stub-operators-finished-without-work.md) — **as-built** stub contract (batch convert, save extract) until P1
- [docs/solutions/integration-issues/operator-error-report-runtimeerror.md](../../docs/solutions/integration-issues/operator-error-report-runtimeerror.md) — `report(ERROR)` → `RuntimeError` in tests
- [docs/solutions/integration-issues/open-addon-preferences-background.md](../../docs/solutions/integration-issues/open-addon-preferences-background.md) — prefs in background mode
- [docs/solutions/test-failures/](../../docs/solutions/test-failures/) — operator init, ASCII MDL smoke
- [docs/solutions/debugging-patterns/](../../docs/solutions/debugging-patterns/) — Makefile test drift, plan markdown
- Brainstorms: [2026-03-20 intuitive & accessible](../../docs/brainstorms/2026-03-20-intuitive-accessible-extensions-brainstorm.md), [post-completion backlog](../../docs/brainstorms/2026-03-20-kotorblender-post-completion-backlog.md), [2026-03-19 improvements](../../docs/brainstorms/2026-03-19-kotorblender-improvements-brainstorm.md)
- Blender: [Human Interface Guidelines — Accessibility](https://developer.blender.org/docs/features/interface/human_interface_guidelines/accessibility/), [FileHandler](https://docs.blender.org/api/current/bpy.types.FileHandler.html), [`bpy_extras.io_utils`](https://docs.blender.org/api/current/bpy_extras.io_utils.html)

---

## Enhancement Summary (plan-level /deepen-plan hook)

**Latest update:** 2026-03-20 — **Section K** (mechanical integration, DoD, external agent checklist); **Research insights → Fourth pass**.

**Sections enhanced (cumulative):** Taxonomy; A (**A.1–A.3**); B.1–B.4; C; F; G; H; I; **J**; **K**; phases; acceptance; success metrics; **Research insights** (four dated subsections).

**Research agents used:** code-reviewer, architecture-strategist, agent-native-reviewer — prior passes + **mechanical wiring / DoD / automation checklist** pass.

**Key improvements to pursue next**

1. **P1 (step 0):** Fix **A.2** + **`new_utc`** return semantics and copy; add disk proof tests for real creators.
2. **P1:** CONTRIBUTING stub link + **A.1** CANCELLED/WARNING; optional shared **`io/`** minimal GFF create for GFF-family `new_*`.
3. **B.3 honesty pass**; **P2** export polls; **P3** progress template.

**New considerations**

- **No `TODO`/`FIXME`/`HACK`** in `io_scene_kotor` per grep — track gaps via strings, **A.2**, and section **I**.
- **Eleven `new_*` operators** claim creation without writing — document in registry as **non-persistent** until fixed.
- **Section K** captures registration/menu/FileHandler/manifest drift — separate from stub taxonomy.
- Walkmesh **standalone import** is implemented (`kb.bwmimport`, FileHandler); treat repo as source of truth.
- `Walkmesh.attach_to_collection` naming supersedes older `add_to_collection` wording in stray plans.
