---
name: Blender Integration Enhancement Plan
overview: Enhance KotorBlender's integration with Blender's 3D environment and add missing HolocronToolset functionality. Focus on completing stub operators, adding missing file format support (2DA, ARE, GIT, VIS, BIF), implementing 3D area editing workflows, module validation, NSS compilation, and enhanced UI/UX within Blender's native interface.
todos:
  - id: complete-file-search
    content: "Implement KB_OT_file_search: Create search panel/dialog, integrate PyKotor path utilities, add to module browser"
    status: cancelled
  - id: complete-module-designer
    content: "Implement KB_OT_module_designer: Create unified panel with structure tree, dependencies, batch ops, validation dashboard"
    status: cancelled
  - id: complete-indoor-map-builder
    content: "Implement KB_OT_indoor_map_builder: 3D viewport mode for area editing with gizmos and overlays"
    status: cancelled
  - id: complete-clone-module
    content: "Implement KB_OT_clone_module: Copy module with reference renaming using PyKotor"
    status: cancelled
  - id: complete-kotor-diff
    content: "Implement KB_OT_kotor_diff: Module/resource comparison with Blender text editor or custom panel"
    status: cancelled
  - id: complete-tslpatchdata
    content: "Implement KB_OT_tslpatchdata_editor: XML parser, property panel, validation, export"
    status: cancelled
  - id: add-2da-support
    content: "Add 2DA file support: Import/export operators, CSV conversion, property panel for editing"
    status: cancelled
  - id: add-are-editor
    content: "Add ARE file editor: GFF-based, property panel, integration with LYT and minimap"
    status: cancelled
  - id: add-git-support
    content: "Add GIT file support: 3D visualization of area objects, gizmo editing, property panels"
    status: cancelled
  - id: add-vis-support
    content: "Add VIS file support: Room connection visualization and editing in 3D viewport"
    status: cancelled
  - id: add-bif-browser
    content: "Add BIF archive browser: Browse/extract resources, integrate with module browser"
    status: cancelled
  - id: add-nss-compiler
    content: "Add NSS → NCS compilation: External compiler integration or PyKotor support"
    status: cancelled
  - id: 3d-area-editing
    content: "Implement 3D area editing workflow: Area edit mode, room visualization, object placement, gizmos"
    status: cancelled
  - id: module-validation
    content: "Implement module validation system: Structure checks, missing files, broken references, validation panel"
    status: cancelled
  - id: enhance-module-browser
    content: "Enhance module browser: Resource previews, advanced search/filter, bulk operations, dependency graph"
    status: cancelled
  - id: holocron-source-audit
    content: When vendor/PyKotor/Tools/HolocronToolset/src/toolset/ is available, audit vs KotorBlender menus/operators; document gaps only (no Qt/toolset imports)
    status: pending
isProject: false
---

# Blender Integration Enhancement Plan

## Overview

This plan identifies gaps between KotorBlender's current capabilities and HolocronToolset's feature set, then proposes enhancements that leverage Blender's 3D environment for better KotOR modding workflows. The focus is on completing stub implementations, adding missing file format support, and creating native Blender workflows for area editing, module management, and resource operations.

## Holocron parity checklist (no vendored toolset required)

Use this when `vendor/PyKotor/Tools/HolocronToolset/src/toolset/` is **not** in the tree. Mirror Holocron **workflows** in Blender using PyKotor wheels only (see repo policy above).

| Holocron-style bucket | KotorBlender surface | Gap / next step |
|----------------------|---------------------|-----------------|
| Install + discovery | Scene → KotOR Game Installation, autodetect | None critical |
| Module list + open | Refresh modules, open module, module browser | Previews / dependency graph still open |
| Resource browser + extract | Tabs, refresh, open/extract, batch + `bulk_select` in `KB_UL_resources` | Deep link “jump to resref” |
| File search | `kb.file_search` | Optional: search inside `.mod` without extracting |
| Pack / unpack / clone | Pack, unpack, clone + **Module Designer** panel | Clone: in-mod GFF reference rewrite |
| Validation | **`kb.validate_module`** → `last_validation_report` + panel preview | Extend: resref cross-refs, LYT/VIS/GIT consistency |
| 2DA / ARE / GIT / VIS | Adapter: 2DA + VIS helpers; scene props scaffold | Operators + import empties workflow |
| Area / indoor editor | `kotor_area_edit_active`, Indoor Map stub | GizmoGroup + GIT import |
| Diff / patch | KotorDiff, TSLPatchData stubs | Subprocess to `kotordiff` or text diff |
| NSS | Edit in Text Editor | NCS: external compiler pref |

---

## Repo sync (build checkpoint)

**Checked:** 2026-03-20 (workspace); **2026-03-20b** — `kb.validate_module`, plan parity table

| Item | Status |
|------|--------|
| `vendor/PyKotor/Tools/HolocronToolset/src/toolset/` | **Not present** in this clone — use junction to PyKotor monorepo for read-only audit (see todo `holocron-source-audit` in frontmatter). |
| `KB_OT_file_search` | **Implemented** — walks install subdirs, fills `resource_list` ([file_search.py](../io_scene_kotor/ops/tools/file_search.py)). |
| [pykotor_adapter.py](../io_scene_kotor/vendor/pykotor_adapter.py) | Already exposes **ERF/MOD** listing, **BIF** list/get, **2DA** load/save/TSV, **VIS** load/save pairs, install resolution — many Part 2 items can wire UI to these before new parsers. |
| `ScenePropertyGroup` | Already has `pack_source_directory`, `active_bif_path`, `kotor_area_edit_active`, `vis_edges`, `active_twoda_text_name`, `tslpatchdata_*`, `last_validation_report`, etc. ([scene.py](../io_scene_kotor/ui/props/scene.py)). |
| **Module Designer (MVP)** | **Shipped:** `KB_PT_module_designer` — pack/BIF/refresh + **Validate**; `kb.module_designer` opens sidebar ([module_designer.py](../io_scene_kotor/ui/panel/module_designer.py)). **`kb.validate_module`** writes `last_validation_report` ([validate_module.py](../io_scene_kotor/ops/module/validate_module.py)). Next: ERF tree UI, reference rewriting on clone. |

### PyKotor adapter → plan phase map (quick reference)

- **Phase 1 stubs:** File search done; clone/pack/unpack exist — focus **KotorDiff**, **TSLPatchData** UI, **Indoor Map** gizmo poll on `kotor_area_edit_active`.
- **Phase 2 formats:** Prefer `load_twoda_file` / `save_twoda_file` / `twoda_to_tsv_string` for 2DA; `load_vis_visibility_pairs` / `save_vis_visibility_pairs` for VIS; GFF stack for ARE/GIT; `try_list_bif_resources` for BIF tab (path UI now on Module Designer panel).
- **Phase 3:** Module validation should write `kb.last_validation_report` (panel already previews first lines).

---

## Enhancement Summary

**Deepened on:** 2026-03-20 (follow-up: Holocron parity table + `kb.validate_module` implementation)  
**Sections enhanced:** Holocron alignment policy, Parts 1–3 (per-section research notes), cross-cutting technical risks, success criteria, references, **Repo sync**, **Holocron parity checklist (source-agnostic)**  
**Research inputs:** Blender 4.2 `GizmoGroup` / `UIList` API patterns; repo policy from [.cursor/plans/remove_pykotor_mdl_usage_and_align_with_toolset_ideas_f67938ca.plan.md](remove_pykotor_mdl_usage_and_align_with_toolset_ideas_f67938ca.plan.md); prior gap analysis (formats, stubs, module browser)

### Key improvements added by deepening

1. **Explicit HolocronToolset boundary** — Parity with Holocron is achieved by **PyKotor library APIs + Blender operators/panels** in `io_scene_kotor`, not by importing or embedding HolocronToolset (Qt) code. When `vendor/PyKotor/Tools/HolocronToolset/src/toolset/` is missing, use a local PyKotor checkout or upstream repo for **read-only** feature audit.
2. **Blender-first UX patterns** — Prefer `GizmoGroup.poll/setup/refresh`, keep `Panel.draw()` free of filesystem scans, use addon preferences for external tool paths; avoid claiming a custom Object Mode unless using a real workspace/mode workflow.
3. **De-risked scope** — NSS→NCS and heavy previews are called out for path validation, licensing of bundled compilers, and main-thread Blender API constraints.

### New considerations discovered

- **Threading:** Blender’s Python API is not thread-safe; long I/O should use Blender’s progress API (`wm.progress_begin` / `progress_update` / `progress_end`) or modal operators with timed steps—not background threads mutating `bpy.data`.
- **VIS / LYT coupling:** Room graphs depend on consistent naming between LYT, VIS, and module resources; editing one without the others can produce engine-invalid areas—validation (Part 3.2) should cross-check.
- **2DA editing:** Community workflow is often CSV round-trip; a full in-Blender grid is high effort—phase CSV import/export before a spreadsheet-style UI.
- **KotorDiff / external diff:** Launching `meld`/`kdiff3` via `subprocess` is simpler than a custom side-by-side panel; still validate paths (see PyKotor path-safety patterns in upstream docs).

---

## HolocronToolset reference path and repository policy

**Path:** `vendor/PyKotor/Tools/HolocronToolset/src/toolset/` (optional; may be absent until vendored or junctioned to the PyKotor monorepo.)

**Policy (must not regress):**

- **Do not** add runtime imports from HolocronToolset packages or ship Holocron Qt UI inside the Blender extension.
- **Do** use HolocronToolset (when available on disk) as a **behavioral checklist**: which resource types, dialogs, and workflows users expect; then reimplement using [io_scene_kotor/vendor/pykotor_adapter.py](io_scene_kotor/vendor/pykotor_adapter.py) and PyKotor wheels per [io_scene_kotor/blender_manifest.toml](io_scene_kotor/blender_manifest.toml).
- **MDL pipeline** remains native `format/mdl` + `io/mdl` (no PyKotor MDL load/save in IO); new features should not reintroduce PyKotor MDL in `load_mdl`/`save_mdl`.

**Audit checklist when toolset source is available:**

- Map Holocron “installation / module / resource browser / extract / editors” flows to existing `KB_PT`** / `KB_OT`**; note any format or action still missing in Blender.
- Skim toolset **resource type registry** (or equivalent) for GFF/2DA/BIF/NSS workflows not yet exposed in `Editor > KotOR`.
- Record **non-goals**: e.g. full Qt PropertyEditor parity inside Blender in one release—ship incremental panels + operators instead.

---

## Current State Analysis

### Completed Features

- ✅ Game installation browser (`KB_PT_game_installation`)
- ✅ Module browser panel (`KB_PT_module_browser`)
- ✅ Resource creation operators (14 types: UTC, UTP, UTD, etc.)
- ✅ Resource property panels (10 panels)
- ✅ Resource editor operators (14 types)
- ✅ Module operations (pack/unpack, extract, batch extract)
- ✅ Texture operations (convert, extract)
- ✅ Save game operations
- ✅ Menu system with submenus

### Stub Operators (Need Implementation)

- `KB_OT_module_designer` — **Operator** now opens the sidebar; **panel** `KB_PT_module_designer` holds pack/BIF/validation preview (tree/deps still TODO).
- `KB_OT_indoor_map_builder` - Reports "coming in a future release"
- `KB_OT_file_search` — **Implemented** (install walk + fill resource list)
- `KB_OT_clone_module` — **File-level clone** of selected `.mod` exists; **GFF reference rename** inside module still TODO
- `KB_OT_kotor_diff` - Reports "not yet implemented"
- `KB_OT_tslpatchdata_editor` - Reports "Editor UI coming in a future release"

### Missing File Format Support

- **2DA files** - No support (HolocronToolset has 2DA editor with CSV conversion)
- **ARE files** - No editor (only minimap rendering exists)
- **GIT files** - No support (area instance placement)
- **VIS files** - No support (room visibility connections)
- **BIF archives** - No browser/extractor (mentioned in docs but not implemented)
- **NCS compilation** - No NSS → NCS compiler

### Missing Workflows

- **3D area editing** - No interactive placement of area objects in viewport
- **Module validation** - No validation of module structure/consistency
- **Resource dependency tracking** - No visualization of resource dependencies
- **Enhanced module browser** - No previews, advanced search, or bulk operations

---

## Part 1: Complete Stub Operator Implementations

### 1.1 File Search Operator

**File**: `io_scene_kotor/ops/tools/file_search.py`

**Implementation**:

- Create a Blender popup dialog or panel for file search
- Use PyKotor's `BinaryReader` and path utilities to search game installation
- Search across: modules, override, core, textures, saves
- Filter by resource type, name pattern, or file extension
- Display results in a list with "Open" and "Extract" buttons
- Integrate with module browser panel

**UI Options**:

- Option A: Popup dialog with search field and results list
- Option B: Dedicated panel in 3D Viewport sidebar (recommended)
- Option C: Add search field to existing module browser panel

**Dependencies**: PyKotor adapter, game installation preferences

---

### 1.2 Module Designer

**File**: `io_scene_kotor/ops/tools/module_designer.py`

**Implementation**:

- Create a unified Module Designer workspace panel
- Features:
  - Module structure tree view (ERF/RIM contents)
  - Resource dependency visualization
  - Batch operations panel (extract, convert, delete)
  - Module validation dashboard
  - Resource preview thumbnails (TPC, MDL)
- Panel location: 3D Viewport sidebar or Properties Editor (Scene context)

**UI Structure**:

```
Module Designer Panel:
├── Module Selector (dropdown)
├── Structure Tree (outliner-style)
│   ├── Resources (grouped by type)
│   └── Dependencies (graph view)
├── Batch Operations
│   ├── Extract Selected
│   ├── Convert Selected
│   └── Delete Selected
└── Validation Status
    ├── Missing Files
    ├── Broken References
    └── Format Checks
```

**Dependencies**: PyKotor adapter, module browser infrastructure

---

### 1.3 Indoor Map Builder

**File**: `io_scene_kotor/ops/tools/indoor_map_builder.py`

**Implementation**:

- Create a 3D viewport mode for area editing
- Features:
  - Visual room placement (drag-and-drop from LYT)
  - Room connection editor (VIS file visualization)
  - Area object placement (placeables, doors, triggers, waypoints)
  - Real-time walkmesh preview overlay
  - Snapping to grid/room boundaries
- Use Blender's `gizmo` system for interactive placement
- Integrate with LYT import/export

**UI Components**:

- Toggle button in 3D Viewport header: "KotOR Area Edit Mode"
- Property panel for area object properties
- Gizmo handles for moving/rotating area objects
- Overlay for room boundaries and connections

**Dependencies**: LYT import/export, GIT file support (Part 2.3)

---

### 1.4 Clone Module Operator

**File**: `io_scene_kotor/ops/tools/clone_module.py`

**Implementation**:

- Copy entire module (ERF/RIM) to new location
- Rename all internal references (module name, resource paths)
- Update GFF files that reference the module
- Create new module entry in module list
- Use PyKotor's module utilities

**UI**:

- File browser dialog for destination
- Progress bar for large modules
- Option to rename module during clone

**Dependencies**: PyKotor adapter, module operations

---

### 1.5 KotorDiff Operator

**File**: `io_scene_kotor/ops/tools/kotor_diff.py`

**Implementation**:

- Compare two modules or resource files
- Display differences in a Blender text editor or custom panel
- Support formats: GFF, TLK, 2DA, ERF structure
- Highlight added/removed/modified entries
- Export diff report to text file

**UI Options**:

- Option A: Blender Text Editor with syntax highlighting
- Option B: Custom panel with side-by-side comparison
- Option C: External diff tool integration (meld, kdiff3)

**Dependencies**: PyKotor adapter, file comparison utilities

---

### 1.6 TSLPatchData Editor

**File**: `io_scene_kotor/ops/tools/tslpatchdata_editor.py`

**Implementation**:

- Parse TSLPatchData XML format
- Property panel for editing patch entries
- Validate patch structure
- Preview patch effects (what files will be modified)
- Export modified patch file

**UI**:

- Property panel in Properties Editor
- List of patch entries with expand/collapse
- Entry editor (file path, operation, data)

**Dependencies**: XML parsing (Python stdlib), PyKotor adapter

### Research Insights (Part 1: Stub operators)

**Best practices**

- **Dialogs vs sidebars:** Operators that need a query (`file_search`) should use `invoke_props_dialog` or a **sidebar panel** that writes results into `Scene.kb` (or a dedicated `bpy.types.PropertyGroup`) so users can act on results without closing a modal—matches existing [module_browser.py](io_scene_kotor/ui/panel/module_browser.py) patterns.
- **External tools:** For KotorDiff, prefer **subprocess** to `kotordiff` CLI or system diff tools with paths constrained under game/install roots; never pass unsanitized user strings to shell=True.
- **Module Designer scope:** Ship a **minimal viable panel** first (module tree + extract + validate summary) before dependency graphs and thumbnails—avoid blocking Part 1 on GPU preview work.

**Performance / UX**

- Clone/pack/unpack on large RIMs: use **progress reporting** and optional cancellation via modal operator; avoid freezing the UI thread.

**Edge cases**

- PyKotor unavailable: stub operators already gate on `is_pykotor_available()`—extended features should **degrade gracefully** (greyed UI + clear `poll` messages), consistent with [AGENTS.md](AGENTS.md).

---

## Part 2: Missing File Format Support

### 2.1 2DA File Support

**Files**:

- `io_scene_kotor/format/2da/reader.py` (new)
- `io_scene_kotor/format/2da/writer.py` (new)
- `io_scene_kotor/format/2da/types.py` (new)
- `io_scene_kotor/ops/2da/importop.py` (new)
- `io_scene_kotor/ops/2da/export.py` (new)
- `io_scene_kotor/ui/panel/2da.py` (new)

**Implementation**:

- Parse 2DA binary format (or use PyKotor's 2DA reader)
- Import 2DA as Blender spreadsheet or text datablock
- Export from spreadsheet/text back to 2DA
- CSV conversion option (import CSV → 2DA, export 2DA → CSV)
- Property panel for editing 2DA entries

**UI**:

- Import/Export operators in File menu
- Property panel showing 2DA structure (rows/columns)
- Table view in Blender (use `bpy.types.UIList` or spreadsheet addon if available)

**Dependencies**: PyKotor 2DA support or custom parser

---

### 2.2 ARE File Editor

**Files**:

- `io_scene_kotor/format/are/reader.py` (new) - Use PyKotor or GFF reader
- `io_scene_kotor/format/are/writer.py` (new)
- `io_scene_kotor/ops/are/importop.py` (new)
- `io_scene_kotor/ops/are/export.py` (new)
- `io_scene_kotor/ui/panel/are.py` (new)

**Implementation**:

- ARE files are GFF format (use existing GFF reader)
- Property panel for area properties:
  - Area name, tag, resref
  - Minimap coordinates (already supported via minimap render)
  - Area flags, scripts, events
  - Weather, lighting, ambient sound
- Integrate with LYT import (area layout)
- Link ARE editor to Indoor Map Builder (Part 1.3)

**UI**:

- Import/Export operators
- Property panel in Properties Editor (Scene context when ARE loaded)
- Link to minimap render operator

**Dependencies**: GFF reader, LYT import, minimap render

---

### 2.3 GIT File Editor

**Files**:

- `io_scene_kotor/format/git/reader.py` (new) - Use PyKotor or GFF reader
- `io_scene_kotor/format/git/writer.py` (new)
- `io_scene_kotor/ops/git/importop.py` (new)
- `io_scene_kotor/ops/git/export.py` (new)
- `io_scene_kotor/ui/panel/git.py` (new)

**Implementation**:

- GIT files are GFF format (area instance data)
- 3D viewport visualization of area objects:
  - Placeables (UTP) - show as empty objects with icons
  - Doors (UTD) - show as planes with connection lines
  - Triggers (UTT) - show as wireframe boxes
  - Waypoints (UTW) - show as spheres
  - Encounters (UTE) - show as groups
- Property panel for selected area object
- Gizmo-based editing (move, rotate, scale)
- Link to Indoor Map Builder (Part 1.3)

**UI**:

- Import/Export operators
- 3D viewport overlay showing area objects
- Property panel for selected area object
- Toggle visibility per object type

**Dependencies**: GFF reader, Indoor Map Builder, 3D gizmo system

---

### 2.4 VIS File Support

**Files**:

- `io_scene_kotor/format/vis/reader.py` (new)
- `io_scene_kotor/format/vis/writer.py` (new)
- `io_scene_kotor/ops/vis/importop.py` (new)
- `io_scene_kotor/ops/vis/export.py` (new)

**Implementation**:

- Parse VIS binary format (room visibility connections)
- Visualize room connections in 3D viewport
- Edit connections (add/remove room links)
- Export modified VIS file
- Integrate with LYT import (room layout)

**UI**:

- Import/Export operators
- 3D viewport overlay showing room connections (lines between rooms)
- Property panel for room visibility settings

**Dependencies**: LYT import, VIS format parser

---

### 2.5 BIF Archive Browser

**Files**:

- `io_scene_kotor/ops/bif/browse.py` (new)
- `io_scene_kotor/ops/bif/extract.py` (new)
- `io_scene_kotor/ui/panel/bif_browser.py` (new)

**Implementation**:

- Browse BIF archive contents (use PyKotor's BIF reader)
- List resources in BIF
- Extract resources from BIF
- Search BIF contents
- Integrate with module browser (add BIF as a source)

**UI**:

- Panel in 3D Viewport sidebar or Properties Editor
- File browser to select BIF file
- Resource list with extract buttons
- Search field

**Dependencies**: PyKotor BIF support

---

### 2.6 NSS → NCS Compilation

**Files**:

- `io_scene_kotor/ops/nss/compile.py` (new)
- `io_scene_kotor/ui/panel/nss_compiler.py` (new)

**Implementation**:

- Compile NSS script to NCS bytecode
- Options:
  - Option A: Use external compiler (nwnnsscomp.exe) via subprocess
  - Option B: Use PyKotor's NSS compiler (if available)
  - Option C: Python-based NSS parser → NCS generator
- Validate NSS syntax before compilation
- Show compilation errors in Blender console/panel

**UI**:

- Operator: "Compile NSS to NCS" in Editor → KotOR → Tools
- Property panel for compiler settings (compiler path, flags)
- Error display in panel or console

**Dependencies**: External compiler or PyKotor NSS support

### Research Insights (Part 2: Formats)

**Best practices**

- **Reuse GFF stack:** ARE/GIT are GFF instances—implement via existing [format/gff](io_scene_kotor/format/gff/) and [io_scene_kotor/io](io_scene_kotor/io/) patterns instead of parallel parsers; map structs ↔ Blender custom properties on empties or a single scene-level datablock.
- **2DA:** Start with **import as Text datablock or CSV-friendly intermediate** before investing in `UIList` row editors; validate column counts and row keys on export.
- **BIF:** Treat as **read-only browse/extract** in v1; writing BIFs is rarely needed for Blender-centric art workflows.

**Pitfalls**

- **VIS:** Confirm binary vs text variants and game-specific quirks before committing to a single `format/vis` layout; add round-trip tests with small fixtures in `test/blender/` or `test/unit/` when fixtures exist.
- **NCS:** Bundling `nwnnsscomp.exe` raises **GPL + redistribution** questions; prefer addon preference “path to compiler” with user-supplied binary, or document PyKotor compile API if upstream exposes it without extra binaries.

**Testing**

- Add focused round-trip tests for each new format (similar to [test_gff_io.py](test/blender/test_gff_io.py)) to keep CI honest without `DATA_DIR`.

---

## Part 3: Enhanced Blender Integration

### 3.1 3D Area Editing Workflow

**Goal**: Enable visual editing of area layouts and area objects directly in Blender's 3D viewport.

**Components**:

#### 3.1.1 Area Edit Mode Toggle

- Add mode selector in 3D Viewport header: "Object Mode" → "KotOR Area Edit Mode"
- When active, show area-specific gizmos and overlays
- Disable normal Blender object manipulation (or make it optional)

#### 3.1.2 Room Visualization

- Import LYT → create empty objects for each room
- Draw room boundaries as wireframe boxes
- Show room names as text overlays
- Color-code rooms by type (indoor/outdoor)

#### 3.1.3 Area Object Placement

- Import GIT → create Blender objects for placeables, doors, triggers, waypoints
- Use custom icons/empties to represent each type
- Gizmo handles for moving/rotating objects
- Property panel updates when object selected
- Export GIT when changes made

#### 3.1.4 Room Connection Visualization

- Import VIS → draw lines between connected rooms
- Interactive connection editor (click to add/remove connections)
- Export VIS when connections modified

**Files to Create/Modify**:

- `io_scene_kotor/ops/area/edit_mode.py` (new) - Toggle area edit mode
- `io_scene_kotor/ui/gizmo/area_object.py` (new) - Gizmo for area objects
- `io_scene_kotor/ui/overlay/area.py` (new) - 3D viewport overlay
- Modify `io_scene_kotor/ops/lyt/importop.py` - Add room object creation
- Modify `io_scene_kotor/ops/git/importop.py` - Add area object creation

**Dependencies**: LYT import, GIT support (Part 2.3), VIS support (Part 2.4)

---

### 3.2 Module Validation System

**Files**:

- `io_scene_kotor/ops/module/validate.py` (new)
- `io_scene_kotor/ui/panel/module_validation.py` (new)

**Implementation**:

- Validate module structure:
  - Check for missing files (referenced but not present)
  - Verify file formats (corrupt files)
  - Check resource references (broken links)
  - Validate GFF structure
  - Check texture paths
- Display validation results in panel
- Export validation report to text file
- Auto-fix common issues (optional)

**UI**:

- Operator: "Validate Module" in Editor → KotOR → Modules
- Panel showing validation results:
  - Errors (red)
  - Warnings (yellow)
  - Info (blue)
- "Fix Selected Issues" button (for auto-fixable problems)

**Dependencies**: PyKotor adapter, module operations

---

### 3.3 Enhanced Module Browser

**Current**: Basic resource listing with tabs

**Enhancements**:

#### 3.3.1 Resource Previews

- TPC thumbnails (use Blender's image preview system)
- MDL preview (render small viewport snapshot)
- Generic file icon for other types

#### 3.3.2 Advanced Search/Filter

- Search by resource name (real-time filtering)
- Filter by resource type (multi-select)
- Filter by module location (Core, Modules, Override)
- Filter by file size or date

#### 3.3.3 Bulk Operations

- Multi-select resources (Ctrl+Click)
- Batch extract selected
- Batch convert selected (TPC → TGA, etc.)
- Batch delete selected (with confirmation)

#### 3.3.4 Resource Dependency Graph

- Visualize resource dependencies (which resources reference others)
- Show dependency tree/graph
- Highlight missing dependencies
- Navigate to dependent resources

**Files to Modify**:

- `io_scene_kotor/ui/panel/module_browser.py` - Add search, filters, bulk ops
- `io_scene_kotor/ui/list/resources.py` - Add multi-select, previews
- `io_scene_kotor/ops/module/show_dependencies.py` (new) - Dependency visualization

**Dependencies**: Module browser infrastructure, PyKotor adapter

---

### 3.4 Context-Sensitive Property Panels

**Enhancement**: Show relevant KotOR property panels based on selected object type.

**Implementation**:

- Detect object type from `kb` custom property or `dummytype`
- Automatically expand relevant property panel
- Add visual indicators in 3D viewport (icons, overlays)
- Quick-edit popups for common properties

**Files to Modify**:

- All resource property panels - Add `poll()` methods for context detection
- `io_scene_kotor/ui/overlay/object_indicators.py` (new) - 3D viewport indicators

---

### 3.5 Timeline/Sequencing Editor

**Goal**: Add timeline editor for area events, cutscenes, and scripted sequences.

**Implementation**:

- Use Blender's Timeline editor or create custom panel
- Timeline tracks for:
  - Area scripts (OnEnter, OnExit, OnHeartbeat)
  - Cutscene sequences
  - Dialog triggers
  - Animation events
- Keyframe-based editing
- Export to GFF/script format

**Files**:

- `io_scene_kotor/ui/panel/timeline.py` (new)
- `io_scene_kotor/ops/timeline/add_event.py` (new)
- `io_scene_kotor/ops/timeline/export_sequence.py` (new)

**Dependencies**: ARE editor, script compilation

### Research Insights (Part 3: Blender integration)

**Gizmos (Blender 4.2 API)**

- Use `bpy.types.GizmoGroup` with `**bl_space_type = 'VIEW_3D'`**, correct `bl_region_type` (often `WINDOW`), and `bl_options` including `'3D'`, `'SELECT'`, `'DEPTH_3D'` where interaction is needed.
- Implement `**poll**` to show gizmos only when a KotOR “area edit” context is active (e.g. scene flag or collection); use `**setup**` to create gizmos once and `**refresh**` to sync transforms—avoid recreating gizmos every redraw ([GizmoGroup](https://docs.blender.org/api/4.2/bpy.types.GizmoGroup.html)).
- **Do not** replace Blender’s Object Mode with a fake mode name; prefer a **boolean scene property**, workspace, or operator-driven overlay so tutorials and keymaps stay understandable.

**UIList / module browser**

- `**draw()` must stay cheap:** no directory walks or PyKotor archive opens per redraw; cache module listings on `refresh_modules` / operator invoke and store serialized names on `Scene.kb` (existing pattern).
- **Previews:** `layout.template_preview()` / icon IDs require image loading—**lazy-load** and cap concurrent thumbnails; MDL snapshots are expensive—defer to Phase 3+ or optional dependency.

**Overlays**

- `GPU` module drawing for room graphs is powerful but version-sensitive; gate features behind Blender version checks and fall back to **curve/line objects** in the scene for older LTS if needed.

**Accessibility**

- Every new gizmo or overlay must keep **menu-exposed operators** with `bl_description` for the same actions (per [AGENTS.md](AGENTS.md) accessibility notes).

---

## Part 4: Implementation Phases

### Phase 1: Foundation (Weeks 1-2)

1. Complete stub operators (File Search, Clone Module, KotorDiff)
2. Add 2DA file support (import/export, CSV conversion)
3. Implement module validation system

### Phase 2: Area Editing (Weeks 3-4)

1. Add ARE file editor
2. Add GIT file support with 3D visualization
3. Add VIS file support
4. Implement Indoor Map Builder (3D area editing)

### Phase 3: Enhanced Workflows (Weeks 5-6)

1. Complete Module Designer panel
2. Enhance module browser (previews, search, bulk ops)
3. Add BIF archive browser
4. Implement NSS → NCS compilation

### Phase 4: Advanced Features (Weeks 7-8)

1. Complete TSLPatchData editor
2. Add resource dependency visualization
3. Implement timeline/sequencing editor
4. Context-sensitive property panels

### Research Insights (Part 4: Phasing)

- **Reorder if needed:** If module browser enhancements unblock many workflows, consider moving **3.3 Enhanced Module Browser** earlier (e.g. late Phase 1) so search/filter benefits land before heavy GIT/VIS work.
- **Vertical slices:** Prefer one complete flow (e.g. GIT import → move empties → export) over parallel half-finished format writers—reduces invalid intermediate states.
- **Milestone demos:** After each phase, record a short checklist (import LYT, place object, export) for manual QA without full game `DATA_DIR`.

---

## Technical Considerations

### PyKotor Integration

- Leverage PyKotor adapter (`io_scene_kotor/vendor/pykotor_adapter.py`)
- Use PyKotor for format reading where available (2DA, GFF, BIF)
- Maintain compatibility when PyKotor unavailable (graceful fallback)
- **Do not** route MDL load/save through PyKotor in `io/mdl.py` (see [remove_pykotor_mdl_usage plan](remove_pykotor_mdl_usage_and_align_with_toolset_ideas_f67938ca.plan.md)); new features should respect that split.

### Blender API Usage

- Use `bpy.types.Gizmo` / `GizmoGroup` for interactive 3D editing (see Part 3 research notes)
- Use `bpy.types.UIList` for resource lists; keep `draw_item` lightweight
- Use `bpy.types.OperatorFileListElement` for file browsers where appropriate
- Follow Blender 4.x patterns; test on **3.6 LTS and 4.2 LTS** at minimum ([AGENTS.md](AGENTS.md))

### Performance and threading

- Lazy-load resource previews (generate on demand)
- Cache module structure (don't re-scan on every panel draw)
- **Avoid Python background threads** that touch `bpy.data`; for long tasks use modal operators, progress bars, or chunked work on the main thread
- If truly asynchronous I/O is needed, use a pattern that **defers bpy mutations** to a main-thread timer—document any exception in code comments

### Security and paths

- Resolve all user-selected paths under allowed roots (game dir, module dir, output dir); align with PyKotor **path_safety** guidance when using upstream APIs
- Subprocess calls (compiler, diff, optional CLI): list arguments, no shell injection, validate executable path exists

### Testing

- Unit tests for format readers/writers (no Blender where possible)
- Blender background tests for operators (`test/blender/test_*.py` pattern)
- E2E tests for workflows only where `DATA_DIR` or bundled fixtures exist; otherwise skip gracefully per [AGENTS.md](AGENTS.md)

---

## Success Criteria (target state)

1. Stub operators either **implemented** or **intentionally scoped** with updated `bl_description` and docs (no misleading “coming soon” where shipping is not planned)
2. **Priority formats** available with clear read/write matrix: 2DA, ARE, GIT, VIS, BIF browse/extract—as far as agreed per phase
3. **Area workflow:** import LYT/GIT/VIS → edit in viewport → export without silent data loss; validation reports mismatches
4. **Module validation** produces actionable messages (missing resrefs, broken texture paths, invalid GFF)
5. **Module browser:** search/filter and optional previews without UI stalls
6. **NSS → NCS:** documented path (user compiler or supported API) and operator reports errors verbatim
7. All user-facing actions remain reachable from **menus** (and optional keymaps only as extras)
8. **AGENTS.md** / **README.md** updated for new formats, external tools, and PyKotor requirements

---

## References

- [Blender 4.2 GizmoGroup API](https://docs.blender.org/api/4.2/bpy.types.GizmoGroup.html)
- [Blender 4.2 UIList](https://docs.blender.org/api/4.2/bpy.types.UIList.html)
- PyKotor repository: [https://github.com/NickHugi/PyKotor](https://github.com/NickHugi/PyKotor)
- HolocronToolset source (optional audit): `vendor/PyKotor/Tools/HolocronToolset/src/toolset/` — **reference only**, no runtime dependency
- Prior UI expansion plan: [.cursor/plans/pykotor_integration_and_ui_expansion_91971bed.plan.md](pykotor_integration_and_ui_expansion_91971bed.plan.md)
- Policy: Holocron as ideas only + no PyKotor MDL in IO: [.cursor/plans/remove_pykotor_mdl_usage_and_align_with_toolset_ideas_f67938ca.plan.md](remove_pykotor_mdl_usage_and_align_with_toolset_ideas_f67938ca.plan.md)
- KotorBlender architecture / operator stubs note: [AGENTS.md](../AGENTS.md)

