#!/usr/bin/env python3
"""
Diff first N bytes of unfixed vs fixed MDL pairs for reader strictness diagnosis.

Usage (from repo root):
  python test/test_files/diff_unfixed_fixed.py [basename] [N]

Example:
  python test/test_files/diff_unfixed_fixed.py KOQ200_01a 64

If basename is omitted, lists available pairs. Reads from test_files/unfixed and
test_files/fixed/converted (same basename .mdl in both).
"""

from __future__ import annotations

import os
import sys

from collections.abc import Generator

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
UNFIXED_DIR = os.path.join(SCRIPT_DIR, "unfixed")
FIXED_DIR = os.path.join(SCRIPT_DIR, "fixed", "converted")


def _pairs() -> Generator[tuple[str, str, str], None, None] | None:
    """Yield (basename, unfixed_mdl, fixed_mdl) for matching pairs."""
    if not os.path.isdir(FIXED_DIR):
        return
    for entry in os.listdir(FIXED_DIR):
        if not entry.lower().endswith(".mdl"):
            continue
        base = os.path.splitext(entry)[0]
        fixed_mdl = os.path.join(FIXED_DIR, entry)
        unfixed_mdl = os.path.join(UNFIXED_DIR, entry)
        if os.path.isfile(fixed_mdl) and os.path.isfile(unfixed_mdl):
            yield base, unfixed_mdl, fixed_mdl


def main():
    n_bytes = 64
    basename = None
    if len(sys.argv) >= 2:
        basename = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            n_bytes = int(sys.argv[2])
        except ValueError:
            n_bytes = 64

    pairs = list(_pairs())
    if not pairs:
        print("No unfixed/fixed MDL pairs found.")
        return 0

    if basename is None:
        print("Available basenames:", ", ".join(p[0] for p in pairs))
        return 0

    match = [p for p in pairs if p[0] == basename]
    if not match:
        print(f"Unknown basename: {basename}")
        return 1

    _, unfixed_mdl, fixed_mdl = match[0]
    with open(unfixed_mdl, "rb") as f:
        u = f.read(n_bytes)
    with open(fixed_mdl, "rb") as f:
        v = f.read(n_bytes)

    print(f"First {n_bytes} bytes: {basename}.mdl")
    print("  Unfixed:", u.hex())
    print("  Fixed: ", v.hex())
    if u != v:
        first_diff = next((i for i in range(min(len(u), len(v))) if u[i] != v[i]), None)
        if first_diff is not None:
            print(f"  First difference at byte offset {first_diff}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
