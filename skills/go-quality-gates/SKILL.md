---
name: go-quality-gates
description: Set up Go quality gates (build, vet, golangci-lint, goimports, duplicates, dead code, complexity, mod tidy drift, coverage) in any Go repo, wired through `prek` (pre-commit reimagined) with a `check.sh` orchestrator underneath. Use when the user says "add quality gates for Go", "set up Go linting", "add golangci-lint", "add go checks", "Go quality gate setup", "add prek for Go", or wants to establish code quality infrastructure in a Go project (as opposed to TypeScript or Python).
---

# Go Quality Gates Setup

Set up a quality gate system for a Go project. The prescribed checker command is `prek run --all-files`. The deliverables are a `.pre-commit-config.yaml` that points `prek` at a `check.sh` orchestrator, a `.golangci.yml` config, and any extra tool configs (`dupl`, `deadcode`, `gocyclo`) — wired to the repo's actual module layout and build tags. For larger repos, Step 12 describes the upgrades that production setups use.

## Step 1: Assess the repo before touching anything

Before writing or installing anything, understand the repo. Two outcomes are possible: a **mature system already exists** (stop and defer — Step 2), or it doesn't (proceed from Step 3).

Gather in parallel:

1. `go.mod` / `go.work` — Go version, module path, workspace layout, existing dependencies.
2. Existing config files: `.golangci.yml` / `.golangci.yaml` / `.golangci.toml`, `.revive.toml`, `staticcheck.conf`, `.goreleaser.yml`, `.pre-commit-config.yaml`, any `scripts/check*.sh` / `scripts/lint*.sh` / `Makefile` targets (`make check`, `make lint`, `make test`).
3. `CLAUDE.md` / `AGENTS.md` — canonical commands already documented.
4. Source layout: top-level `cmd/`, `internal/`, `pkg/`, nested modules, build tags (`//go:build cgo`, `//go:build integration`), generated files (`*_gen.go`, `zz_generated_*.go`).
5. CGo / native deps — look for `CGO_ENABLED`, `CGO_LDFLAGS`, or `cgo` build tags; these change how every gate must be invoked.

### Build tags and CGo — detect once, use everywhere

Go is simpler than JS here (one toolchain, no package managers), but build tags are the equivalent trap. **Some repos cannot run `go test ./...` without `CGO_ENABLED=1` and specific tags**, and running it without them produces silent no-ops for tagged files or, worse, link failures. Check for:

- `GOFLAGS` in the environment or in `Makefile` / `scripts/*.sh`.
- `//go:build` directives in packages you plan to gate.
- Existing pre-push hooks (`.githooks/pre-push`, `.husky/`) that already set `CGO_LDFLAGS`, `MACOSX_DEPLOYMENT_TARGET`, etc.

Throughout this skill, `<GOFLAGS>` means whatever tag/env combination the repo already uses. If the detected setup is ambiguous or tag-gated packages exist, ask before generating.

## Step 2: Inventory existing gates and implement the delta

Most Go repos have **some** gates already (a `Makefile` running `go vet`, a stale `.golangci.yml`, a pre-push hook calling `gofmt`) but not the full set this skill installs. The default behavior is to **fill in the missing gates**, not to stop. Only defer the whole job when every row of the checklist below is already ✅ or when the existing orchestrator is genuinely incompatible with adding gates (rare — see end of step).

Walk this checklist before writing anything. For each gate, check the listed signal; mark ✅ if present and working, ❌ if missing or broken on disk.

| Gate                                      | Detection signal                                                                                               | Where to add if ❌ |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------ |
| `go build` / `go vet` baseline            | Always available in a Go module                                                                                | Step 4 invocation  |
| `.golangci.yml` config                    | `.golangci.yml` / `.golangci.yaml` / `.golangci.toml` exists with `version: "2"` and a non-trivial linter list | Step 5             |
| goimports formatting check                | Existing orchestrator runs `goimports -l` or `gofmt -l` with a non-empty-output failure                        | Step 6 + check.sh  |
| `go mod tidy` drift check                 | Existing orchestrator detects drift after running `go mod tidy`                                                | Step 8             |
| `deadcode` reachability gate              | Tool installed AND invoked by orchestrator (binary repos only — skip for libraries; see Step 7)                | Step 7 + check.sh  |
| `dupl` duplication gate                   | Tool installed AND invoked by orchestrator                                                                     | Step 7 + check.sh  |
| Test gate                                 | Existing orchestrator runs `go test ./...` (ideally with `-race`)                                              | Step 8             |
| `check.sh` orchestrator                   | `check.sh` (or equivalent `Makefile`/`scripts/check.sh` target) runs the full gate sequentially                | Step 8             |
| `.pre-commit-config.yaml` + `prek` wiring | File exists and wires `check.sh` (or per-gate hooks) for `prek`/`pre-commit`                                   | Step 9             |

Run the existing orchestrator once (`make check`, `scripts/check.sh`, `./check.sh`) before counting any ✅. A passing run earns it; a failing run means the gate is broken regardless of config presence — treat as ❌ and fix or replace.

Then report a short table to the user and **proceed to implement every ❌ row** without asking permission per row. Two modes:

- **No existing orchestrator** — create `check.sh` and `.pre-commit-config.yaml` per Steps 8–9; add only the gates the inventory marked ❌.
- **Existing orchestrator present** — **extend it** rather than replacing. Add new targets to the `Makefile`, append gate invocations to the existing `check.sh`, or register new hooks in `.pre-commit-config.yaml`. Keep the user's entry point name. Only mention replacement if the orchestrator is structurally hostile to new gates (see below).

Two cases where you stop or ask first:

1. **Everything is ✅** — every gate is present and the orchestrator passes cleanly. Report "all gates already in place" and stop. Nothing to do.
2. **Incompatible orchestrator** — Bazel rules, a vendored CI runner that owns the lint config and forbids local invocation, a project-specific gate suite that overlaps non-trivially with this skill's (custom CGo cross-compile checks, generated-code freshness, schema-drift checks, protobuf regen, vuln scanning, license audits). Ask whether to (a) wire missing gates into that system using its native idiom, or (b) add `check.sh` + `prek` alongside as a developer-facing fast path (some duplication, stable second entry point). Don't auto-replace.

Conflict cases that need a one-line confirmation before proceeding (not a "stop entirely"):

- A pre-v2 `.golangci.yml` (no `version:` key, or `version: "1"`) — the v2 schema in Step 5 won't merge cleanly; ask whether to migrate or leave as-is and add missing gates outside golangci-lint.
- An existing `tools.go` with pinned tool versions different from Step 3's `@latest` — prefer the repo's pins; don't bump versions silently.
- CGo / build-tag setup that means `go test ./...` silently no-ops on some packages — confirm the right `GOFLAGS` / `CGO_ENABLED` invocation before generating.

## Step 3: Install dev tools

Go tools are installed per-user with `go install`, not as project dependencies. Prefer pinning versions via `tools.go` or a `Makefile` install target so CI gets the same versions as developers.

### Core (every Go project)

```text
github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest  # meta-linter (govet, staticcheck, errcheck, unused, ineffassign, etc.)
golang.org/x/tools/cmd/goimports@latest                        # format + import management
```

Also install `prek` — the prescribed checker entry point. It reads `.pre-commit-config.yaml`, installs git hooks, and runs the gate. `check.sh` (Step 8) is the orchestrator underneath; `prek` just wraps it.

```text
cargo install --locked prek    # or: brew install prek, pip install prek, pipx install prek
```

As of golangci-lint v2 (2024+), `gosimple` was merged into `staticcheck` — don't list it separately anywhere, the config will fail to validate.

### Recommended add-ons

```text
golang.org/x/tools/cmd/deadcode@latest                       # dead code (reachability-based, more accurate than `unused`)
github.com/mibk/dupl@latest                                  # copy-paste duplication
github.com/fzipp/gocyclo/cmd/gocyclo@latest                  # cyclomatic complexity
golang.org/x/vuln/cmd/govulncheck@latest                     # known CVEs in deps
```

If the repo already has a `tools.go` file with `// +build tools` or `//go:build tools`, add tool imports there and let `go install` pick them up from `go.mod`. That pins versions for reproducible CI.

`gofmt` and `go vet` are part of the toolchain — nothing to install.

## Step 4: Build + vet as the baseline

`go build ./...` and `go vet ./...` are the floor. They require no config, catch real bugs, and run fast. If either fails on a clean checkout, stop and fix before adding further gates — there is no point layering linters on top of a repo that doesn't build.

If the repo needs tags or CGo env, record the exact invocation in `check.sh` rather than assuming `./...` works bare:

```bash
# Example — adapt to the repo's detected flags
CGO_ENABLED=1 GOFLAGS="-tags=cgo,integration" go build ./...
```

## Step 5: golangci-lint config

`golangci-lint` aggregates ~20 of the linters you'd otherwise wire up individually. Create `.golangci.yml` at the repo root. This config is deliberately strict-but-practical — fail loudly on real bugs, warn on style, leave room for the user to tune.

```yaml
version: "2"

run:
  timeout: 5m
  tests: true
  # If the repo uses build tags (CGo, integration, etc.), list them here so
  # rowserrcheck/sqlclosecheck/etc. can see tag-gated files. Without this, linters
  # silently skip those packages and you get no signal from them.
  # build-tags:
  #   - cgo
  #   - integration
  # Directory-level exclusions belong here, not in `exclusions.paths` — these are
  # cheaper (golangci never loads the packages) and survive upgrades better.
  skip-dirs:
    - ^gen$
    - ^gen/
    - ^vendor$
    - ^vendor/
    - ^third_party$
    - ^third_party/
  skip-files:
    - _generated\.go$

linters:
  # `default: standard` auto-enables the v2 baseline (govet, errcheck, ineffassign,
  # staticcheck, unused). Prefer it over `default: none` + enumerating — the enumeration
  # silently drifts from v2 defaults on every golangci-lint upgrade. Use `default: none`
  # only when you actively want to pin exactly which linters run.
  default: standard
  enable:
    # Style / hygiene — gofmt/goimports live under `formatters:` in v2, not here
    - revive
    - misspell
    - unconvert
    - unparam
    # Bug-prone patterns
    - bodyclose
    - nilerr
    - errorlint
    - rowserrcheck
    - sqlclosecheck

  settings:
    govet:
      enable-all: true
      disable:
        - fieldalignment # noisy; enable only if you care about struct packing
    revive:
      rules:
        - name: exported
          disabled: true # enable when public API docs are a priority
    errcheck:
      check-type-assertions: true
      # check-blank: true  # uncomment only for max strictness; very noisy on real repos

  exclusions:
    generated: lax # skip generated files (detected via `// Code generated … DO NOT EDIT.` header)
    rules:
      - path: _test\.go
        linters: [errcheck, unparam, unused]

formatters:
  enable:
    - gofmt
    - goimports
```

Notes on deliberate omissions:

- **`gocyclo` / `gocognit` / `cyclop` linters are off** — they fire per-function with arbitrary thresholds and produce noise developers learn to ignore. Step 12 shows how to track per-file complexity as a tracked metric instead.
- **`funlen` / `lll` off** — function length and line length correlate poorly with defect rate. Use `max-lines`-style per-file caps in the orchestrator if you want file-size pressure.
- **`depguard` / `gochecknoglobals` off by default** — project-specific policy, enable when the user asks.

## Step 6: Formatting (gofmt + goimports)

Go has an unambiguous canonical format. There is no bikeshedding config (unlike Prettier). `goimports` is a superset of `gofmt` that also manages imports — prefer it.

The `gofmt` and `goimports` linters inside `golangci-lint` already check formatting. For the `--fix` path, the `check.sh` script below calls `goimports -w` directly.

If the repo uses a custom import grouping (e.g. stdlib / external / internal with a local prefix), set it in `.golangci.yml`:

```yaml
formatters:
  settings:
    goimports:
      local-prefixes:
        - github.com/your-org/your-repo
```

## Step 7: Dead code, duplication, complexity

These are cheap to run and catch things the core linters miss.

### deadcode

```bash
deadcode -test ./...
```

More accurate than golangci-lint's `unused` for cross-package reachability — **but only for binaries.** `deadcode` starts from `main` and walks the call graph, so in a library or a repo that exposes exported API for external consumers it will flag huge swaths of legitimately-used code. For libraries, either scope the command to `./cmd/...` or skip this gate and rely on `unused`. First run on a legacy codebase may report many findings — triage with the user before enforcing. Adjust via `-filter` flags rather than disabling the gate.

### dupl

```bash
dupl -threshold 50 ./...
```

Threshold is tokens, not lines. 50 catches meaningful copy-paste without firing on trivial repetition. Raise to 75–100 for noisier codebases.

### gocyclo (reporting, not blocking)

```bash
gocyclo -over 15 -avg $(go list -f '{{.Dir}}' ./...)
```

Passing package dirs from `go list` avoids walking `vendor/`, `.git/`, and other noise that a bare `.` would include.

Report functions over 15; use as a signal, not a hard gate (the skill does not fail on this by default — the threshold is a judgment call). Step 12 shows a per-file tracked metric approach instead.

## Step 8: Create `check.sh`

A thin bash entry point that calls each gate sequentially. Fine for small/medium repos; see Step 12 for the parallel-orchestrator upgrade.

Substitute `<GOFLAGS>` and any CGo env from Step 1. Do **not** leave the placeholders literal in the generated file.

```bash
#!/usr/bin/env bash
# Code quality gates — run before pushing.
# Usage: ./check.sh [--fix]
set -euo pipefail

FIX="${1:-}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Adapt these to the repo's detected build setup (Step 1).
export CGO_ENABLED="${CGO_ENABLED:-1}"
# export GOFLAGS="-tags=cgo,integration"

echo "══════════════════════════════════════"
echo "  Go Quality Gates"
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

# Build — the floor
run_gate "go build" go build ./...

# Vet — builtin static analysis
run_gate "go vet" go vet ./...

# Package dirs from `go list` — avoids walking vendor/, .git/, and ignored paths.
PKG_DIRS=$(go list -f '{{.Dir}}' ./... | tr '\n' ' ')

# Formatting — goimports is a superset of gofmt
if [ "$FIX" = "--fix" ]; then
  run_gate "goimports (write)" bash -c "goimports -w $PKG_DIRS"
else
  # -l lists files that would change; non-empty output = failure
  run_gate "goimports (check)" bash -c "
    out=\$(goimports -l $PKG_DIRS)
    if [ -n \"\$out\" ]; then
      echo \"\$out\"
      exit 1
    fi
  "
fi

# go mod tidy drift — catches missing/unused deps before they break downstream builds
run_gate "go mod tidy (drift)" bash -c '
  cp go.mod go.mod.bak; cp go.sum go.sum.bak 2>/dev/null || true
  go mod tidy
  diff=$(diff -u go.mod.bak go.mod || true)
  sumdiff=$(diff -u go.sum.bak go.sum 2>/dev/null || true)
  mv go.mod.bak go.mod; mv go.sum.bak go.sum 2>/dev/null || true
  if [ -n "$diff" ] || [ -n "$sumdiff" ]; then
    echo "go.mod/go.sum out of sync — run: go mod tidy"
    echo "$diff"; echo "$sumdiff"
    exit 1
  fi
'

# golangci-lint (aggregate of govet, staticcheck, errcheck, unused, ...)
if [ "$FIX" = "--fix" ]; then
  run_gate "golangci-lint" golangci-lint run --fix
else
  run_gate "golangci-lint" golangci-lint run
fi

# Dead code (reachability)
if command -v deadcode >/dev/null 2>&1; then
  run_gate "deadcode" bash -c '
    out=$(deadcode -test ./...)
    if [ -n "$out" ]; then
      echo "$out"
      exit 1
    fi
  '
fi

# Duplication — dupl exits 0 even on findings, so gate on output being empty
if command -v dupl >/dev/null 2>&1; then
  run_gate "dupl" bash -c "
    out=\$(dupl -threshold 50 $PKG_DIRS)
    if [ -n \"\$out\" ]; then
      echo \"\$out\"
      exit 1
    fi
  "
fi

# Tests — only if there are _test.go files. -race is strongly recommended for
# any package doing concurrency; add it once your test suite is clean under it.
if find . -name '*_test.go' -not -path './vendor/*' -print -quit | grep -q .; then
  run_gate "go test" go test ./... -timeout 120s
  # Upgrade to: go test ./... -race -count=1 -timeout 120s
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

- **Bash file-length loop** — file size is a weak signal in Go; most large files are generated code or legitimate package-level orchestrators. Track it as a metric (Step 12) rather than a hard gate.
- **Coverage gate** — needs `go test -coverprofile=…` across the whole tree plus a summarizer. Making it conditional on a file existing silently no-ops when coverage wasn't generated. If you want coverage enforcement, see the reliable pattern in Step 11.
- **`govulncheck`** — valuable but network-dependent and can flake in air-gapped CI. Add in Step 12 once the core gate is stable.
- **Auto-creating `CLAUDE.md`** — an agent shouldn't fabricate agent docs the user didn't ask for.

Make the file executable: `chmod +x check.sh`.

## Step 9: Wire up `prek`

`prek` is the prescribed checker entry point — `.pre-commit-config.yaml` lets `prek` invoke `check.sh` from git hooks and from the command line under one stable interface. Even though `check.sh` runs fine on its own, route users through `prek` so the same gates fire on commit, on push, and on manual runs without three different invocations.

Create `.pre-commit-config.yaml` at the repo root:

```yaml
repos:
  - repo: local
    hooks:
      - id: quality-gates
        name: Go quality gates
        entry: ./check.sh
        language: system
        pass_filenames: false
        always_run: true
        stages: [pre-commit, pre-push, manual]
```

`pass_filenames: false` and `always_run: true` matter: Go gates run against `./...` (the whole module), not per-file, so we don't want `prek` to pass the staged file list to `check.sh` or skip the run when nothing Go-shaped changed.

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

For per-gate granularity (each tool as its own hook with its own file-type filter, plus separate fast and full stages), see Step 12.

## Step 10: Document (existing docs only)

If the repo already has `CLAUDE.md` or `AGENTS.md`, append a compact "Quality Gates" section:

```markdown
## Quality Gates

- `prek run --all-files` — runs all gates (~60s) — prescribed entry point
- `./check.sh --fix` — auto-fix path (prek doesn't pass flags through)
- `prek install` — wire up git hooks (one-time per checkout)

Gates: build · vet · goimports · golangci-lint · deadcode · dupl (+ go test if present).
```

Do **not** create `CLAUDE.md` just to document the gates. That's agent-clutter the user didn't ask for; the `check.sh` header comment and `Makefile` are self-documenting.

## Step 11: First run

Run `prek run --all-files` and fix anything that comes up. Expect:

- `prek: command not found` — install per Step 3 (`brew install prek`, `cargo install --locked prek`, or `pip install prek`).
- Missing tools — `goimports`, `deadcode`, `dupl` not on `$PATH`. Add `GOPATH/bin` to `$PATH` or install with `go install` as per Step 3.
- Build failures on a fresh clone because of missing CGo env — add the flags to `check.sh`'s `export` block based on what Step 1 detected.
- Pre-existing lint errors — fix before calling the setup done. If the volume is large, adjust `.golangci.yml` `exclusions` rather than disabling linters wholesale.
- `deadcode` flagging large swaths of code on library-style repos that expose public API — it reports unreachable-from-`main` by default, which is wrong for libraries. Either scope the command to `./cmd/...` or switch to `unused` (weaker but library-aware).

## Step 12: Advanced patterns (propose for larger repos; don't apply unprompted)

These are proven production patterns for Go monorepos and larger services. They cost setup time, so pitch them and get buy-in before applying.

### Parallel orchestrator instead of sequential bash

A sequential `check.sh` with 6+ gates commonly hits 2–3 min wall time. A Go orchestrator (or a `make -j` target) that fans gates out in parallel compresses that to the slowest single gate (usually tests).

```go
// cmd/check/main.go — requires Go 1.22+ for per-iteration loop variable semantics
package main

import (
    "context"
    "fmt"
    "os"
    "os/exec"
    "sync"
    "time"
)

type gate struct {
    name string
    argv []string
}

type result struct {
    name   string
    output []byte
    err    error
}

func main() {
    gates := []gate{
        {"build",    []string{"go", "build", "./..."}},
        {"vet",      []string{"go", "vet", "./..."}},
        {"lint",     []string{"golangci-lint", "run"}},
        {"deadcode", []string{"deadcode", "-test", "./..."}},
        {"dupl",     []string{"dupl", "-threshold", "50", "./..."}},
        {"test",     []string{"go", "test", "./...", "-race", "-timeout", "120s"}},
    }

    // One global deadline — a hung gate can't pin the whole run.
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
    defer cancel()

    var wg sync.WaitGroup
    results := make([]result, len(gates))

    for i, g := range gates {
        wg.Add(1)
        go func(i int, g gate) {
            defer wg.Done()
            cmd := exec.CommandContext(ctx, g.argv[0], g.argv[1:]...)
            out, err := cmd.CombinedOutput()
            results[i] = result{name: g.name, output: out, err: err}
        }(i, g)
    }
    wg.Wait()

    // Print in deterministic order after all gates finish — avoids interleaving.
    var failed []string
    for _, r := range results {
        fmt.Printf("── %s ──\n%s\n", r.name, r.output)
        if r.err != nil {
            failed = append(failed, r.name)
        }
    }
    if len(failed) > 0 {
        for _, n := range failed {
            fmt.Fprintln(os.Stderr, "FAIL:", n)
        }
        os.Exit(1)
    }
}
```

Note: for a more polished experience, wrap each gate's stdout/stderr in a per-gate `io.Writer` that prefixes every line with `[name]` and streams live; that's worth the complexity once the orchestrator is your daily driver. The version above is the minimal correct shape — parallel, bounded, deterministic output.

Keep `check.sh` as a thin wrapper that calls the orchestrator so external consumers (CI, IDEs, hooks) still see a stable entry point.

### Per-file complexity as a tracked metric

ESLint-style per-function complexity gates are noisy in Go too. Persist `reports/gocyclo.txt` (sorted output of `gocyclo -avg .`) as a tracked artifact so PR reviewers can diff complexity. Enforce a soft cap (warn ~15, fail ~25, calibrate per repo). For pre-commit speed, check only changed packages:

```bash
gocyclo -over 25 $(git diff --cached --name-only --diff-filter=d | grep '\.go$')
```

### `govulncheck` on a schedule

`govulncheck ./...` catches known CVEs in dependencies but needs network and is slow. Run it in CI on a schedule (daily) rather than on every push, and on pre-release. Failing every PR on an upstream CVE disclosure turns the gate into noise.

### Generated code freshness

If the repo uses `go generate` (mocks, protobuf, OpenAPI clients, schema registries), add a freshness gate: regenerate, then fail if `git diff` is non-empty. This catches stale generated code before it causes confusing review comments.

```bash
go generate ./...
if ! git diff --quiet; then
  echo "Generated code is stale. Run: go generate ./..."
  git diff --stat
  exit 1
fi
```

### Pre-commit / pre-push split

Pre-commit must be <15s or developers start using `--no-verify`. Split:

- **pre-commit (~10s)**: `goimports -l` on staged files, `go vet` on changed packages, `golangci-lint run --new-from-rev=HEAD` (only new issues).
- **pre-push (~45–90s)**: the full orchestrator — build, vet, full lint, tests, dead code, duplication, generated-code freshness.

`golangci-lint` has first-class support for "only report new issues" via `--new-from-rev` / `--new-from-patch`, which makes the pre-commit fast-path trivial.

### Coverage the reliable way

Run tests with coverage as part of the orchestrator:

```bash
go test ./... -coverprofile=coverage.out -covermode=atomic
go tool cover -func=coverage.out | tail -1  # total coverage
```

Then have a script read `coverage.out` and fail if any package is below a per-package threshold (stricter than a global floor, which lets one well-tested package mask the rest). Do not make coverage conditional on a file existing — make generating the file part of the gate.

### Project-specific gates belong in the orchestrator

Mature Go repos often need custom checks the template doesn't cover: schema migration freshness, protobuf regen, OpenAPI contract drift, log-field audits, license compliance, cross-compile smoke (`GOOS=linux go build ./...` on a macOS dev box). Add them as additional commands invoked from the orchestrator — don't try to cram them into `check.sh`.

## Customization options

Ask the user if they want to adjust:

- **Complexity threshold** — default 15 report / 25 fail (via `gocyclo`).
- **Duplication threshold** — default 50 tokens (via `dupl`).
- **Lint strictness** — enable/disable individual linters via `.golangci.yml`.
- **Coverage minimum** — only if adopting Step 12's coverage pattern.
- **Additional gates** — `govulncheck`, generated-code freshness, cross-compile smoke.
- **Monorepo / workspace support** — run gates per-module or from root via `go.work`.
