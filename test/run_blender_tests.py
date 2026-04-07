#!/usr/bin/env python3
"""
Run all test/blender/test_*.py scripts under Blender (background).
Use when make/bash is not available (e.g. Windows).

Usage:
  python test/run_blender_tests.py [--filter SUBSTRING]
  BLENDER=/path/to/blender python test/run_blender_tests.py

Exit: 0 if all pass, 1 if any fail.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
TEST_DIR = os.path.join(SCRIPT_DIR, "blender")
ADDON_SOURCE = os.path.join(WORKSPACE_ROOT, "io_scene_kotor")


def _find_blender() -> str:
    env = os.environ.get("BLENDER")
    if env:
        return env
    if sys.platform == "win32":
        for base in [
            os.environ.get("ProgramFiles", "C:\\Program Files"),
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
        ]:
            if not base or not os.path.isdir(base):
                continue
            try:
                for name in os.listdir(base):
                    if "Blender" not in name:
                        continue
                    parent = os.path.join(base, name)
                    # e.g. Blender Foundation/Blender 4.4/blender.exe
                    exe = os.path.join(parent, "blender.exe")
                    if os.path.isfile(exe):
                        return exe
                    for sub in os.listdir(parent):
                        exe = os.path.join(parent, sub, "blender.exe")
                        if os.path.isfile(exe):
                            return exe
            except OSError:
                continue
    return "blender"


BLENDER = _find_blender()


def _sync_addon_to_blender(blender_exe: str) -> None:
    """Copy repo addon into Blender's extensions dir so tests load current code."""
    if not os.path.isdir(ADDON_SOURCE):
        return
    try:
        ver_out = subprocess.run(
            [blender_exe, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if ver_out.returncode != 0:
            return
        # e.g. "Blender 4.4.1" or "Blender 5.1"
        match = re.search(r"Blender\s+(\d+\.\d+)", ver_out.stdout or ver_out.stderr or "")
        if not match:
            return
        major_minor = match.group(1)
        if sys.platform == "win32":
            base = os.environ.get("APPDATA", "")
            if not base:
                return
            ext_base = os.path.join(
                base, "Blender Foundation", "Blender", major_minor, "extensions", "user_default"
            )
        else:
            base = os.environ.get("HOME", os.path.expanduser("~"))
            ext_base = os.path.join(
                base, ".config", "blender", major_minor, "extensions", "user_default"
            )
        if not os.path.isdir(ext_base):
            return
        dest = os.path.join(ext_base, "io_scene_kotor")
        for root, dirs, files in os.walk(ADDON_SOURCE):
            rel = os.path.relpath(root, ADDON_SOURCE)
            target_dir = os.path.join(dest, rel) if rel != "." else dest
            if not os.path.isdir(target_dir):
                os.makedirs(target_dir)
            for f in files:
                shutil.copy2(os.path.join(root, f), os.path.join(target_dir, f))
    except Exception:
        pass


def main():
    filter_sub = None
    args = list(sys.argv[1:])
    if args and args[0] == "--filter" and len(args) >= 2:
        filter_sub = args[1]
        args = args[2:]

    if not os.path.isdir(TEST_DIR):
        print(f"ERROR: Test directory not found: {TEST_DIR}", file=sys.stderr)
        return 1

    try:
        ver = subprocess.run(
            [BLENDER, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if ver.returncode != 0:
            print(f"ERROR: Blender not found or failed: {BLENDER}", file=sys.stderr)
            return 1
        print("=== KotorBlender Tests |", (ver.stdout or ver.stderr or "").split("\n")[0])
        _sync_addon_to_blender(BLENDER)
    except FileNotFoundError:
        print(
            f"ERROR: Blender not found at '{BLENDER}'.",
            "Set BLENDER to your executable (e.g. on Windows: set BLENDER=C:\\...\\Blender 4.2\\blender.exe)",
            file=sys.stderr,
        )
        return 1

    passed: int = 0
    failed: int = 0
    failed_names: list[str] = []

    for name in sorted(os.listdir(TEST_DIR)):
        if not name.startswith("test_") or not name.endswith(".py"):
            continue
        if filter_sub and filter_sub not in name:
            continue
        path = os.path.join(TEST_DIR, name)
        if not os.path.isfile(path):
            continue
        print("")
        print(">>>", name)
        exit_code = subprocess.run(
            [BLENDER, "--background", "--python", path],
            cwd=os.path.dirname(os.path.dirname(SCRIPT_DIR)),
            timeout=120,
        ).returncode
        if exit_code == 0:
            passed += 1
        else:
            failed += 1
            failed_names.append(name)

    print("")
    print(f"=== Results: {passed} passed, {failed} failed ===")
    if failed:
        print("Failed:")
        for n in failed_names:
            print("  -", n)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
