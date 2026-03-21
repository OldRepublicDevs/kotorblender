# KotorBlender — Post-completion backlog brainstorm (2026-03-20)

**Context:** The [2026-03-19 improvements brainstorm](2026-03-19-kotorblender-improvements-brainstorm.md) tracked P0/P1 work (CONTRIBUTING, PR template, operator UX, docs links, architecture in AGENTS.md). That wave is **done**. This note captures **what to explore next** (WHAT, not HOW).

**Linked plan:** [.cursor/plans/kotorblender_improvements_brainstorm_c53764b7.plan.md](../../.cursor/plans/kotorblender_improvements_brainstorm_c53764b7.plan.md) — enhancement summaries passes 1–8.

---

## What we might build next (themes)

1. **Operator smoke coverage** — PyKotor-gated and asset-free paths for module tools, `file_search`, `kotor_diff`, `validate_module`, `refresh_modules`, save-game editor, extended bake/minimap operators; keep patterns from existing `test_ops_*_smoke.py` files.
2. **Registration / inventory accuracy** — `test_registration.py` vs full `kb.*` surface (optional: generated list or relaxed “minimum set” doc).
3. **Contributor ergonomics** — `.github/ISSUE_TEMPLATE/` (Blender version, OS, repro); short “Troubleshooting” in CONTRIBUTING or TESTING pointing at [docs/solutions/](../solutions/).
4. **pytest without Blender** — More `test/unit` coverage for pure helpers (`game_install_detect`, `log_config`, …) to widen CI signal cheaply.
5. **Markdown hygiene in plans** — After automated edits, preview plan files; optional markdownlint in CI ([guidance](../solutions/debugging-patterns/markdown-nested-emphasis-corruption-in-plans.md)).

---

## Why these themes (not big new features)

- **YAGNI:** Modders need stable MDL/LYT/PTH/WOK round-trips and predictable game-folder workflows more than new UI surface.
- **Risk reduction:** Operator smokes catch `RuntimeError` from `report({'ERROR'})`, bad prefs, and PyKotor absence—classes of bugs users hit in the field.
- **Compounding docs:** Each `docs/solutions/*.md` entry shortens the next debugging session.

---

## Key decisions (proposed)

- **Prioritize** operator smokes that mirror **real menu paths** (same as [AGENTS.md](../../AGENTS.md) user preference).
- **Defer** golden-file expansion in CI until there is a policy for proprietary assets vs synthetic fixtures.
- **Treat** `docs/solutions` as append-only institutional memory; link from CONTRIBUTING when adding a new category of failure.

---

## Open questions (need your input later)

1. **CI budget:** Add markdownlint / link-check job, or keep CI minimal (lint + Blender tests only)?
2. **PyKotor in CI:** Keep optional wheels vs always-on for module-operator tests?
3. **Issue templates:** Bug-only vs bug + feature request + blank?

---

## Addendum (2026-03-20) — integration audit linkage

Canonical **stub / gap inventory** (including **false-success `new_*` operators**): [docs/plans/2026-02-19-feat-integration-gaps-stubs-audit-plan.md](../plans/2026-02-19-feat-integration-gaps-stubs-audit-plan.md) sections **A.2**, **I**, **K** (mechanical wiring: `classes` vs menus vs FileHandler, manifest). For theme (1) operator smokes, add **on-disk asserts** for any `kb.new_*` / export that claims file creation; consider **FileHandler == menu op** coverage when touching drops.

---

## Next step

When scope is clear, run **`/workflows:plan`** (or a focused plan) on a **single** theme above—e.g. “operator smoke pack for module + file_search” — rather than mixing all five in one PR.
