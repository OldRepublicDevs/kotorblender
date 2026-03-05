# KotorBlender Makefile
# ─────────────────────────────────────────────────────────────────────────────
# Targets:
#   build          – build the Blender extension .zip package
#   test           – run all background-mode tests (no game assets required)
#   test-e2e       – run full MDL round-trip tests (requires DATA_DIR)
#   test-all       – run both test and test-e2e
#   lint           – Python syntax check + ruff (error-level only)
#   lint-full      – ruff full report (informational, non-blocking)
#   syntax-check   – py_compile only (fast)
#   clean          – remove build and test output artefacts
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: build test test-e2e test-all lint lint-full syntax-check clean
.PHONY: test-registration test-gff test-pth test-lyt test-aabb test-constants test-mdl

BLENDER ?= blender

# ── Extension Build ──────────────────────────────────────────────────────────
build:
	mkdir -p ./build
	$(BLENDER) --command extension build \
		--source-dir ./io_scene_kotor \
		--output-dir ./build

# ── Background-mode Tests (no game assets needed) ────────────────────────────
test:
	BLENDER="$(BLENDER)" bash test/run_blender_tests.sh

# Individual test targets for rapid iteration during development
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

# ── Full E2E Test (game assets required) ─────────────────────────────────────
test-e2e:
ifndef DATA_DIR
	$(error DATA_DIR is not set. Usage: DATA_DIR=/path/to/kotor/assets make test-e2e)
endif
	$(BLENDER) --background --python ./test/test_models.py

test-all: test test-e2e

# ── Lint ─────────────────────────────────────────────────────────────────────
syntax-check:
	python3 -c "import py_compile, os; [py_compile.compile(os.path.join(r,f), doraise=True) for r,_,fs in os.walk('io_scene_kotor') for f in fs if f.endswith('.py')]"
	@echo "Syntax check passed."

lint: syntax-check
	python3 -m ruff check --select E9,F821,F823 io_scene_kotor/ || true

lint-full:
	python3 -m ruff check io_scene_kotor/ --statistics || true

# ── Clean ────────────────────────────────────────────────────────────────────
clean:
	rm -rf build/*
	rm -rf test/out/*
