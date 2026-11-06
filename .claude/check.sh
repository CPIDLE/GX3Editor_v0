#!/usr/bin/env bash
# Project test gate — runs after each Write/Edit (PostToolUse hook). The edit is already written.
# On a failure it prints the test output to stderr and exits 2: that is the only way the output
# reaches cc (exit 1 is logged as a non-blocking error the model never sees; stdout is dropped).
#
# Runs only the tests related to the edited file, so the hook stays fast as the suite grows
# (2026-10-08: running the full suite after every edit took ~5 min in WorldModel_Statecore_v1):
#   - a file outside this project, or not a code file (docs, config, data)  -> nothing
#   - run_tests uses pytest:
#       the edited file is a test file (test_*.py / *_test.py)          -> that file
#       another .py                                                      -> test files at the project root or
#                                                                           under test_dirs (default tests/, test/)
#                                                                           that mention its module name
#       conftest.py / __init__.py, no related test, or not a .py file    -> nothing
#   - any other command, on a code edit                                  -> the whole run_tests command
# The full suite is cc's job before each commit (global CLAUDE.md, Coding Discipline).
#
# /pm new fills run_tests with the detected test command, or with `true` when none is detected.
# It must stay valid bash: never leave the raw placeholder in a deployed copy. For pytest the
# related test files are appended as arguments, so keep the pytest command plain (no paths, no &&).
set -e
cd "$(dirname "$0")/.."

run_tests() { true "$@"; }
test_dirs=(tests test)   # where to look for related test files besides the project root
skip_tests=()            # test files the hook never runs (slow ones), as paths or globs relative to the project root

is_pytest=""
declare -f run_tests | grep -q pytest && is_pytest=1

# Run a command; if it fails, show its output to cc (stderr + exit 2).
# pytest's exit 5 ("no tests collected", e.g. the related file is on an --ignore list) counts as a pass.
check() {
  local out rc=0
  out=$("$@" 2>&1) || rc=$?
  if [ "$rc" -ne 0 ] && ! { [ "$rc" -eq 5 ] && [ "$1" = run_tests ] && [ -n "$is_pytest" ]; }; then
    printf 'check.sh: tests failed after editing %s\n' "$f" >&2
    printf '%s\n' "$out" | tail -n 80 >&2
    exit 2
  fi
  printf '%s\n' "$out" | tail -n 1   # one-line summary (stdout of a passing hook stays out of the model's context)
}

lower() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]'; }

payload=$(cat)
py=""
for c in python python3; do
  # `command -v` alone is not enough: Windows' Store alias "python" exists but does not run.
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import json' >/dev/null 2>&1; then py=$c; break; fi
done
if [ -n "$py" ]; then
  f=$(printf '%s' "$payload" | "$py" -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null || true)
else
  # No Python: pull "file_path" out of the JSON by pattern (JSON escapes a backslash as \\).
  f=$(printf '%s' "$payload" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/^.*:[[:space:]]*"//; s/"$//' || true)
  f=${f//\\\\//}
fi
f=${f//\\//}

root=$(pwd -W 2>/dev/null || pwd)
case "$(lower "$f")" in
  "$(lower "$root")"/*) ;;
  *) exit 0 ;;
esac

# --- project-specific checks (optional) go here; wrap each command in `check` ---

if [ -n "$is_pytest" ]; then
  case "$f" in
    *.py) ;;
    *) exit 0 ;;
  esac
  base=$(basename "$f" .py)
  tests=()
  case "$base" in
    test_*|*_test) tests=("$f") ;;
    # conftest / __init__ affect most of the suite (HomeHIVE: __init__ pulled in 497 tests, 100 s):
    # left to the full run before commit.
    conftest|__init__) exit 0 ;;
    *)
      while IFS= read -r t; do tests+=("$t"); done < <(
        grep -lw -- "$base" test_*.py *_test.py 2>/dev/null || true
        # an empty test_dirs would make grep -r search the whole tree (.venv included)
        [ ${#test_dirs[@]} -eq 0 ] || grep -rlw --include='test_*.py' --include='*_test.py' -- "$base" "${test_dirs[@]}" 2>/dev/null || true
      )
      ;;
  esac
  lroot="$(lower "$root")/"
  keep=()
  for t in "${tests[@]}"; do
    rel=$t
    case "$(lower "$t")" in "$lroot"*) rel=${t:${#lroot}} ;; esac
    for pat in "${skip_tests[@]}"; do
      # shellcheck disable=SC2254
      case "$rel" in $pat) continue 2 ;; esac
    done
    keep+=("$t")
  done
  [ ${#keep[@]} -gt 0 ] || exit 0
  check run_tests "${keep[@]}"
else
  case "$f" in
    *.py|*.js|*.jsx|*.mjs|*.cjs|*.ts|*.tsx|*.vue|*.svelte|*.go|*.rs|*.java|*.kt|*.kts|*.scala|*.rb|*.php|*.c|*.h|*.cpp|*.hpp|*.cs|*.swift|*.dart|*.lua|*.sh|*.ps1)
      check run_tests ;;
  esac
fi
