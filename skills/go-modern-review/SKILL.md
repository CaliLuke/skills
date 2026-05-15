---
name: go-modern-review
description: Review and refactor Go code for modern release features (Go 1.25 and 1.26) — new language and stdlib APIs, `go fix` workflows, tooling, and newly deprecated or tightened behaviors. Use after upgrading Go, during code review, or when modernizing concurrency, error handling, logging, testing, http/proxy, or reflection code.
---

# Go Modern Review (1.25 + 1.26)

Use this skill to find actionable Go adoption opportunities during review or refactor work after upgrading to Go 1.25 or 1.26. Prioritize changes that improve correctness, clarity, safety, maintainability, or test ergonomics. Do not force mechanical churn for features that add no material value.

First, confirm which Go version the package targets and scope recommendations to that version (or higher). If both apply, prefer the newer pattern.

## Review Workflow

1. Confirm the package's Go version, or that the user explicitly wants forward-looking recommendations.
2. Start with the highest-value adoption points for the target version (see the per-version shortlists below).
3. On Go 1.26, run or consider `go fix` modernizers before doing manual cleanup.
4. Check for deprecations, tightened validation, or behavioral changes that should influence refactors.
5. Recommend toolchain and operational follow-ups where relevant (vet analyzers, runtime/metrics, flight recorder, etc.).
6. Keep recommendations ranked:
   - correctness and security first
   - maintainability and tooling second
   - testability and observability third
   - readability and stylistic cleanups last

## Refactor Rules

- Prefer refactors that remove bespoke code, unsafe hooks, or error-prone boilerplate.
- Preserve existing architecture and repo invariants.
- Avoid adding `GOEXPERIMENT` dependencies unless the user explicitly wants experimental adoption.
- Treat automatic runtime/compiler wins as context, not as reasons to rewrite source.
- When recommending a change, state:
  - the old pattern
  - the Go replacement (and minimum version)
  - the concrete benefit
  - any migration caveat or rollout risk

## Go 1.25 — High-Value Features

- `sync.WaitGroup.Go`: Replace manual `Add(1)` + `go func(){ defer Done() ... }()` when the wrapper adds no real behavior.
- `testing/synctest`: Rewrite timing-sensitive concurrent tests that depend on sleeps, polling, or race-prone coordination.
- `net.JoinHostPort`: Replace unsafe string-built network addresses, especially anything that may see IPv6.
- `net/http.CrossOriginProtection`: Consider for browser-exposed state-changing endpoints lacking CSRF protection.
- `runtime/trace.FlightRecorder`: Add for debugging rare production stalls, deadlocks, or latency spikes.
- `slog.GroupAttrs`: Use when building slog groups from a precomputed `[]slog.Attr`.
- `reflect.TypeAssert`: Use in hot or allocation-sensitive reflection paths that currently do `v.Interface().(T)`.
- `mime/multipart.FileContentDisposition`: Replace handwritten multipart file content-disposition formatting.
- `io/fs.ReadLinkFS` (with `os`, `archive/tar`, `testing/fstest` support): Simplify symlink-aware filesystem logic and tests.
- `crypto.SignMessage` / `crypto.MessageSigner`: Use when supporting signers that hash internally.

Correctness hazards newly exposed by Go 1.25:

- Use of values before checking `err`, especially nilable results from constructors/open calls.
- Fragile `unsafe.Pointer` patterns that may break because more slice backing arrays now stack-allocate.

## Go 1.26 — High-Value Features

- `go fix`: Run or inspect modernizers before hand-editing old idioms.
- `new(expr)`: Replace local helper closures or temp variables used only to take pointers to optional scalar values.
- `errors.AsType`: Replace `var target *T; if errors.As(err, &target)` boilerplate with typed extraction.
- `slog.NewMultiHandler`: Replace custom "fan out to multiple handlers" plumbing.
- `httputil.ReverseProxy.Rewrite`: Migrate away from deprecated and unsafe `Director`.
- `b.Loop`: Replace ad hoc benchmark loops where relevant.
- `testing.T.ArtifactDir`: Use for tests that emit files or diagnostic artifacts.
- `testing/cryptotest.SetGlobalRandom`: Use in tests that need deterministic crypto randomness under the new crypto behavior.
- `os/signal.NotifyContext` cause propagation: Use `context.Cause` when signal-aware shutdown paths need to know which signal fired.
- Goroutine leak profile experiment: Consider for CI or production debugging of blocked-goroutine leaks.
- `runtime/metrics` scheduler metrics: Prefer built-in scheduler gauges over custom approximations.

Deprecations and tightened behaviors to flag during review:

- Deprecated `httputil.ReverseProxy.Director`.
- Deprecated unsafe RSA PKCS #1 v1.5 encryption padding.
- Stricter URL parsing with malformed host colons.
- Crypto APIs that no longer honor custom randomness parameters.

## Review Prompts

Ask these while reviewing:

- Is this manual concurrency plumbing now expressible with `WaitGroup.Go`? _(1.25+)_
- Is this concurrent test fighting the scheduler instead of using `testing/synctest`? _(1.25+)_
- Is this host/port string construction unsafe for IPv6? _(1.25+)_
- Is this browser-facing HTTP surface missing a simpler CSRF defense? _(1.25+)_
- Is this logging code assembling attr groups in a clumsy way? _(1.25+)_
- Is this reflection code paying allocation cost to get back to a concrete type? _(1.25+)_
- Is this production debugging path a candidate for `FlightRecorder` instead of ad hoc logging? _(1.25+)_
- Is this code incorrect under Go 1.25 because it touches a nilable result before checking `err`?
- Can `go fix` or a modernizer do this migration more safely than a manual edit? _(1.26+)_
- Is this pointer-helper boilerplate now clearer as `new(expr)`? _(1.26+)_
- Is this `errors.As` pattern just typed extraction boilerplate? _(1.26+)_
- Is this reverse proxy still using `Director` when it should use `Rewrite`? _(1.26+)_
- Is this logging fan-out code reinventing `slog.NewMultiHandler`? _(1.26+)_
- Are these crypto tests depending on custom randomness parameters that Go 1.26 now ignores?
- Should this test write files through `ArtifactDir` instead of ad hoc temp-path handling? _(1.26+)_
- Is this shutdown path able to inspect the signal cause from `NotifyContext` cancellation? _(1.26+)_
- Is this URL parsing logic assuming malformed hosts will still pass? _(1.26+)_

## Non-Adoption Notes

Some release changes matter for review but are not usually direct refactor targets:

- No 1.25/1.26 language change requires source rewrites.
- Container-aware `GOMAXPROCS` (1.25) is an operational/runtime behavior change.
- Green Tea GC: experiment in 1.25 (`GOEXPERIMENT=greenteagc`), default in 1.26.
- JSON v2 (`GOEXPERIMENT=jsonv2`) remains experimental — suggest trials, not broad adoption.
- DWARF5, linker alignment/layout, VMA names, cgo call overhead, heap base randomization, `io.ReadAll`/JPEG improvements, and many crypto/runtime speedups are mostly automatic wins.
- Several 1.26 crypto and TLS changes are defaults or behavior changes rather than API migrations.

Experimental features should stay opt-in unless explicitly requested: `simd/archsimd`, `runtime/secret`, goroutine leak profile.

## Validation

When you make Go-version-driven code changes, run the normal repo gates plus targeted checks:

```bash
go test ./...
golangci-lint run ./...
go vet ./...
```

If the review touched concurrency or networking patterns, pay special attention to vet output from the `waitgroup` and `hostport` analyzers (1.25+). If it touched proxying, crypto, or testing utilities, pay special attention to integration coverage and compatibility behavior rather than just compile success.
