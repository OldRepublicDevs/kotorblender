#!/usr/bin/env python3
"""Fail fast if the extension build would ship without a PyKotor wheel."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WHEEL_DIR = REPO_ROOT / "io_scene_kotor" / "wheels"
MANIFEST = REPO_ROOT / "io_scene_kotor" / "blender_manifest.toml"


def main() -> int:
    if not WHEEL_DIR.is_dir():
        print(f"ERROR: missing wheels directory: {WHEEL_DIR}", file=sys.stderr)
        return 1
    pykotor_wheels = sorted(WHEEL_DIR.glob("pykotor-*.whl"))
    if not pykotor_wheels:
        print(
            "ERROR: no PyKotor wheel in io_scene_kotor/wheels (expected pykotor-*.whl). "
            "Run `make wheel-download` from the repo root (or set PYKOTOR_SPEC).",
            file=sys.stderr,
        )
        return 1
    text = MANIFEST.read_text(encoding="utf-8")
    for whl in pykotor_wheels:
        needle = f'./wheels/{whl.name}'
        if needle not in text:
            print(
                f"ERROR: {whl.name} is not listed in blender_manifest.toml "
                f"(run: {sys.executable} helper_scripts/sync_extension_wheels.py)",
                file=sys.stderr,
            )
            return 1
    if not re.search(r"pykotor-[\w.-]+\.whl", text):
        print(
            "ERROR: blender_manifest.toml has no pykotor wheel entry",
            file=sys.stderr,
        )
        return 1
    names = ", ".join(p.name for p in pykotor_wheels)
    print(f"OK: bundled PyKotor wheel(s): {names}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
