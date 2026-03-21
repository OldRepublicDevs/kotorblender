# KotorBlender Makefile
#
# Requires GNU Make (Git Bash / MSYS2 / WSL / macOS / Linux / Windows). On Windows, PYTHON defaults to `python`
# (avoids the Microsoft Store `python3` stub); override with PYTHON=... or BLENDER=... as needed.
#
# Targets:
#   build        – fetch PyKotor wheels from PyPI (unless SKIP_WHEEL_DOWNLOAD=1), then build the .zip
#   test         – run all background-mode tests (no game assets needed)
#   test-e2e     – full MDL round-trip tests  (requires DATA_DIR=...)
#   lint         – syntax check + ruff (fatal errors only)
#   clean        – remove build and test output artefacts
#
# Individual test targets for development iteration:
#   test-registration  test-gff  test-pth  test-lyt
#   test-aabb          test-constants      test-mdl
#   test-material      test-format-bwm-roundtrip  test-ops-bwm-import-smoke  test-io-lyt-load
#   test-scene-modules test-ops-io-smoke test-ops-anim-smoke test-analyst-coverage test-coverage-matrix

.PHONY: build build-bundled test test-e2e test-unit lint syntax-check clean wheel-download verify-bundled-wheels
.PHONY: test-registration test-gff test-pth test-lyt test-aabb test-constants test-mdl test-mdl-import-op test-community-mdl test-pykotor-compatibility test-pykotor-ascii-mdl
.PHONY: test-material test-format-bwm-roundtrip test-ops-bwm-import-smoke test-io-lyt-load test-scene-modules test-ops-io-smoke test-ops-anim-smoke test-analyst-coverage test-coverage-matrix

# Windows: `python3` is often the Microsoft Store stub; real installs use `python`.
# Override anytime: `make build PYTHON=python3` or `BLENDER=/path/to/blender`.
ifeq ($(OS),Windows_NT)
PYTHON ?= python
BLENDER ?= "C:/Program Files/Blender Foundation/Blender 4.4/blender.exe"
else
PYTHON ?= python3
BLENDER ?= blender
endif
# Bundled PyKotor version (exact PyPI pin). Override: PYKOTOR_SPEC=pykotor==2.3.9 make wheel-download
PYKOTOR_SPEC ?= pykotor==2.3.1

# Portable mkdir / clean (Windows cmd.exe has no mkdir -p; use Python).
FS = $(PYTHON) helper_scripts/makefile_fs.py

# Blender extensions do not pip-install at enable time; wheels must be in the .zip.
# SKIP_WHEEL_DOWNLOAD=1 when wheels are already present (e.g. CI ran wheel-download).
build:
ifneq ($(SKIP_WHEEL_DOWNLOAD),1)
	$(MAKE) wheel-download
endif
	$(MAKE) verify-bundled-wheels
	$(FS) makedirs build
	$(BLENDER) --command extension build --source-dir ./io_scene_kotor --output-dir ./build

# Require a PyKotor .whl on disk and a matching blender_manifest.toml entry (even if wheels were pre-fetched).
verify-bundled-wheels:
	$(PYTHON) helper_scripts/verify_bundled_wheels.py

# Python runner: works from PowerShell/cmd (no bash). Passes explicit --blender for paths with spaces.
test:
	$(PYTHON) test/run_blender_tests.py --blender $(BLENDER)

# Unit tests (no Blender): format, constants, options. Discoverable by pytest and VS Code Test Explorer.
test-unit:
	$(PYTHON) -m pytest test/unit -v

test-registration:
	$(BLENDER) --background --python test/blender/test_registration.py

test-gff:
	$(BLENDER) --background --python test/blender/test_gff_io.py

test-pth:
	$(BLENDER) --background --python test/blender/test_pth_io.py

test-lyt:
	$(BLENDER) --background --python test/blender/test_lyt_export.py

test-aabb:
	$(BLENDER) --background --python test/blender/test_aabb.py

test-constants:
	$(BLENDER) --background --python test/blender/test_constants.py

test-mdl:
	$(BLENDER) --background --python test/blender/test_mdl_minimal.py

test-mdl-import-op:
	$(BLENDER) --background --python test/blender/test_mdl_import_op.py

test-community-mdl:
	$(BLENDER) --background --python test/blender/test_community_mdl_load.py

test-pykotor-compatibility:
	$(BLENDER) --background --python test/blender/test_pykotor_compatibility.py

test-pykotor-ascii-mdl:
	$(BLENDER) --background --python test/blender/test_pykotor_ascii_mdl.py

test-material:
	$(BLENDER) --background --python test/blender/test_material.py

test-format-bwm-roundtrip:
	$(BLENDER) --background --python test/blender/test_format_bwm_roundtrip.py

test-io-lyt-load:
	$(BLENDER) --background --python test/blender/test_io_lyt_load.py

test-scene-modules:
	$(BLENDER) --background --python test/blender/test_scene_walkmesh.py
	$(BLENDER) --background --python test/blender/test_scene_model.py
	$(BLENDER) --background --python test/blender/test_scene_armature.py
	$(BLENDER) --background --python test/blender/test_scene_modelnode_dummy.py
	$(BLENDER) --background --python test/blender/test_scene_animation_animnode.py
	$(BLENDER) --background --python test/blender/test_scene_modelnode_reference_light.py

test-ops-io-smoke:
	$(BLENDER) --background --python test/blender/test_ops_io_smoke.py

test-ops-anim-smoke:
	$(BLENDER) --background --python test/blender/test_ops_anim_smoke.py

# Package bl_info, addonprefs paths, resource_helpers, mdlexport/pthexport+pthimport,
# file handlers, lytexport, rebuild_armature operators.
test-analyst-coverage:
	$(BLENDER) --background --python test/blender/test_io_scene_kotor_package.py
	$(BLENDER) --background --python test/blender/test_addonprefs_paths.py
	$(BLENDER) --background --python test/blender/test_ops_resource_helpers.py
	$(BLENDER) --background --python test/blender/test_ops_mdl_export_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_armature_keyframes_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_bake_minimap_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_pth_export_import_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_file_handlers.py
	$(BLENDER) --background --python test/blender/test_ops_bwm_import_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_lyt_export_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_rebuild_armature_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_ascii_mdl_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_open_module_stub_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_pykotor_stub_texture_save_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_path_connection_smoke.py
	$(BLENDER) --background --python test/blender/test_scene_modelnode_skin_dangly_saber.py
	$(BLENDER) --background --python test/blender/test_format_bwm_reader_errors.py
	$(BLENDER) --background --python test/blender/test_ops_lensflare_smoke.py
	$(BLENDER) --background --python test/blender/test_format_mdl_reader_errors.py
	$(BLENDER) --background --python test/blender/test_ops_convert_tpc_to_tga_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_rebuild_material_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_autodetect_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_rebuild_all_materials_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_showhide_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_showhide_extended_categories_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_tools_stub_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_new_gff_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_open_preferences_smoke.py
	$(BLENDER) --background --python test/blender/test_ops_convert_tga_to_tpc_smoke.py
	$(BLENDER) --background --python test/blender/test_pykotor_adapter_smoke.py

# Regenerates test/io_scene_kotor_coverage_matrix.md (module ↔ test import heuristic).
test-coverage-matrix:
	$(PYTHON) test/scripts/coverage_inventory.py --write

# Requires extracted KotOR game assets; set DATA_DIR to their location.
test-e2e:
ifeq ($(strip $(DATA_DIR)),)
	$(error DATA_DIR is not set. Usage: DATA_DIR=/path/to/assets make test-e2e (Windows: use forward slashes or a quoted path))
endif
	$(BLENDER) --background --python ./test/test_models.py

syntax-check:
	$(PYTHON) -c "import py_compile, os; [py_compile.compile(os.path.join(r,f), doraise=True) for r,_,fs in os.walk('io_scene_kotor') for f in fs if f.endswith('.py')]"
	@echo "Syntax OK"

# Only check for errors that actually break the extension at load time.
# The 400+ pre-existing star-import warnings (F401/F403) are excluded.
lint: syntax-check
	-$(PYTHON) -m ruff check --select E9,F821,F823 io_scene_kotor/

# Download PyKotor + dependencies into io_scene_kotor/wheels/ and refresh blender_manifest.toml.
# Required for module browser, pack/unpack, BIF, etc. CI runs this before tests and extension build.
wheel-download:
	$(FS) clean-whl io_scene_kotor/wheels
	$(FS) makedirs io_scene_kotor/wheels
	$(PYTHON) -m pip install -U pip
	$(PYTHON) -m pip wheel "$(PYKOTOR_SPEC)" -w io_scene_kotor/wheels
	$(PYTHON) helper_scripts/sync_extension_wheels.py

# Same as `make build` (wheels are bundled by default).
build-bundled: build

clean:
	$(FS) clean-dirs build test/out
