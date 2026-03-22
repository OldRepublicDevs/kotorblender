#!/usr/bin/env python3
"""
Rewrite ``wheels = [...]`` in io_scene_kotor/blender_manifest.toml from files in
io_scene_kotor/wheels/*.whl (sorted). Run after ``pip wheel pykotor -w io_scene_kotor/wheels``.

Blender 4.4+ requires explicit wheel filenames (no globs).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WHEEL_DIR = REPO_ROOT / "io_scene_kotor" / "wheels"
MANIFEST = REPO_ROOT / "io_scene_kotor" / "blender_manifest.toml"


def _replace_wheels_array(content: str, wheel_basenames: list[str]) -> str:
    m: re.Match[str] | None = re.search(r"^wheels\s*=\s*\[", content, re.MULTILINE)
    if not m:
        msg = "Could not find 'wheels = [' in blender_manifest.toml"
        raise ValueError(msg)
    start = m.start()
    # Opening '[' of wheels = [ ... ]
    bracket_open = m.end() - 1
    if content[bracket_open] != "[":
        msg = "internal: expected '[' after wheels ="
        raise ValueError(msg)
    depth = 0
    end: int | None = None
    for j in range(bracket_open, len(content)):
        c = content[j]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    if end is None:
        msg = "Unclosed wheels = [ ... ] in blender_manifest.toml"
        raise ValueError(msg)

    if wheel_basenames:
        lines = "\n".join(f'  "./wheels/{name}",' for name in wheel_basenames)
        new_block = f"wheels = [\n{lines}\n]"
    else:
        new_block = "wheels = []"

    return content[:start] + new_block + content[end:]


def main() -> int:
    WHEEL_DIR.mkdir(parents=True, exist_ok=True)
    wheels = sorted(p.name for p in WHEEL_DIR.glob("*.whl"))
    if not wheels:
        print(
            "ERROR: no .whl files in io_scene_kotor/wheels — run pip wheel for pykotor",
            file=sys.stderr,
        )
        return 1
    if not any(name.startswith("pykotor-") for name in wheels):
        print(
            "ERROR: io_scene_kotor/wheels has no pykotor-*.whl (extension requires PyKotor bundled)",
            file=sys.stderr,
        )
        return 1
    text = MANIFEST.read_text(encoding="utf-8")
    out = _replace_wheels_array(text, wheels)
    MANIFEST.write_text(out, encoding="utf-8")
    print(f"Wrote {len(wheels)} wheel(s) to {MANIFEST.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
