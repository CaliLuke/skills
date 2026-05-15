---
name: ts-quality-gates
description: Set up TypeScript quality gates (typecheck, ESLint, Prettier, complexity, dead code, duplicates, coverage, file length) in any TS repo, wired through `prek` (pre-commit reimagined) with a `check.sh` orchestrator underneath. Use when the user says "add quality gates", "set up linting", "add ts checks", "quality gate setup", "add prek", "add check script", or wants to establish code quality infrastructure in a TypeScript project.
---

# TypeScript Quality Gates Setup

Set up a comprehensive quality gate system for a TypeScript project. The prescribed checker command is `prek run --all-files`. This creates a `.pre-commit-config.yaml` that points `prek` at a `check.sh` orchestrator, plus all supporting tool configs.

## Step 0: Inventory existing gates and implement the delta

Most TS repos have **some** gates already (a `lint` script, an `eslint.config.js`, an old `.prettierrc`) but not the full set this skill installs. The default behavior is to **fill in the missing gates**, not to stop. Only defer the whole job when every row of the checklist below is already ✅ or when the existing orchestrator is genuinely incompatible with adding gates (rare — see end of step).

Walk this checklist before writing anything. For each gate, check the listed signal; mark ✅ if present and working, ❌ if missing or broken on disk.

| Gate                                      | Detection signal                                                                                                  | Where to add if ❌ |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------ |
| `tsc` typecheck script                    | `package.json` has a `typecheck` (or equivalent) script invoking `tsc -b` / `tsc --noEmit`                        | Step 3             |
| ESLint flat config + lint script          | `eslint.config.*` (flat config, not legacy `.eslintrc*`) AND a `lint` script                                      | Step 4             |
| Prettier config + format-check script     | `.prettierrc*` / `prettier.config.*` AND a `format:check` script (or `prettier --check` in orchestrator)          | Step 5             |
| Knip dead-code gate                       | `knip` in devDeps AND invoked by orchestrator                                                                     | Step 6             |
| jscpd duplication gate                    | `jscpd` in devDeps AND invoked by orchestrator (with config or CLI threshold)                                     | Step 7 + check.sh  |
| File-length cap                           | ESLint `max-lines` rule configured, OR orchestrator runs a `wc -l` / `find` length check                          | Step 4 + check.sh  |
| Test + coverage script                    | `package.json` has a `test` script AND `coverage` script (or test command emits `coverage/coverage-summary.json`) | Step 7 + check.sh  |
| `check.sh` orchestrator                   | `check.sh` (or equivalent `scripts/lint-workflow.*`, `make check`) runs the full gate                             | Step 7             |
| `.pre-commit-config.yaml` + `prek` wiring | File exists and wires `check.sh` (or per-gate hooks) for `prek`/`pre-commit`                                      | Step 8             |

Run the existing orchestrator once (`npm run check`, `bun run lint:workflow`, `pnpm check`, `./check.sh`) before counting any ✅. A passing run earns it; a failing run means the gate is broken regardless of config presence — treat as ❌ and fix or replace.

Then report a short table to the user and **proceed to implement every ❌ row** without asking permission per row. Two modes:

- **No existing orchestrator** — create `check.sh` and `.pre-commit-config.yaml` per Steps 7–8; add only the gates the inventory marked ❌. Detect the package manager once (npm / pnpm / yarn / bun) and use it consistently — see Step 10's "Package manager — always use what the repo uses" table.
- **Existing orchestrator present** — **extend it** rather than replacing. Add scripts to `package.json`, append gate invocations to the existing `check.sh` / Node orchestrator (`scripts/lint-workflow.mjs`, etc.), or register new hooks in `.pre-commit-config.yaml`. Keep the user's entry point name. Only mention replacement if the orchestrator is structurally hostile to new gates (see below).

Two cases where you stop or ask first:

1. **Everything is ✅** — every gate is present and the orchestrator passes cleanly. Report "all gates already in place" and stop. Nothing to do.
2. **Incompatible orchestrator** — Nx/Turbo target with custom executors that owns lint config, a project-specific gate suite this skill's template overlaps with non-trivially (FTA complexity, test inventory, logging audits, API contract generation, duplication budgets). Ask whether to (a) wire missing gates into that system using its native idiom (Nx target dependencies, Turbo pipeline tasks), or (b) add `check.sh` + `prek` alongside as a developer-facing fast path (some duplication, stable second entry point). Don't auto-replace.

Conflict cases that need a one-line confirmation before proceeding (not a "stop entirely"):

- Legacy `.eslintrc.*` config (not flat config) — Step 4's flat-config template can't merge; ask whether to migrate or skip the ESLint gate.
- `biome.json` present — Biome is an ESLint+Prettier alternative; if it's already the canonical setup, skip the ESLint/Prettier rows and add the remaining gates (typecheck, knip, jscpd, tests) only.
- Husky hooks in `.husky/` AND a request to install `prek` — running both installs duplicate git hooks. Confirm which should drive (Step 8 covers this).

## Step 1: Assess the repo

Before creating anything, read the existing state:

1. Find `package.json` — identify the package manager (npm, pnpm, yarn, bun), existing scripts, and dependencies.
2. Check for existing config: `tsconfig*.json`, `eslint.config.*`, `.eslintrc*`, `biome.json`, `.prettierrc*`.
3. Check for existing `check.sh` or similar scripts.
4. Identify the source directory (usually `src/`).
5. Check if the project uses React (look for `react` in dependencies).

Report findings to the user and confirm before proceeding. Do NOT overwrite existing configs without asking.

## Step 2: Install dev dependencies

Use the detected package manager. Always add as devDependencies.

### Core (every TS project)

```text
typescript eslint @eslint/js typescript-eslint eslint-plugin-simple-import-sort jscpd knip prettier
```

Also install `prek` — the prescribed checker entry point. It reads `.pre-commit-config.yaml`, installs git hooks, and runs the gate. `check.sh` (Step 7) is the orchestrator underneath; `prek` just wraps it. `prek` is a per-machine tool, not a project dev-dependency:

```bash
brew install prek          # or: pip install prek, pipx install prek, cargo install --locked prek
```

### React projects (add these too)

```text
eslint-plugin-react eslint-plugin-react-hooks eslint-plugin-jsx-a11y
```

For npm, always use `--legacy-peer-deps` if the project already does (check for `.npmrc` or existing lockfile hints).

## Step 3: TypeScript config

If `tsconfig.json` exists, leave it alone. If not, create a sensible default with `strict: true`. Ensure the config has `"noEmit": true` or a build step that runs `tsc -b`.

Add a `typecheck` script to `package.json` if missing:

```json
"typecheck": "tsc -b"
```

## Step 4: ESLint config

Create `eslint.config.js` (flat config format, ESLint 9+). Adapt based on whether React is present.

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
    plugins: {
      "simple-import-sort": simpleImportSort,
    },
    rules: {
      // TypeScript
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/no-explicit-any": "error",

      // Import sorting
      "simple-import-sort/imports": "warn",
      "simple-import-sort/exports": "warn",

      // Code quality
      "max-lines": [
        "warn",
        { max: 500, skipBlankLines: true, skipComments: true },
      ],
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "prefer-const": "error",
      "no-var": "error",
      complexity: ["warn", 15],
      eqeqeq: ["error", "always"],
    },
  },
);
```

### React additions (merge into the config above)

Add plugins and rules:

```js
import reactPlugin from 'eslint-plugin-react'
import reactHooksPlugin from 'eslint-plugin-react-hooks'
import jsxA11yPlugin from 'eslint-plugin-jsx-a11y'

// In plugins:
react: reactPlugin,
'react-hooks': reactHooksPlugin,
'jsx-a11y': jsxA11yPlugin,

// In settings:
settings: { react: { version: 'detect' } },

// Additional rules:
'react-hooks/rules-of-hooks': 'error',
'react-hooks/exhaustive-deps': 'warn',
'react/jsx-no-target-blank': 'error',
'react/no-array-index-key': 'warn',
'react/self-closing-comp': 'warn',
'jsx-a11y/alt-text': 'warn',
'jsx-a11y/no-autofocus': 'warn',
'jsx-a11y/anchor-is-valid': 'warn',
```

Add lint scripts to `package.json` if missing:

```json
"lint": "eslint src",
"lint:fix": "eslint src --fix",
"check": "npm run typecheck && npm run lint"
```

Replace `src` with the actual source directory.

## Step 5: Prettier config

If no `.prettierrc` or `prettier.config.*` exists, create `.prettierrc` with sensible defaults:

```json
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2
}
```

Add format scripts to `package.json` if missing:

```json
"format": "prettier --write src",
"format:check": "prettier --check src"
```

## Step 6: Knip config (dead code detection)

Knip works zero-config for most projects. If the project has non-standard entry points or workspaces, create `knip.json`:

```json
{
  "entry": ["src/index.ts", "src/main.tsx"],
  "project": ["src/**/*.{ts,tsx}"],
  "ignore": ["src/**/*.test.{ts,tsx}", "src/**/*.d.ts"]
}
```

Knip finds unused files, exports, dependencies, and types. On first run in an existing codebase it may report many findings — triage with the user before enforcing as a gate.

## Step 7: Create `check.sh`

Create a `check.sh` at the project root. Make it executable (`chmod +x`).

Template — adapt the package manager commands (`npm run` / `pnpm` / `yarn` / `bun run`) and source directory:

```bash
#!/usr/bin/env bash
# Code quality gates — run before pushing.
# Usage: ./check.sh [--fix]
set -euo pipefail

FIX="${1:-}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Detect source dir — adjust if your project differs
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

# ── TypeScript: type check ───────────────────────────────────────────────────

run_gate "TypeScript: tsc type check" npm run typecheck

# ── TypeScript: lint ─────────────────────────────────────────────────────────

if [ "$FIX" = "--fix" ]; then
  run_gate "TypeScript: ESLint" npm run lint:fix
else
  run_gate "TypeScript: ESLint" npm run lint
fi

# ── TypeScript: file length ──────────────────────────────────────────────────

echo ""
echo "▶  TypeScript: file length (max 500 lines)"
TS_OVER=0
while IFS= read -r f; do
  lines=$(wc -l < "$f")
  if [ "$lines" -gt 500 ]; then
    echo "  $f: $lines lines (max 500)"
    TS_OVER=$((TS_OVER + 1))
  fi
done < <(find "$SRC_DIR" \( -name '*.ts' -o -name '*.tsx' \) -not -path '*/node_modules/*')
if [ "$TS_OVER" -gt 0 ]; then
  echo "  $TS_OVER file(s) over limit"
  FAILED+=("TypeScript: file length (max 500 lines)")
fi

# ── TypeScript: duplicate code ───────────────────────────────────────────────

run_gate "TypeScript: duplicate detection (jscpd)" \
  npx jscpd "$SRC_DIR" --min-lines 10 --min-tokens 50 --reporters console --threshold 5

# ── TypeScript: format check ────────────────────────────────────────────────

if [ "$FIX" = "--fix" ]; then
  run_gate "TypeScript: Prettier format" npx prettier --write "$SRC_DIR"
else
  run_gate "TypeScript: Prettier format" npx prettier --check "$SRC_DIR"
fi

# ── TypeScript: dead code / unused exports ──────────────────────────────────

run_gate "TypeScript: dead code detection (knip)" npx knip

# ── Tests (if test script exists) ────────────────────────────────────────────

if node -e "const p=JSON.parse(require('fs').readFileSync('package.json'));process.exit(p.scripts?.test?0:1)"; then
  run_gate "Tests" npm test
elif [ -f "vitest.config.ts" ] || [ -f "vitest.config.js" ]; then
  run_gate "Tests: vitest" npx vitest run
fi

# ── Test coverage (if vitest or jest with coverage) ─────────────────────────

if [ -f "coverage/coverage-summary.json" ]; then
  echo ""
  echo "▶  TypeScript: per-file coverage (min 30%)"
  node -e "
    const data = JSON.parse(require('fs').readFileSync('./coverage/coverage-summary.json','utf8'));
    const fails = [];
    for (const [path, info] of Object.entries(data)) {
      if (path === 'total') continue;
      const pct = info.statements.pct;
      if (pct < 30) fails.push([path, pct]);
    }
    if (fails.length) {
      fails.sort((a,b) => a[1]-b[1]).forEach(([p,pct]) => console.log('  ' + p + ': ' + pct + '% (min 30%)'));
      console.log('  ' + fails.length + ' file(s) below 30% coverage');
      process.exit(1);
    }
  " || FAILED+=("TypeScript: per-file coverage (min 30%)")
fi

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

## Step 8: Wire up `prek`

`prek` is the prescribed checker entry point — `.pre-commit-config.yaml` lets `prek` invoke `check.sh` from git hooks and from the command line under one stable interface. Even though `check.sh` runs fine on its own, route users through `prek` so the same gates fire on commit, on push, and on manual runs without three different invocations.

Create `.pre-commit-config.yaml` at the repo root:

```yaml
repos:
  - repo: local
    hooks:
      - id: quality-gates
        name: TypeScript quality gates
        entry: ./check.sh
        language: system
        pass_filenames: false
        always_run: true
        stages: [pre-commit, pre-push, manual]
```

`pass_filenames: false` and `always_run: true` matter: typecheck, knip, and coverage gates need to see the whole project, not a per-file slice.

If the repo already uses Husky, plan a migration path — running both Husky and prek installs duplicate hooks. Either remove `.husky/` or skip `prek install` and let Husky drive (calling `prek run` from a Husky hook).

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

For per-gate granularity (each tool as its own hook with its own file-type filter, plus separate fast and full stages), see Step 11.

## Step 9: Add to CLAUDE.md

If a `CLAUDE.md` exists in the repo, append a "Quality Gates" section with three commands: `prek run --all-files` (prescribed checker), `./check.sh --fix` (fix path), and `prek install` (one-time hook setup). If no `CLAUDE.md` exists, create one with this section plus basic commands.

## Step 10: Run it

Run `prek run --all-files` and fix any issues that come up. The first run usually surfaces:

- `prek: command not found` — install per Step 2 (`brew install prek`, `pip install prek`, etc.).
- Missing `type: "module"` in package.json (needed for ESM eslint config)
- Existing lint errors — fix them
- Files over 500 lines — report to user, split if asked
- Coverage gate needs `--coverage` flag on test runs (e.g. `vitest run --coverage` or `jest --coverage`) to generate `coverage/coverage-summary.json`. Add `"coverage": "vitest run --coverage"` to package.json scripts if using vitest.
- Knip may report many findings on first run in legacy codebases — triage with user before enforcing

## Step 11: Advanced patterns (recommend for larger repos)

The default `check.sh` is sequential bash — fine for small/medium repos. For larger codebases or repos with multiple gates, recommend these upgrades (patterns proven in production TS monorepos). Propose them; do not apply unprompted.

### Package manager — always use what the repo uses

Detect the package manager once (npm / pnpm / yarn / bun / deno) and use it in every generated script and doc. Never hardcode `npm run` or `npx` — **some projects cannot use bun, some cannot use npx, some are pinned to pnpm workspaces**. Map:

| PM   | run script    | run binary                    |
| ---- | ------------- | ----------------------------- |
| npm  | `npm run X`   | `npx Y`                       |
| pnpm | `pnpm X`      | `pnpm dlx Y` or `pnpm exec Y` |
| yarn | `yarn X`      | `yarn dlx Y`                  |
| bun  | `bun run X`   | `bunx Y`                      |
| deno | `deno task X` | `deno run …`                  |

If uncertain, ask the user before generating.

### Parallel orchestrator (Node script) instead of sequential bash

A sequential `check.sh` with 6+ gates easily hits 2–3 min wall time. A Node orchestrator that fans gates out in parallel with prefixed output typically cuts this to the slowest single gate (often tests). Pattern:

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

const results = await Promise.all(gates.map(runGate));
const failed = results.filter((r) => r.code !== 0);
process.exit(failed.length ? 1 : 0);
```

Prefix each gate's stdout with `[name]` and print a compact summary table at the end. Keep `check.sh` as a thin entry point that calls the orchestrator.

### FTA for complexity (replaces ESLint `complexity` rule)

`eslint-plugin` complexity rules fire per-function and are noisy. **FTA** (`fta-cli`) gives per-file scores that correlate with real review difficulty. Enforce a soft cap (warn around 50, fail around 70–80, calibrate per repo). Persist `reports/fta.json` as a tracked artifact so reviewers can diff complexity in PRs. Add an enforcement script that only checks changed files on pre-commit:

```bash
node scripts/check-fta-cap.mjs --changed="$(git diff --cached --name-only | tr '\n' ',')"
```

### `jscpd.json` instead of CLI flags

A config file ignoring generated code, stories, and tests gives stable results across machines:

```json
{
  "threshold": 2,
  "reporters": ["console"],
  "ignore": ["**/*.test.*", "**/*.stories.*", "**/generated/**", "dist/**"],
  "gitignore": true,
  "absolute": false,
  "minLines": 10,
  "minTokens": 50
}
```

Lower thresholds (2–3%) are realistic once generated code is excluded.

### Husky split: fast pre-commit, full pre-push

Pre-commit must be <15s or developers bypass it. Split:

- **pre-commit (~10s)**: eslint on _staged_ files only (`lint-staged`), typecheck with `--incremental`.
- **pre-push (~45–90s)**: full orchestrator — tests, duplication, knip, prettier check, complexity cap.

### FIXME.md non-blocking failure pattern

Instead of blocking every commit on lint errors, write failures to a tracked-but-gitignored `FIXME.md` at the repo root and let the commit proceed. Block `pre-push` if `FIXME.md` still exists. This keeps developers in flow while still enforcing cleanliness before publication.

### Per-changed-files mode for all gates

Every gate should accept `--changed=<list>` and check only those files when invoked from pre-commit. Full sweeps run on pre-push and CI. This is the single biggest factor in making a 10-gate setup fast enough to live with.

### Project-specific gates belong in the orchestrator

Mature repos often need custom checks the template doesn't cover: test-inventory CSV consistency, generated API contract freshness, logging-convention audits, monorepo alias assertions, bundle-size budgets. Add them as additional Node scripts invoked from the orchestrator — do not try to cram them into `check.sh`.

### Document the commands in CLAUDE.md / AGENTS.md

For any generated system, add a compact table to the repo's agent doc listing: what each gate checks, how long it takes, which hook it runs in, and the fix command. Agents reading the repo later will re-use the canonical commands instead of inventing parallel ones.

## Customization options

Ask the user if they want to adjust:

- **Max file length** — default 500, some projects prefer 300 or 800
- **Complexity threshold** — default 15, lower for stricter codebases
- **Duplicate threshold** — default 5%, raise for legacy codebases
- **Coverage minimum** — default 30% per-file, adjust up for mature projects
- **Knip strictness** — can ignore specific patterns via `knip.json`
- **Additional gates** — bundle size limits (`size-limit`), Lighthouse CI
- **Monorepo support** — run gates per-package or from root
