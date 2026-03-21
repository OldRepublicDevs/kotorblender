#!/usr/bin/env python3
"""
Scan io_scene_kotor Python modules and test files to report which addon modules
are directly referenced from tests.

Usage:
  python test/scripts/coverage_inventory.py              # print summary to stdout
  python test/scripts/coverage_inventory.py --markdown   # full markdown table
  python test/scripts/coverage_inventory.py --write      # write test/io_scene_kotor_coverage_matrix.md

Heuristic: a source module is "covered" if some test file contains an import line
referencing that module (from io_scene_kotor.... import / import io_scene_kotor...).
Barrel __init__.py files are flagged separately.
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path


def _workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _source_modules(addon_root: Path) -> list[Path]:
    return sorted(p for p in addon_root.rglob("*.py") if p.is_file())


def _module_dotted(path: Path, addon_root: Path) -> str:
    rel = path.relative_to(addon_root).with_suffix("")
    parts = rel.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return "io_scene_kotor." + ".".join(parts) if parts else "io_scene_kotor"


def _is_barrel_init(path: Path) -> bool:
    if path.name != "__init__.py":
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    return len(lines) <= 12 and all(
        ln.startswith(("from ", "import ", "__all__", "from __future__")) for ln in lines
    )


def _collect_test_texts(test_root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for sub in ("blender", "unit"):
        d = test_root / sub
        if not d.is_dir():
            continue
        for p in sorted(d.glob("test_*.py")):
            out[str(p.relative_to(test_root.parent))] = p.read_text(encoding="utf-8", errors="replace")
    return out


_IMPORT_LINE = re.compile(
    r"^from\s+(io_scene_kotor(?:\.[a-zA-Z0-9_]+)*)\s+import\s+(.+)$",
    re.MULTILINE,
)
_IMPORT_DIRECT = re.compile(r"^import\s+(io_scene_kotor(?:\.[a-zA-Z0-9_]+)*)", re.MULTILINE)


def _strip_comment(line: str) -> str:
    if "#" in line:
        return line.split("#", 1)[0].strip()
    return line.strip()


def _imported_modules(test_source: str) -> set[str]:
    found: set[str] = set()
    for m in _IMPORT_DIRECT.finditer(test_source):
        found.add(m.group(1))
    for m in _IMPORT_LINE.finditer(test_source):
        base = m.group(1)
        rhs = _strip_comment(m.group(2))
        if rhs.startswith("("):
            rhs = rhs[1:]
        if ")" in rhs:
            rhs = rhs.split(")", 1)[0]
        for part in rhs.split(","):
            token = part.strip().split()[0] if part.strip() else ""
            if not token or token == "(":
                continue
            if token in ("*", "TYPE_CHECKING"):
                continue
            # as alias
            if " as " in token:
                token = token.split(" as ", 1)[0].strip()
            if not re.match(r"^[a-zA-Z0-9_]+$", token):
                continue
            found.add(f"{base}.{token}")
        found.add(base)
    return found


def _covers(covered_prefixes: set[str], dotted: str) -> bool:
    if dotted in covered_prefixes:
        return True
    for prefix in covered_prefixes:
        if dotted.startswith(prefix + ".") and len(dotted) > len(prefix) + 1:
            return True
    return False


def _matching_tests(dotted: str, tests: dict[str, str]) -> list[str]:
    names: list[str] = []
    for rel, src in tests.items():
        imps = _imported_modules(src)
        if dotted in imps:
            names.append(rel)
            continue
        for imp in imps:
            if dotted.startswith(imp + "."):
                names.append(rel)
                break
    return sorted(set(names))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", action="store_true", help="print markdown table")
    parser.add_argument(
        "--write",
        action="store_true",
        help="write markdown to test/io_scene_kotor_coverage_matrix.md",
    )
    args = parser.parse_args()

    root = _workspace_root()
    addon = root / "io_scene_kotor"
    test_dir = root / "test"
    tests = _collect_test_texts(test_dir)

    all_imports: set[str] = set()
    for src in tests.values():
        all_imports |= _imported_modules(src)

    modules = _source_modules(addon)
    rows: list[tuple[str, str, str, str]] = []

    for path in modules:
        dotted = _module_dotted(path, addon)
        rel = str(path.relative_to(root)).replace("\\", "/")
        barrel = _is_barrel_init(path)
        covered = _covers(all_imports, dotted)
        match_tests = _matching_tests(dotted, tests) if covered else []
        status = "barrel" if barrel and not covered else ("yes" if covered else "no")
        test_col = ", ".join(match_tests) if match_tests else ("—" if not covered else "?")
        rows.append((rel, dotted, status, test_col))

    covered_n = sum(1 for _, _, s, _ in rows if s == "yes")
    total_n = len(rows)

    if args.markdown or args.write:
        lines = [
            "# io_scene_kotor test coverage matrix",
            "",
            "Generated by `python test/scripts/coverage_inventory.py --write`. "
            "**Covered** means at least one test file imports this module (or a parent package). "
            "**barrel** marks short `__init__.py` re-export stubs with no direct test import.",
            "",
            f"Summary: **{covered_n}** modules with test imports / **{total_n}** Python files under `io_scene_kotor/`.",
            "",
            "| Source | Module | Status | Test files |",
            "|--------|--------|--------|------------|",
        ]
        for rel, dotted, status, test_col in rows:
            lines.append(f"| `{rel}` | `{dotted}` | {status} | {test_col} |")
        body = "\n".join(lines) + "\n"
        if args.write:
            out_path = test_dir / "io_scene_kotor_coverage_matrix.md"
            out_path.write_text(body, encoding="utf-8")
            print(f"Wrote {out_path}")
        else:
            print(body, end="")
        return 0

    print(f"io_scene_kotor modules: {total_n}, with test import match: {covered_n}")
    uncovered = [r for r in rows if r[2] == "no"]
    print(f"Uncovered (strict): {len(uncovered)}")
    for rel, dotted, _, _ in uncovered[:40]:
        print(f"  {dotted}")
    if len(uncovered) > 40:
        print(f"  ... and {len(uncovered) - 40} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
