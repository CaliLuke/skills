---
name: py-quality-gates
description: Set up Python quality gates (ruff lint/format, type checking, pytest + coverage, complexity, dead code, duplicates, file length) in any Python repo, wired through `prek` (pre-commit reimagined) with a `check.sh` orchestrator underneath. This skill should be used when the user says "add quality gates", "set up linting", "add python checks", "quality gate setup", "add prek", "add check script", "enforce code quality", or wants to establish code quality infrastructure in a Python project.
---

# Python Quality Gates Setup

Set up a comprehensive quality gate system for a Python project. The prescribed checker command is `prek run --all-files`. This creates a `.pre-commit-config.yaml` that points `prek` at a `check.sh` orchestrator, plus all supporting tool configs.

## Step 1: Assess the repo

Before creating anything, read the existing state:

1. Find `pyproject.toml`, `setup.py`, or `setup.cfg` — identify the package manager (uv, pip, poetry, pdm), existing config, and dependencies.
2. Check for existing config: `ruff.toml`, `.flake8`, `mypy.ini`, `.pylintrc`, `.pre-commit-config.yaml`, `pyproject.toml` `[tool.*]` sections.
3. Check for existing `check.sh` or similar scripts.
4. Identify the source directory (often `src/`, the project name, or top-level package).
5. Check the Python version (`python_requires`, `.python-version`, `pyproject.toml`).

## Step 1.5: Inventory existing gates and implement the delta

Most Python repos have **some** gates already (ruff configured in `pyproject.toml`, a `pytest` invocation in CI, an old `.flake8`) but not the full set this skill installs. The default behavior is to **fill in the missing gates**, not to stop. Only defer the whole job when every row of the checklist below is already ✅ or when the existing orchestrator is genuinely incompatible with adding gates (rare — see end of step).

Walk this checklist before writing anything. For each gate, check the listed signal; mark ✅ if present and working, ❌ if missing or broken on disk.

| Gate                                      | Detection signal                                                                                                   | Where to add if ❌ |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------ |
| ruff lint config                          | `[tool.ruff.lint]` in `pyproject.toml` (or `ruff.toml`) with a non-trivial `select = [...]`                        | Step 3             |
| ruff format check                         | `[tool.ruff.format]` configured AND orchestrator runs `ruff format --check`                                        | Step 3 + check.sh  |
| Type checker (ty / mypy / pyright)        | Tool installed AND invoked by orchestrator; config exists in `pyproject.toml` or `mypy.ini` / `pyrightconfig.json` | Step 5             |
| pytest + coverage config                  | `[tool.pytest.ini_options]` AND `[tool.coverage.*]` in `pyproject.toml`; orchestrator runs `pytest --cov`          | Step 4 + check.sh  |
| Per-file coverage threshold               | Orchestrator parses `coverage.json` and fails on files below threshold                                             | Step 6 + check.sh  |
| File-length cap                           | Orchestrator runs a `wc -l` / `find` length check                                                                  | Step 6 + check.sh  |
| Cyclomatic complexity (`radon cc`)        | `radon` installed AND invoked by orchestrator                                                                      | Step 6 + check.sh  |
| Maintainability index (`radon mi`)        | `radon` installed AND `mi` invoked by orchestrator                                                                 | Step 6 + check.sh  |
| Dead-code (`vulture`)                     | `vulture` installed AND invoked by orchestrator                                                                    | Step 6 + check.sh  |
| Duplicate detection (`pylint R0801`)      | `pylint` installed AND invoked with `--enable=duplicate-code` by orchestrator                                      | Step 6 + check.sh  |
| `check.sh` orchestrator                   | `check.sh` (or equivalent `Makefile`/`tox`/`nox` target) runs the full gate sequentially                           | Step 6             |
| `.pre-commit-config.yaml` + `prek` wiring | File exists and wires `check.sh` (or per-gate hooks) for `prek`/`pre-commit`                                       | Step 7             |

Run the existing orchestrator once (`uv run check`, `poetry run task check`, `make check`, `./check.sh`, `tox`, `nox`) before counting any ✅. A passing run earns it; a failing run means the gate is broken regardless of config presence — treat as ❌ and fix or replace.

Then report a short table to the user and **proceed to implement every ❌ row** without asking permission per row. Two modes:

- **No existing orchestrator** — create `check.sh` and `.pre-commit-config.yaml` per Steps 6–7; add only the gates the inventory marked ❌. Use the package runner detected in Step 1 (`uv run` / `poetry run` / `python -m` / plain) consistently.
- **Existing orchestrator present** — **extend it** rather than replacing. Add to `Makefile`/`tox.ini`/`noxfile.py`, append gate invocations to the existing `check.sh`, or register new hooks in `.pre-commit-config.yaml`. Keep the user's entry point name. Only mention replacement if the orchestrator is structurally hostile to new gates (see below).

Two cases where you stop or ask first:

1. **Everything is ✅** — every gate is present and the orchestrator passes cleanly. Report "all gates already in place" and stop. Nothing to do.
2. **Incompatible orchestrator** — a Bazel `py_library`/`py_test` setup that owns the lint config, a `tox` matrix that already encodes the full gate, a project-specific suite that overlaps non-trivially (bandit security, docstring coverage, import-graph audits). Ask whether to (a) wire missing gates into that system using its native idiom (a new `tox` env, a new `nox` session, an extra `Makefile` target), or (b) add `check.sh` + `prek` alongside as a developer-facing fast path (some duplication, stable second entry point). Don't auto-replace.

Conflict cases that need a one-line confirmation before proceeding (not a "stop entirely"):

- Existing `.flake8` plus the new `[tool.ruff.lint]` config — ruff supersedes flake8; ask whether to remove `.flake8` or keep both temporarily.
- `mypy` and `pyright` both configured — pick one; running both is redundant and noisy.
- A project-wide `coverage fail_under` already at a different threshold than this skill's per-file 30% — confirm which is canonical before overwriting.

## Step 2: Install dev dependencies

Use the detected package manager. Always add as dev dependencies.

```text
ruff radon vulture pylint pytest pytest-cov
```

For type checking, pick one based on what the project already uses or ask:

- `ty` — fast, from the ruff team, good for new projects
- `mypy` — mature, widest ecosystem support
- `pyright` — good for projects also using VS Code

For uv: `uv add --dev ruff radon vulture pylint pytest pytest-cov ty`

For pip: `pip install ruff radon vulture pylint pytest pytest-cov ty`

For poetry: `poetry add --group dev ruff radon vulture pylint pytest pytest-cov ty`

Also install `prek` — the prescribed checker entry point. It reads `.pre-commit-config.yaml`, installs git hooks, and runs the gate. `check.sh` (Step 6) is the orchestrator underneath; `prek` just wraps it. `prek` is a per-machine tool, not a project dev-dependency:

```bash
pipx install prek          # or: pip install prek, brew install prek, cargo install --locked prek
```

## Step 3: Ruff config

If no ruff config exists, add a `[tool.ruff]` section to `pyproject.toml`. If no `pyproject.toml` exists, create `ruff.toml`.

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "SIM",  # flake8-simplify
    "TCH",  # flake8-type-checking
    "RUF",  # ruff-specific rules
]

[tool.ruff.format]
quote-style = "double"
```

Adjust `target-version` to match the project's Python version.

## Step 4: Pytest config

If no pytest config exists, add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

Add coverage config:

```toml
[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
fail_under = 30
show_missing = true

[tool.coverage.json]
output = "coverage.json"
```

Replace `src` with the actual source directory throughout.

## Step 5: Type checker config

For ty, no config file needed — it works out of the box.

For mypy, add to `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
```

For pyright, create `pyrightconfig.json`:

```json
{
  "pythonVersion": "3.12",
  "typeCheckingMode": "basic",
  "reportMissingImports": true
}
```

## Step 6: Create `check.sh`

Create a `check.sh` at the project root. Make it executable (`chmod +x`).

Template — adapt the package runner (`uv run` / `python -m` / `poetry run`), source directory, and type checker:

```bash
#!/usr/bin/env bash
# Code quality gates — run before pushing.
# Usage: ./check.sh [--fix]
set -euo pipefail

FIX="${1:-}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Adjust these for your project
SRC_DIR="src"
RUN="uv run"

echo "══════════════════════════════════════"
echo "  Python Quality Gates"
echo "══════════════════════════════════════"

FAILED=()

run_gate() {
  local name="$1"; shift
  echo ""
  echo "▶  $name"
  if "$@"; then
    return 0
  else
    FAILED+=("$name")
    return 1
  fi
}

# ── Python: lint ──────────────────────────────────────────────────────────────

if [ "$FIX" = "--fix" ]; then
  run_gate "Python: ruff lint" $RUN ruff check "$SRC_DIR" --fix
else
  run_gate "Python: ruff lint" $RUN ruff check "$SRC_DIR"
fi

# ── Python: format ────────────────────────────────────────────────────────────

if [ "$FIX" = "--fix" ]; then
  run_gate "Python: ruff format" $RUN ruff format "$SRC_DIR"
else
  run_gate "Python: ruff format" $RUN ruff format --check "$SRC_DIR"
fi

# ── Python: type check ───────────────────────────────────────────────────────

run_gate "Python: type check" $RUN ty check "$SRC_DIR"

# ── Python: tests + coverage ─────────────────────────────────────────────────

run_gate "Python: pytest + coverage" $RUN pytest "$SRC_DIR" -q --cov="$SRC_DIR" --cov-report=json

# ── Python: per-file coverage ────────────────────────────────────────────────

if [ -f "coverage.json" ]; then
  echo ""
  echo "▶  Python: per-file coverage (min 30%)"
  if ! $RUN python -c "
import json, sys
with open('coverage.json') as f:
    data = json.load(f)
fails = []
for path, info in sorted(data['files'].items()):
    pct = info['summary']['percent_covered']
    if pct < 30:
        fails.append((path, pct))
if fails:
    for path, pct in fails:
        print(f'  {path}: {pct:.1f}% (min 30%)')
    print(f'  {len(fails)} file(s) below 30% coverage')
    sys.exit(1)
"; then
    FAILED+=("Python: per-file coverage (min 30%)")
  fi
fi

# ── Python: file length ──────────────────────────────────────────────────────

echo ""
echo "▶  Python: file length (max 500 lines)"
PY_OVER=0
while IFS= read -r f; do
  lines=$(wc -l < "$f")
  if [ "$lines" -gt 500 ]; then
    echo "  $f: $lines lines (max 500)"
    PY_OVER=$((PY_OVER + 1))
  fi
done < <(find "$SRC_DIR" -name '*.py' -not -path '*/__pycache__/*')
if [ "$PY_OVER" -gt 0 ]; then
  echo "  $PY_OVER file(s) over limit"
  FAILED+=("Python: file length (max 500 lines)")
fi

# ── Python: cyclomatic complexity ─────────────────────────────────────────────

# Grade C or worse = fail. Show only B+ for awareness, fail on C+.
run_gate "Python: cyclomatic complexity (radon cc)" $RUN radon cc "$SRC_DIR" -a -nc

# ── Python: maintainability index ─────────────────────────────────────────────

# Show files with MI below B grade (< 20).
run_gate "Python: maintainability index (radon mi)" $RUN radon mi "$SRC_DIR" -nb

# ── Python: dead code detection ───────────────────────────────────────────────

run_gate "Python: dead code detection (vulture)" $RUN vulture "$SRC_DIR" --min-confidence 80

# ── Python: duplicate code ────────────────────────────────────────────────────

run_gate "Python: duplicate detection (pylint R0801)" $RUN pylint "$SRC_DIR" \
  --ignore=tests \
  --disable=all \
  --enable=duplicate-code \
  --min-similarity-lines=12 \
  --score=n

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "══════════════════════════════════════"
if [ "${#FAILED[@]}" -eq 0 ]; then
  echo "  All checks passed"
else
  echo "  ${#FAILED[@]} check(s) failed:"
  for name in "${FAILED[@]}"; do
    echo "     - $name"
  done
  exit 1
fi
echo "══════════════════════════════════════"
```

### Adapting the template

- **Package runner**: Replace `RUN="uv run"` with `RUN="poetry run"` or `RUN=""` (for plain pip/venv).
- **Type checker**: Replace `ty check` with `mypy "$SRC_DIR"` or `pyright` as needed.
- **Source dir**: Replace `SRC_DIR="src"` with the actual package directory.

## Step 7: Wire up `prek`

`prek` is the prescribed checker entry point — `.pre-commit-config.yaml` lets `prek` invoke `check.sh` from git hooks and from the command line under one stable interface. Even though `check.sh` runs fine on its own, route users through `prek` so the same gates fire on commit, on push, and on manual runs without three different invocations.

Create `.pre-commit-config.yaml` at the repo root:

```yaml
repos:
  - repo: local
    hooks:
      - id: quality-gates
        name: Python quality gates
        entry: ./check.sh
        language: system
        pass_filenames: false
        always_run: true
        stages: [pre-commit, pre-push, manual]
```

`pass_filenames: false` and `always_run: true` matter: pytest, coverage, vulture, and pylint duplicate-detection scan the whole project, not a per-file slice.

Heads-up: the Python ecosystem already has a popular tool called `pre-commit` (the original, written in Python). `prek` is a faster Rust reimplementation that reads the same `.pre-commit-config.yaml`. If the repo already uses `pre-commit`, either swap it for `prek` (drop-in) or let `pre-commit` keep driving — both consume the same config. Don't run both.

Wire to git hooks once per checkout:

```bash
prek install                          # both pre-commit and pre-push by default
# or, if pre-commit is too slow for the full gate, push-only:
prek install --hook-type pre-push
```

Daily invocation — `prek run --all-files` is the prescribed command:

```bash
prek run --all-files     # full sweep — the canonical entry point
prek run                 # staged files only (fast pre-commit path)
./check.sh               # still works; prek is just calling this
./check.sh --fix         # auto-fix path — call check.sh directly since prek doesn't pass flags
```

## Step 8: Add to CLAUDE.md

If a `CLAUDE.md` exists in the repo, append a "Quality Gates" section with three commands: `prek run --all-files` (prescribed checker), `./check.sh --fix` (fix path), and `prek install` (one-time hook setup). If no `CLAUDE.md` exists, create one with this section plus basic commands.

## Step 9: Run it

Run `prek run --all-files` and fix any issues that come up. The first run usually surfaces:

- `prek: command not found` — install per Step 2 (`pipx install prek`, `brew install prek`, etc.).
- Ruff lint errors — run `./check.sh --fix` to auto-fix most
- Missing `__init__.py` files causing import issues for type checkers
- vulture false positives — create a `vulture_whitelist.py` with dummy usages and pass it: `vulture src vulture_whitelist.py`
- pylint duplicate detection may be noisy on first run — adjust `--min-similarity-lines` if needed
- Coverage gate needs tests to exist — if the project has no tests yet, comment out the coverage gates until tests are added

## Customization options

Ask the user if they want to adjust:

- **Max file length** — default 500, some projects prefer 300 or 800
- **Complexity threshold** — radon defaults to C grade fail, can tighten to B
- **Coverage minimum** — default 30% per-file, adjust up for mature projects
- **Vulture confidence** — default 80%, lower catches more but more false positives
- **Duplicate threshold** — default 12 similar lines, adjust for legacy codebases
- **Additional gates** — bandit (security), import sorting strictness, docstring coverage
