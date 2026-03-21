# Contributing to KotorBlender

Thank you for your interest in contributing to KotorBlender. This document explains how to get started, run tests, and submit changes.

## Before you start

- **Small fixes** (typos, docs, single-operator tweaks) can go straight to a pull request.
- **Larger changes** (new features, refactors, format support) — please open an issue first to align with maintainers and the roadmap. This avoids duplicate work and ensures the approach fits the project.

## One topic per pull request

Keep each PR focused on a single logical change. Split refactors, new features, and bug fixes into separate PRs when possible. This makes review faster and history clearer.

## Tests and documentation

- **New behavior** should add or update tests where relevant, and update documentation (README, AGENTS.md, or in-code docstrings) as needed.
- **Existing tests** must continue to pass. Run the test suite before submitting (see below).

## How to run tests

KotorBlender is tightly coupled to the Blender Python API, so tests run inside Blender in background mode.

- **All background-mode tests (no game assets):**
  ```bash
  make test
  ```
  On Windows, if Blender is not on `PATH`, set the `BLENDER` environment variable to your Blender executable, or use `test/run_blender_tests.py` (see AGENTS.md).

- **Individual test modules** (for development):
  ```bash
  make test-registration   # Extension loading, operators
  make test-gff            # GFF binary format
  make test-pth            # PTH import/export
  make test-lyt            # LYT export
  make test-aabb           # AABB tree
  make test-constants      # Enums, utilities
  make test-mdl            # Minimal MDL roundtrip
  make test-mdl-import-op  # MDL import operator smoke
  make test-material       # scene/material shader rebuild
  make test-format-bwm-roundtrip  # BWM write/read
  make test-ops-bwm-import-smoke  # standalone walkmesh import operator
  make test-io-lyt-load    # load_lyt smoke
  make test-scene-modules  # scene walkmesh/model/armature/… (several scripts)
  make test-ops-io-smoke   # lyt/mdl/pth import ops
  make test-ops-anim-smoke
  make test-analyst-coverage  # Makefile bundle of many operator/format smokes
  make test-community-mdl   # Community MDL load (if test_files present)
  make test-pykotor-compatibility
  make test-pykotor-ascii-mdl
  make test-unit           # pytest under test/unit (no Blender)
  ```

- **Test layout:** Tests live under `test/blender/test_*.py`. The runner is `test/run_blender_tests.sh` (Linux/macOS) or `test/run_blender_tests.py` (Windows). See [AGENTS.md](AGENTS.md) for the full test template, `make test-analyst-coverage` script list, and CI details.

- **E2E tests** (require extracted game assets) are not run in CI:
  ```bash
  DATA_DIR=/path/to/extracted/assets make test-e2e
  ```

## Code style

- **Lint:** We use `ruff` with a minimal rule set for CI. From the repo root:
  ```bash
  make lint
  ```
  This runs a syntax check and `ruff check --select E9,F821,F823` on `io_scene_kotor/`. Only errors that break the extension at load time are enforced; many pre-existing star-import warnings (F401/F403) are accepted. Match the style of the file you are editing and avoid introducing new blocking errors.

- **Reference:** [AGENTS.md](AGENTS.md) describes repository structure, Blender extension setup, and agent/CI conventions.

## PyKotor wheels (development and release builds)

Blender does not resolve PyPI at install time; **`make build`** (default release path) runs `wheel-download` first so the `.zip` always contains PyKotor at the pinned version (**default `PYKOTOR_SPEC=pykotor==2.3.1`**, from PyPI) unless you set `SKIP_WHEEL_DOWNLOAD=1`.

**Windows:** Use **GNU Make** (Git Bash, MSYS2, etc.); native `nmake` will not work. If `python3` is missing, run e.g. `PYTHON=python make build`.

For a **symlinked** dev copy (no zip):

1. `make wheel-download` — `pip wheel` into `io_scene_kotor/wheels/` + `helper_scripts/sync_extension_wheels.py`.
2. Pin: `PYKOTOR_SPEC=pykotor==x.y.z make wheel-download`.
3. Windows: `PYTHON=python make wheel-download` if `python3` is unavailable.

Wheel files are gitignored; committed `blender_manifest.toml` may show `wheels = []` until you run the steps above or CI.

## Troubleshooting & solutions library

Institutional notes for stub operators, test quirks, and integration audits live under [docs/solutions/](docs/solutions/).

| Topic | Document |
|--------|----------|
| **Operator inventory** (stubs, false-success `new_*`, mechanical wiring **§K**, phases P1–P5) | [docs/plans/2026-02-19-feat-integration-gaps-stubs-audit-plan.md](docs/plans/2026-02-19-feat-integration-gaps-stubs-audit-plan.md) |
| PyKotor stub operators — **current** FINISHED/INFO behavior & smoke contract | [docs/solutions/logic-errors/pykotor-stub-operators-finished-without-work.md](docs/solutions/logic-errors/pykotor-stub-operators-finished-without-work.md) |
| `bpy.ops` + `report({"ERROR"}, …)` → **RuntimeError** in tests | [docs/solutions/integration-issues/operator-error-report-runtimeerror.md](docs/solutions/integration-issues/operator-error-report-runtimeerror.md) |
| Open add-on preferences from background/tests | [docs/solutions/integration-issues/open-addon-preferences-background.md](docs/solutions/integration-issues/open-addon-preferences-background.md) |

## Extension name (Blender 4.2+)

When enabling the extension from script or docs, use the full module name:

- **Blender 4.2+:** `bl_ext.user_default.io_scene_kotor`
- Not the bare name `io_scene_kotor` (that is the package directory name).

## Pull requests

Please use our [pull request template](.github/PULL_REQUEST_TEMPLATE.md) when opening a PR. It asks for a description of the problem, proposed solution, alternatives considered, limitations, and a short checklist (tests, lint, docs).
