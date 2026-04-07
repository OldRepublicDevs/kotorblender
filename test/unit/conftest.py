"""
conftest.py – Pytest hooks and shared setup for test/unit

Makes io_scene_kotor.format and io_scene_kotor.constants importable without
loading the addon's __init__.py (which requires Blender). We load only the
format and constants modules by path so unit tests run with system Python.

Also emits discovery output in the format expected by the Python Test Adapter
(LittleFoxTeam) so test discovery works when the extension's plugin does not load.
"""

import importlib.util
import json
import os
import sys
import types

import pytest  # pyright: ignore[reportMissingImports]

_this_dir = os.path.dirname(os.path.abspath(__file__))
_workspace_root = os.path.dirname(os.path.dirname(_this_dir))
_addon_root = os.path.join(_workspace_root, "io_scene_kotor")

if _workspace_root not in sys.path:
    sys.path.insert(0, _workspace_root)


def _load_module(name: str, path: str, package: str | None = None):
    """Load a module from path and register it in sys.modules."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {name} from {path}")
    mod = importlib.util.module_from_spec(spec)
    if package is not None:
        mod.__package__ = package
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _ensure_package(name: str, path: str | None = None):
    """Ensure a package exists in sys.modules (empty if not yet loaded)."""
    if name not in sys.modules:
        mod = types.ModuleType(name)
        mod.__path__ = [path or os.path.join(_addon_root, *name.split(".")[1:])]
        sys.modules[name] = mod
    return sys.modules[name]


# Create package stubs and load only format + constants (no bpy).
_ensure_package("io_scene_kotor", _addon_root)
_ensure_package("io_scene_kotor.format", os.path.join(_addon_root, "format"))
_ensure_package("io_scene_kotor.format.gff", os.path.join(_addon_root, "format", "gff"))

# Load format modules in dependency order (no bpy).
_load_module(
    "io_scene_kotor.format.binreader",
    os.path.join(_addon_root, "format", "binreader.py"),
    "io_scene_kotor.format",
)
_load_module(
    "io_scene_kotor.format.binwriter",
    os.path.join(_addon_root, "format", "binwriter.py"),
    "io_scene_kotor.format",
)
_load_module(
    "io_scene_kotor.format.gff.types",
    os.path.join(_addon_root, "format", "gff", "types.py"),
    "io_scene_kotor.format.gff",
)
_load_module(
    "io_scene_kotor.format.gff.reader",
    os.path.join(_addon_root, "format", "gff", "reader.py"),
    "io_scene_kotor.format.gff",
)
_load_module(
    "io_scene_kotor.format.gff.writer",
    os.path.join(_addon_root, "format", "gff", "writer.py"),
    "io_scene_kotor.format.gff",
)

# Wire up format package so "from io_scene_kotor.format.gff.reader import GffReader" works.
sys.modules["io_scene_kotor"].format = sys.modules["io_scene_kotor.format"]  # pyright: ignore[reportAttributeAccessIssue]
sys.modules["io_scene_kotor.format"].binreader = sys.modules["io_scene_kotor.format.binreader"]  # pyright: ignore[reportAttributeAccessIssue]
sys.modules["io_scene_kotor.format"].binwriter = sys.modules["io_scene_kotor.format.binwriter"]  # pyright: ignore[reportAttributeAccessIssue]
sys.modules["io_scene_kotor.format"].gff = sys.modules["io_scene_kotor.format.gff"]  # pyright: ignore[reportAttributeAccessIssue]
sys.modules["io_scene_kotor.format.gff"].types = sys.modules["io_scene_kotor.format.gff.types"]  # pyright: ignore[reportAttributeAccessIssue]
sys.modules["io_scene_kotor.format.gff"].reader = sys.modules["io_scene_kotor.format.gff.reader"]  # pyright: ignore[reportAttributeAccessIssue]
sys.modules["io_scene_kotor.format.gff"].writer = sys.modules["io_scene_kotor.format.gff.writer"]  # pyright: ignore[reportAttributeAccessIssue]

# Load constants (standalone, no bpy).
_load_module(
    "io_scene_kotor.constants", os.path.join(_addon_root, "constants.py"), "io_scene_kotor"
)
sys.modules["io_scene_kotor"].constants = sys.modules["io_scene_kotor.constants"]  # pyright: ignore[reportAttributeAccessIssue]


def pytest_collection_finish(session: pytest.Session) -> None:
    """Emit discovery output for Python Test Adapter (LittleFoxTeam) when its plugin is not loaded."""
    if not getattr(session.config.option, "collectonly", False):
        return
    try:
        from _pytest.compat import getfslineno  # pyright: ignore[reportMissingImports]
    except ImportError:
        getfslineno = None
    tests: list[dict[str, str]] = []
    for item in session.items:
        line = None
        if getattr(item, "location", None) is not None:
            line = item.location[1]
        elif getfslineno is not None and getattr(item, "obj", None) is not None:
            try:
                line = getfslineno(item.obj)[1]
            except Exception:
                pass
        tests.append({"id": item.nodeid, "line": line if line is not None else ""})
    errors: list[dict[str, str]] = []
    for report in getattr(session, "_collection_reports", []) or []:
        if getattr(report, "failed", False) and getattr(report, "longrepr", None):
            try:
                loc = getattr(report, "location", None)
                file = loc[0] if loc else None
                msg = str(report.longrepr) if report.longrepr else ""
                errors.append({"file": file if file is not None else "", "message": msg})
            except Exception:
                pass
    print("==DISCOVERED TESTS BEGIN==")
    print(json.dumps({"tests": tests, "errors": errors}))
    print("==DISCOVERED TESTS END==")
