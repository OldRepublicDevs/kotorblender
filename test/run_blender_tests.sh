#!/usr/bin/env bash
# run_blender_tests.sh
#
# Runs all KotorBlender background-mode Blender tests.
# Tests live in test/blender/test_*.py and each exits with 0 (pass) or 1 (fail).
#
# Usage:
#   bash test/run_blender_tests.sh [--blender /path/to/blender] [--filter pattern]
#
# Environment variables:
#   BLENDER   – path to the Blender executable (default: blender)
#   VERBOSE   – if non-empty, show full Blender output for passing tests too
#
# Exit code: 0 if all tests pass, 1 if any fail.

set -euo pipefail

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
BLENDER="${BLENDER:-blender}"
FILTER=""
VERBOSE="${VERBOSE:-}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --blender) BLENDER="$2"; shift 2 ;;
        --filter)  FILTER="$2";  shift 2 ;;
        --verbose) VERBOSE=1;    shift ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Locate test directory
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$SCRIPT_DIR/blender"

if [[ ! -d "$TEST_DIR" ]]; then
    echo "ERROR: Test directory not found: $TEST_DIR" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Verify Blender is available
# ---------------------------------------------------------------------------
if ! command -v "$BLENDER" &>/dev/null 2>&1 && [[ ! -x "$BLENDER" ]]; then
    echo "ERROR: Blender not found at '$BLENDER'" >&2
    echo "  Set BLENDER env var or use --blender /path/to/blender" >&2
    exit 1
fi

BLENDER_VERSION=$("$BLENDER" --version 2>&1 | head -1 || true)
echo "========================================"
echo " KotorBlender Test Suite"
echo " Blender: $BLENDER_VERSION"
echo " Tests:   $TEST_DIR"
echo "========================================"

# ---------------------------------------------------------------------------
# Run tests
# ---------------------------------------------------------------------------
PASSED=0
FAILED=0
SKIPPED=0
FAILED_TESTS=()

for test_file in "$TEST_DIR"/test_*.py; do
    test_name="$(basename "$test_file")"

    # Apply filter if specified
    if [[ -n "$FILTER" && "$test_name" != *"$FILTER"* ]]; then
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    echo ""
    echo ">>> Running: $test_name"

    # Capture output; show it unconditionally or only on failure
    tmpout="$(mktemp)"
    exit_code=0

    "$BLENDER" \
        --background \
        --python "$test_file" \
        -- \
        2>&1 | tee "$tmpout" || exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        PASSED=$((PASSED + 1))
        echo "    [PASS] $test_name"
    else
        FAILED=$((FAILED + 1))
        FAILED_TESTS+=("$test_name")
        echo "    [FAIL] $test_name (exit code $exit_code)"
        if [[ -z "$VERBOSE" ]]; then
            echo "    --- Output ---"
            cat "$tmpout"
            echo "    --- End Output ---"
        fi
    fi

    rm -f "$tmpout"
done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "========================================"
echo " Results: $PASSED passed, $FAILED failed, $SKIPPED skipped"
echo "========================================"

if [[ ${#FAILED_TESTS[@]} -gt 0 ]]; then
    echo " Failed tests:"
    for t in "${FAILED_TESTS[@]}"; do
        echo "   - $t"
    done
    echo "========================================"
    exit 1
fi

exit 0
