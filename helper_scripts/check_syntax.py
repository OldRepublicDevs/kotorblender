#!/usr/bin/env python3
"""
check_syntax.py – Syntax check all Python files in io_scene_kotor

Compiles all .py files in the io_scene_kotor directory to verify syntax.
Exits with code 0 if all files pass, 1 if any have syntax errors.

Usage:
    python3 helper_scripts/check_syntax.py
"""

from __future__ import annotations

import os
import py_compile
import sys
from pathlib import Path


def main():
    """Check syntax of all Python files in io_scene_kotor directory."""
    # Get the workspace root (parent of helper_scripts)
    script_dir: Path = Path(__file__).parent
    workspace_root: Path = script_dir.parent
    addon_dir: Path = workspace_root / "io_scene_kotor"

    if not addon_dir.exists():
        print(f"ERROR: Addon directory not found: {addon_dir}", file=sys.stderr)
        sys.exit(1)

    errors: list[str] = []
    for root, _, files in os.walk(addon_dir):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                try:
                    py_compile.compile(path, doraise=True)
                except py_compile.PyCompileError as e:
                    errors.append(str(e))

    if errors:
        for error in errors:
            print(f"SYNTAX ERROR: {error}", file=sys.stderr)
        sys.exit(1)

    print("All .py files pass syntax check")
    sys.exit(0)


if __name__ == "__main__":
    main()
