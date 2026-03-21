#!/usr/bin/env python3
"""
Run all test/blender/test_*.py scripts under Blender (background).
Cross-platform (Windows PowerShell, cmd, Linux, macOS); ``make test`` uses this script.

Usage:
  python test/run_blender_tests.py [--blender PATH] [--filter SUBSTRING]
  python test/run_blender_tests.py --blender "C:/Program Files/.../blender.exe" --sync-only
  BLENDER=/path/to/blender python test/run_blender_tests.py   # optional env fallback

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


def _strip_quotes(path: str) -> str:
    p = path.strip()
    if len(p) >= 2 and p[0] == p[-1] and p[0] in "\"'":
        return p[1:-1]
    return p


def _parse_runner_argv(argv: list[str]) -> tuple[str | None, list[str]]:
    """Split ``--blender PATH`` from argv; return (override or None, remaining args)."""
    override: str | None = None
    rest: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "--blender" and i + 1 < len(argv):
            override = _strip_quotes(argv[i + 1])
            i += 2
            continue
        rest.append(argv[i])
        i += 1
    return override, rest


def _resolve_blender_exe(cli_override: str | None) -> str:
    if cli_override:
        return cli_override
    return _find_blender()


def _strip_glob_wheels_from_manifest(manifest_path: str) -> bool:
    """Blender 4.4+ rejects wheel paths with * or ?. Clear wheels[] in the copied manifest if needed."""
    try:
        import tomllib
    except ImportError:
        return False
    try:
        with open(manifest_path, "rb") as f:
            raw = f.read()
        data = tomllib.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return False
    wheels = data.get("wheels")
    if not isinstance(wheels, list):
        return False
    if not any(isinstance(w, str) and ("*" in w or "?" in w) for w in wheels):
        return False
    try:
        with open(manifest_path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return False
    out: list[str] = []
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)wheels\s*=\s*(.*)$", lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        indent, rest = m.group(1), m.group(2)
        depth = rest.count("[") - rest.count("]")
        if depth == 0 and "]" in rest:
            out.append(f"{indent}wheels = []\n")
            i += 1
            continue
        out.append(f"{indent}wheels = []\n")
        i += 1
        while i < len(lines) and depth > 0:
            depth += lines[i].count("[") - lines[i].count("]")
            i += 1
    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.writelines(out)
    except OSError:
        return False
    print(
        "Note: cleared glob wheel entries in synced blender_manifest.toml "
        "(Blender 4.4+ requires concrete .whl filenames; run `make wheel-download` to bundle PyKotor).",
        file=sys.stderr,
    )
    return True


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
            ext_base = os.path.join(base, "Blender Foundation", "Blender", major_minor, "extensions", "user_default")
        else:
            base = os.environ.get("HOME", os.path.expanduser("~"))
            ext_base = os.path.join(base, ".config", "blender", major_minor, "extensions", "user_default")
        os.makedirs(ext_base, exist_ok=True)
        dest = os.path.join(ext_base, "io_scene_kotor")
        for root, dirs, files in os.walk(ADDON_SOURCE):
            rel = os.path.relpath(root, ADDON_SOURCE)
            target_dir = os.path.join(dest, rel) if rel != "." else dest
            if not os.path.isdir(target_dir):
                os.makedirs(target_dir)
            for f in files:
                shutil.copy2(os.path.join(root, f), os.path.join(target_dir, f))
        manifest_dest = os.path.join(dest, "blender_manifest.toml")
        if os.path.isfile(manifest_dest):
            _strip_glob_wheels_from_manifest(manifest_dest)
    except Exception as e:
        print(f"Warning: addon sync failed ({e})", file=sys.stderr)


def main() -> int:
    blender_override, args = _parse_runner_argv(sys.argv[1:])
    blender_exe = _resolve_blender_exe(blender_override)

    if args and args[0] == "--sync-only":
        # Used by .vscode tasks: sync addon to Blender's extensions dir then exit.
        try:
            ver = subprocess.run(
                [blender_exe, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if ver.returncode != 0:
                print(f"ERROR: Blender not found or failed: {blender_exe}", file=sys.stderr)
                return 1
            _sync_addon_to_blender(blender_exe)
            return 0
        except FileNotFoundError:
            print(
                f"ERROR: Blender not found at '{blender_exe}'. "
                "Pass --blender PATH or set BLENDER.",
                file=sys.stderr,
            )
            return 1

    filter_sub: str | None = None
    if args and args[0] == "--filter" and len(args) >= 2:
        filter_sub = args[1]
        args = args[2:]
    if args:
        print(f"ERROR: unknown arguments: {' '.join(args)}", file=sys.stderr)
        return 1

    if not os.path.isdir(TEST_DIR):
        print(f"ERROR: Test directory not found: {TEST_DIR}", file=sys.stderr)
        return 1

    try:
        ver = subprocess.run(
            [blender_exe, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if ver.returncode != 0:
            print(f"ERROR: Blender not found or failed: {blender_exe}", file=sys.stderr)
            return 1
        print("=== KotorBlender Tests |", (ver.stdout or ver.stderr or "").split("\n")[0])
        _sync_addon_to_blender(blender_exe)
    except FileNotFoundError:
        print(
            f"ERROR: Blender not found at '{blender_exe}'. "
            "Use: make test (from repo root) or python test/run_blender_tests.py --blender PATH",
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
            [blender_exe, "--background", "--python", path],
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
