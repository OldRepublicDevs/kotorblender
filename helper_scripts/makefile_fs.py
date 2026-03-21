"""
Cross-platform directory helpers for the root Makefile (Windows + Unix).

Avoids mkdir -p / rm -rf, which break under Windows cmd.exe when recipes run there.
"""
from __future__ import annotations

import argparse
import glob
import os
import shutil
import sys


def cmd_makedirs(paths: list[str]) -> None:
    for path in paths:
        os.makedirs(path, exist_ok=True)


def cmd_clean_dirs(paths: list[str]) -> None:
    """Remove contents of each directory (like rm -rf dir/*); create missing dirs."""
    for d in paths:
        if os.path.isdir(d):
            for entry in glob.glob(os.path.join(d, "*")):
                if os.path.isdir(entry):
                    shutil.rmtree(entry)
                else:
                    try:
                        os.remove(entry)
                    except OSError:
                        pass
        else:
            os.makedirs(d, exist_ok=True)


def cmd_clean_whl_dirs(paths: list[str]) -> None:
    """Remove only *.whl under each directory (avoids stale pykotor-x.y when pin changes)."""
    for d in paths:
        if not os.path.isdir(d):
            continue
        for path in glob.glob(os.path.join(d, "*.whl")):
            try:
                os.remove(path)
            except OSError:
                pass


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("makedirs", help="Create directories if missing")
    m.add_argument("paths", nargs="+", metavar="DIR")

    c = sub.add_parser("clean-dirs", help="Empty directory contents (keep dirs)")
    c.add_argument("paths", nargs="+", metavar="DIR")

    w = sub.add_parser("clean-whl", help="Delete *.whl only under each directory")
    w.add_argument("paths", nargs="+", metavar="DIR")

    args = p.parse_args()
    if args.cmd == "makedirs":
        cmd_makedirs(args.paths)
    elif args.cmd == "clean-dirs":
        cmd_clean_dirs(args.paths)
    elif args.cmd == "clean-whl":
        cmd_clean_whl_dirs(args.paths)
    else:
        p.error(f"unknown command {args.cmd!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
