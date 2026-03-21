---
title: "Broken bold/code nesting in Markdown plan files (e.g. .cursor/plans)"
category: debugging-patterns
tags: [markdown, documentation, automation, CommonMark, plans]
module: .cursor/plans
symptom: "Enhancement summaries show literal backticks and stars like `**word**` or mismatched `**` so GitHub/Cursor preview looks wrong"
root_cause: "Mixing inline code spans with emphasis by placing `**` inside backticks or doubling delimiters (tool output pasted without normalization)"
---

## Problem

Long brainstorm or plan Markdown (for example `.cursor/plans/*.md`) can accumulate lines such as:

- `` `**mdlexport` with SKIN…** `` — emphasis split across a code span
- `` `**todos/*.md**` `` — bold intended but wrapped in monospace, so it renders as code, not emphasis
- `` `**{"FINISHED"}`** `` — nested `` ` `` and `**` in the wrong order

Readers see noisy punctuation instead of clear **bold** or `inline code`.

## Working fix

- **Emphasis outside code:** use **`**word**`** for bold, or `` `identifier` `` for code — not both interleaved on the same token.
- **File names / paths:** prefer `` `path/to/file.py` `` without wrapping the whole phrase in extra `**`.
- **Scan enhancement blocks** after automated edits: search for patterns like `` `** `` or `` **\` `` and rewrite to valid [CommonMark](https://spec.commonmark.org/current/) (inline code cannot contain raw `*` as emphasis).

## Prevention

- Prefer **fenced code blocks** for multi-token examples; keep headings/lists separated by blank lines ([markdownlint](https://github.com/DavidAnson/markdownlint) rules MD022/MD031 help).
- Optional CI: **markdownlint-cli2** + **markdown-link-check** / **lychee** on `*.md` with sensible ignores.
- When appending “deepen plan” sections, paste through a quick preview (GitHub or IDE) before committing.

## Related

- [contributing-makefile-test-target-drift.md](./contributing-makefile-test-target-drift.md)
- [kotorblender_improvements_brainstorm_c53764b7.plan.md](../../../.cursor/plans/kotorblender_improvements_brainstorm_c53764b7.plan.md) (passes 2–5 normalized in-repo)
