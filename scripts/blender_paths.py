#!/usr/bin/env python3
"""Resolve the Blender executable: BLENDER, BLENDER_DIR, standard installs, or PATH."""
from __future__ import annotations

import os
import re
import shutil
import sys

_BLENDER_VERSION_IN_NAME = re.compile(r"(\d+)\.(\d+)")


def _parse_blender_version_from_dirname(dirname: str) -> tuple[int, int]:
    m = _BLENDER_VERSION_IN_NAME.search(dirname)
    if m:
        return int(m.group(1)), int(m.group(2))
    return 0, 0


def _strip_quotes(s: str) -> str:
    p = s.strip()
    if len(p) >= 2 and p[0] == p[-1] and p[0] in "\"'":
        return p[1:-1]
    return p


def _blender_exe_name() -> str:
    return "blender.exe" if sys.platform == "win32" else "blender"


def _exe_in_dir(directory: str) -> str:
    return os.path.join(directory, _blender_exe_name())


def _windows_collect_blender_exes() -> list[tuple[tuple[int, int], str]]:
    candidates: list[tuple[tuple[int, int], str]] = []
    seen: set[str] = set()
    bases = [
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
        r"C:\Program Files",
        r"C:\Program Files (x86)",
    ]
    for base in bases:
        if not base or not os.path.isdir(base):
            continue
        try:
            for name in os.listdir(base):
                if "Blender" not in name:
                    continue
                parent = os.path.join(base, name)
                if not os.path.isdir(parent):
                    continue
                exe = os.path.join(parent, "blender.exe")
                if os.path.isfile(exe):
                    key = os.path.normcase(os.path.normpath(exe))
                    if key not in seen:
                        seen.add(key)
                        candidates.append((_parse_blender_version_from_dirname(name), exe))
                try:
                    subs = os.listdir(parent)
                except OSError:
                    continue
                for sub in subs:
                    subpath = os.path.join(parent, sub)
                    if not os.path.isdir(subpath):
                        continue
                    exe = os.path.join(subpath, "blender.exe")
                    if os.path.isfile(exe):
                        key = os.path.normcase(os.path.normpath(exe))
                        if key not in seen:
                            seen.add(key)
                            candidates.append((_parse_blender_version_from_dirname(sub), exe))
        except OSError:
            continue
    return candidates


def discover_blender_executable() -> str:
    """
    Resolve a Blender executable path.

    Order: ``BLENDER`` (file or PATH name), ``BLENDER_DIR``/blender(.exe),
    Windows install folders (highest x.y wins), then ``shutil.which("blender")``,
    else the bare name ``blender`` for subprocess to resolve.
    """
    blender_env = os.environ.get("BLENDER")
    if blender_env:
        p = _strip_quotes(blender_env)
        if os.path.isfile(p):
            return p
        w = shutil.which(p)
        if w:
            return w

    blender_dir = os.environ.get("BLENDER_DIR")
    if blender_dir:
        d = _strip_quotes(blender_dir)
        exe = _exe_in_dir(d)
        if os.path.isfile(exe):
            return exe

    if sys.platform == "win32":
        ranked = _windows_collect_blender_exes()
        ranked.sort(key=lambda t: t[0], reverse=True)
        if ranked:
            return ranked[0][1]

    if sys.platform == "darwin":
        app_roots = [
            "/Applications/Blender.app/Contents/MacOS/Blender",
            os.path.expanduser("~/Applications/Blender.app/Contents/MacOS/Blender"),
        ]
        for app in app_roots:
            if os.path.isfile(app):
                return app

    w = shutil.which("blender")
    if w:
        return w

    return "blender"
