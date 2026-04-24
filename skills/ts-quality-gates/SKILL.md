---
name: ts-quality-gates
description: Set up TypeScript quality gates (typecheck, ESLint, Prettier, duplicates, dead code, file length) in any TS repo with a `check.sh` entry point — and an optional parallel orchestrator for larger setups. Use when the user says "add quality gates", "set up linting", "add ts checks", "quality gate setup", "add check script", or wants to establish code quality infrastructure in a TypeScript project.
---

# TypeScript Quality Gates Setup

Set up a quality gate system for a TypeScript project. The deliverable is a `check.sh` entry point, an ESLint flat config, Prettier defaults, and `knip`/`jscpd` configs — wired to the repo's actual package manager and source layout. For larger repos, Step 11 describes the upgrades that production setups use.

## Step 1: Assess the repo before touching anything

Before writing or installing anything, understand the repo. Two outcomes are possible: a **mature system already exists** (stop and defer — Step 2), or it doesn't (proceed from Step 3).

Gather in parallel:

1. `package.json` — package manager, existing scripts, React presence, dependencies.
2. Existing config files: `tsconfig*.json`, `eslint.config.*`, `.eslintrc*`, `biome.json`, `.prettierrc*`, `prettier.config.*`, `knip.json`, `jscpd.json`/`.jscpd.json`, `.husky/`, and any `scripts/*-workflow.*` orchestrator.
3. `CLAUDE.md` / `AGENTS.md` — canonical commands already documented.
4. Source directory (usually `src/`, but some repos use `lib/`, `app/`, or multiple).

### Package manager — detect once, use everywhere

Detect the PM from `packageManager` in `package.json`, the lockfile (`package-lock.json` / `pnpm-lock.yaml` / `yarn.lock` / `bun.lock` / `bun.lockb` / `deno.lock`), or an explicit user statement. **Some projects cannot use `npm`/`npx`, some cannot use `bun`, some are pinned to `pnpm` workspaces.** Use this table for every generated script, doc, and commit message — never hardcode `npm run` or `npx`:

| PM   | run script    | run binary                      | lockfile                 |
| ---- | ------------- | ------------------------------- | ------------------------ |
| npm  | `npm run X`   | `npx Y`                         | `package-lock.json`      |
| pnpm | `pnpm X`      | `pnpm exec Y` (or `pnpm dlx Y`) | `pnpm-lock.yaml`         |
| yarn | `yarn X`      | `yarn dlx Y`                    | `yarn.lock`              |
| bun  | `bun run X`   | `bunx Y`                        | `bun.lock` / `bun.lockb` |
| deno | `deno task X` | `deno run …`                    | `deno.lock`              |

Throughout this skill, `<PM_RUN>` means the left column for the detected PM and `<PM_EXEC>` means the middle column. If the detected PM is ambiguous or the user mentions a constraint, ask before generating.

## Step 2: Stop if a mature system already exists

A repo with a working orchestrator and matching configs should not be silently overwritten. Signals:

- An orchestrator script runs multiple gates (e.g. `scripts/lint-workflow.*`, `scripts/check.*`, Nx/Turbo `check` target). Inspect scripts named `lint:workflow`, `check`, `verify`, `ci`, `quality`.
- Config files for each gate already exist (`eslint.config.*`, `knip.json`, `jscpd.json`, `.prettierrc*`, Husky hooks in `.husky/`).
- `CLAUDE.md` / `AGENTS.md` lists canonical lint/test/typecheck commands.
- Project-specific gates the skill's template does NOT cover (FTA complexity, test-inventory consistency, logging audits, API contract generation, bundle-size budgets).

If **two or more** signals are present:

1. Run the existing orchestrator once to confirm it still works — this is both a sanity check and a way to show the user their current state.
2. Report what you found and list the gates it already covers.
3. Ask the user to choose: **(a) skip**, **(b) add a thin `check.sh` wrapper that calls the existing orchestrator** (same entry point across repos, zero behavior change), or **(c) extend the existing orchestrator with a specific named missing gate** (ask which one — Prettier, per-file coverage, etc.).
4. Only proceed to Step 3+ if the user explicitly asks to replace the existing system.

Why this matters: the skill's default `check.sh` is sequential bash with a fixed gate list and defaults tuned for a fresh repo. A parallel orchestrator, a non-`npm` PM, or project-specific gates are strictly **more** than the template provides — overwriting them is a downgrade that usually breaks pre-commit/pre-push hooks in the process. Do not assume the template is better than what's there.

## Step 3: Install dev dependencies

Use the detected PM. Always add as devDependencies.

### Core (every TS project)

```text
typescript eslint @eslint/js typescript-eslint eslint-plugin-simple-import-sort jscpd knip prettier
```

### React projects (add these too)

```text
eslint-plugin-react eslint-plugin-react-hooks eslint-plugin-jsx-a11y
```

If the existing `.npmrc` already has `legacy-peer-deps=true`, preserve it. Do not add that flag preemptively — ESLint 9 + typescript-eslint don't need it in most modern setups.

## Step 4: TypeScript config

If `tsconfig.json` exists, **leave it alone**. If not, create a strict default and ensure `"noEmit": true` (or a build step that runs `tsc -b`).

Add a `typecheck` script to `package.json` if missing:

```json
"typecheck": "tsc -b"
```

## Step 5: ESLint config

Create `eslint.config.js` (flat config, ESLint 9+). Use a `.mjs` extension or set `"type": "module"` in `package.json`.

### Base config (non-React)

```js
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import simpleImportSort from "eslint-plugin-simple-import-sort";

export default tseslint.config(
  { ignores: ["dist", "node_modules", "build", "coverage"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    plugins: { "simple-import-sort": simpleImportSort },
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/no-explicit-any": "error",
      "simple-import-sort/imports": "warn",
      "simple-import-sort/exports": "warn",
      "max-lines": [
        "warn",
        { max: 500, skipBlankLines: true, skipComments: true },
      ],
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "prefer-const": "error",
      "no-var": "error",
      eqeqeq: ["error", "always"],
    },
  },
);
```

The ESLint `complexity` rule is intentionally **not** included. It fires per-function and produces noise that developers learn to ignore. For per-file complexity tracking (which actually correlates with review difficulty), use FTA in Step 11. `max-lines` already catches the worst offenders as a cheap proxy.

### React additions

Merge in the React plugins:

```js
import reactPlugin from 'eslint-plugin-react'
import reactHooksPlugin from 'eslint-plugin-react-hooks'
import jsxA11yPlugin from 'eslint-plugin-jsx-a11y'

// plugins:  react, 'react-hooks', 'jsx-a11y'
// settings: { react: { version: 'detect' } }
// rules:
'react-hooks/rules-of-hooks': 'error',
'react-hooks/exhaustive-deps': 'warn',
'react/jsx-no-target-blank': 'error',
'react/no-array-index-key': 'warn',
'react/self-closing-comp': 'warn',
'jsx-a11y/alt-text': 'warn',
'jsx-a11y/no-autofocus': 'warn',
'jsx-a11y/anchor-is-valid': 'warn',
```

Add scripts using the detected PM. Substitute `<PM_RUN>` with the actual command (e.g. `pnpm`, `bun run`, `npm run`):

```json
"lint": "eslint src",
"lint:fix": "eslint src --fix",
"check": "<PM_RUN> typecheck && <PM_RUN> lint"
```

Replace `src` with the actual source directory.

## Step 6: Prettier config

If a `.prettierrc*` or `prettier.config.*` already exists, **leave it alone** — the user's existing style choices win, and overwriting them will re-format the entire codebase on the next run. If none exists, create `.prettierrc`:

```json
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2
}
```

Add scripts:

```json
"format": "prettier --write src",
"format:check": "prettier --check src"
```

## Step 7: Knip config

Knip works zero-config for most projects. Create `knip.json` only if the repo has non-standard entry points or workspaces:

```json
{
  "entry": ["src/index.ts", "src/main.tsx"],
  "project": ["src/**/*.{ts,tsx}"],
  "ignore": ["src/**/*.test.{ts,tsx}", "src/**/*.d.ts"]
}
```

First run on a legacy codebase may report many findings. Triage with the user before enforcing in CI — adjust the config's `ignore` patterns rather than disabling the gate.

## Step 8: Create `check.sh`

A thin bash entry point that calls each gate sequentially. Fine for small/medium repos; see Step 11 for the parallel-orchestrator upgrade.

Substitute `<PM_RUN>` and `<PM_EXEC>` with the detected PM's commands (Step 1 table). Do **not** leave the placeholders literal in the generated file.

```bash
#!/usr/bin/env bash
# Code quality gates — run before pushing.
# Usage: ./check.sh [--fix]
set -euo pipefail

FIX="${1:-}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

SRC_DIR="src"

echo "══════════════════════════════════════"
echo "  TypeScript Quality Gates"
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

# Typecheck
run_gate "TypeScript: tsc" <PM_RUN> typecheck

# ESLint (max-lines covers file length; no separate bash loop needed)
if [ "$FIX" = "--fix" ]; then
  run_gate "ESLint" <PM_RUN> lint:fix
else
  run_gate "ESLint" <PM_RUN> lint
fi

# Duplication — prefer jscpd.json if present
if [ -f jscpd.json ]; then
  run_gate "Duplication (jscpd)" <PM_EXEC> jscpd --config jscpd.json
else
  run_gate "Duplication (jscpd)" <PM_EXEC> jscpd "$SRC_DIR" \
    --min-lines 10 --min-tokens 50 --reporters console --threshold 5
fi

# Prettier
if [ "$FIX" = "--fix" ]; then
  run_gate "Prettier" <PM_EXEC> prettier --write "$SRC_DIR"
else
  run_gate "Prettier" <PM_EXEC> prettier --check "$SRC_DIR"
fi

# Dead code
run_gate "Dead code (knip)" <PM_EXEC> knip

# Tests — only if a test runner is configured
if [ -f vitest.config.ts ] || [ -f vitest.config.js ] || [ -f vitest.config.mts ]; then
  run_gate "Tests (vitest)" <PM_EXEC> vitest run
fi

# Summary
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

Intentionally **not** in this default template (to avoid double-gating or fragile behavior):

- **Bash file-length loop** — duplicates ESLint's `max-lines` rule.
- **Coverage gate** — needs `coverage/coverage-summary.json`, which needs tests to be run with `--coverage`. Making it conditional on the file existing silently no-ops when coverage wasn't generated. If you want coverage enforcement, see the reliable pattern in Step 11.
- **Auto-creating `CLAUDE.md`** — an agent shouldn't fabricate agent docs the user didn't ask for.

Make the file executable: `chmod +x check.sh`.

## Step 9: Document (existing docs only)

If the repo already has `CLAUDE.md` or `AGENTS.md`, append a compact "Quality Gates" section:

```markdown
## Quality Gates

- `./check.sh` — runs all gates (~60s)
- `./check.sh --fix` — auto-fix + check

Gates: typecheck · eslint · duplication · prettier · knip (+ vitest if configured).
```

Do **not** create `CLAUDE.md` just to document the gates. That's agent-clutter the user didn't ask for; the scripts in `package.json` are already self-documenting.

## Step 10: First run

Run `./check.sh` and fix anything that comes up. Expect:

- `"type": "module"` missing in `package.json` (required for ESM eslint config).
- Pre-existing lint errors — fix before calling the setup done.
- Files over 500 lines flagged by `max-lines` — report to the user, ask whether to split.
- Knip flagging many things on legacy codebases — triage via `knip.json` `ignore` patterns, not by disabling the gate.

## Step 11: Advanced patterns (propose for larger repos; don't apply unprompted)

These are proven production patterns for TS monorepos and larger apps. They cost setup time, so pitch them and get buy-in before applying.

### Parallel orchestrator instead of sequential bash

A sequential `check.sh` with 6+ gates commonly hits 2–3 min wall time. A Node orchestrator that fans gates out in parallel compresses that to the slowest single gate (usually tests).

```js
// scripts/lint-workflow.mjs
import { spawn } from "node:child_process";

const gates = [
  { name: "typecheck", cmd: "tsc", args: ["-b"] },
  { name: "eslint", cmd: "eslint", args: ["src", "--cache"] },
  { name: "prettier", cmd: "prettier", args: ["--check", "src"] },
  { name: "duplication", cmd: "jscpd", args: ["--config", "jscpd.json"] },
  { name: "knip", cmd: "knip", args: [] },
  { name: "tests", cmd: "vitest", args: ["run"] },
];

// spawn each, prefix stdout with [name], collect exit codes, Promise.all
const results = await Promise.all(gates.map(runGate));
const failed = results.filter((r) => r.code !== 0);
process.exit(failed.length ? 1 : 0);
```

Keep `check.sh` as a thin wrapper that calls the orchestrator so external consumers (CI, IDEs, hooks) still see a stable entry point.

### FTA for complexity

ESLint's per-function `complexity` rule is noisy. **FTA** (`fta-cli`) scores per file and correlates with review difficulty. Persist `reports/fta.json` as a tracked artifact so PR reviewers can diff complexity. Enforce a soft cap (warn ~50, fail ~70–80, calibrate per repo). For pre-commit speed, check only changed files:

```bash
node scripts/check-fta-cap.mjs --changed="$(git diff --cached --name-only | tr '\n' ',')"
```

### `jscpd.json` over CLI flags

Stable results across machines, especially once generated code is excluded:

```json
{
  "threshold": 2,
  "reporters": ["console"],
  "ignore": ["**/*.test.*", "**/*.stories.*", "**/generated/**", "dist/**"],
  "gitignore": true,
  "minLines": 10,
  "minTokens": 50
}
```

Lower thresholds (2–3%) become realistic once generated code and stories are ignored.

### Husky split: fast pre-commit, full pre-push

Pre-commit must be <15s or developers start using `--no-verify`. Split:

- **pre-commit (~10s)**: eslint on _staged_ files only (`lint-staged`), incremental typecheck.
- **pre-push (~45–90s)**: the full orchestrator — tests, duplication, knip, prettier check, complexity cap.

### FIXME.md non-blocking failure pattern

Instead of blocking every commit on lint errors, write failures to a tracked-but-gitignored `FIXME.md` at the repo root and let the commit proceed. Block `pre-push` if `FIXME.md` still exists. Keeps developers in flow while still enforcing cleanliness before publication.

### Per-changed-files mode everywhere

Every gate should accept `--changed=<list>` and check only those files when invoked from pre-commit. Full sweeps run on pre-push and CI. This is the single biggest factor in making a 10-gate setup fast enough to live with.

### Coverage the reliable way

Run tests with coverage as part of the orchestrator (`vitest run --coverage`), then have a Node script read `coverage/coverage-summary.json` and fail if any file is below a per-file threshold. Do not make coverage conditional on a file existing — make generating the file part of the gate.

### Project-specific gates belong in the orchestrator

Mature repos often need custom checks the template doesn't cover: test-inventory consistency, generated API contract freshness, logging-convention audits, monorepo alias assertions, bundle-size budgets. Add them as additional Node scripts invoked from the orchestrator — don't try to cram them into `check.sh`.

## Customization options

Ask the user if they want to adjust:

- **Max file length** — default 500 (via ESLint `max-lines`).
- **Duplicate threshold** — default 5% basic, 2% advanced (with exclusions).
- **Knip strictness** — ignore patterns via `knip.json`.
- **Coverage minimum** — only if adopting Step 11's coverage pattern.
- **Additional gates** — bundle size (`size-limit`), Lighthouse CI.
- **Monorepo support** — run gates per-package or from root.
