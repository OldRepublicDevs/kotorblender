#!/usr/bin/env bash
# run_blender_tests.sh
#
# Runs all KotorBlender background-mode Blender tests.
# Each test/blender/test_*.py script exits 0 (pass) or 1 (fail).
#
# Usage:
#   bash test/run_blender_tests.sh [--filter pattern]
#
# Environment variables:
#   BLENDER  – path to Blender executable (default: blender)
#
# Exit code: 0 if all tests pass, 1 if any fail.

set -euo pipefail

BLENDER="${BLENDER:-blender}"
FILTER=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --filter) FILTER="$2"; shift 2 ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$SCRIPT_DIR/blender"

if [[ ! -d "$TEST_DIR" ]]; then
    echo "ERROR: Test directory not found: $TEST_DIR" >&2; exit 1
fi

if ! command -v "$BLENDER" &>/dev/null && [[ ! -x "$BLENDER" ]]; then
    echo "ERROR: Blender not found at '$BLENDER'" >&2; exit 1
fi

BLENDER_VER=$("$BLENDER" --version 2>&1 | head -1 || true)
echo "=== KotorBlender Tests | $BLENDER_VER ==="

PASSED=0; FAILED=0; FAILED_TESTS=()

for test_file in "$TEST_DIR"/test_*.py; do
    name="$(basename "$test_file")"
    [[ -n "$FILTER" && "$name" != *"$FILTER"* ]] && continue

    echo ""
    echo ">>> $name"
    exit_code=0
    "$BLENDER" --background --python "$test_file" || exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        PASSED=$((PASSED + 1))
    else
        FAILED=$((FAILED + 1))
        FAILED_TESTS+=("$name")
    fi
done

echo ""
echo "=== Results: $PASSED passed, $FAILED failed ==="
[[ $FAILED -eq 0 ]] && exit 0

echo "Failed:"
for t in "${FAILED_TESTS[@]}"; do echo "  - $t"; done
exit 1
