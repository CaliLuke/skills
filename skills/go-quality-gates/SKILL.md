---
name: go-quality-gates
description: Set up Go quality gates (build, vet, golangci-lint, goimports, duplicates, dead code, complexity, mod tidy drift, coverage) in any Go repo with a `check.sh` entry point — and an optional parallel orchestrator for larger setups. Use when the user says "add quality gates for Go", "set up Go linting", "add golangci-lint", "add go checks", "Go quality gate setup", "add check.sh for Go", or wants to establish code quality infrastructure in a Go project (as opposed to TypeScript or Python).
---

# Go Quality Gates Setup

Set up a quality gate system for a Go project. The deliverable is a `check.sh` entry point, a `.golangci.yml` config, and any extra tool configs (`dupl`, `deadcode`, `gocyclo`) — wired to the repo's actual module layout and build tags. For larger repos, Step 11 describes the upgrades that production setups use.

## Step 1: Assess the repo before touching anything

Before writing or installing anything, understand the repo. Two outcomes are possible: a **mature system already exists** (stop and defer — Step 2), or it doesn't (proceed from Step 3).

Gather in parallel:

1. `go.mod` / `go.work` — Go version, module path, workspace layout, existing dependencies.
2. Existing config files: `.golangci.yml` / `.golangci.yaml` / `.golangci.toml`, `.revive.toml`, `staticcheck.conf`, `.goreleaser.yml`, any `scripts/check*.sh` / `scripts/lint*.sh` / `Makefile` targets (`make check`, `make lint`, `make test`).
3. `CLAUDE.md` / `AGENTS.md` — canonical commands already documented.
4. Source layout: top-level `cmd/`, `internal/`, `pkg/`, nested modules, build tags (`//go:build cgo`, `//go:build integration`), generated files (`*_gen.go`, `zz_generated_*.go`).
5. CGo / native deps — look for `CGO_ENABLED`, `CGO_LDFLAGS`, or `cgo` build tags; these change how every gate must be invoked.

### Build tags and CGo — detect once, use everywhere

Go is simpler than JS here (one toolchain, no package managers), but build tags are the equivalent trap. **Some repos cannot run `go test ./...` without `CGO_ENABLED=1` and specific tags**, and running it without them produces silent no-ops for tagged files or, worse, link failures. Check for:

- `GOFLAGS` in the environment or in `Makefile` / `scripts/*.sh`.
- `//go:build` directives in packages you plan to gate.
- Existing pre-push hooks (`.githooks/pre-push`, `.husky/`) that already set `CGO_LDFLAGS`, `MACOSX_DEPLOYMENT_TARGET`, etc.

Throughout this skill, `<GOFLAGS>` means whatever tag/env combination the repo already uses. If the detected setup is ambiguous or tag-gated packages exist, ask before generating.

## Step 2: Stop if a mature system already exists

A repo with a working orchestrator and matching configs should not be silently overwritten. Signals:

- A `Makefile` or script runs multiple gates (e.g. `make check`, `scripts/run-golangci.sh`, `scripts/check.sh`). Inspect targets named `check`, `verify`, `ci`, `quality`, `lint`.
- Config files for each gate already exist (`.golangci.yml`, any per-tool configs, repo-specific lint runners).
- `CLAUDE.md` / `AGENTS.md` lists canonical lint/test/build commands.
- Project-specific gates the skill's template does NOT cover (CGo cross-compilation checks, generated-code freshness, schema-drift checks, protobuf regen checks, vuln scanning, license audits).

If **two or more** signals are present:

1. Run the existing orchestrator once to confirm it still works — this is both a sanity check and a way to show the user their current state.
2. Report what you found and list the gates it already covers.
3. Ask the user to choose: **(a) skip**, **(b) add a thin `check.sh` wrapper that calls the existing orchestrator** (same entry point across repos, zero behavior change), or **(c) extend the existing orchestrator with a specific named missing gate** (ask which one — duplicates, dead code, vuln scan, etc.).
4. Only proceed to Step 3+ if the user explicitly asks to replace the existing system.

Why this matters: the skill's default `check.sh` is sequential bash with a fixed gate list and defaults tuned for a fresh repo. A Makefile orchestrator, custom CGo flags, or project-specific gates are strictly **more** than the template provides — overwriting them is a downgrade that usually breaks pre-commit/pre-push hooks in the process.

## Step 3: Install dev tools

Go tools are installed per-user with `go install`, not as project dependencies. Prefer pinning versions via `tools.go` or a `Makefile` install target so CI gets the same versions as developers.

### Core (every Go project)

```text
github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest  # meta-linter (govet, staticcheck, errcheck, unused, ineffassign, etc.)
golang.org/x/tools/cmd/goimports@latest                        # format + import management
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

- **`gocyclo` / `gocognit` / `cyclop` linters are off** — they fire per-function with arbitrary thresholds and produce noise developers learn to ignore. Step 11 shows how to track per-file complexity as a tracked metric instead.
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

Report functions over 15; use as a signal, not a hard gate (the skill does not fail on this by default — the threshold is a judgment call). Step 11 shows a per-file tracked metric approach instead.

## Step 8: Create `check.sh`

A thin bash entry point that calls each gate sequentially. Fine for small/medium repos; see Step 11 for the parallel-orchestrator upgrade.

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

- **Bash file-length loop** — file size is a weak signal in Go; most large files are generated code or legitimate package-level orchestrators. Track it as a metric (Step 11) rather than a hard gate.
- **Coverage gate** — needs `go test -coverprofile=…` across the whole tree plus a summarizer. Making it conditional on a file existing silently no-ops when coverage wasn't generated. If you want coverage enforcement, see the reliable pattern in Step 11.
- **`govulncheck`** — valuable but network-dependent and can flake in air-gapped CI. Add in Step 11 once the core gate is stable.
- **Auto-creating `CLAUDE.md`** — an agent shouldn't fabricate agent docs the user didn't ask for.

Make the file executable: `chmod +x check.sh`.

## Step 9: Document (existing docs only)

If the repo already has `CLAUDE.md` or `AGENTS.md`, append a compact "Quality Gates" section:

```markdown
## Quality Gates

- `./check.sh` — runs all gates (~60s)
- `./check.sh --fix` — auto-fix + check

Gates: build · vet · goimports · golangci-lint · deadcode · dupl (+ go test if present).
```

Do **not** create `CLAUDE.md` just to document the gates. That's agent-clutter the user didn't ask for; the `check.sh` header comment and `Makefile` are self-documenting.

## Step 10: First run

Run `./check.sh` and fix anything that comes up. Expect:

- Missing tools — `goimports`, `deadcode`, `dupl` not on `$PATH`. Add `GOPATH/bin` to `$PATH` or install with `go install` as per Step 3.
- Build failures on a fresh clone because of missing CGo env — add the flags to `check.sh`'s `export` block based on what Step 1 detected.
- Pre-existing lint errors — fix before calling the setup done. If the volume is large, adjust `.golangci.yml` `exclusions` rather than disabling linters wholesale.
- `deadcode` flagging large swaths of code on library-style repos that expose public API — it reports unreachable-from-`main` by default, which is wrong for libraries. Either scope the command to `./cmd/...` or switch to `unused` (weaker but library-aware).

## Step 11: Advanced patterns (propose for larger repos; don't apply unprompted)

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
- **Coverage minimum** — only if adopting Step 11's coverage pattern.
- **Additional gates** — `govulncheck`, generated-code freshness, cross-compile smoke.
- **Monorepo / workspace support** — run gates per-module or from root via `go.work`.
