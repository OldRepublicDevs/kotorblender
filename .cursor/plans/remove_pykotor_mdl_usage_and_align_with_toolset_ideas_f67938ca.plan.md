---
name: Remove PyKotor MDL usage and align with toolset ideas
overview: Remove all use of PyKotor for MDL load/save from the IO layer while keeping the conversion functions and helpers in the adapter (unused). Use the Holocron Toolset only as a reference for ideas; implement equivalent functionality in io_scene_kotor with Blender UI and existing PyKotor/io code.
todos: []
isProject: false
status: completed
---

# Remove PyKotor MDL usage and align with toolset ideas

## Part 1: Remove PyKotor MDL usage from the IO layer

**Goal:** MDL load and save always use the existing [io_scene_kotor/format/mdl/](io_scene_kotor/format/mdl/) reader/writer. Keep conversion functions in the adapter but do not call them.

### 1.1 [io_scene_kotor/io/mdl.py](io_scene_kotor/io/mdl.py)

- **Imports:** Remove `convert_pykotor_mdl_to_scene`, `convert_scene_model_to_pykotor`, `get_use_pykotor_readers`, `load_mdl_via_pykotor`, `save_mdl_via_pykotor` from the pykotor_adapter import. If no other symbols are needed from the adapter here, remove the import entirely.
- **load_mdl() (binary MDL):** Remove the `get_use_pykotor_readers()` branch. Always use:
  - `mdl = MdlReader(filepath)` and `model = mdl.load()`.
- **save_mdl() (binary MDL):** Remove the `get_use_pykotor_readers()` / PyKotor export branch. Use only:
  - ASCII: existing `AsciiMdlWriter` path.
  - Binary: single path with `MdlWriter(...)` and `mdl.save()`.

Result: Binary MDL load/save never touches PyKotor; ASCII path unchanged.

### 1.2 [io_scene_kotor/vendor/pykotor_adapter.py](io_scene_kotor/vendor/pykotor_adapter.py)

- **Keep (do not remove):** `load_mdl_via_pykotor`, `save_mdl_via_pykotor`, `convert_pykotor_mdl_to_scene`, `convert_scene_model_to_pykotor`, and all their helpers (e.g. `_convert_pykotor_node_to_scene_node`, `_convert_scene_node_to_pykotor`, animation/node conversion helpers). They remain in the file but are unused by the MDL IO layer.
- **Optional:** Add a short comment at the top of the MDL-related block that these are kept for potential future use or external callers but are not used by `io.mdl` load/save.

### 1.3 Tests

- **[test/blender/test_pykotor_compatibility.py](test/blender/test_pykotor_compatibility.py):** The tests `test_pykotor_mdl_roundtrip_kotor1` and `test_pykotor_mdl_roundtrip_kotor2` call `load_mdl_via_pykotor` and compare with the current reader. Options:
  - **A)** Remove only the MDL roundtrip tests (so we no longer assert PyKotor MDL vs MdlReader); keep TPC/GFF tests.
  - **B)** Keep the MDL tests as “adapter-only” tests: they still verify that `load_mdl_via_pykotor` returns a PyKotor MDL and that basic attributes are readable, without using that path in `load_mdl()`.

Recommendation: **B** — keep the two MDL tests so the adapter’s MDL load path is still exercised in CI; no change to the test file if you prefer that. Otherwise choose A and delete the two MDL test functions and any MDL-only helpers (e.g. `_first_fixed_mdl_path`) if unused.

### 1.4 Other references

- **get_use_pykotor_readers():** Still used by TPC, GFF, and other operators ([io_scene_kotor/scene/material.py](io_scene_kotor/scene/material.py), [io_scene_kotor/io/pth.py](io_scene_kotor/io/pth.py), various ops). Do not remove the flag or adapter; only MDL stops using it for load/save.
- No changes to [io_scene_kotor/constants.py](io_scene_kotor/constants.py) or to `USE_PYKOTOR_READERS` for this task.

---

## Part 2: Use Holocron Toolset as reference only (no direct integration)

**Goal:** Treat the Holocron Toolset as a source of **examples and ideas** only. Do not import or run the toolset; implement equivalent behavior in io_scene_kotor using Blender UI, PyKotor (via existing adapter where applicable), and io_scene_kotor’s own code.

### 2.1 Reference audit (optional, for implementation follow-up)

- When the path `vendor/PyKotor/Tools/HolocronToolset/src/toolset/` is available (e.g. via junction to PyKotor repo), review:
  - Which features the toolset exposes (e.g. game installation, module list, resource browser, open/extract, editors).
  - How it uses PyKotor (installation discovery, module loading, resource types).
- Map those to existing io_scene_kotor panels/operators (game installation, module browser, refresh modules, open module, extract, editors) and identify gaps.

### 2.2 Implementation direction

- **No new dependency on the toolset code:** No imports from `toolset` or vendoring of Holocron Toolset into the repo.
- **Implement “toolset-like” features in io_scene_kotor:** Use PyKotor (e.g. `pykotor.extract.installation`, resource APIs) and the existing [io_scene_kotor/vendor/pykotor_adapter.py](io_scene_kotor/vendor/pykotor_adapter.py) (e.g. `find_kotor_paths_from_default`, TPC/GFF load/save) to implement behavior suggested by the toolset (e.g. module list, resource list, open/extract) in Blender operators and panels.
- Existing plan [.cursor/plans/pykotor_integration_and_ui_expansion_91971bed.plan.md](.cursor/plans/pykotor_integration_and_ui_expansion_91971bed.plan.md) already added many “Holocron Toolset–inspired” panels and operators; Part 2 is to ensure any remaining ideas from the toolset are implemented as **our own** logic in io_scene_kotor, not by integrating the toolset’s codebase.

No concrete code changes are **required** in Part 2 for this plan; it sets the policy (use toolset for ideas only, implement ourselves) and optionally an audit step. If you want a follow-up task to add specific features based on the toolset, that can be a separate plan.

---

## Summary


| Area                                                                                     | Action                                                                                                                                       |
| ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| [io_scene_kotor/io/mdl.py](io_scene_kotor/io/mdl.py)                                     | Remove PyKotor MDL imports and branches; binary MDL uses only MdlReader/MdlWriter.                                                           |
| [io_scene_kotor/vendor/pykotor_adapter.py](io_scene_kotor/vendor/pykotor_adapter.py)     | Keep all MDL conversion functions and helpers; do not call them from mdl.py.                                                                 |
| [test/blender/test_pykotor_compatibility.py](test/blender/test_pykotor_compatibility.py) | Either keep MDL adapter-only tests (B) or remove MDL tests (A).                                                                              |
| Holocron Toolset                                                                         | Use only as reference; implement similar features in io_scene_kotor with Blender + PyKotor + existing adapter; no toolset imports or launch. |


---

## Implementation completed

- **1.1 io/mdl.py:** No PyKotor imports; load_mdl/save_mdl use only MdlReader/MdlWriter (binary) and AsciiMdlReader/AsciiMdlWriter (ASCII). Module docstring states MDL IO does not use PyKotor.
- **1.2 pykotor_adapter.py:** MDL conversion functions kept; block comment states they are not used by io.mdl. `get_use_pykotor_readers()` docstring updated to state MDL is excluded.
- **1.3 Tests:** MDL adapter-only tests kept (B). Added `test_mdl_io_does_not_import_pykotor_mdl()` so CI enforces that io.mdl does not expose any PyKotor MDL symbols.
- **1.4:** No changes to constants or other callers of get_use_pykotor_readers(); MDL simply does not call it.
- **Part 2:** No code changes required (policy only).

### Verification checklist


| Requirement                                                          | Status |
| -------------------------------------------------------------------- | ------ |
| 1.1 io/mdl.py: no pykotor_adapter import                             | [x]    |
| 1.1 load_mdl() binary path: MdlReader only                           | [x]    |
| 1.1 save_mdl() binary path: MdlWriter only; ASCII: AsciiMdlWriter    | [x]    |
| 1.2 Adapter: MDL functions kept, block comment present               | [x]    |
| 1.2 get_use_pykotor_readers() docstring: MDL excluded                | [x]    |
| 1.3 test_pykotor_mdl_roundtrip_kotor1/2 kept (adapter-only)          | [x]    |
| 1.3 test_mdl_io_does_not_import_pykotor_mdl() added and in run_tests | [x]    |
| 1.4 get_use_pykotor_readers() unchanged for TPC/GFF/ops              | [x]    |
| 1.4 constants.py and USE_PYKOTOR_READERS unchanged                   | [x]    |
| Part 2: no toolset imports or code changes                           | [x]    |

**No further implementation required.** All required and optional items are done; Part 2 is policy-only with no code changes. Run `make test-pykotor-compatibility` (or `make test`) in an environment with Blender on PATH to confirm tests pass.

