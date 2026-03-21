# AGENTS.md

## Cursor Cloud specific instructions

### Overview

KotorBlender (`io_scene_kotor`) is a pure-Python Blender extension (GPL v3)
for importing, editing, and exporting Star Wars: KotOR 1 & 2 game assets:
MDL/MDX models, LYT area layouts, PTH path/navigation files, BWM walkmeshes,
and TPC/TGA textures.  It targets **Blender 3.6 LTS – 5.0** (4.2 LTS recommended).

**Dependencies:**
- **PyKotor** (required for module browser, pack/unpack, BIF/RIM tooling, and most “game” workflows): Shipped **inside the extension .zip** as wheels (Blender’s extension format — not `pip install` at enable time). **`make build`** runs `pip wheel` from PyPI, syncs `blender_manifest.toml`, then packs the zip so installs get PyKotor automatically. Use `SKIP_WHEEL_DOWNLOAD=1 make build` only when wheels are already present. Symlinked dev trees: `make wheel-download` or install PyKotor into Blender’s Python manually.
  Development dependencies in `pyproject.toml`.
  **MDL/MDX I/O** uses only `format/mdl` readers and writers (MdlReader/MdlWriter, AsciiMdlReader/AsciiMdlWriter), not PyKotor.

---

### Blender installation

- **Installed at:** `/opt/blender/blender`
- **Symlink:** `/usr/local/bin/blender`
- **Required system package for GUI mode:** `libegl1`
- Background mode (`blender --background`) works without `libegl1`.

---

### Extension setup

The add-on is symlinked into Blender's extensions directory so Blender finds it
automatically:

```
~/.config/blender/4.2/extensions/user_default/io_scene_kotor  →  /workspace/io_scene_kotor
```

It is enabled persistently in Blender user preferences.  
Extension module name: `bl_ext.user_default.io_scene_kotor`

---

### Repository structure

```
.
├── AGENTS.md                        ← Cloud agent instructions (this file)
├── Makefile                         ← Build, test, lint targets
├── io_scene_kotor/                  ← Extension package (81 .py files)
│   ├── blender_manifest.toml        ← Blender 4.x extension manifest
│   ├── __init__.py                  ← Registration of all extension classes
│   ├── constants.py                 ← Enums, walkmesh materials, anim constants
│   ├── utils.py                     ← Helper predicates and logger
│   ├── aabb.py                      ← AABB BSP tree generator (walkmesh export)
│   ├── addonprefs.py                ← Add-on preferences (texture/lightmap paths)
│   ├── format/                      ← Binary format parsers
│   │   ├── binreader.py / binwriter.py
│   │   ├── mdl/  reader.py writer.py types.py   ← KotOR binary model
│   │   ├── bwm/  reader.py writer.py types.py   ← Walkmesh
│   │   ├── gff/  reader.py writer.py types.py   ← Generic File Format (PTH)
│   │   └── tpc/  reader.py                      ← Texture (DXT1/5 decompressor)
│   ├── vendor/                      ← Third-party library adapters
│   │   └── pykotor_adapter.py       ← PyKotor API wrapper for io/ layer compatibility
│   ├── io/                          ← High-level I/O entry points
│   │   ├── mdl.py   load_mdl / save_mdl
│   │   ├── bwm.py   load_bwm (standalone .wok/.pwk/.dwk)
│   │   ├── lyt.py   load_lyt / save_lyt
│   │   └── pth.py   load_pth / save_pth
│   ├── scene/                       ← Intermediate scene representation
│   │   ├── model.py / walkmesh.py / animation.py / animnode.py
│   │   ├── material.py              ← Blender Cycles/EEVEE shader graph builder
│   │   ├── armature.py
│   │   └── modelnode/  base dummy reference trimesh danglymesh skinmesh
│   │                   emitter light aabb lightsaber
│   ├── ops/                         ← Blender operator implementations
│   │   ├── mdl/  importop.py export.py
│   │   ├── bwm/  importop.py
│   │   ├── lyt/  importop.py export.py
│   │   ├── pth/  importop.py export.py addconnection.py removeconnection.py
│   │   ├── anim/ add.py delete.py move.py play.py event/
│   │   ├── lensflare/ add.py delete.py move.py
│   │   ├── game/ select_installation.py refresh_modules.py open_module.py
│   │   ├── module/ open_resource.py extract_resource.py extract_tpc.py
│   │   │         extract_mdl_textures.py pack_module.py unpack_module.py batch_extract.py
│   │   │         refresh_module_resources.py validate_module.py
│   │   ├── resource/ new_utc.py new_utp.py new_utd.py new_uti.py new_uts.py
│   │   │           new_utt.py new_utm.py new_utw.py new_ute.py new_dlg.py
│   │   │           new_nss.py new_tlk.py new_erf.py new_gff.py
│   │   ├── tools/ module_designer.py indoor_map_builder.py file_search.py
│   │   │        clone_module.py kotor_diff.py tslpatchdata_editor.py
│   │   ├── editor/ edit_tlk.py edit_jrl.py edit_utc.py edit_utp.py edit_utd.py
│   │   │          edit_uti.py edit_uts.py edit_utt.py edit_utm.py edit_utw.py
│   │   │          edit_ute.py edit_dlg.py edit_nss.py edit_erf.py edit_gff.py
│   │   ├── misc/ open_addon_preferences.py
│   │   ├── texture/ convert_tpc_to_tga.py convert_tga_to_tpc.py
│   │   │           extract_tpc_textures.py batch_convert_textures.py
│   │   ├── save/ open_editor.py extract.py
│   │   ├── bakelightmaps.py renderminimap.py rebuildmaterial.py
│   │   ├── rebuildallmaterials.py rebuildarmature.py
│   │   ├── armatureapplykeyframes.py armatureunapplykeyframes.py
│   │   ├── file_handler_drop.py     ← Drag-and-drop .mdl/.lyt/.pth/.wok/.pwk/.dwk onto viewport
│   │   └── showhideobjects.py
│   └── ui/                          ← Panels, menus, lists, property groups
│       ├── menu/  kotor.py (expanded with game/module/resources/tools/editors submenus)
│       ├── panel/ model.py animations.py pathpoint.py modelnode/
│       │         game_installation.py module_browser.py module_designer.py save_game.py
│       │         resource/ (creature.py placeable.py door.py item.py sound.py
│       │                   trigger.py merchant.py waypoint.py encounter.py dialog.py)
│       ├── list/  lensflares.py pathpoints.py modules.py resources.py
│       └── props/ object.py scene.py image.py anim.py animevent.py
│                  lensflare.py pathconnection.py (ModulePropertyGroup added)
└── test/
    ├── test_models.py               ← E2E MDL roundtrip (requires game assets)
    ├── run_blender_tests.py         ← Runner for all background-mode tests (``make test``; optional ``run_blender_tests.sh``)
    ├── scripts/coverage_inventory.py ← Generates io_scene_kotor_coverage_matrix.md
    ├── io_scene_kotor_coverage_matrix.md ← `make test-coverage-matrix`
    └── blender/                     ← Background-mode tests (no assets needed)
        ├── test_registration.py     ← Extension loading, expected kb.* operators list
        ├── test_material.py         ← scene/material (shader graph rebuild)
        ├── test_gff_io.py           ← GFF binary format roundtrip (10 cases)
        ├── test_pth_io.py           ← PTH import/export roundtrip (6 cases)
        ├── test_lyt_export.py       ← LYT file export (7 cases)
        ├── test_io_lyt_load.py      ← load_lyt smoke (no MDL assets)
        ├── test_format_bwm_roundtrip.py ← BWM writer/reader roundtrip
        ├── test_format_bwm_reader_errors.py ← invalid / truncated BWM files
        ├── test_ops_bwm_import_smoke.py ← bpy.ops.kb.bwmimport standalone .wok
        ├── test_format_mdl_reader_errors.py ← invalid / truncated binary MDL
        ├── test_scene_*.py          ← walkmesh, model, armature, dummy; animation/animnode; reference/light
        ├── test_ops_io_smoke.py     ← bpy.ops.kb lyt/mdl/pth import smoke
        ├── test_ops_anim_smoke.py   ← bpy.ops.kb.add/delete/move/play_animation, anim events
        ├── test_ops_lensflare_smoke.py ← bpy.ops.kb.add/move/delete_lens_flare
        ├── test_ops_convert_tpc_to_tga_smoke.py ← bpy.ops.kb.convert_tpc_to_tga
        ├── test_ops_rebuild_material_smoke.py ← bpy.ops.kb.rebuild_material
        ├── test_ops_rebuild_all_materials_smoke.py ← bpy.ops.kb.rebuild_all_materials
        ├── test_ops_showhide_smoke.py ← hide/show walkmeshes, untextured, blockers, emitters, lights
        ├── test_ops_showhide_extended_categories_smoke.py ← unlightmapped, characters, placeables/doors, hide_items
        ├── test_ops_tools_stub_smoke.py ← module_designer, indoor_map_builder, clone_module, tslpatchdata_editor gates
        ├── test_ops_new_gff_smoke.py ← bpy.ops.kb.new_gff (minimal GFF file)
        ├── test_ops_open_preferences_smoke.py ← bpy.ops.kb.open_addon_preferences (no crash)
        ├── test_ops_convert_tga_to_tpc_smoke.py ← bpy.ops.kb.convert_tga_to_tpc (PyKotor gate)
        ├── test_pykotor_adapter_smoke.py ← is_pykotor_available / get_use_pykotor_readers
        ├── test_ops_autodetect_smoke.py ← bpy.ops.kb.autodetect_game_installation
        ├── test_io_scene_kotor_package.py ← bl_info vs manifest
        ├── test_addonprefs_paths.py ← prefs strings → semicolon_separated_to_absolute_paths
        ├── test_ops_resource_helpers.py ← module browser resource_helpers (LOOSE bytes)
        ├── test_ops_mdl_export_smoke.py ← bpy.ops.kb.mdlexport (incl. animations + walkmeshes)
        ├── test_ops_armature_keyframes_smoke.py ← bpy.ops.kb.armature_apply/unapply_keyframes
        ├── test_ops_bake_minimap_smoke.py ← bpy.ops.kb.bake_lightmaps_* / render_minimap_manual (no-op paths)
        ├── test_ops_pth_export_import_smoke.py ← bpy.ops.kb.pthexport / pthimport
        ├── test_ops_file_handlers.py ← FileHandler drag-and-drop registration
        ├── test_ops_lyt_export_smoke.py ← bpy.ops.kb.lytexport
        ├── test_ops_rebuild_armature_smoke.py ← bpy.ops.kb.rebuild_armature
        ├── test_ops_ascii_mdl_smoke.py ← asciimdlexport/import + export anim+walkmesh
        ├── test_ops_open_module_stub_smoke.py ← bpy.ops.kb.open_module (no selection)
        ├── test_ops_pykotor_stub_texture_save_smoke.py ← batch_convert_textures / extract_save gates
        ├── test_ops_path_connection_smoke.py ← bpy.ops.kb.add/remove_path_connection
        ├── test_scene_modelnode_skin_dangly_saber.py ← Skinmesh/Danglymesh/Lightsaber node classes
        ├── test_aabb.py             ← AABB tree generation (13 cases)
        ├── test_constants.py        ← Enums, walkmesh materials, utilities (15 cases)
        └── test_mdl_minimal.py      ← Minimal MDL export/reimport (5 cases)
```

### Architecture (data flow)

- **format/** — Low-level binary parsers (MDL/MDX, BWM, GFF, TPC). Read/write bytes; no Blender types.
- **io/** — High-level I/O: `load_mdl`/`save_mdl`, `load_bwm` (standalone walkmesh), `load_lyt`/`save_lyt`, `load_pth`/`save_pth`. Take an operator (for `report()`) and file path; build or consume **scene** structures.
- **scene/** — Intermediate representation: `model`, `walkmesh`, `animation`, `animnode`, `material`, `armature`, **modelnode/** (base, dummy, reference, trimesh, danglymesh, skinmesh, emitter, light, aabb, lightsaber). Converted to/from Blender objects and format types.
- **ops/** — Blender operators. Call into **io/** and **scene/**; handle exceptions and `self.report()`.
- **ui/** — Panels, menus, lists, property groups. Drive operator invocation and display **scene**-backed props.

Import flow: file → **format** (parse) → **io** (to scene) → **scene** (to Blender objects). Export: Blender objects → **scene** (from props) → **io** (from scene) → **format** (serialize) → file.

---

### IDE setup (type stubs)

Install dev dependencies so your IDE (VS Code / Cursor / PyCharm) gets full
autocomplete for `bpy`, `mathutils`, `bmesh`, etc.:

```bash
pip install ".[dev]"
```

This installs **`fake-bpy-module-4.2`** (Blender 4.2 LTS type stubs), **`pytest`**,
**`ruff`**, and **`pykotor`** (optional for non-Blender workflows). Pyright/Pylance
read **`[tool.pyright]`** in `pyproject.toml` at the repo root.

### Key commands

```bash
# Build extension package (.zip for distribution; fetches PyKotor wheels from PyPI first)
make build

# Run all background-mode tests (no game assets needed)
make test

# Run individual test files during development
make test-registration    # Extension loading, operators, panels, menus
make test-gff             # GFF binary format roundtrip
make test-pth             # PTH import/export roundtrip
make test-lyt             # LYT area layout export
make test-aabb            # AABB BSP tree generation
make test-constants       # Enums, walkmesh materials, utility functions
make test-mdl             # Minimal MDL export/reimport
make test-material        # scene/material shader rebuild suite
make test-format-bwm-roundtrip  # BWM write/read roundtrip
make test-ops-bwm-import-smoke  # standalone kb.bwmimport / .wok smoke
make test-io-lyt-load     # load_lyt (empty / missing MDL)
make test-scene-modules   # walkmesh, model, armature, DummyNode
make test-ops-io-smoke    # bpy.ops.kb file import operators
make test-ops-anim-smoke  # bpy.ops.kb.add_animation
make test-analyst-coverage # broad operator/format smoke bundle (Makefile lists all Blender scripts)
make test-coverage-matrix # Regenerate test/io_scene_kotor_coverage_matrix.md
make test-unit            # Pytest (test/unit: GFF + reader errors, TPC, bin I/O, game_install_detect, log_config, BWM/MDL types, constants)

# Full E2E test (requires extracted KotOR game assets in DATA_DIR)
DATA_DIR=/path/to/kotor/assets make test-e2e

# Syntax check + lint
make lint
```

---

### CI/CD (GitHub Actions)

Two workflows live in `.github/workflows/`:

| File | Trigger | Jobs |
|------|---------|------|
| `ci.yml` | Every push / PR | **lint** (syntax + ruff, no Blender) · **test-and-build** (downloads/caches Blender, runs all tests via `test/run_blender_tests.py`, uploads `.zip` artifact) |
| `release.yml` | Tags `v*.*.*` | Builds the package and creates a GitHub Release with the `.zip` attached |

Blender (~200 MB) is cached by version so repeat CI runs skip the download.

---

### How to write a new background-mode test

Create `test/blender/test_myfeature.py` following the existing template:

```python
"""
test_myfeature.py – description

Run with:
    blender --background --python test/blender/test_myfeature.py
"""
import os, sys
import bpy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

MODULE = "bl_ext.user_default.io_scene_kotor"
if MODULE not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module=MODULE)

# Import from the source package (not the extension namespace)
from io_scene_kotor.constants import DummyType
# ... your imports ...

def test_something():
    # ... test logic ...
    ok = True
    print("  PASS test_something" if ok else "  FAIL test_something")
    return ok

def run_tests():
    print("\n=== test_myfeature.py ===")
    results = [test_something()]
    passed, total = sum(results), len(results)
    status = "OK" if all(results) else "FAIL"
    print(f"\n[{status}] {passed}/{total} passed in test_myfeature.py\n")
    return all(results)

if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
```

The test runner (`test/run_blender_tests.py`, invoked by `make test`) automatically picks up any
`test/blender/test_*.py` file.

---

### Gotchas

- **E2E tests require proprietary game data.**  
  `make test-e2e` / `test/test_models.py` needs `DATA_DIR` pointing to
  extracted KotOR BIF archives.  Not available in cloud environments.

- **Extension module name.**  
  In Blender 4.2+, extensions use the `bl_ext.user_default.*` prefix.
  Always enable via:
  ```python
  bpy.ops.preferences.addon_enable(module='bl_ext.user_default.io_scene_kotor')
  ```
  Not the bare name `io_scene_kotor`.

- **Background mode context.**  
  `bpy.context.collection` is available in background mode after Blender
  starts.  Use `bpy.context.scene.collection` as an equivalent.

- **GUI mode requires `libegl1`.**  
  `sudo apt-get install -y libegl1` before launching Blender with a display.

- **Accessibility (keyboard).**
  All KotOR operators are reachable via Blender menus (File → Import/Export,
  Editor → KotOR, including **Quick access** for search/prefs/docs shortcuts).
  **F3** (operator search) finds actions by “KotOR”, “module”, “pack”, etc.
  Optional addon keymaps (when not in background mode): Ctrl+Alt+O
  (Open Module), Ctrl+Alt+W (Show Walkmeshes), Shift+Ctrl+Alt+W (Hide Walkmeshes).
  Keyboard-only users can use Blender’s built-in menu navigation (Tab, arrows, Enter).
  Operators and submenus use `bl_label` and `bl_description` for tooltips and screen readers;
  KotOR sidebar panels include short on-screen hints where helpful.

- **Star imports cause ruff warnings.**  
  There are 400+ pre-existing `F401`/`F403` warnings from star imports across
  several files.  Only `E9` / `F821` / `F823` (actual errors) are treated as
  blocking in CI.

- **`pyproject.toml`.**  
  Ruff, pytest, Pyright, and optional dev dependencies (`pip install ".[dev]"`) live there.
  All 81 `.py` files are also validated via `py_compile` (the `syntax-check` target).

- **`bpy.ops.wm.read_homefile()` disables add-ons.**  
  If a test calls `read_homefile`, re-enable the extension afterwards with
  `bpy.ops.preferences.addon_enable(module=MODULE)`.

- **Operator stubs.**  
  Some operators still report “not yet implemented” or minimal behavior (e.g. KotorDiff,
  TSLPatchData editor UI, Indoor Map Builder, some resource editors). Module workflow
  pieces that are implemented include **File Search**, **Module Designer** sidebar panel
  (pack/unpack/clone/BIF path), **Clone Module**, **Batch Extract**, **Pack/Unpack Module**,
  and **Refresh** resource lists when PyKotor is available.

---

### Supported file formats

| Format | Extension(s) | Read | Write | Notes |
|--------|-------------|------|-------|-------|
| KotOR Binary Model | `.mdl` + `.mdx` | ✓ | ✓ | K1-PC, K1-Xbox, K2-PC, K2-Xbox |
| Binary Walkmesh | `.wok` `.pwk` `.dwk` | ✓ | ✓ | Area / Placeable / Door; **standalone import** via File → Import → **KotOR Walkmesh** (`kb.bwmimport` / `io/bwm.load_bwm`) or drag-drop; with MDL via model import. Export still expects MDL context for walkmeshes in the same file. |
| Area Layout | `.lyt` | ✓ | ✓ | Plain text |
| Path / Navigation | `.pth` | ✓ | ✓ | GFF binary container |
| KotOR Texture | `.tpc` | ✓ | – | DXT1/DXT5 + grayscale/RGBA |
| Texture Info | `.txi` | ✓ | – | Sidecar parsed inline |
| Targa | `.tga` | ✓ | – | Via Blender built-in |

**Drag-and-drop:** Users can drag `.mdl`, `.mdl.ascii`, `.lyt`, `.pth`, `.wok`, `.pwk`, and `.dwk` files onto the 3D Viewport or Outliner (ViewLayer mode); the corresponding import operator runs with the dropped path (FileHandler API, Blender 3.2+). See `ops/file_handler_drop.py`.

---

### Key constants (quick reference)

| Constant | Value | Purpose |
|----------|-------|---------|
| `ANIM_FPS` | 30 | Hard-coded KotOR engine animation rate |
| `ANIM_REST_POSE_OFFSET` | 5 | Frames before animation starts |
| `ANIM_PADDING` | 60 | Frames between animations |
| `UV_MAP_MAIN` | `"UVMap"` | Diffuse texture UV layer name |
| `UV_MAP_LIGHTMAP` | `"UVMap_lm"` | Lightmap UV layer name |

---

### Mock operator pattern (for direct function testing)

Many `io/` functions take a Blender operator as first argument (for `report()`).
Use this minimal mock in tests:

```python
class _Op:
    def report(self, level, message):
        print(f"  [{next(iter(level))}] {message}")
```

---

## Learned User Preferences

- Prefer tests that avoid monkeypatching; use real temp files, real bpy objects, and real data structures. For new `test/blender/test_*.py` files, follow the same structural pattern as `test_material.py` (workspace root on `sys.path`, enable `bl_ext.user_default.io_scene_kotor`, explicit `run_tests()`); scale depth and combinatorics to module risk, not necessarily material.py’s full breadth for every file.
- When asked to run or fix tests, continue until the suite passes (run/fix until functional), unless the user explicitly restricts testing for that specific request.
- Tests should use the exact same pipeline as the GUI (e.g., `bpy.ops.kb.mdlimport` with real addon prefs) rather than only direct function calls, to catch operator-level issues.
- Prefer full type hints in io_scene_kotor; do not use pyright: ignore or type: ignore—use isinstance or if/raise and `getattr(obj, "kb", None)` with None checks for Blender dynamic obj.kb and scene.kb.
- Use enums and constants from constants.py (e.g. PropertyName) for UI property names and enum values instead of string literals.
- When asked to implement a plan that already has todos, execute those todos to completion without recreating the list.

---

## Learned Workspace Facts

- On Windows (PowerShell or cmd), `make test` uses `python test/run_blender_tests.py --blender …` with the Makefile’s default Blender path; override with `BLENDER=… make test` or pass `--blender` when invoking the script directly. Auto-detect under Program Files applies when neither is set.
- **`make build` / `make wheel-download`:** Use **GNU Make** (Git Bash, MSYS2, Chocolatey `make`, etc.); `nmake` is unsupported. The Makefile uses `$(PYTHON) helper_scripts/makefile_fs.py` instead of `mkdir -p` / `rm -rf` so recipes work under Windows `cmd.exe`. Set **`PYTHON=python`** if `python3` is not on `PATH`. Default **`PYKOTOR_SPEC=pykotor==2.3.1`** pins an exact PyPI build; a constraint like `pykotor>=2.3.1` resolves to the latest matching release, not a fixed version. Each `wheel-download` runs **`clean-whl`** first so an older PyKotor wheel is not left beside a new pin.
- **`blender_manifest.toml`:** `tagline` must be **64 characters or fewer** or `blender --command extension build` fails (Blender 4.4+).
- The test runner syncs the repo addon into Blender’s extensions directory (creates `extensions/user_default` if needed) so tests run against current code; on Windows it uses overwrite-only copy (no rmtree). After copy it strips invalid `wheels` glob entries (e.g. `pykotor-*.whl`) because Blender 4.4+ rejects them—run tests via `python test/run_blender_tests.py`, or `python test/run_blender_tests.py --sync-only` then open Blender. The manifest should list concrete `.whl` names or `wheels = []` when PyKotor is not bundled. To verify PyKotor is actually bundled, run **`make build`** (or `blender --command extension build`) and inspect the produced `.zip` for `wheels/*.whl`; the manifest alone does not prove the artifact was built correctly.
- In addon preferences, avoid `StringProperty` or other typing that triggers `get_type_hints` in Blender 4.4 or addon registration can fail.
- In `scene/modelnode/base.py`, `find_node` must be recursive so an AabbNode under a nested dummy (e.g. root → pivot → areawalk) is found for WOK export; use `from __future__ import annotations` there when `BaseNode` appears in type hints in the same module.
- Tests that depend on `test_files/` (e.g. fixed MDL, PyKotor assets) should skip gracefully when the directory or files are missing so CI without assets exits 0.
- KotorBlender is distributed as a Blender extension `.zip` (Preferences → Extensions → Install from Disk), not an installer `.exe`. Bump **`io_scene_kotor/blender_manifest.toml`** and **`io_scene_kotor/__init__.py`** (`bl_info`); tagging **`v*.*.*`** triggers `.github/workflows/release.yml` and attaches the zip to a GitHub Release.
- For VS Code/Cursor Test Explorer and pytest, restrict discovery to `test/unit` only (`[tool.pytest.ini_options]` in `pyproject.toml` and `python.testing.pytestArgs`); install `pip install ".[dev]"` in the project `.venv` so discovery runs without Blender.
- MDL import treats a missing MDX file as optional; when the MDX is absent the reader uses empty geometry data instead of raising. In Blender 5.x, addon preference properties can return `_PropertyDeferred` instead of strings; coerce with `str()` before utilities like `semicolon_separated_to_absolute_paths()`.
- Game-install autodetection and PyKotor “installation not found” issues are much easier to trace with add-on preferences **Diagnostics → Logging verbosity** set to Debug (`log_config` / `io_scene_kotor` package loggers on the system console).
- Within io_scene_kotor use relative imports (e.g. `from ..constants`) rather than absolute `from io_scene_kotor`; when testing str Enum classes, assert `{e.value for e in EnumClass}` rather than using `dir()` so string methods are not mistaken for members.
