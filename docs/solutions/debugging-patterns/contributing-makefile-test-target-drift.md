---
title: "CONTRIBUTING.md test targets drifting from Makefile / AGENTS.md"
category: debugging-patterns
tags: [documentation, Makefile, tests, CONTRIBUTING, CI, drift]
module: docs
symptom: "Contributors follow CONTRIBUTING.md but miss standard targets that exist in Makefile and AGENTS.md"
root_cause: "Multiple hand-maintained lists of make targets; only some files updated when new test-* targets are added"
---

## Problem

`CONTRIBUTING.md` listed a short subset of **`make test-*`** targets while **`Makefile`** and **`AGENTS.md`** accumulated more (`test-mdl-import-op`, `test-material`, `test-analyst-coverage`, PyKotor targets, `test-unit`, etc.). New contributors could assume the short list was complete and skip useful local workflows that CI or maintainers rely on.

## Working solution

- Expand **Individual test modules** in `CONTRIBUTING.md` to include the same high-value targets as `Makefile` phony targets / `AGENTS.md` pointers.
- In the **Test layout** bullet, explicitly reference **`make test-analyst-coverage`** as the bundled operator/format smoke set and link readers to **AGENTS.md** for the full matrix and CI behavior.

## Prevention (best practice)

- Treat **`Makefile`** (and the workflow that invokes it) as the **source of truth** for runnable commands.
- Keep **`CONTRIBUTING.md`** to a **curated** list of targets contributors use often; when adding a `make test-*` target, update **CONTRIBUTING** in the same PR or add a short maintainer note in **AGENTS.md** / PR template.
- Prefer **linking** to **AGENTS.md** for exhaustive detail over duplicating every future target; optionally add **`make help`** later so prose stays short ([self-documenting Makefile pattern](https://victoria.dev/blog/how-to-create-a-self-documenting-makefile/)).
- Align with GitHub’s guidance: contributing docs should stay concise and point at canonical process docs ([Setting guidelines for repository contributors](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors)).

## Related

- [ascii-mdl-smoke-trimesh-kb-on-mesh-object.md](../test-failures/ascii-mdl-smoke-trimesh-kb-on-mesh-object.md) — MDL test pitfalls
- [AGENTS.md](../../../AGENTS.md), [CONTRIBUTING.md](../../../CONTRIBUTING.md), [Makefile](../../../Makefile)
