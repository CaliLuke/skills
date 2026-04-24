---
name: py-quality-gates
description: Set up Python quality gates (ruff lint/format, type checking, pytest + coverage, complexity, dead code, duplicates, file length) in any Python repo with a single check.sh script. This skill should be used when the user says "add quality gates", "set up linting", "add python checks", "quality gate setup", "add check script", "enforce code quality", or wants to establish code quality infrastructure in a Python project.
---

# Python Quality Gates Setup

Set up a comprehensive quality gate system for a Python project. This creates a `check.sh` script and configures all supporting tools.

## Step 1: Assess the repo

Before creating anything, read the existing state:

1. Find `pyproject.toml`, `setup.py`, or `setup.cfg` — identify the package manager (uv, pip, poetry, pdm), existing config, and dependencies.
2. Check for existing config: `ruff.toml`, `.flake8`, `mypy.ini`, `.pylintrc`, `pyproject.toml` `[tool.*]` sections.
3. Check for existing `check.sh` or similar scripts.
4. Identify the source directory (often `src/`, the project name, or top-level package).
5. Check the Python version (`python_requires`, `.python-version`, `pyproject.toml`).

Report findings to the user and confirm before proceeding. Do NOT overwrite existing configs without asking.

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

## Step 7: Add to CLAUDE.md

If a `CLAUDE.md` exists in the repo, append a "Quality Gates" section with two commands: `./check.sh` (check only) and `./check.sh --fix` (fix + check). If no `CLAUDE.md` exists, create one with this section plus basic commands.

## Step 8: Run it

Run `./check.sh` and fix any issues that come up. The first run usually surfaces:

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
