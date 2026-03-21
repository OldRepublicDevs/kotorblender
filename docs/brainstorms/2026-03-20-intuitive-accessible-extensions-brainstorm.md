# Intuitivity, accessibility & extension API — brainstorm (2026-03-20)

**Feature angle:** What else could make KotorBlender **more intuitive and accessible**? What **Blender extension / Python API** capabilities are we **not** fully using? What do **other extensions** do that we could learn from?

**Related:** [.cursor/plans/kotorblender_improvements_brainstorm_c53764b7.plan.md](../../.cursor/plans/kotorblender_improvements_brainstorm_c53764b7.plan.md) — *Enhancement summaries pass 9–10*.

---

## What we’re exploring (WHAT, not HOW)

1. **Smoother discovery** — First-time modders find import/export and game-folder workflows without reading AGENTS.md first.
2. **Accessibility alignment** — Labels, descriptions, and keyboard/menu paths stay consistent with Blender HIG expectations.
3. **Extension parity** — Use manifest, FileHandler, and prefs patterns closer to polished extensions on [extensions.blender.org](https://extensions.blender.org/).

---

## What we already do well

- **FileHandler** drag-and-drop for **MDL / ASCII MDL / LYT / PTH**.
- **Top bar:** **File → Import / Export** entries for KotOR formats (plus module/save import) and **Editor** top-bar menu — same discovery path as built-in Blender I/O.
- **UIList** for path points, modules, lens flares, resources.
- **Optional keymaps** (Open Module, walkmesh visibility) when not in background mode.
- **Sidebar panels** + **Quick access** + **Editor → KotOR** tree.
- **P0 UX wave:** `bl_description` and `poll_message_set()` on gated operators.
- **Manifest:** tagline, wheels for PyKotor.

---

## Approaches (pick one theme per PR)

### A — **Expand drag-and-drop (recommended first)**

Add **FileHandler** entries for other formats the add-on already imports (e.g. **walkmeshes**, textures where applicable) so behavior matches the “drop files on the viewport” expectation set by extensions like [Drag and Drop Support](https://extensions.blender.org/add-ons/drag-and-drop-support/).

- **Pros:** High intuitivity, reuses existing operators, matches peer extensions.
- **Cons:** Must validate **handler ordering / conflicts** if users install multiple drop add-ons.

### B — **Preferences “health” + onboarding**

Short status in **addon prefs**: game path resolved?, PyKotor available?, link to docs; optional note about **keymaps** and conflicts.

- **Pros:** Low code, big clarity for support burden.
- **Cons:** Does not replace broken workflows—only surfaces state.

### C — **Export ergonomics**

Add **`poll()` + `poll_message_set()`** where export can fail (no selection, wrong object type) so greyed menu items explain **why**.

- **Pros:** Directly improves accessibility and “why can’t I click this?”
- **Cons:** Touches many operators; needs consistent copy.

### D — **Progress for slow I/O (orthogonal)**

Use **`wm.progress_begin` / `progress_update` / `progress_end`** (or modal/timer-safe updates) on **one or two** worst-case operators so users see work during long imports or batch steps.

- **Pros:** Matches expectations set by Blender’s own heavy operators; reduces “is it frozen?” support.
- **Cons:** Easy to get wrong with threads; scope to **main-thread** updates first.

---

## Key decisions (proposed)

- **Lead with A or B** before large new UI (wizards, gizmos, asset libraries).
- **Defer** Asset Browser / heavy viewport tooling unless product scope explicitly includes it.
- **Follow** Blender [accessibility](https://developer.blender.org/docs/features/interface/human_interface_guidelines/accessibility/) and [best practices](https://developer.blender.org/docs/features/interface/human_interface_guidelines/best_practices/) for wording and layout.

---

## Peer extension takeaway

**Drag and Drop Support** and the **native `FileHandler`** migration ([API](https://docs.blender.org/api/main/bpy.types.FileHandler.html)) show the pattern: **one clear drop path per format**, document **conflicts** with other handlers, and prefer **official API** over fragile workarounds.

---

## Open questions

1. Which **extra formats** get FileHandlers first (**WOK/BWM** vs **TPC/TGA** vs both)?
2. Should **keymaps** be **off by default** or stay on with stronger **prefs** documentation?
3. Is **extensions.blender.org** distribution a goal (affects manifest **permissions / doc URL** fields)?
4. Which **long-running** operators deserve **`wm.progress_*`** first (MDL import, module unpack, batch extract)?

---

## Round 2 (pass 10) — refined gaps

- **Do not duplicate** standard **File → Import/Export** work — it exists; next step is **parity** (new formats) or **submenu grouping** if the flat list feels crowded.
- **Progress API:** KotorBlender does not use [`WindowManager.progress_begin`](https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.progress_begin) today; worth considering for **slow** paths only, with **main-thread** updates (modal/timer pattern if needed).
- **Peer extensions:** [Drag and Drop Support](https://extensions.blender.org/add-ons/drag-and-drop-support/) remains the clearest analog for **FileHandler breadth**; heavy **online/asset** extensions (e.g. asset-store style) are a **different** product shape — borrow **status + feedback** ideas, not architecture wholesale.

---

## Addendum (2026-03-20) — honest “success” before UX polish

**Poll**, **progress**, and **FileHandler** work should assume **correct operator semantics**: treat **`{"FINISHED"}`** as “durable effect occurred” (file written, data loaded, etc.). Stub and **false-success** operators (see [integration audit plan](../plans/2026-02-19-feat-integration-gaps-stubs-audit-plan.md) sections **A**, **A.2**, **G**) should be fixed or clearly gated **before** investing in progress UI that would imply a completed workflow.

---

## Next step

Choose **A, B, or C** (or a thin slice of each), optionally add **progress** for one slow operator as **D**, then run **`/workflows:plan`** for implementation detail.
