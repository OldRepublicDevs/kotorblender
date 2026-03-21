"""One-off: normalize garbled markdown in brainstorm plan pass 4."""
from __future__ import annotations

import sys

PLAN = r"c:\GitHub\kotorblender\.cursor\plans\kotorblender_improvements_brainstorm_c53764b7.plan.md"


def main() -> int:
    lines = open(PLAN, encoding="utf-8").read().splitlines(keepends=True)
    for i, line in enumerate(lines):
        if "Analyst ideas used" in line and "Deferred for later: pytest" in line:
            lines[i] = (
                "**Analyst ideas used:** Extended show/hide (classification matrix, unlightmapped, items-global "
                "behavior); tools ops stub smoke (`module_designer`, `indoor_map_builder`, `clone_module`, "
                "`tslpatchdata_editor`). Deferred for later: pytest `MdlWriter`↔`MdlReader` (both sides pull in "
                "**mathutils** / **scene** — keep in Blender or refactor format layer).\n"
            )
        if line.startswith("**Tests added (pass 4):**"):
            lines[i] = (
                "**Tests added (pass 4):** **test_ops_showhide_extended_categories_smoke.py**; "
                "**test_ops_tools_stub_smoke.py**.\n"
            )
    open(PLAN, "w", encoding="utf-8", newline="").writelines(lines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
