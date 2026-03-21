---
name: PyKotor Integration and UI Expansion
overview: Add PyKotor as a dependency and expand Blender UI with Holocron Toolset-inspired features including game installation browser, module selector, and many additional operators/panels throughout the interface.
todos:
  - id: pykotor-deps
    content: "Add PyKotor dependency: Create pyproject.toml for dev, update blender_manifest.toml with wheels array, add wheel bundling to Makefile"
    status: completed
  - id: pykotor-adapter
    content: "Create PyKotor adapter layer: io_scene_kotor/vendor/pykotor_adapter.py to wrap PyKotor APIs for io/ layer compatibility"
    status: completed
  - id: game-installation-panel
    content: "Create game installation panel: KB_PT_game_installation in Properties Editor (Scene context) with game selector, path browser, module list"
    status: completed
  - id: module-browser-panel
    content: "Create module browser panel: KB_PT_module_browser in 3D viewport sidebar with resource tabs, resource list, open/extract buttons"
    status: completed
  - id: resource-creation-ops
    content: "Create resource creation operators: KB_OT_new_utc, KB_OT_new_utp, KB_OT_new_utd, KB_OT_new_uti, KB_OT_new_uts, KB_OT_new_utt, KB_OT_new_utm, KB_OT_new_utw, KB_OT_new_ute, KB_OT_new_dlg, KB_OT_new_nss, KB_OT_new_tlk, KB_OT_new_erf, KB_OT_new_gff"
    status: completed
  - id: tool-operators
    content: "Create tool operators: KB_OT_module_designer, KB_OT_indoor_map_builder, KB_OT_file_search, KB_OT_clone_module, KB_OT_kotor_diff, KB_OT_tslpatchdata_editor"
    status: completed
  - id: editor-operators
    content: "Create editor operators: KB_OT_edit_tlk, KB_OT_edit_jrl, and editors for all resource types (UTC, UTP, UTD, UTI, UTS, UTT, UTM, UTW, UTE, DLG, NSS, ERF, GFF)"
    status: completed
  - id: resource-panels
    content: "Create resource property panels: KB_PT_creature, KB_PT_placeable, KB_PT_door, KB_PT_item, KB_PT_sound, KB_PT_trigger, KB_PT_merchant, KB_PT_waypoint, KB_PT_encounter, KB_PT_dialog"
    status: completed
  - id: expand-menus
    content: "Expand menu system: Add KB_MT_kotor_game, KB_MT_kotor_module, KB_MT_kotor_resources, KB_MT_kotor_tools, KB_MT_kotor_editors submenus, add File menu items for module/save import"
    status: completed
  - id: module-operations
    content: "Create module operations: KB_OT_open_module, KB_OT_refresh_modules, KB_OT_extract_resource, KB_OT_extract_tpc, KB_OT_extract_mdl_textures, KB_OT_pack_module, KB_OT_unpack_module"
    status: completed
  - id: texture-operations
    content: "Create texture operations: KB_OT_convert_tpc_to_tga, KB_OT_convert_tga_to_tpc, KB_OT_extract_tpc_textures, KB_OT_batch_convert_textures"
    status: completed
  - id: expand-showhide
    content: "Expand show/hide menu: Add operators for characters, placeables, doors, items, triggers, waypoints"
    status: completed
  - id: save-operations
    content: "Create save game operations: KB_OT_open_save_editor, KB_OT_extract_save, KB_PT_save_game panel"
    status: completed
  - id: pykotor-migration
    content: "Migrate format readers: Replace MDL reader with PyKotor, replace TPC reader with PyKotor, replace GFF reader with PyKotor, test round-trip compatibility"
    status: cancelled
  - id: register-all
    content: "Register all new classes: Update io_scene_kotor/__init__.py to register all new operators, panels, menus, property groups"
    status: completed
  - id: update-docs
    content: "Update documentation: Update AGENTS.md with PyKotor dependency info, add user guide for new features, update README.md"
    status: completed
  - id: context-menus
    content: "Menu integration: Add KotOR context menu draw to VIEW3D_MT_object_context_menu and OUTLINER_MT_context_menu (poll by kb/dummytype)"
    status: completed
  - id: header-menus
    content: "Menu integration: Add KotOR header draw to VIEW3D_HT_header (optional OUTLINER_HT_header, PROPERTIES_HT_header); optional VIEW3D_MT_editor_menus"
    status: completed
  - id: nss-text-editor
    content: "NSS editing: Edit NSS operator creates/opens text datablock and opens in Blender Text Editor; optional external editor + reload"
    status: completed
  - id: optional-keymaps
    content: "Optional: Register addon keymaps for 2-3 high-frequency KotOR operators via keyconfigs.addon; document in AGENTS.md"
    status: completed
isProject: false
---

## Enhancement Summary

**Deepened on:** 2026-03-20  
**Sections enhanced:** Part 3 (UI Expansion), new Part 3.10 (Additional Menu Integration), Part 9 (Research Insights).  
**Research agents used:** best-practices-researcher (Blender 4.x addon menus, context menus, headers, keymaps, area/NSS/DLG workflows).

### Key Improvements

1. **Additional menu integration** — Context menus (3D View + Outliner), header menus (3D View, optional Outliner/Properties), optional 3D View topbar duplicate, area/module editing workflows, NSS in Text Editor, optional addon keymaps.
2. **Best-practices grounding** — All new UI entry points use Blender 4.x API (append/remove draw, poll by `kb`/`dummytype`, `keyconfigs.addon` only, cheap header draw).
3. **Accessibility preserved** — Keymaps optional; all actions remain menu-reachable and keyboard-accessible; clear labels/descriptions.

### New Considerations Discovered

- Use operator `poll()` for context menu visibility; single draw function + separator.
- Header draw must be cheap (no file I/O); conditional draw based on `getattr(obj, "kb", None)`.
- NSS: text datablock + Text Editor + optional external editor with Blender reload.
- Store `(km, kmi)` for keymap cleanup; check `keyconfigs.addon is None` in background mode.

---

# PyKotor Integration and UI Expansion Plan

## Overview

This plan covers two major enhancements:

1. **PyKotor Dependency Integration**: Add PyKotor as a dependency and begin replacing `io_scene_kotor/format/` code with PyKotor equivalents where possible
2. **UI Expansion**: Add extensive UI elements inspired by Holocron Toolset, including game installation browser, module selector, and many additional buttons/panels throughout Blender

## Part 1: PyKotor Dependency Management

### Current State

- No `pyproject.toml` exists (AGENTS.md notes this is intentional)
- `requirements-dev.txt` only has dev dependencies (fake-bpy-module, pytest, ruff)
- Extension uses `blender_manifest.toml` for metadata
- Pure Python extension with no runtime dependencies

### Approach: Dual Dependency Management

**Option A: Blender Extension Wheels (Recommended for Distribution)**

- Add `wheels` array to `blender_manifest.toml`
- Bundle PyKotor wheel in `./wheels/` directory
- Download platform-appropriate wheels:

```bash
  pip wheel pykotor -w ./wheels
  

```

- Update `blender_manifest.toml`:

```toml
  wheels = [
    "./wheels/pykotor-*.whl",
    # Include all PyKotor dependencies
  ]
  

```

**Option B: Development pyproject.toml (For Local Development)**

- Create `pyproject.toml` for development tooling only
- Add PyKotor to `[project.optional-dependencies]` or `[tool.poetry.dependencies]`
- Keep `requirements-dev.txt` for CI compatibility
- Document that runtime uses bundled wheels from manifest

**Implementation Steps:**

1. Create `pyproject.toml` with PyKotor in dev dependencies
2. Update `blender_manifest.toml` with wheels array (if distributing)
3. Add wheel bundling script or Makefile target
4. Update AGENTS.md to document dependency approach
5. Test import: `from pykotor.resource.formats.mdl import read_mdl, write_mdl`

### Files to Modify

- `pyproject.toml` (new file)
- `blender_manifest.toml` (add wheels array)
- `Makefile` (add wheel-download target)
- `AGENTS.md` (update dependency section)

## Part 2: PyKotor Code Replacement

### Replacement Strategy

**Phase 1: Identify Replacement Candidates**

- `io_scene_kotor/format/mdl/reader.py` → `pykotor.resource.formats.mdl.read_mdl()`
- `io_scene_kotor/format/mdl/writer.py` → `pykotor.resource.formats.mdl.write_mdl()`
- `io_scene_kotor/format/gff/reader.py` → PyKotor GFF readers
- `io_scene_kotor/format/tpc/reader.py` → `pykotor.resource.formats.tpc.read_tpc()`
- `io_scene_kotor/format/bwm/reader.py` → PyKotor walkmesh readers

**Phase 2: Create Adapter Layer**

- Create `io_scene_kotor/vendor/pykotor_adapter.py`
- Wrap PyKotor APIs to match existing `io/` layer interface
- Maintain backward compatibility with existing operators
- Example adapter:

```python
  def load_mdl_via_pykotor(filepath: str) -> MDL:
      from pykotor.resource.formats.mdl import read_mdl
      mdl = read_mdl(filepath)
      # Convert PyKotor MDL to io_scene_kotor scene representation
      return convert_pykotor_mdl_to_scene(mdl)
  

```

**Phase 3: Gradual Migration**

- Start with read-only operations (imports)
- Add feature flags to toggle between old/new implementations
- Test round-trip compatibility
- Migrate write operations after read operations are stable

### Files to Create/Modify

- `io_scene_kotor/vendor/pykotor_adapter.py` (new)
- `io_scene_kotor/io/mdl.py` (add PyKotor path with feature flag)
- `io_scene_kotor/io/pth.py` (add PyKotor GFF support)
- `io_scene_kotor/io/tpc.py` (new, using PyKotor)

### Integration Points

- `io_scene_kotor/ops/mdl/importop.py` - Use adapter for imports
- `io_scene_kotor/ops/mdl/export.py` - Use adapter for exports (later phase)
- `io_scene_kotor/scene/model.py` - Add conversion functions

## Part 3: UI Expansion - Holocron Toolset Features

### 3.1 Game Installation Browser

**New Panel: `KB_PT_game_installation`**

- Location: Properties Editor → Scene context
- Features:
  - Game selector dropdown (KotOR 1, KotOR 2, Custom path)
  - Installation path property (with file browser button)
  - Module list (template_list) showing available modules
  - "Open Module" button to load module assets
  - "Refresh Modules" button

**Implementation:**

- `io_scene_kotor/ui/panel/game_installation.py` (new)
- `io_scene_kotor/ui/props/scene.py` (extend ScenePropertyGroup)
- `io_scene_kotor/ops/game/select_installation.py` (new operator)
- `io_scene_kotor/ops/game/refresh_modules.py` (new operator)
- `io_scene_kotor/ops/game/open_module.py` (new operator)

**Dependencies:**

- Use PyKotor's `HTInstallation` or `pykotor.extract.installation` for module discovery

### 3.2 Module Browser Panel

**New Panel: `KB_PT_module_browser`**

- Location: 3D Viewport sidebar (VIEW_3D + UI)
- Features:
  - Module dropdown selector
  - Resource type tabs (Core, Modules, Override, Textures, Saves)
  - Resource list (template_list) with search/filter
  - "Open Selected" button
  - "Extract Selected" button
  - Extract options (TPC decompile, extract TXI, MDL decompile, extract textures)

**Implementation:**

- `io_scene_kotor/ui/panel/module_browser.py` (new)
- `io_scene_kotor/ui/list/resources.py` (new UI list)
- `io_scene_kotor/ops/module/open_resource.py` (new)
- `io_scene_kotor/ops/module/extract_resource.py` (new)
- `io_scene_kotor/ops/module/extract_tpc.py` (new)
- `io_scene_kotor/ops/module/extract_mdl_textures.py` (new)

### 3.3 Extended Menu System

**Expand `KB_MT_kotor` Menu:**

- Add submenus:
  - `KB_MT_kotor_game` - Game installation operations
  - `KB_MT_kotor_module` - Module operations
  - `KB_MT_kotor_resources` - Resource operations
  - `KB_MT_kotor_tools` - Toolset features
  - `KB_MT_kotor_editors` - File editors

**New Menu Items:**

- File → New → KotOR Resources (submenu with UTC, UTP, UTD, UTI, UTS, UTT, UTM, UTW, UTE, DLG, NSS, TLK, etc.)
- Tools → Module Designer
- Tools → Indoor Map Builder
- Tools → File Search
- Tools → Clone Module
- Edit → Edit Talk Table
- Edit → Edit Journal

**Implementation:**

- `io_scene_kotor/ui/menu/kotor.py` (extend with new submenus)
- `io_scene_kotor/ui/menu/resources.py` (new - resource creation menu)
- `io_scene_kotor/ui/menu/tools.py` (new - tools menu)
- `io_scene_kotor/ui/menu/editors.py` (new - editor menu)

### 3.4 Resource Creation Operators

**New Operators for GFF Resource Creation:**

- `KB_OT_new_utc` - Create new Creature (UTC)
- `KB_OT_new_utp` - Create new Placeable (UTP)
- `KB_OT_new_utd` - Create new Door (UTD)
- `KB_OT_new_uti` - Create new Item (UTI)
- `KB_OT_new_uts` - Create new Sound (UTS)
- `KB_OT_new_utt` - Create new Trigger (UTT)
- `KB_OT_new_utm` - Create new Merchant (UTM)
- `KB_OT_new_utw` - Create new Waypoint (UTW)
- `KB_OT_new_ute` - Create new Encounter (UTE)
- `KB_OT_new_dlg` - Create new Dialog (DLG)
- `KB_OT_new_nss` - Create new Script (NSS)
- `KB_OT_new_tlk` - Create new Talk Table (TLK)
- `KB_OT_new_erf` - Create new ERF archive
- `KB_OT_new_gff` - Create new GFF file

**Implementation:**

- `io_scene_kotor/ops/resource/new_utc.py` (new)
- `io_scene_kotor/ops/resource/new_utp.py` (new)
- `io_scene_kotor/ops/resource/new_utd.py` (new)
- `io_scene_kotor/ops/resource/new_uti.py` (new)
- `io_scene_kotor/ops/resource/new_uts.py` (new)
- `io_scene_kotor/ops/resource/new_utt.py` (new)
- `io_scene_kotor/ops/resource/new_utm.py` (new)
- `io_scene_kotor/ops/resource/new_utw.py` (new)
- `io_scene_kotor/ops/resource/new_ute.py` (new)
- `io_scene_kotor/ops/resource/new_dlg.py` (new)
- `io_scene_kotor/ops/resource/new_nss.py` (new)
- `io_scene_kotor/ops/resource/new_tlk.py` (new)
- `io_scene_kotor/ops/resource/new_erf.py` (new)
- `io_scene_kotor/ops/resource/new_gff.py` (new)

**Dependencies:**

- Use PyKotor's GFF creation APIs: `pykotor.resource.formats.gff.write_gff()`

### 3.5 Tool Operators

**New Tool Operators:**

- `KB_OT_module_designer` - Open module designer (external window or Blender panel)
- `KB_OT_indoor_map_builder` - Open indoor map builder
- `KB_OT_file_search` - Search for files in installation
- `KB_OT_clone_module` - Clone existing module
- `KB_OT_kotor_diff` - Compare KotOR files (KotorDiff tool)
- `KB_OT_tslpatchdata_editor` - Edit TSLPatchData files

**Implementation:**

- `io_scene_kotor/ops/tools/module_designer.py` (new)
- `io_scene_kotor/ops/tools/indoor_map_builder.py` (new)
- `io_scene_kotor/ops/tools/file_search.py` (new)
- `io_scene_kotor/ops/tools/clone_module.py` (new)
- `io_scene_kotor/ops/tools/kotor_diff.py` (new)
- `io_scene_kotor/ops/tools/tslpatchdata_editor.py` (new)

### 3.6 Editor Operators

**New Editor Operators:**

- `KB_OT_edit_tlk` - Edit Talk Table
- `KB_OT_edit_jrl` - Edit Journal
- `KB_OT_edit_utc` - Edit Creature
- `KB_OT_edit_utp` - Edit Placeable
- `KB_OT_edit_utd` - Edit Door
- `KB_OT_edit_uti` - Edit Item
- `KB_OT_edit_uts` - Edit Sound
- `KB_OT_edit_utt` - Edit Trigger
- `KB_OT_edit_utm` - Edit Merchant
- `KB_OT_edit_utw` - Edit Waypoint
- `KB_OT_edit_ute` - Edit Encounter
- `KB_OT_edit_dlg` - Edit Dialog
- `KB_OT_edit_nss` - Edit Script
- `KB_OT_edit_erf` - Edit ERF archive
- `KB_OT_edit_gff` - Edit GFF file

**Implementation:**

- `io_scene_kotor/ops/editor/edit_tlk.py` (new)
- `io_scene_kotor/ops/editor/edit_jrl.py` (new)
- `io_scene_kotor/ops/editor/edit_utc.py` (new)
- `io_scene_kotor/ops/editor/edit_utp.py` (new)
- `io_scene_kotor/ops/editor/edit_utd.py` (new)
- `io_scene_kotor/ops/editor/edit_uti.py` (new)
- `io_scene_kotor/ops/editor/edit_uts.py` (new)
- `io_scene_kotor/ops/editor/edit_utt.py` (new)
- `io_scene_kotor/ops/editor/edit_utm.py` (new)
- `io_scene_kotor/ops/editor/edit_utw.py` (new)
- `io_scene_kotor/ops/editor/edit_ute.py` (new)
- `io_scene_kotor/ops/editor/edit_dlg.py` (new)
- `io_scene_kotor/ops/editor/edit_nss.py` (new)
- `io_scene_kotor/ops/editor/edit_erf.py` (new)
- `io_scene_kotor/ops/editor/edit_gff.py` (new)

**Note:** Editors can be simple property panels or full-featured editors. Start with property panels, add full editors later.

### 3.7 Additional Property Panels

**New Panels for Resource Editing:**

- `KB_PT_creature` - Creature (UTC) properties panel
- `KB_PT_placeable` - Placeable (UTP) properties panel
- `KB_PT_door` - Door (UTD) properties panel
- `KB_PT_item` - Item (UTI) properties panel
- `KB_PT_sound` - Sound (UTS) properties panel
- `KB_PT_trigger` - Trigger (UTT) properties panel
- `KB_PT_merchant` - Merchant (UTM) properties panel
- `KB_PT_waypoint` - Waypoint (UTW) properties panel
- `KB_PT_encounter` - Encounter (UTE) properties panel
- `KB_PT_dialog` - Dialog (DLG) properties panel

**Implementation:**

- `io_scene_kotor/ui/panel/resource/creature.py` (new)
- `io_scene_kotor/ui/panel/resource/placeable.py` (new)
- `io_scene_kotor/ui/panel/resource/door.py` (new)
- `io_scene_kotor/ui/panel/resource/item.py` (new)
- `io_scene_kotor/ui/panel/resource/sound.py` (new)
- `io_scene_kotor/ui/panel/resource/trigger.py` (new)
- `io_scene_kotor/ui/panel/resource/merchant.py` (new)
- `io_scene_kotor/ui/panel/resource/waypoint.py` (new)
- `io_scene_kotor/ui/panel/resource/encounter.py` (new)
- `io_scene_kotor/ui/panel/resource/dialog.py` (new)

### 3.8 Save Game Operations

**New Save Game Operators:**

- `KB_OT_open_save_editor` - Open save game editor
- `KB_OT_extract_save` - Extract save game resources

**Implementation:**

- `io_scene_kotor/ops/save/open_editor.py` (new)
- `io_scene_kotor/ops/save/extract.py` (new)
- `io_scene_kotor/ui/panel/save_game.py` (new panel)

### 3.9 Additional Utility Operators

**Expand Show/Hide Menu:**

- Add more granular show/hide options:
  - `KB_OT_show_characters` / `KB_OT_hide_characters`
  - `KB_OT_show_placeables` / `KB_OT_hide_placeables`
  - `KB_OT_show_doors` / `KB_OT_hide_doors`
  - `KB_OT_show_items` / `KB_OT_hide_items`
  - `KB_OT_show_triggers` / `KB_OT_hide_triggers`
  - `KB_OT_show_waypoints` / `KB_OT_hide_waypoints`

**Texture Operations:**

- `KB_OT_convert_tpc_to_tga` - Convert TPC to TGA
- `KB_OT_convert_tga_to_tpc` - Convert TGA to TPC
- `KB_OT_extract_tpc_textures` - Extract textures from TPC
- `KB_OT_batch_convert_textures` - Batch convert texture files

**Module Operations:**

- `KB_OT_pack_module` - Pack module into ERF/RIM
- `KB_OT_unpack_module` - Unpack ERF/RIM module
- `KB_OT_validate_module` - Validate module structure

### 3.10 Additional Menu Integration (from brainstorm)

Port more Holocron/PyKotor-inspired entry points and workflows into Blender menus and context.

**Context menus (right-click):**

- **3D Viewport:** Append to `VIEW3D_MT_object_context_menu`: separator + KotOR actions (e.g. "Edit Waypoint", "Edit Placeable", "Edit Trigger") when selection has `kb` custom properties and matching `dummytype` (path point, placeable, trigger, etc.). Use each operator’s `poll()` for visibility; single draw function that adds separator + operators.
- **Outliner:** Append to `OUTLINER_MT_context_menu`: same logic based on selected object(s) and `getattr(obj, "kb", None)` / `kb.dummytype` (or equivalent from `constants.py`).

**Header menus (per-editor):**

- **3D Viewport:** Append draw to `VIEW3D_HT_header`: show KotOR menu or a few high-frequency buttons (e.g. "KotOR" dropdown). Option A: always show. Option B: only when a KotOR object is active (`getattr(context.active_object, "kb", None)`).
- **Outliner / Properties:** Optionally append to `OUTLINER_HT_header` and `PROPERTIES_HT_header` for consistency; keep draw logic cheap (no file I/O).

**3D View topbar duplicate (optional):**

- Append KotOR menu to `VIEW3D_MT_editor_menus` so it appears in the 3D View’s topbar as well as the main topbar (viewport-heavy workflows).

**Area/module editing workflows:**

- Placeables, triggers, waypoints: keep in-viewport representation (empties with `kb` props); "Edit …" operators open existing GFF/UTC/UTP/UTT/UTW editors with resource path from object. Lightweight fields (position, tag) editable in Blender panels; complex GFF in editor. Avoid loading full GFF in viewport draw.

**Conversation/dialog tree editors:**

- Keep "Edit Dialog" as operator opening existing DLG editor (inline panel or external). If a scene object references a DLG, store path on object and pass to editor.

**Script (NSS) editing:**

- "Edit NSS" operator: ensure a text datablock exists (create or open from module path), open in Blender Text Editor; optional "Open in external editor" and rely on Blender’s auto-reload for external changes.

**Texture/TPC management:**

- Already covered in 3.9 (convert, extract, batch). Optional: add context menu entries when image/TPC is selected (e.g. "Convert to TGA" from image editor context).

**Save game editing:**

- Already covered in 3.8; ensure save-related actions appear in KotOR menu and, if useful, in a relevant context menu (e.g. when a save resource is selected in module browser).

**Keyboard shortcuts (optional):**

- Register addon keymaps via `wm.keyconfigs.addon` only; store `(km, kmi)` per item and remove in unregister; check `keyconfigs.addon` is not None (e.g. background mode). Prefer Ctrl/Alt/Shift combinations to reduce conflicts. Keep all actions reachable from menus for accessibility; add keymaps only for high-frequency ops (e.g. toggle walkmesh, edit waypoint).

**Implementation (high level):**

- New draw functions in `io_scene_kotor/ui/menu/kotor.py` (or dedicated `context_menu.py` / `header.py`): `draw_kotor_context_view3d`, `draw_kotor_context_outliner`, `kb_view3d_header_draw`, optional `VIEW3D_MT_editor_menus` append. Register/unregister in `__init__.py` (append/remove).
- Optional keymap registration in `__init__.py` with `addon_keymaps` list and safe unregister.
- NSS: operator that creates/opens text datablock and switches to Text Editor (or sets active text).

**Todos (for implementation plan):**

- Add context menu draw for 3D View and Outliner (KotOR object types).
- Add 3D View header draw (KotOR menu or buttons); optional Outliner/Properties header.
- Optionally add KotOR to `VIEW3D_MT_editor_menus`.
- Optional: addon keymaps for 2–3 high-frequency operators; document in AGENTS.md.

#### Research Insights (3.10)

**Best practices:**

- Append to `VIEW3D_MT_object_context_menu` and `OUTLINER_MT_context_menu`; one draw function per menu; each operator’s `poll()` controls visibility (no duplicate poll logic in draw).
- Use `getattr(context.active_object, "kb", None)` and `kb.dummytype` (or `DummyType` from `constants.py`) to show KotOR actions only for relevant objects.
- Header: append to `VIEW3D_HT_header` (and optionally `OUTLINER_HT_header`, `PROPERTIES_HT_header`); keep draw logic cheap; optional conditional draw when KotOR object active.
- Keymaps: use `wm.keyconfigs.addon` only; store `(km, kmi)` and remove in unregister; check `kc is None` in background mode; prefer Ctrl/Alt/Shift to avoid conflicts.

**Implementation details:**

- Context menu: `bpy.types.VIEW3D_MT_object_context_menu.append(draw_kotor_context)`; in draw, `layout.separator()` then `layout.operator("kb.edit_utw", ...)` etc.; mirror with `remove` in unregister.
- NSS: create/open `bpy.data.texts[name]`, switch area to Text Editor or set active text; optional “Open in external editor” and rely on Blender auto-reload.

**References:**

- Blender 4.2 API: Menu, Header, KeyMaps, KeyConfigurations; addon keymap pattern (addon_keymaps list, remove in unregister).

## Part 4: UI Organization

### Panel Hierarchy

**Properties Editor (Object Context):**

- `KB_PT_model` (existing)
- `KB_PT_animations` (existing)
- `KB_PT_modelnode` (existing)
- `KB_PT_creature` (new, when UTC selected)
- `KB_PT_placeable` (new, when UTP selected)
- `KB_PT_door` (new, when UTD selected)
- `KB_PT_item` (new, when UTI selected)
- `KB_PT_trigger` (new, when UTT selected)
- `KB_PT_waypoint` (new, when UTW selected)
- `KB_PT_encounter` (new, when UTE selected)

**Properties Editor (Scene Context):**

- `KB_PT_game_installation` (new)
- `KB_PT_module_browser` (new, can also be in 3D viewport)

**3D Viewport Sidebar:**

- `KB_PT_module_browser` (new)
- `KB_PT_quick_actions` (new - quick access to common operations)

### Menu Organization

**Topbar → Editor → KotOR:**

- Game (submenu)
  - Select Installation
  - Refresh Modules
  - Open Module
- Modules (submenu)
  - Open Module Designer
  - Open Indoor Map Builder
  - Clone Module
  - Pack Module
  - Unpack Module
- Resources (submenu)
  - New (submenu with all resource types)
  - Extract Selected
  - Batch Extract
- Tools (submenu)
  - File Search
  - KotorDiff
  - TSLPatchData Editor
- Editors (submenu)
  - Edit Talk Table
  - Edit Journal
  - [All resource editors]
- Lightmaps (existing)
- Minimap (existing)
- Show/Hide (existing, expanded)

**File Menu:**

- Import → KotOR MDL (existing)
- Import → KotOR LYT (existing)
- Import → KotOR PTH (existing)
- Import → KotOR Module (new)
- Import → KotOR Save Game (new)
- Export → KotOR MDL (existing)
- Export → KotOR LYT (existing)
- Export → KotOR PTH (existing)
- Export → KotOR Module (new)

## Part 5: Implementation Phases

### Phase 1: Foundation (Week 1)

1. Add PyKotor dependency (pyproject.toml + blender_manifest.toml)
2. Create PyKotor adapter layer
3. Add game installation panel (basic)
4. Add module browser panel (basic)

### Phase 2: Core Features (Week 2)

1. Implement module selection and loading
2. Add resource list and basic extraction
3. Create resource creation operators (UTC, UTP, UTD, etc.)
4. Add basic property panels for resources

### Phase 3: Advanced Features (Week 3)

1. Implement full module browser with tabs
2. Add tool operators (Module Designer, File Search, etc.)
3. Add editor operators
4. Expand show/hide menu

### Phase 4: PyKotor Migration (Week 4) — *cancelled*

**Superseded by plan "Remove PyKotor MDL usage and align with toolset ideas":** MDL load/save use only native `format/mdl` readers and writers (no PyKotor). TPC and GFF retain optional PyKotor path via `get_use_pykotor_readers()` and the adapter; no full replacement.

1. ~~Replace MDL reader with PyKotor~~ — not done; MDL stays native.
2. TPC/GFF: optional PyKotor path remains; native readers unchanged.
3. Round-trip tests: existing test_pykotor_compatibility covers adapter and io.mdl contract.

### Phase 5: Polish (Week 5)

1. Add remaining utility operators
2. Improve UI organization and hierarchy
3. Add tooltips and descriptions
4. Update documentation

## Part 6: Testing Strategy

### Unit Tests

- Test PyKotor adapter layer
- Test resource creation operators
- Test module browser functionality

### Integration Tests

- Test game installation detection
- Test module loading
- Test resource extraction

### E2E Tests

- Test full workflow: Install → Module → Resource → Edit → Export
- Test round-trip: Import → Edit → Export → Re-import

## Part 7: Documentation Updates

### Files to Update

- `AGENTS.md` - Document PyKotor dependency and new UI features
- `README.md` - Update feature list
- Add docstrings to all new operators and panels
- Create user guide for new features

## Part 8: Considerations

### Performance

- Module browser may need async loading for large installations
- Resource lists should use pagination or lazy loading
- Cache module metadata to avoid repeated file system access

### Error Handling

- Graceful degradation if PyKotor unavailable
- Clear error messages for missing installations
- Validation for resource operations

### Accessibility

- All new operators accessible via menus
- Proper tooltips and descriptions
- Keyboard navigation support

### Backward Compatibility

- Maintain existing import/export functionality
- Feature flags for PyKotor migration
- Deprecation warnings for old code paths

## Files Summary

### New Files (Estimated 80+ files)

- `pyproject.toml`
- `io_scene_kotor/vendor/pykotor_adapter.py`
- `io_scene_kotor/ui/panel/game_installation.py`
- `io_scene_kotor/ui/panel/module_browser.py`
- `io_scene_kotor/ui/panel/quick_actions.py`
- `io_scene_kotor/ui/panel/resource/*.py` (10 files)
- `io_scene_kotor/ui/panel/save_game.py`
- `io_scene_kotor/ui/menu/resources.py`
- `io_scene_kotor/ui/menu/tools.py`
- `io_scene_kotor/ui/menu/editors.py`
- `io_scene_kotor/ui/list/resources.py`
- `io_scene_kotor/ops/game/*.py` (3 files)
- `io_scene_kotor/ops/module/*.py` (5 files)
- `io_scene_kotor/ops/resource/*.py` (14 files)
- `io_scene_kotor/ops/tools/*.py` (6 files)
- `io_scene_kotor/ops/editor/*.py` (14 files)
- `io_scene_kotor/ops/save/*.py` (2 files)
- `io_scene_kotor/ops/texture/*.py` (4 files)
- `io_scene_kotor/ops/showhide/*.py` (12 files)
- Plus property groups, types, and utilities

### Modified Files

- `blender_manifest.toml` (add wheels)
- `io_scene_kotor/__init__.py` (register new classes)
- `io_scene_kotor/ui/menu/kotor.py` (expand menu)
- `io_scene_kotor/ui/props/scene.py` (add game installation props)
- `io_scene_kotor/io/mdl.py` (add PyKotor path)
- `io_scene_kotor/io/pth.py` (add PyKotor GFF support)
- `AGENTS.md` (update documentation)
- `Makefile` (add wheel-download target)

This plan provides a comprehensive roadmap for integrating PyKotor and expanding the UI with Holocron Toolset-inspired features while maintaining the existing architecture and patterns.

---

## Part 9: Deepening – Research Insights

### Menu and context integration (Blender 4.x)


| Topic                             | API / pattern                                                                                    |
| --------------------------------- | ------------------------------------------------------------------------------------------------ |
| Top-level menu                    | `TOPBAR_MT_editor_menus.append(draw)` (already used)                                             |
| 3D View menu                      | `VIEW3D_MT_editor_menus.append(draw)` for optional duplicate KotOR entry                         |
| Context menu 3D                   | `VIEW3D_MT_object_context_menu.append(draw)`; operator `poll` for KotOR type                     |
| Context menu Outliner             | `OUTLINER_MT_context_menu.append(draw)`; use context/selection in draw or operator poll          |
| Header 3D / Outliner / Properties | `VIEW3D_HT_header`, `OUTLINER_HT_header`, `PROPERTIES_HT_header`; `append`/`prepend(draw)`       |
| Keymaps                           | `wm.keyconfigs.addon`; store `(km, kmi)`; remove in unregister; check `kc is None` in background |
| Poll by KotOR type                | `getattr(obj, "kb", None)` and `kb.dummytype` (or `DummyType` from constants)                    |


### Area editing and NSS/DLG

- **Placeables/triggers/waypoints:** In-viewport representation with `kb` props; “Edit …” opens GFF editor with resource path from object; lightweight fields in panels, complex GFF in editor.
- **Dialog:** Keep “Edit Dialog” as operator opening DLG editor; store DLG path on object when referenced from scene.
- **NSS:** Text datablock + Blender Text Editor; optional external editor + Blender auto-reload; “Edit NSS” creates/opens text and switches to Text Editor.

