# PyKotor Format Reader Migration Plan

## Overview

This plan details the step-by-step migration of KotorBlender's format readers (MDL, TPC, GFF) from custom implementations to PyKotor equivalents, while maintaining full backward compatibility with the existing `io/` layer interface.

## Current State

- **UI Infrastructure**: Complete (80+ operators, panels, menus)
- **PyKotor Adapter**: Exists at `io_scene_kotor/vendor/pykotor_adapter.py` with placeholder functions
- **Format Readers to Replace**:
  - `io_scene_kotor/format/mdl/reader.py` → PyKotor `read_mdl()`
  - `io_scene_kotor/format/tpc/reader.py` → PyKotor `read_tpc()`
  - `io_scene_kotor/format/gff/reader.py` → PyKotor `read_gff()`
- **IO Layer Interface**: `io/mdl.py`, `io/pth.py` (uses GFF), material loading (uses TPC)

## Requirements

1. Maintain backward compatibility with existing `io/` layer interface
2. Test round-trip compatibility (import → export → re-import)
3. Handle both KOTOR1 and KOTOR2 formats
4. Preserve all existing functionality
5. Feature flag to toggle between old/new implementations during migration

---

## Phase 1: Foundation & Testing Infrastructure

### Task 1.1: Create Feature Flag System
**File**: `io_scene_kotor/constants.py`  
**Dependencies**: None  
**Testing**: Unit test for flag defaults

**Actions**:
- Add `USE_PYKOTOR_READERS` boolean flag to `constants.py` (default: `False`)
- Add getter function `get_use_pykotor_readers() -> bool` that checks:
  1. Flag value
  2. PyKotor availability (`is_pykotor_available()`)
  3. Returns `False` if PyKotor unavailable (graceful fallback)

**Test Requirements**:
- `test/unit/test_constants.py`: Verify flag defaults to `False`
- Verify fallback when PyKotor unavailable

---

### Task 1.2: Create PyKotor Compatibility Test Suite
**File**: `test/blender/test_pykotor_compatibility.py` (new)  
**Dependencies**: Task 1.1  
**Testing**: Round-trip tests for each format

**Actions**:
- Create test file with structure:
  ```python
  def test_pykotor_mdl_roundtrip_kotor1()
  def test_pykotor_mdl_roundtrip_kotor2()
  def test_pykotor_tpc_roundtrip()
  def test_pykotor_gff_roundtrip()
  ```
- Each test should:
  1. Load file with current reader → scene representation
  2. Load same file with PyKotor → convert to scene representation
  3. Compare key properties (node structure, dimensions, data integrity)
  4. Export both → compare binary output (byte-level or checksum)

**Test Requirements**:
- Tests skip gracefully if PyKotor unavailable
- Tests skip gracefully if test assets missing
- Compare scene.Model properties: name, classification, node count, animation count
- Compare TPC properties: width, height, encoding, pixel data checksum
- Compare GFF properties: struct count, field count, tree structure

---

### Task 1.3: Document PyKotor API Surface
**File**: `docs/pykotor_api_mapping.md` (new, optional)  
**Dependencies**: None  
**Testing**: None

**Actions**:
- Document PyKotor API structure for MDL, TPC, GFF
- Map PyKotor types to io_scene_kotor scene types:
  - `PyKotorMDL` → `scene.Model`
  - `PyKotorTPC` → `TpcImage` (or direct Blender image)
  - `PyKotorGFF` → GFF tree dict
- Document version differences (KOTOR1 vs KOTOR2)
- Document edge cases and known limitations

---

## Phase 2: TPC Reader Migration (Simplest, Lowest Risk)

### Task 2.1: Implement TPC Conversion Functions
**File**: `io_scene_kotor/vendor/pykotor_adapter.py`  
**Dependencies**: Task 1.1  
**Testing**: Unit tests for conversion

**Actions**:
- Implement `convert_pykotor_tpc_to_tpcimage(pykotor_tpc: PyKotorTPC) -> TpcImage | None`
  - Extract width, height from PyKotor TPC
  - Extract pixel data (handle DXT1/DXT5 decompression if needed)
  - Extract TXI lines if present
  - Return `TpcImage` matching current `TpcReader.load()` output format
- Handle encoding types: GRAYSCALE, RGB, RGBA, DXT1, DXT5
- Handle cubemap textures (6 faces)
- Handle mipmaps (use top-level mip for compatibility)

**Test Requirements**:
- `test/unit/test_pykotor_adapter_tpc.py`: 
  - Test conversion for each encoding type
  - Test cubemap handling
  - Test TXI extraction
  - Verify pixel data matches current reader output

---

### Task 2.2: Integrate PyKotor TPC into Material Loading
**File**: `io_scene_kotor/scene/material.py`  
**Dependencies**: Task 2.1  
**Testing**: Integration test

**Actions**:
- Modify `create_image()` function:
  ```python
  if tpc_path:
      if get_use_pykotor_readers():
          tpc = load_tpc_via_pykotor(tpc_path)
          if tpc:
              tpc_image = convert_pykotor_tpc_to_tpcimage(tpc)
          else:
              # Fallback to current reader
              tpc_image = TpcReader(tpc_path).load()
      else:
          tpc_image = TpcReader(tpc_path).load()
      # ... rest of existing code
  ```
- Ensure error handling falls back to current reader on failure

**Test Requirements**:
- `test/blender/test_material_tpc_loading.py`:
  - Test material creation with PyKotor TPC reader enabled
  - Test fallback to current reader when PyKotor fails
  - Verify Blender image properties match (width, height, pixels)

---

### Task 2.3: Update TPC Operators to Use PyKotor
**Files**: 
- `io_scene_kotor/ops/texture/convert_tpc_to_tga.py`
- `io_scene_kotor/ops/texture/extract_tpc_textures.py`
- `io_scene_kotor/ops/module/extract_tpc.py`

**Dependencies**: Task 2.1  
**Testing**: Operator execution tests

**Actions**:
- Update operators to use `load_tpc_via_pykotor()` when flag enabled
- Implement conversion logic (TPC → TGA, TPC extraction)
- Add error handling with user-friendly messages

**Test Requirements**:
- Manual testing: Execute operators with test TPC files
- Verify output matches expected format

---

### Task 2.4: Enable TPC Migration
**Dependencies**: Tasks 2.1, 2.2, 2.3, 1.2  
**Testing**: Full round-trip test suite

**Actions**:
- Run compatibility test suite (Task 1.2) for TPC
- Fix any discrepancies
- Set `USE_PYKOTOR_READERS = True` for TPC-specific code path
- Monitor for regressions

**Test Requirements**:
- All TPC tests pass
- No regressions in material loading
- Round-trip compatibility verified

---

## Phase 3: GFF Reader Migration (Medium Complexity)

### Task 3.1: Implement GFF Conversion Functions
**File**: `io_scene_kotor/vendor/pykotor_adapter.py`  
**Dependencies**: Task 1.1  
**Testing**: Unit tests for conversion

**Actions**:
- Implement `convert_pykotor_gff_to_tree(pykotor_gff: PyKotorGFF) -> dict`
  - Convert PyKotor GFF structure to dict format matching current `GffReader.load()`
  - Preserve field types, struct types, list indices
  - Maintain `_type` and `_fields` metadata format
- Implement `convert_tree_to_pykotor_gff(tree: dict, file_type: str) -> PyKotorGFF | None`
  - Convert dict tree to PyKotor GFF object
  - Handle all GFF field types (DWORD, FLOAT, STRING, LIST, etc.)

**Test Requirements**:
- `test/unit/test_pykotor_adapter_gff.py`:
  - Test conversion for all GFF field types
  - Test nested structures
  - Test list fields
  - Verify round-trip: tree → PyKotor → tree → compare

---

### Task 3.2: Integrate PyKotor GFF into PTH Loading
**File**: `io_scene_kotor/io/pth.py`  
**Dependencies**: Task 3.1  
**Testing**: Integration test

**Actions**:
- Modify `load_pth()` function:
  ```python
  if get_use_pykotor_readers():
      gff = load_gff_via_pykotor(filepath)
      if gff:
          tree = convert_pykotor_gff_to_tree(gff)
      else:
          # Fallback to current reader
          loader = GffReader(filepath, "PTH")
          tree = loader.load()
  else:
      loader = GffReader(filepath, "PTH")
      tree = loader.load()
  ```
- Ensure error handling falls back gracefully

**Test Requirements**:
- `test/blender/test_pth_io_pykotor.py`:
  - Test PTH import with PyKotor GFF reader
  - Test fallback to current reader
  - Verify path points and connections match

---

### Task 3.3: Integrate PyKotor GFF into PTH Saving
**File**: `io_scene_kotor/io/pth.py`  
**Dependencies**: Task 3.1  
**Testing**: Integration test

**Actions**:
- Modify `save_pth()` function:
  ```python
  tree = # ... existing tree construction ...
  
  if get_use_pykotor_readers():
      gff = convert_tree_to_pykotor_gff(tree, "PTH")
      if gff:
          if save_gff_via_pykotor(gff, filepath):
              return
      # Fallback to current writer
  saver = GffWriter(tree, filepath, "PTH")
  saver.save()
  ```

**Test Requirements**:
- `test/blender/test_pth_io_pykotor.py`:
  - Test PTH export with PyKotor GFF writer
  - Test round-trip: import → export → re-import
  - Verify binary compatibility with game

---

### Task 3.4: Update GFF Editor Operators
**Files**: 
- `io_scene_kotor/ops/editor/edit_gff.py`
- `io_scene_kotor/ops/resource/new_gff.py`

**Dependencies**: Task 3.1  
**Testing**: Operator execution tests

**Actions**:
- Update operators to use PyKotor GFF functions when flag enabled
- Maintain backward compatibility with current GFF format

**Test Requirements**:
- Manual testing: Edit GFF files, create new GFF files
- Verify operations work correctly

---

### Task 3.5: Enable GFF Migration
**Dependencies**: Tasks 3.1, 3.2, 3.3, 3.4, 1.2  
**Testing**: Full round-trip test suite

**Actions**:
- Run compatibility test suite (Task 1.2) for GFF
- Fix any discrepancies
- Enable PyKotor GFF for PTH operations
- Monitor for regressions

**Test Requirements**:
- All GFF tests pass
- All PTH tests pass
- Round-trip compatibility verified

---

## Phase 4: MDL Reader Migration (Most Complex)

### Task 4.1: Analyze MDL Structure Mapping
**File**: `docs/mdl_structure_mapping.md` (new, optional)  
**Dependencies**: None  
**Testing**: None

**Actions**:
- Document mapping between PyKotor MDL and io_scene_kotor scene.Model:
  - Node hierarchy: PyKotor nodes → scene.modelnode types
  - Geometry: PyKotor meshes → TrimeshNode/SkinmeshNode
  - Animations: PyKotor animations → scene.Animation
  - Materials: PyKotor materials → scene material representation
  - Special nodes: Emitter, Light, Lightsaber, AABB, Danglymesh, Reference
- Document KOTOR1 vs KOTOR2 differences
- Document Xbox vs PC differences

---

### Task 4.2: Implement MDL Node Conversion (Part 1: Basic Nodes)
**File**: `io_scene_kotor/vendor/pykotor_adapter.py`  
**Dependencies**: Task 4.1  
**Testing**: Unit tests for each node type

**Actions**:
- Implement helper functions:
  - `_convert_pykotor_node_to_scene_node(pykotor_node, parent) -> BaseNode`
  - Handle node types: Dummy, Trimesh, Skinmesh, Reference
  - Extract: name, position, rotation, scale, parent relationship
- Implement geometry conversion:
  - PyKotor vertices → Blender-compatible vertex arrays
  - PyKotor faces → face indices
  - UV coordinates, normals, vertex colors

**Test Requirements**:
- `test/unit/test_pykotor_adapter_mdl_nodes.py`:
  - Test each node type conversion
  - Test geometry data accuracy
  - Test node hierarchy preservation

---

### Task 4.3: Implement MDL Node Conversion (Part 2: Special Nodes)
**File**: `io_scene_kotor/vendor/pykotor_adapter.py`  
**Dependencies**: Task 4.2  
**Testing**: Unit tests for special nodes

**Actions**:
- Implement special node conversions:
  - **EmitterNode**: Extract emitter properties (spawn type, update, render, blend, texture, etc.)
  - **LightNode**: Extract light properties (type, color, radius, multiplier, etc.)
  - **LightsaberNode**: Extract saber geometry and properties
  - **AabbNode**: Extract AABB data, roomlinks
  - **DanglymeshNode**: Extract vertex constraints
- Handle node-specific data structures

**Test Requirements**:
- `test/unit/test_pykotor_adapter_mdl_special_nodes.py`:
  - Test each special node type
  - Verify all properties are preserved

---

### Task 4.4: Implement MDL Animation Conversion
**File**: `io_scene_kotor/vendor/pykotor_adapter.py`  
**Dependencies**: Task 4.2  
**Testing**: Unit tests for animations

**Actions**:
- Implement `_convert_pykotor_animations_to_scene(pykotor_mdl) -> list[Animation]`
  - Extract animation data from PyKotor MDL
  - Convert to `scene.Animation` objects
  - Preserve: name, duration, keyframes, node references
  - Handle animation scale (animscale)
- Implement `_convert_pykotor_animnode_to_scene(pykotor_animnode) -> AnimationNode`
  - Extract per-node animation data
  - Convert keyframes to Blender-compatible format

**Test Requirements**:
- `test/unit/test_pykotor_adapter_mdl_animations.py`:
  - Test animation conversion
  - Test keyframe accuracy
  - Test animation node mapping

---

### Task 4.5: Implement Complete MDL to Scene Conversion
**File**: `io_scene_kotor/vendor/pykotor_adapter.py`  
**Dependencies**: Tasks 4.2, 4.3, 4.4  
**Testing**: Integration test

**Actions**:
- Implement `convert_pykotor_mdl_to_scene()` (replace placeholder):
  - Convert PyKotor MDL header: name, classification, supermodel, bounding box, etc.
  - Build node hierarchy using node conversion functions
  - Attach animations
  - Preserve all model metadata

**Test Requirements**:
- `test/blender/test_pykotor_mdl_to_scene.py`:
  - Test complete MDL conversion
  - Compare with current reader output
  - Verify all properties match

---

### Task 4.6: Implement Scene to PyKotor MDL Conversion (Export Path)
**File**: `io_scene_kotor/vendor/pykotor_adapter.py`  
**Dependencies**: Task 4.5  
**Testing**: Integration test

**Actions**:
- Implement `convert_scene_model_to_pykotor()` (replace placeholder):
  - Convert scene.Model header to PyKotor MDL header
  - Convert node hierarchy to PyKotor nodes
  - Convert animations to PyKotor format
  - Handle export options: TSL, Xbox, quaternion compression

**Test Requirements**:
- `test/blender/test_scene_to_pykotor_mdl.py`:
  - Test scene → PyKotor conversion
  - Test export options (TSL, Xbox)
  - Verify binary output matches current writer

---

### Task 4.7: Integrate PyKotor MDL into IO Layer
**File**: `io_scene_kotor/io/mdl.py`  
**Dependencies**: Tasks 4.5, 4.6  
**Testing**: Integration test

**Actions**:
- Modify `load_mdl()` function:
  ```python
  if get_use_pykotor_readers():
      pykotor_mdl = load_mdl_via_pykotor(filepath)
      if pykotor_mdl:
          model = convert_pykotor_mdl_to_scene(pykotor_mdl)
          if not model:
              # Fallback to current reader
              mdl = MdlReader(filepath)
              model = mdl.load()
      else:
          # Fallback to current reader
          mdl = MdlReader(filepath)
          model = mdl.load()
  else:
      mdl = MdlReader(filepath)
      model = mdl.load()
  ```
- Handle MDX file loading (PyKotor may handle this automatically)
- Preserve walkmesh loading logic (unchanged)

**Test Requirements**:
- `test/blender/test_mdl_io_pykotor.py`:
  - Test MDL import with PyKotor
  - Test fallback to current reader
  - Verify Blender objects created correctly

---

### Task 4.8: Integrate PyKotor MDL Export
**File**: `io_scene_kotor/io/mdl.py`  
**Dependencies**: Task 4.6  
**Testing**: Integration test

**Actions**:
- Modify `save_mdl()` function:
  ```python
  model = Model.from_mdl_root(mdl_root, options)
  
  if get_use_pykotor_readers():
      pykotor_mdl = convert_scene_model_to_pykotor(model, options)
      if pykotor_mdl:
          if save_mdl_via_pykotor(pykotor_mdl, filepath):
              # Success
              return
      # Fallback to current writer
  mdl = MdlWriter(filepath, model, ...)
  mdl.save()
  ```

**Test Requirements**:
- `test/blender/test_mdl_io_pykotor.py`:
  - Test MDL export with PyKotor
  - Test round-trip: import → export → re-import
  - Verify binary compatibility

---

### Task 4.9: Handle MDX File Compatibility
**File**: `io_scene_kotor/vendor/pykotor_adapter.py`  
**Dependencies**: Task 4.7  
**Testing**: Integration test

**Actions**:
- Verify PyKotor handles MDX files correctly
- If PyKotor requires separate MDX handling:
  - Implement MDX loading via PyKotor
  - Ensure geometry data matches current reader behavior
- Test with MDL files that have MDX companions

**Test Requirements**:
- Test MDL+MDX loading with PyKotor
- Verify geometry matches current reader

---

### Task 4.10: Enable MDL Migration
**Dependencies**: Tasks 4.1-4.9, 1.2  
**Testing**: Full round-trip test suite

**Actions**:
- Run compatibility test suite (Task 1.2) for MDL
- Test with KOTOR1 and KOTOR2 models
- Test with Xbox and PC formats
- Fix any discrepancies
- Enable PyKotor MDL for import/export
- Monitor for regressions

**Test Requirements**:
- All MDL tests pass
- Round-trip compatibility verified for:
  - KOTOR1 PC models
  - KOTOR2 PC models
  - KOTOR1 Xbox models (if supported)
  - KOTOR2 Xbox models (if supported)
- All node types work correctly
- Animations play correctly
- Materials/textures load correctly

---

## Phase 5: Validation & Cleanup

### Task 5.1: Comprehensive Round-Trip Testing
**Dependencies**: Phases 2, 3, 4 complete  
**Testing**: Full test suite

**Actions**:
- Run all existing tests with PyKotor readers enabled
- Run compatibility test suite (Task 1.2)
- Test with real game assets (if available):
  - Various MDL models (characters, placeables, doors, etc.)
  - Various TPC textures (diffuse, lightmaps, cubemaps)
  - Various PTH files (area paths)
- Document any known limitations or differences

**Test Requirements**:
- All tests pass
- No regressions in functionality
- Performance acceptable (may be slower/faster than current readers)

---

### Task 5.2: Performance Benchmarking
**Dependencies**: Task 5.1  
**Testing**: Performance tests

**Actions**:
- Benchmark PyKotor readers vs current readers:
  - MDL import time
  - TPC loading time
  - GFF read/write time
- Document performance characteristics
- Identify optimization opportunities if needed

**Test Requirements**:
- Performance report comparing old vs new readers

---

### Task 5.3: Update Documentation
**Dependencies**: All phases complete  
**Testing**: Documentation review

**Actions**:
- Update `AGENTS.md` with PyKotor migration notes
- Update README if needed
- Document feature flag usage
- Document any breaking changes or limitations

**Test Requirements**:
- Documentation is accurate and complete

---

### Task 5.4: Remove Legacy Code (Optional, Future)
**Dependencies**: All phases complete, stable for several releases  
**Testing**: Full regression suite

**Actions**:
- **DO NOT DO THIS IMMEDIATELY** - Keep legacy code for at least 2-3 releases
- After validation period, consider:
  - Deprecating old readers
  - Removing old reader code (if confident)
  - Or keeping as fallback option

**Test Requirements**:
- Full regression test suite passes
- User feedback indicates no issues

---

## Testing Strategy Summary

### Unit Tests
- `test/unit/test_pykotor_adapter_tpc.py` - TPC conversion
- `test/unit/test_pykotor_adapter_gff.py` - GFF conversion
- `test/unit/test_pykotor_adapter_mdl_nodes.py` - MDL node conversion
- `test/unit/test_pykotor_adapter_mdl_special_nodes.py` - Special nodes
- `test/unit/test_pykotor_adapter_mdl_animations.py` - Animation conversion

### Integration Tests
- `test/blender/test_pykotor_compatibility.py` - Round-trip compatibility
- `test/blender/test_material_tpc_loading.py` - TPC material loading
- `test/blender/test_pth_io_pykotor.py` - PTH import/export
- `test/blender/test_mdl_io_pykotor.py` - MDL import/export
- `test/blender/test_pykotor_mdl_to_scene.py` - MDL to scene conversion

### Regression Tests
- All existing tests in `test/blender/` and `test/unit/`
- E2E tests in `test/test_models.py` (if assets available)

---

## Risk Mitigation

1. **Feature Flag**: Always allow fallback to current readers
2. **Gradual Migration**: Start with TPC (simplest), then GFF, then MDL (most complex)
3. **Comprehensive Testing**: Round-trip tests ensure compatibility
4. **Error Handling**: Graceful fallback on any PyKotor failure
5. **Documentation**: Clear mapping of PyKotor APIs to scene representation

---

## Dependencies Between Tasks

```
Phase 1 (Foundation)
├── Task 1.1 (Feature Flag) → All other tasks
├── Task 1.2 (Test Suite) → All validation tasks
└── Task 1.3 (Documentation) → Optional

Phase 2 (TPC)
├── Task 2.1 → Task 2.2, 2.3
├── Task 2.2, 2.3 → Task 2.4
└── Task 2.4 depends on Task 1.2

Phase 3 (GFF)
├── Task 3.1 → Task 3.2, 3.3, 3.4
├── Task 3.2, 3.3, 3.4 → Task 3.5
└── Task 3.5 depends on Task 1.2

Phase 4 (MDL)
├── Task 4.1 → Task 4.2, 4.3, 4.4
├── Task 4.2, 4.3, 4.4 → Task 4.5
├── Task 4.5 → Task 4.6
├── Task 4.6 → Task 4.7, 4.8
├── Task 4.7 → Task 4.9
└── Task 4.10 depends on Tasks 4.1-4.9, 1.2

Phase 5 (Validation)
└── All previous phases → Phase 5 tasks
```

---

## Success Criteria

1. ✅ All format readers successfully migrated to PyKotor
2. ✅ Round-trip compatibility verified (import → export → re-import)
3. ✅ All existing tests pass
4. ✅ No regressions in functionality
5. ✅ Feature flag allows easy rollback
6. ✅ Documentation updated
7. ✅ Performance acceptable

---

## Estimated Timeline

- **Phase 1**: 1-2 days (foundation)
- **Phase 2**: 2-3 days (TPC migration)
- **Phase 3**: 3-4 days (GFF migration)
- **Phase 4**: 7-10 days (MDL migration - most complex)
- **Phase 5**: 2-3 days (validation)

**Total**: ~15-22 days of focused development

---

## Notes

- Keep legacy readers as fallback for at least 2-3 releases
- Monitor user feedback after enabling PyKotor readers
- Consider performance implications (PyKotor may be faster/slower)
- Some edge cases may require special handling (document as discovered)
