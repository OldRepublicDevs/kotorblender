# KotorBlender Makefile
#
# Targets:
#   build        – build the Blender extension .zip package
#   test         – run all background-mode tests (no game assets needed)
#   test-e2e     – full MDL round-trip tests  (requires DATA_DIR=...)
#   lint         – syntax check + ruff (fatal errors only)
#   clean        – remove build and test output artefacts
#
# Individual test targets for development iteration:
#   test-registration  test-gff  test-pth  test-lyt
#   test-aabb          test-constants      test-mdl

.PHONY: build test test-e2e lint syntax-check clean
.PHONY: test-registration test-gff test-pth test-lyt test-aabb test-constants test-mdl

BLENDER ?= blender

build:
	mkdir -p ./build
	$(BLENDER) --command extension build \
		--source-dir ./io_scene_kotor \
		--output-dir ./build

test:
	BLENDER="$(BLENDER)" bash test/run_blender_tests.sh

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

# Requires extracted KotOR game assets; set DATA_DIR to their location.
test-e2e:
	@test -n "$(DATA_DIR)" || { echo "ERROR: DATA_DIR is not set. Usage: DATA_DIR=/path/to/assets make test-e2e" >&2; exit 1; }
	$(BLENDER) --background --python ./test/test_models.py

syntax-check:
	python3 -c "import py_compile, os; [py_compile.compile(os.path.join(r,f), doraise=True) for r,_,fs in os.walk('io_scene_kotor') for f in fs if f.endswith('.py')]"
	@echo "Syntax OK"

# Only check for errors that actually break the extension at load time.
# The 400+ pre-existing star-import warnings (F401/F403) are excluded.
lint: syntax-check
	python3 -m ruff check --select E9,F821,F823 io_scene_kotor/ || true

clean:
	rm -rf build/*
	rm -rf test/out/*
