# Gate orchestration

If a compatible orchestrator exists, use it. If no canonical check exists, create this structure.

Official references:

- [Prek configuration and hook groups](https://prek.j178.dev/reference/configuration/)
- [Prek workspace mode](https://prek.j178.dev/workspace/)
- [Prek usage and hook stages](https://prek.j178.dev/usage/)
- [Prek GitHub Action](https://github.com/j178/prek-action)

## Contents

- [Package scripts](#package-scripts)
- [`check.sh`](#checksh)
- [Polyglot and workspace layouts](#polyglot-and-workspace-layouts)
- [jscpd](#jscpd)
- [`prek`](#prek)
- [CI](#ci)

## Package scripts

Adapt names and commands to the detected package manager and existing conventions:

```json
{
  "scripts": {
    "lint": "oxlint --type-aware --type-check --deny-warnings",
    "lint:fast": "oxlint --deny-warnings",
    "lint:fix": "oxlint --fix",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "deadcode": "knip",
    "duplicates": "jscpd --config jscpd.json",
    "test:coverage": "vitest run --coverage",
    "coverage:check": "node tools/check-coverage-ratchet.mjs --new-file-min 80",
    "check": "./check.sh"
  }
}
```

Adapt `test:coverage` to the established test runner. Copy the skill's `scripts/check-coverage-ratchet.mjs` to the shown repository path, or preserve an equivalent existing ratchet.

Keep the root Oxlint configuration syntax-only for this fast/full split. Oxlint currently has enabling flags for type-aware linting and type checking, but no CLI flags that disable root-enabled modes. If Oxlint provides all type diagnostics, do not add a separate typecheck script. Add build or framework scripts only for additional semantics.

Use the correct script/binary forms consistently:

| Manager | Run script | Run installed binary |
| --- | --- | --- |
| npm | `npm run NAME` | `npx --no-install BIN` |
| pnpm | `pnpm NAME` | `pnpm exec BIN` |
| Yarn | `yarn NAME` | `yarn exec BIN` |
| Bun | `bun run NAME` | `bunx --no-install BIN` |
| Deno | `deno task NAME` | use the pinned Deno command |

## `check.sh`

Hardcode the detected package manager commands in the generated file. Do not add runtime package-manager guessing to every check.

```bash
#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

MODE="${1:---full}"
FAILED=()

run_gate() {
  local name="$1"
  shift
  printf '\n▶ %s\n' "$name"
  if ! "$@"; then
    FAILED+=("$name")
  fi
  return 0
}

case "$MODE" in
  --fast)
    run_gate "Oxlint" npm run lint:fast
    run_gate "Format" npm run format:check
    ;;
  --full)
    run_gate "Oxlint + TypeScript diagnostics" npm run lint
    run_gate "Format" npm run format:check
    run_gate "Dead code" npm run deadcode
    run_gate "Duplicates" npm run duplicates
    run_gate "Reset coverage artifact" rm -f -- coverage/coverage-summary.json
    run_gate "Tests with coverage" npm run test:coverage
    run_gate "Coverage ratchet" npm run coverage:check
    # Add build or framework commands only when applicable.
    ;;
  --fix)
    run_gate "Oxlint fixes" npm run lint:fix
    run_gate "Format fixes" npm run format
    ;;
  *)
    printf 'Usage: %s [--fast|--full|--fix]\n' "$0" >&2
    exit 2
    ;;
esac

if ((${#FAILED[@]})); then
  printf '\nFailed gates:\n'
  printf '  - %s\n' "${FAILED[@]}"
  exit 1
fi

printf '\nAll quality gates passed.\n'
```

Do not use `set -e` with this runner. It can stop before the runner prints the failure summary. Keep the explicit `return 0`: `run_gate` records failures and the summary owns the final exit status.

For a large repository, use its task graph or a small Node orchestrator. Run independent gates in parallel.

If `--fix` can change only lint or format output, do not run tests from that path.

The `--fast` and `--full` modes do not modify tracked files. The full mode replaces generated coverage output. The `--fix` mode changes only lint and format output.

## Polyglot and workspace layouts

Do not replace a root gate that belongs to another language. Put the TypeScript gate in its project root, for example `frontend/check.sh`.

Use one of these integrations:

- Extend an existing root orchestrator with a named gate such as `run_gate "Frontend" ./frontend/check.sh --full`.
- Put a nested `.pre-commit-config.yaml` in the TypeScript project. Prek workspace mode discovers nested configurations and runs each one from its own project directory.
- Use the repository task graph if it already provides cross-language aggregation.

Run package-manager commands only from the directory that owns their lockfile. Keep hook IDs unique, such as `typescript-fast` and `typescript-full`; do not reuse a root ID such as `quality-gates`.

## jscpd

Commit stable policy in `jscpd.json`:

```json
{
  "threshold": 3,
  "reporters": ["console"],
  "ignore": [
    "**/*.snap",
    "**/fixtures/**",
    "**/generated/**",
    "dist/**",
    "build/**",
    "coverage/**"
  ],
  "gitignore": true,
  "absolute": false,
  "minLines": 10,
  "minTokens": 50
}
```

Calibrate the threshold to an existing baseline. Review findings before you exclude tests or stories.

## `prek`

Use the fast/full split by default:

```yaml
repos:
  - repo: local
    hooks:
      - id: typescript-fast
        name: TypeScript fast gates
        entry: ./check.sh --fast
        language: system
        pass_filenames: false
        always_run: true
        stages: [pre-commit]
        groups: [fast]
      - id: typescript-full
        name: TypeScript full gates
        entry: ./check.sh --full
        language: system
        pass_filenames: false
        always_run: true
        stages: [pre-push, manual]
        groups: [full, ci]
```

The fast gate uses syntax-aware Oxlint and the formatter check. The full gate uses type-aware Oxlint, compiler diagnostics, dead code, duplicates, tests, coverage, and required builds.

Install only one hook manager. If Husky is canonical, let Husky invoke the check or `prek run`.

Do not run `prek install` for the same hook types.

### A mutating pre-commit stage must stage what it rewrites

The split above keeps pre-commit non-mutating, which sidesteps this. If a
repository instead runs the fixer at pre-commit — `./check.sh --fix`, `oxlint
--fix`, a formatter write — then every commit that trips a formatter fails with
`files were modified by this hook` and has to be retyped. Prek compares the
unstaged diff before and after a hook, so a hook that rewrites a file and leaves
it unstaged always looks like a failure, even though the gate itself passed.

Staging the rewrites closes that diff and the commit proceeds on the first
attempt. Run the fixer through a wrapper rather than putting the logic in
`entry:`:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

./check.sh --fix

rewritten="$(git diff --name-only)"
[[ -n "$rewritten" ]] || exit 0

count="$(grep -c '' <<<"$rewritten")"
if [[ -n "${GIT_INDEX_FILE:-}" ]]; then
  git add -u
  printf '\n  auto-staged %s file(s) rewritten by --fix:\n' "$count"
else
  printf '\n  %s file(s) rewritten by --fix (not staged):\n' "$count"
fi
sed 's/^/    /' <<<"$rewritten"
```

Three things are load-bearing:

- **Gate on `GIT_INDEX_FILE`, not `PRE_COMMIT`.** The same hook also runs under
  a bare `prek run --all-files`, where nothing is stashed — there `git add -u`
  would sweep the developer's unrelated working-tree edits into the index. Git
  exports `GIT_INDEX_FILE` only when it runs a hook, so it separates the two
  modes; prek sets `PRE_COMMIT=1` in both and cannot. Measured inside a commit:
  `PRE_COMMIT=1 GIT_INDEX_FILE=.git/index`.
- **`git add -u`, never `git add -A`.** Updates tracked files only, so build
  output and scratch files are never committed by accident.
- **Print the paths.** A formatter edit that lands in a commit invisibly is
  worse than the failure it replaces. Prek hides hook stdout on success, so the
  list surfaces only when something else fails — which is the right time.

Its scope is bounded by the stash: during a commit the only tracked
modifications the wrapper can see are the content already staged plus the
fixer's own edits. One caveat remains — a fixer that reformats a tracked file
nobody touched (because it was committed unformatted) will sweep that file into
the commit. Formatting the repository once removes the case.

Verify it rather than assuming: commit a deliberately misformatted file and
confirm both that the commit succeeds without a second attempt and that the
recorded blob is the formatted one.

Prek stashes unstaged changes for pre-commit runs. Pause agents, editors, watchers, and generators that can change the tree during the hook. If that cannot be guaranteed, install only the pre-push hook for the slow suite and run the fast gate manually until the tree is stable.

Canonical manual verification:

```text
prek run --all-files --group full
```

CI selects the same full hook with `prek run --all-files --group ci`.

## CI

Install the repository's pinned runtime, package manager, and dependencies before Prek. Then run the same group used by the full gate.

```yaml
steps:
  - uses: actions/checkout@v6
  # Set up the pinned runtime and install frozen dependencies here.
  - uses: j178/prek-action@v2
    with:
      extra-args: "--all-files --group ci"
```

Pin action commits if repository policy requires immutable references. Do not repeat lint, test, or coverage commands in this workflow.
