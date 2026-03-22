#!/usr/bin/env python3
"""
Launch Blender from the workspace.

Environment:
  BLENDER     — path or command name (checked with ``shutil.which`` if not a file)
  BLENDER_DIR — install directory (uses blender.exe / blender inside it)

If neither is set, discovers typical install locations (Windows: highest x.y under
Program Files), then falls back to ``which`` / ``where`` via ``shutil.which``.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path


def _load_discover() -> Callable[[], str]:
    path = Path(__file__).resolve().parent / "blender_paths.py"
    spec = importlib.util.spec_from_file_location("_kb_blender_paths", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load blender_paths from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.discover_blender_executable


_discover_blender_executable = _load_discover()


def main() -> int:
    exe = _discover_blender_executable()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return subprocess.run([exe, *sys.argv[1:]], cwd=root).returncode


if __name__ == "__main__":
    sys.exit(main())
