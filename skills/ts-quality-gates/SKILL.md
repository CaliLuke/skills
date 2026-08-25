---
name: ts-quality-gates
description: >-
  Set up or modernize TypeScript 7 quality gates with Oxlint as the only linter.
  Include type diagnostics, formatting, dead code, duplicates, tests, coverage,
  and prek hooks. Use for Oxlint migrations, ESLint replacement, faster TypeScript
  linting, check scripts, and pre-commit or pre-push enforcement.
---

# TypeScript 7 Quality Gates

Build a fast, repo-native gate. Use `prek run --all-files --group full` as the canonical local command.

Use Oxlint for all lint rules. Do not add an ESLint invocation. In the full gate, use one Oxlint program for lint and type diagnostics.

Read these references as needed:

- Read [references/typescript-7.md](references/typescript-7.md) before upgrading TypeScript, changing `tsconfig`, or working with framework/compiler-API dependencies.
- Read [references/oxlint.md](references/oxlint.md) before creating or migrating lint configuration.
- Read [references/adoption.md](references/adoption.md) before replacing a linter, introducing broad formatting changes, or enforcing new thresholds.
- Read [references/coverage.md](references/coverage.md) before adding or changing coverage enforcement.
- Read [references/orchestration.md](references/orchestration.md) before creating `check.sh`, package scripts, or `prek` hooks.

## 1. Inspect the repository

Gather the following before changing files:

1. Identify the repository root and every TypeScript project root. Read each applicable `package.json`, lockfile, `packageManager` field, and runtime pin.
2. Read `tsconfig*.json`, project references, build scripts, and generated-code paths.
3. Detect application and framework boundaries: Node, browser/bundler, React, Next.js, Vue, Svelte, Astro, Angular, MDX, tests, and Storybook.
4. Read existing Oxlint, ESLint, Biome, Deno, Prettier/Oxfmt, Knip, jscpd, coverage, CI, hook, and orchestrator configuration.
5. Read `AGENTS.md`, `CLAUDE.md`, and contributor docs for canonical commands and constraints.
6. Read root and nested gate scripts. Record which working directory and package manager each command requires.
7. Read `.pre-commit-config.yaml` files and existing hook IDs before you add a hook.
8. Run `git status --short`. If the command is safe and bounded, run the existing canonical check once.

Count a configured gate as working only after it passes.

Detect the package manager for each TypeScript project root. Use its pinned manager in that project. A polyglot repository can use another tool outside that root.

## 2. Inventory the gate

Report a compact table with `working`, `missing`, `broken`, or `not applicable` for each row:

| Gate | Working signal |
| --- | --- |
| TypeScript 7 compatibility | Native `tsc` can load every production `tsconfig` without removed options |
| Oxlint baseline | Oxlint configuration and script run successfully with warnings enforced |
| Type-aware lint | `oxlint-tsgolint@7` is installed and the full Oxlint command enables type-aware mode |
| Type diagnostics | The full Oxlint command enables type checking, or an explicit native/framework checker covers additional semantics |
| Build/emit | Required only when the repo emits JS/declarations or validates project references |
| Formatting | Existing formatter has a non-mutating check command |
| Dead code | Knip runs from the canonical gate with reviewed entry points |
| Duplicates | jscpd runs with generated, fixture, and vendor paths excluded |
| Complexity/file size | Oxlint enforces calibrated `complexity` and `max-lines` rules |
| Tests/coverage | Tests emit the required coverage artifact and a committed ratchet rejects regressions |
| Orchestrator | Root or nested checks run every applicable gate from the correct working directory |
| Hooks | Unique `prek` hooks expose a fast pre-commit and full pre-push/manual gate |
| CI | CI runs the same full entry point and cannot bypass it |

Implement each missing or broken row. If every applicable row works, stop.

If another system owns the gate, identify its native integration. If this integration requires a choice, ask the user.

Ask before replacing an established formatter, hook manager, or build orchestrator. Extend compatible systems instead of adding a parallel one.

## 3. Plan safe adoption

Read [references/adoption.md](references/adoption.md). Adopt the gate from a clean tree or isolate its changes from active work.

- Put a repository-wide formatter migration in a separate change with zero behavior changes.
- Measure current coverage, duplication, dead-code, complexity, and file-size results before enforcement.
- Commit or document ratchet baselines. Do not choose arbitrary greenfield thresholds for a legacy project.
- Do not mix gate infrastructure, mass automatic fixes, and product logic in one change.
- Coordinate with active agents, editors, and watchers before a hook stashes unstaged changes.

## 4. Choose the TypeScript 7 path

Use one of these paths:

- **Native TypeScript 7:** Install `typescript@^7`, use its `tsc`, migrate removed options, and use Oxlint type-aware mode.
- **TypeScript 7 plus API compatibility:** Keep native TypeScript 7 for the CLI. Install the TypeScript 6 compatibility package for API consumers. Follow [references/typescript-7.md](references/typescript-7.md).
- **Framework-constrained transition:** Keep the supported framework checker for embedded files. Use Oxlint for JS/TS files. Document the reason for the split.

Do not add `ignoreDeprecations` to force a TypeScript 7 migration. Remove or replace deprecated options.

Keep explicit compiler options that communicate runtime intent. A matching TypeScript 7 default does not remove this requirement.

## 5. Install only required tools

Add the core project tools as development dependencies with the detected package manager:

```text
typescript@^7 oxlint oxlint-tsgolint@7 knip jscpd
```

If a formatter exists, keep it. If no formatter exists, add Prettier.

If the user requests test tools and no runner exists, add test and coverage packages.

Install `prek` as a per-machine tool, not a project dependency:

```text
brew install prek
# alternatives: uv tool install prek, pipx install prek, cargo binstall prek
```

If compiler-API consumers require the TypeScript 6 compatibility package, use the package layout from [references/typescript-7.md](references/typescript-7.md) instead of installing only `typescript@^7`.

Use a version of `oxlint-tsgolint` that tracks the repository's TypeScript 7 release. Do not blindly update one without the other.

## 6. Configure Oxlint as the only linter

For a new setup, create `.oxlintrc.json` or `oxlint.config.ts`. If the runtime cannot execute TypeScript files, use JSON.

Start with Oxlint correctness defaults. Add only high-signal policy rules. Keep the root configuration syntax-only when the repository has separate fast and full gates; enable type-aware linting and compiler diagnostics on the full command.

```jsonc
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "ignorePatterns": ["dist/**", "build/**", "coverage/**", "**/generated/**"],
  "categories": {
    "correctness": "error",
    "suspicious": "warn",
    "perf": "warn"
  },
  "rules": {
    "typescript/no-floating-promises": "error",
    "typescript/no-misused-promises": "error",
    "typescript/no-explicit-any": "error",
    "eslint/complexity": ["warn", { "max": 15 }],
    "eslint/max-lines": ["warn", { "max": 500, "skipBlankLines": true, "skipComments": true }],
    "eslint/no-console": ["warn", { "allow": ["warn", "error"] }]
  }
}
```

Adapt the configuration to the project:

- If the repository uses a built-in plugin, enable it.
- If an existing plugin rule is not native, use `jsPlugins`. Keep its package. Do not keep the ESLint runner.
- Add overrides for tests, scripts, configuration files, generated code, and framework files.
- Run the full pass with `oxlint --type-aware --type-check --deny-warnings`. Fail CI warnings; do not accumulate permanent warning noise.
- Use `oxlint --print-config path/to/file.ts` to verify representative files and `oxlint --debug timings` to investigate slow type-aware rules.

If an ESLint flat configuration exists, run `@oxlint/migrate --type-aware`. Review each migrated rule and override.

Remove ESLint only after Oxlint reproduces the policy. Report each unsupported parser, file type, or rule. Do not drop it silently.

## 7. Avoid duplicate type checking

Run `oxlint --type-aware --type-check --deny-warnings` as the default full application gate. Oxlint and `tsgolint` then share one TypeScript program for typed rules and compiler diagnostics.

If every Oxlint invocation should be typed, the root configuration can instead set `options.typeAware: true` and `options.typeCheck: true`. Do not use that configuration for a fast/full split: current Oxlint can enable these modes from the CLI but cannot disable them with `--type-aware=false` or `--type-check=false`.

If a separate checker validates additional semantics, add it. Use one of these cases:

- JavaScript or declaration emit
- Project-reference build ordering
- Declaration-map or API-extractor inputs
- Framework templates or embedded languages
- A repository-specific build transform

Name the script for its function. Use `build`, `build:types`, or `typecheck:framework`. Do not run the same diagnostic pass twice.

## 8. Configure the remaining gates

Preserve existing policies where present. For a new setup:

- Add `format:check` and `format` scripts for the chosen formatter. Include all files that the project owns.
- Before you enforce Knip, run it once. Verify its framework plugins and entry points. Start with unused files and dependencies as errors. Keep unused exports and types as warnings until the backlog is clean.
- Prefer a committed `jscpd.json` with stable exclusions over long CLI flags. Exclude generated, vendored, fixture, snapshot, and build outputs.
- Enforce complexity and file length in Oxlint rather than a shell `find` loop.
- Run the existing test command. Make the gate fail if its required coverage artifact is missing.
- Preserve an established coverage policy. Otherwise, commit a per-file baseline and reject regressions. Follow [references/coverage.md](references/coverage.md).

## 9. Wire the canonical gate

If an orchestrator exists, extend it. Otherwise, create `check.sh` from [references/orchestration.md](references/orchestration.md). Make it executable. Add each package script.

Create or extend `.pre-commit-config.yaml`. Use unique hook IDs. Make `prek run --all-files --group full` run the canonical full gate.

Use a fast, non-mutating pre-commit gate. Put type-aware lint, dead code, duplicates, tests, coverage, and builds in pre-push, manual, and CI. Do not install Husky and `prek` hooks for the same stage.

Document these commands in the repository's existing agent/contributor guide:

```text
prek run --all-files --group full   # canonical full check
./check.sh --fix       # safe automatic fixes
prek install --hook-type pre-commit --hook-type pre-push
```

If a canonical guide exists, do not create a new `CLAUDE.md` solely for these commands.

## 10. Enforce the gate in CI

Run the same full entry point in CI. Do not duplicate its commands in workflow YAML. Use `prek run --all-files --group ci` after the repository installs its pinned runtime and dependencies.

Pin third-party actions according to repository policy. See [references/orchestration.md](references/orchestration.md) for a minimal workflow.

## 11. Verify

Run, in order:

1. If the task authorizes fixes, run the Oxlint fix path. Then run the formatter fix path.
2. `oxlint --print-config` for representative source, test, and framework files.
3. The canonical package scripts individually so failures identify the responsible tool.
4. `prek run --all-files --group full` as the end-to-end verification.
5. If emit or framework integration is in scope, run the normal build.

Review the final diff. Find unrelated changes, removed rules, broad ignores, lockfile errors, duplicate diagnostics, and incorrect package-manager commands.

Report the final gate composition, TypeScript 7 migration decisions, any compatibility package retained, measured command results, and remaining baseline findings.
