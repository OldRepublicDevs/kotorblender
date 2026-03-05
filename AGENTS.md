# AGENTS.md

## Cursor Cloud specific instructions

### Overview

KotorBlender (`io_scene_kotor`) is a pure-Python Blender extension (GPL v3)
for importing, editing, and exporting Star Wars: KotOR 1 & 2 game assets:
MDL/MDX models, LYT area layouts, PTH path/navigation files, BWM walkmeshes,
and TPC/TGA textures.  It targets **Blender 3.6 LTS – 5.0** (4.2 LTS recommended).
No non-Blender Python dependencies are needed.

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
│   ├── __init__.py                  ← Registration of all 52 classes
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
│   ├── io/                          ← High-level I/O entry points
│   │   ├── mdl.py   load_mdl / save_mdl
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
│   │   ├── lyt/  importop.py export.py
│   │   ├── pth/  importop.py export.py addconnection.py removeconnection.py
│   │   ├── anim/ add.py delete.py move.py play.py event/
│   │   ├── lensflare/ add.py delete.py move.py
│   │   ├── bakelightmaps.py renderminimap.py rebuildmaterial.py
│   │   ├── rebuildallmaterials.py rebuildarmature.py
│   │   ├── armatureapplykeyframes.py armatureunapplykeyframes.py
│   │   └── showhideobjects.py
│   └── ui/                          ← Panels, menus, lists, property groups
│       ├── menu/  kotor.py
│       ├── panel/ model.py animations.py pathpoint.py modelnode/
│       ├── list/  lensflares.py pathpoints.py
│       └── props/ object.py scene.py image.py anim.py animevent.py
│                  lensflare.py pathconnection.py
└── test/
    ├── test_models.py               ← E2E MDL roundtrip (requires game assets)
    ├── run_blender_tests.sh         ← Runner for all background-mode tests
    └── blender/                     ← Background-mode tests (no assets needed)
        ├── test_registration.py     ← Extension loading, all 43 operators
        ├── test_gff_io.py           ← GFF binary format roundtrip (10 cases)
        ├── test_pth_io.py           ← PTH import/export roundtrip (6 cases)
        ├── test_lyt_export.py       ← LYT file export (7 cases)
        ├── test_aabb.py             ← AABB tree generation (13 cases)
        ├── test_constants.py        ← Enums, walkmesh materials, utilities (15 cases)
        └── test_mdl_minimal.py      ← Minimal MDL export/reimport (5 cases)
```

---

### IDE setup (type stubs)

Install dev dependencies so your IDE (VS Code / Cursor / PyCharm) gets full
autocomplete for `bpy`, `mathutils`, `bmesh`, etc.:

```bash
pip install -r requirements-dev.txt
```

This installs **`fake-bpy-module-4.2`** (Blender 4.2 LTS type stubs) and
**`ruff`**.  `pyrightconfig.json` in the repo root configures Pyright/Pylance
to use them with sensible defaults.

### Key commands

```bash
# Build extension package (.zip for distribution)
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
| `ci.yml` | Every push / PR | **lint** (syntax + ruff, no Blender) · **test-and-build** (downloads/caches Blender 4.2, runs all tests via `run_blender_tests.sh`, uploads `.zip` artifact) |
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

The test runner (`test/run_blender_tests.sh`) automatically picks up any
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

- **Star imports cause ruff warnings.**  
  There are 400+ pre-existing `F401`/`F403` warnings from star imports across
  several files.  Only `E9` / `F821` / `F823` (actual errors) are treated as
  blocking in CI.

- **No `pyproject.toml` / `setup.cfg`.**  
  All 81 `.py` files are validated via `py_compile` (the `syntax-check` target).

- **`bpy.ops.wm.read_homefile()` disables add-ons.**  
  If a test calls `read_homefile`, re-enable the extension afterwards with
  `bpy.ops.preferences.addon_enable(module=MODULE)`.

---

### Supported file formats

| Format | Extension(s) | Read | Write | Notes |
|--------|-------------|------|-------|-------|
| KotOR Binary Model | `.mdl` + `.mdx` | ✓ | ✓ | K1-PC, K1-Xbox, K2-PC, K2-Xbox |
| Binary Walkmesh | `.wok` `.pwk` `.dwk` | ✓ | ✓ | Area / Placeable / Door |
| Area Layout | `.lyt` | ✓ | ✓ | Plain text |
| Path / Navigation | `.pth` | ✓ | ✓ | GFF binary container |
| KotOR Texture | `.tpc` | ✓ | – | DXT1/DXT5 + grayscale/RGBA |
| Texture Info | `.txi` | ✓ | – | Sidecar parsed inline |
| Targa | `.tga` | ✓ | – | Via Blender built-in |

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
