#!/usr/bin/env python3
"""Launch Blender from the workspace. Used by .vscode launch.json (reads BLENDER from env)."""
from __future__ import annotations

import os
import subprocess
import sys

def main() -> int:
    blender = os.environ.get("BLENDER", "blender")
    return subprocess.run([blender], cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).returncode

if __name__ == "__main__":
    sys.exit(main())
