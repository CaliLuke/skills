---
name: rust-quality-gates
description: Set up Rust quality gates (cargo check/build, clippy, rustfmt, dead code, unused deps via cargo-machete, doc build, tests) in any Rust repo, wired through `prek` (pre-commit reimagined) with a `check.sh` orchestrator underneath. Use when the user says "add quality gates for Rust", "set up Rust linting", "add clippy", "add cargo clippy and rustfmt", "add cargo checks", "Rust quality gate setup", "add prek for Rust", "add cargo-machete", "Rust pre-commit hooks", or wants to establish code quality infrastructure in a Rust project (as opposed to Go, TypeScript, or Python). Step 12 covers optional cargo-audit/cargo-deny, coverage via cargo-llvm-cov, MSRV verification, miri, and feature-matrix testing via cargo-hack for larger repos.
---

# Rust Quality Gates Setup

Set up a quality gate system for a Rust project. The prescribed checker command is `prek run --all-files`. The deliverables are a `.pre-commit-config.yaml` that points `prek` at a `check.sh` orchestrator, a `clippy.toml` / `rustfmt.toml` pair (plus a `[lints]` table in `Cargo.toml`), and any extra tool configs (`deny.toml`, `cargo-machete` ignore lists) — wired to the repo's actual workspace layout and feature matrix. For larger repos, Step 12 describes the upgrades that production setups use.

## Step 1: Assess the repo before touching anything

Before writing or installing anything, understand the repo. Two outcomes are possible: a **mature system already exists** (stop and defer — Step 2), or it doesn't (proceed from Step 3).

Gather in parallel:

1. `Cargo.toml` (root and per-crate) / `Cargo.lock` — edition, MSRV (`rust-version`), workspace members, feature flags, existing `[lints]` table.
2. `rust-toolchain.toml` / `rust-toolchain` — pinned compiler version, components (`clippy`, `rustfmt`, `llvm-tools-preview`), targets.
3. Existing config files: `clippy.toml`, `rustfmt.toml` / `.rustfmt.toml`, `deny.toml`, `.cargo/config.toml`, `.cargo/audit.toml`, `.pre-commit-config.yaml`, any `scripts/check*.sh` / `scripts/lint*.sh` / `justfile` / `Makefile` targets (`make check`, `just lint`, `make ci`).
4. `CLAUDE.md` / `AGENTS.md` — canonical commands already documented.
5. Source layout: top-level `src/`, `crates/`, `examples/`, `tests/`, `benches/`, workspace members in `[workspace.members]`, `build.rs` scripts, generated files (`OUT_DIR`, `tonic-build`, `prost-build`).
6. Native / FFI deps — look for `build.rs`, `*-sys` crates, `bindgen`, `cc`, `cxx`, or `[target.'cfg(...)'.dependencies]`; these change how every gate must be invoked (system libs, target triple, cross-compilation).

### Features and target-cfg — detect once, use everywhere

Rust is simpler than JS here (one toolchain, one package manager), but **Cargo features are the equivalent trap**. `cargo build` with default features compiles a different subset than `--all-features`, and some feature combinations don't compile together at all. Running `cargo clippy` without `--all-features` (or without `--each-feature` for combinatorial coverage) produces silent no-ops for feature-gated code. Check for:

- Crates with many features in `Cargo.toml` `[features]` (more than 2–3 non-trivial features = a real matrix).
- Mutually exclusive features (e.g. `tls-rustls` vs `tls-openssl`) — `--all-features` will fail; needs `cargo hack` or per-combo invocation.
- `[target.'cfg(...)']` sections — platform-specific code that only compiles on certain targets.
- `no_std` crates or `#![no_std]` directives — the host-tools default toolchain may not even build them without `--target`.
- Existing pre-push hooks (`.githooks/pre-push`, `.husky/`) that already set `CARGO_TARGET_DIR`, `RUSTFLAGS`, `--features`, etc.

Throughout this skill, `<CARGO_FEATURES>` means whatever feature/target combination the repo already uses (commonly `--workspace --all-features` for libraries, `--workspace` for binaries, or a `cargo hack --feature-powerset` for crates with mutually-exclusive features). If the detected setup is ambiguous or has mutually-exclusive features, ask before generating.

## Step 2: Inventory existing gates and implement the delta

Most repos have **some** gates already (a `cargo fmt --check` in CI, a Makefile target running clippy, a half-finished `[workspace.lints]` table) but not the full set this skill installs. The default behavior is to **fill in the missing gates**, not to stop. Only defer the whole job when every row of the checklist below is already ✅ or when the existing orchestrator is genuinely incompatible with adding gates (rare — see end of step).

Walk this checklist before writing anything. For each gate, check the listed signal; mark ✅ if present and working, ❌ if missing or broken on disk.

| Gate                                           | Detection signal                                                                                                                 | Where to add if ❌ |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| `cargo check` / `cargo build` baseline         | Always available in a Rust repo with a valid `Cargo.toml`                                                                        | Step 4 invocation  |
| rustfmt config                                 | `rustfmt.toml` exists, OR rustfmt defaults are explicitly fine for the project                                                   | Step 6             |
| Clippy `[workspace.lints]` policy              | Root `Cargo.toml` has a non-trivial `[workspace.lints.clippy]` AND every workspace member has `[lints] workspace = true`         | Step 5             |
| `clippy.toml` thresholds + test escape hatches | `clippy.toml` exists with at least `allow-unwrap-in-tests`/`allow-expect-in-tests`/`allow-panic-in-tests` configured             | Step 5             |
| Strict doc gate                                | `[workspace.lints.rustdoc] broken_intra_doc_links = "deny"` set, OR existing orchestrator invokes `cargo doc` with `-D warnings` | Step 7             |
| `cargo-machete` unused-deps gate               | Tool installed AND invoked by an existing orchestrator                                                                           | Step 7 + check.sh  |
| Test gate                                      | Existing orchestrator runs `cargo test` / `cargo nextest run` over the workspace                                                 | Step 8             |
| `check.sh` orchestrator                        | `check.sh` (or equivalent `justfile`/`Makefile` target) runs the full gate sequentially                                          | Step 8             |
| `.pre-commit-config.yaml` + `prek` wiring      | File exists and wires `check.sh` (or per-gate hooks) for `prek`/`pre-commit`                                                     | Step 9             |

Run the existing orchestrator once (`just check`, `make ci`, `./check.sh`, `cargo xtask check`) before counting any ✅. A passing run earns it; a failing run means the gate is broken regardless of config presence — treat as ❌ and fix or replace.

Then report a short table to the user and **proceed to implement every ❌ row** without asking permission per row. Two modes:

- **No existing orchestrator** — create `check.sh` and `.pre-commit-config.yaml` per Steps 8–9; add only the gates the inventory marked ❌.
- **Existing orchestrator present** — **extend it** rather than replacing. Add new targets to the `justfile`/`Makefile`, append gate invocations to the existing `check.sh`, or register new hooks in `.pre-commit-config.yaml`. Keep the user's entry point name. Only mention replacement if the orchestrator is structurally hostile to new gates (see below).

Two cases where you stop or ask first:

1. **Everything is ✅** — every gate is present and the orchestrator passes cleanly. Report "all gates already in place" and stop. Nothing to do.
2. **Incompatible orchestrator** — Bazel rules, Nx executors with custom runners, a vendored CI script that forbids local invocation, or a `clippy::all` set via `lib.rs` crate attributes that conflicts with the `[lints]` table this skill writes. Ask whether to (a) wire missing gates into that system using its native idiom, or (b) add `check.sh` + `prek` alongside as a developer-facing fast path (some duplication, stable second entry point). Don't auto-replace.

Conflict cases that need a one-line confirmation before proceeding (not a "stop entirely"):

- Legacy `#![deny(clippy::all)]` in `lib.rs` plus a partial `[lints]` table — Step 5 prefers `[lints]`; ask which form to remove.
- `nightly` pinned `rust-toolchain.toml` enabling `unstable_features` in `rustfmt.toml` — the recommended config assumes stable; confirm before changing the pin.
- Existing `clippy.toml` with `msrv` that mismatches `Cargo.toml`'s `rust-version` — ask which is canonical before overwriting either.

## Step 3: Install dev tools

Rust dev tools come from two sources: rustup components (shipped with the toolchain) and `cargo install` for third-party tools. Prefer pinning third-party tool versions via `rust-toolchain.toml` components, or a `tools/Cargo.toml` workspace, or a `cargo install --locked` in a CI install step.

### Core (every Rust project)

```text
rustup component add clippy rustfmt        # meta-linter + formatter, shipped with the toolchain
```

These ride the toolchain version. If `rust-toolchain.toml` pins a specific version (e.g. `stable-1.85`), `clippy` and `rustfmt` match — no version drift between developers. Pinning a specific stable version (rather than the floating `stable` channel) is what most production repos do; it eliminates "the lint that fired on my machine but not in CI" debugging.

### Recommended add-ons

```text
# Prefer a prebuilt binary — building prek from source via cargo install takes minutes:
brew install prek                          # or: pipx install prek, uv tool install prek, cargo binstall prek
# Cargo-installed tools (slower first install, but no extra package manager required):
cargo install --locked cargo-machete       # unused dependencies (fast, stable, no nightly)
cargo install --locked cargo-deny          # licenses, advisories, banned crates, source policy
cargo install --locked cargo-audit         # RUSTSEC CVE scanning (subset of cargo-deny)
cargo install --locked cargo-nextest       # faster test runner with better output
cargo install --locked cargo-hack          # feature-matrix testing (each-feature, feature-powerset)
```

`prek` (<https://github.com/j178/prek>) is the user-facing entry point: it reads `.pre-commit-config.yaml`, installs git hooks, and runs the gate. The `check.sh` orchestrator (Step 8) does the actual work; `prek` just wraps it.

Optional (nightly-only or niche):

```text
cargo install --locked cargo-udeps         # unused deps via compiler internals (needs nightly, more accurate than machete)
cargo install --locked cargo-llvm-cov      # coverage via llvm-cov (also needs `llvm-tools-preview` component)
cargo install --locked cargo-mutants       # mutation testing
cargo install --locked cargo-semver-checks # public API drift for library crates
```

If the repo already has a `rust-toolchain.toml`, add `clippy`, `rustfmt`, and `llvm-tools-preview` (if using coverage) to its `components` list so every developer and every CI runner gets the same versions automatically.

`cargo check`, `cargo build`, `cargo test`, `cargo doc` are part of cargo — nothing to install.

## Step 4: Check + build as the baseline

`cargo check --workspace --all-targets` and `cargo build --workspace --all-targets` are the floor. They require no config, catch real type errors, and `check` runs much faster than `build` because it skips codegen. If either fails on a clean checkout, stop and fix before adding further gates — there is no point layering linters on top of a repo that doesn't compile.

`--all-targets` is critical: without it, `cargo check` does not compile `tests/`, `examples/`, or `benches/`, and those can rot silently.

`--all-features` is the next layer up. For libraries it's almost always what you want; for binaries with mutually-exclusive feature groups, you need `cargo hack --feature-powerset check` instead. Record the exact invocation in `check.sh`:

```bash
# Library or binary with compatible features:
cargo check --workspace --all-targets --all-features

# Crate with mutually-exclusive features (needs cargo-hack):
cargo hack check --workspace --feature-powerset --depth 2 --all-targets
```

## Step 5: Clippy config

Clippy is to Rust what golangci-lint is to Go — one meta-linter that wraps the dozens of named lints you'd otherwise wire up individually. Since Cargo 1.74, lints can be configured via a `[lints]` table in `Cargo.toml` — an alternative to crate-level `#![warn(...)]` attributes in `lib.rs`, and the preferred form for workspaces because `[workspace.lints]` propagates to every member. Crate-level attributes still work and remain common; pick one form and stick with it.

In the workspace root `Cargo.toml`:

```toml
[workspace.lints.rust]
# Compiler lints — these come from rustc itself, not clippy
unsafe_code = "warn"               # downgrade to "allow" only in crates that genuinely need it
unused_imports = "warn"
unused_must_use = "warn"
unreachable_pub = "warn"
missing_debug_implementations = "warn"
# missing_docs = "warn"            # enable when public API docs are a priority

[workspace.lints.clippy]
# Lint groups (the big knobs). `priority = -1` is required so individual
# lints below (at default priority 0) can override the group level —
# without it, group entries and individual entries collide ambiguously.
# `pedantic` is opt-in by design and very noisy — enable individually if at all.
# `nursery` is unstable; expect false positives.
# `correctness` is already deny-by-default in clippy; listing it here is
# documentation, not hardening.
all         = { level = "warn", priority = -1 }   # the default-warn set
suspicious  = { level = "warn", priority = -1 }
complexity  = { level = "warn", priority = -1 }
perf        = { level = "warn", priority = -1 }
style       = { level = "warn", priority = -1 }

# Individual lints worth enabling beyond the defaults
unwrap_used        = "warn"   # forces explicit error handling at boundaries
expect_used        = "warn"   # same, but for `.expect("…")`
panic              = "warn"   # flag `panic!()` in library code
todo               = "warn"   # `todo!()` shouldn't ship
dbg_macro          = "warn"   # `dbg!()` shouldn't ship either
print_stdout       = "warn"   # use `tracing` / `log` instead
print_stderr       = "warn"

# Frequently-fired pedantic lints that are usually worth the noise
needless_pass_by_value = "warn"
redundant_clone        = "warn"
inefficient_to_string  = "warn"

# Deliberate opt-outs — these fire on legitimate patterns and aren't worth the friction
module_name_repetitions = "allow"  # naming convention, not a bug
must_use_candidate      = "allow"  # noisy on internal helpers
missing_errors_doc      = "allow"  # enable when missing_docs is enabled
missing_panics_doc      = "allow"
```

Then in **each crate**'s `Cargo.toml`, opt in to the workspace policy:

```toml
[lints]
workspace = true
```

Without that opt-in line, `[workspace.lints]` does nothing for that crate. This trips up newcomers — every workspace member needs the `[lints]` table.

For per-threshold tuning, also create `clippy.toml` at the repo root:

```toml
# clippy.toml — thresholds and behavior tweaks that aren't expressible as lint levels
cognitive-complexity-threshold = 25      # default 25; bump for unavoidably-complex code
too-many-arguments-threshold   = 8       # default 7; raise if many builder patterns
type-complexity-threshold      = 250     # default 250
msrv = "1.85"                            # match Cargo.toml rust-version; clippy uses this for "won't compile on MSRV" lints

# These flip off the unwrap/expect/panic lints inside `#[cfg(test)]` modules
# and `tests/` integration tests — the canonical escape hatch, much cleaner
# than scattering `#[allow(clippy::unwrap_used)]` attributes per module.
allow-unwrap-in-tests = true
allow-expect-in-tests = true
allow-panic-in-tests  = true
```

Notes on deliberate omissions:

- **`clippy::pedantic` is off by default** — it includes ~80 lints, most of which fire on idiomatic code (`module_name_repetitions`, `must_use_candidate`, `missing_errors_doc`). Enable individually, not as a group, after the core gate stabilizes.
- **`clippy::restriction` is off, on purpose** — by design it contains _mutually incompatible_ lints (`else_if_without_else` vs `redundant_else`). Never enable as a group.
- **`clippy::nursery` is off** — unstable lints with frequent false positives.

## Step 6: Formatting (rustfmt)

Rust has an unambiguous canonical format. There is no bikeshedding config (unlike Prettier). `rustfmt` is part of the toolchain — no install step beyond `rustup component add rustfmt`.

If the repo wants a few customizations (the only ones worth setting on most projects), put them in `rustfmt.toml` at the repo root:

```toml
# rustfmt.toml — keep this minimal; rustfmt's defaults are good
edition = "2021"                  # match Cargo.toml — rustfmt formats differently per edition
max_width = 100                   # default 100; many style guides prefer 100 or 120

# Anything below requires the nightly rustfmt and is gated behind `unstable_features = true`.
# Do not enable on a stable toolchain — `cargo fmt --check` will silently ignore them and
# CI will pass while local pre-commit fails (or vice versa).
# unstable_features = true
# group_imports = "StdExternalCrate"
# imports_granularity = "Crate"
# wrap_comments = true
```

If the repo's `rust-toolchain.toml` pins **nightly**, the `unstable_features` block is fair game; otherwise leave it commented. The trap to avoid: enabling unstable rustfmt options on a stable toolchain means `cargo fmt --check` returns success without applying them, and developer setups drift silently.

The `check.sh` script below runs `cargo fmt --all -- --check` for verification and `cargo fmt --all` for the `--fix` path.

## Step 7: Unused deps, dead code, duplication, complexity

These are cheap to run and catch things clippy alone misses.

### cargo-machete (unused dependencies)

```bash
cargo machete
```

Detects deps listed in `Cargo.toml` but never `use`d. Fast, stable, no false negatives on most codebases. Has known false positives for crates referenced only via macro expansion (`serde` derive macros, etc.) — silence those with a `package.metadata.cargo-machete.ignored` list. This block lives in the **member crate's** `Cargo.toml` (the one with `[package]`), **not** in the workspace root — pasting it under `[workspace]` is a silent no-op:

```toml
# crates/foo/Cargo.toml  — note this is per-crate, not workspace-root
[package.metadata.cargo-machete]
ignored = ["serde"]   # used via #[derive(Serialize)] but not directly imported
```

Prefer `cargo-machete` over `cargo-udeps` for the default gate. Two reasons, in order: machete is dramatically faster (it parses `Cargo.toml` and greps source, no compilation; `udeps` runs as a rustc plugin and needs a full compile), and machete works on stable while `udeps` requires nightly. Add `udeps` in Step 12 if the user wants the higher accuracy and is willing to pay the time + nightly cost.

### dead_code (intra-crate, via rustc) — weaker than it looks

Rust's `dead_code` lint is enabled by default at warn level and catches functions/types/fields with no internal callers. Two important caveats that bite people coming from the Go ecosystem:

1. **It only checks reachability within a crate.** Cross-crate dead-code analysis is fundamentally hard in Rust because `pub` items can be consumed by code the compiler doesn't see.
2. **It exempts `pub` items entirely.** Anything marked `pub` is assumed to be external API and never flagged — so on a library crate, `dead_code` is largely silent regardless of internal use.

There is no widely-deployed Rust equivalent to Go's `deadcode` reachability walker that starts from `main` and finds unreachable `pub` items. For binary crates, `unreachable_pub` (set to `warn` in the rustc lints above) helps surface `pub` items that aren't actually exported. For libraries, accept the limitation; `cargo-machete` (which finds unused _deps_, not unused _items_) is the closest practical signal. Make sure `[workspace.lints.rust] dead_code = "warn"` (or `deny`) is set so the gate at least catches private-only dead code. No separate tool needed.

### Duplication — deliberately omitted

Unlike Go (`dupl`) or JS (`jscpd`), there isn't a widely-adopted Rust-native duplication detector. The available tools (`simian`, generic `pmd-cpd`) are language-agnostic, ignore Rust semantics (macros, generics), and produce noisy results. Skip the duplication gate for the default setup. If the user specifically asks, recommend running `jscpd --languages rust --min-tokens 50` against the workspace and triaging manually — but don't put it in `check.sh`.

### Complexity (reporting via clippy thresholds)

Clippy already has `cognitive_complexity`, `too_many_arguments`, `type_complexity`, and `too_many_lines` lints — all configurable via `clippy.toml` thresholds (Step 5). There's no separate tool to install. Use the thresholds as soft signals; raising them per-crate via `#[allow(clippy::cognitive_complexity)]` on a specific function is the standard escape hatch. Step 12 shows how to track these as metrics rather than hard gates.

### Doc build (catches broken intra-doc links)

The modern (Rust 1.74+) idiom is to declare doc-lint policy in the same `[workspace.lints]` table as everything else, so the gate doesn't depend on an env var being set:

```toml
[workspace.lints.rustdoc]
broken_intra_doc_links = "deny"
bare_urls              = "warn"
```

Then the gate is just:

```bash
cargo doc --workspace --no-deps --all-features
```

`--no-deps` is what makes a strict policy safe — it skips rendering dependency docs, so deprecation warnings or doctest issues in third-party crates don't fail your build. The older pattern, `RUSTDOCFLAGS="-D warnings -D rustdoc::broken_intra_doc_links" cargo doc ...`, still works and is what you'll see in older codebases; both produce the same result. Prefer the `[lints.rustdoc]` form for new setups so the policy lives alongside the rest of the lint config.

Cheap (runs in seconds for most workspaces) and catches `[Foo]`-style doc links that fail to resolve after a rename. Treat as a hard gate.

## Step 8: Create `check.sh`

A thin bash entry point that calls each gate sequentially. Fine for small/medium repos; see Step 12 for the parallel-orchestrator upgrade.

Substitute `<CARGO_FEATURES>` and any toolchain env from Step 1. Do **not** leave the placeholders literal in the generated file.

```bash
#!/usr/bin/env bash
# Code quality gates — run before pushing.
# Usage: ./check.sh [--fix]
set -euo pipefail

FIX="${1:-}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Adapt these to the repo's detected build setup (Step 1).
# For mutually-exclusive feature crates, replace --all-features with the right combo
# or switch to `cargo hack --feature-powerset`.
CARGO_FEATURES="--workspace --all-targets --all-features"

echo "══════════════════════════════════════"
echo "  Rust Quality Gates"
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

# Formatting — rustfmt has a canonical style; no config debate
if [ "$FIX" = "--fix" ]; then
  run_gate "rustfmt (write)" cargo fmt --all
else
  run_gate "rustfmt (check)" cargo fmt --all -- --check
fi

# Type check — fastest signal, catches most real bugs before clippy or build
run_gate "cargo check" bash -c "cargo check $CARGO_FEATURES"

# Clippy — the meta-linter. `-D warnings` turns every warn into a hard fail.
# Use `--no-deps` to avoid lint noise from dependencies (we can't fix those).
if [ "$FIX" = "--fix" ]; then
  run_gate "clippy" bash -c "cargo clippy $CARGO_FEATURES --no-deps --fix --allow-dirty --allow-staged -- -D warnings"
else
  run_gate "clippy" bash -c "cargo clippy $CARGO_FEATURES --no-deps -- -D warnings"
fi

# Build — full codegen. Catches things `check` misses (link errors, build.rs failures).
run_gate "cargo build" bash -c "cargo build $CARGO_FEATURES"

# Doc build — catches broken intra-doc links and warnings
run_gate "cargo doc" bash -c '
  RUSTDOCFLAGS="-D warnings -D rustdoc::broken_intra_doc_links" \
    cargo doc --workspace --no-deps --all-features
'

# Unused dependencies — cargo-machete is fast and stable
if command -v cargo-machete >/dev/null 2>&1; then
  run_gate "cargo-machete" cargo machete
fi

# Tests — only if there are tests. nextest is faster + better output if installed.
if find . -path ./target -prune -o \( -name '*_test.rs' -o -name 'tests' -type d \) -print 2>/dev/null | grep -q . \
   || grep -qE '#\[(cfg\(test\)|test)\]' -r --include='*.rs' --exclude-dir=target . 2>/dev/null; then
  if command -v cargo-nextest >/dev/null 2>&1; then
    run_gate "cargo nextest" bash -c "cargo nextest run $CARGO_FEATURES"
    # Doc tests don't run under nextest yet — run them separately
    run_gate "cargo test --doc" bash -c "cargo test --doc --workspace --all-features"
  else
    run_gate "cargo test" bash -c "cargo test $CARGO_FEATURES"
  fi
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

- **`cargo audit` / `cargo deny`** — network-dependent (fetches the RUSTSEC advisory DB) and can flake in air-gapped CI. Valuable but belongs on a scheduled CI run; see Step 12.
- **Coverage gate** — needs `cargo llvm-cov` and a threshold-checker. Making it conditional on a file silently no-ops; see Step 12 for the reliable pattern.
- **`cargo test --release`** — much slower than debug tests and rarely catches additional bugs unless the code has `cfg(debug_assertions)` or release-only optimizations. Add explicitly if needed.
- **MSRV verification (`cargo-msrv`)** — slow (builds against multiple toolchains). Run in CI matrix, not on every push.
- **`miri`** — invaluable for `unsafe` code but slow (10–100× test time) and only available on nightly. Add as a separate `miri.sh` script for crates that need it.
- **Bash file-length loop** — file size is a weak signal in Rust; most large files are generated code or large `enum` definitions. Track it as a metric (Step 12) rather than a hard gate.
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
        name: Rust quality gates
        entry: ./check.sh
        language: system
        pass_filenames: false
        always_run: true
        stages: [pre-commit, pre-push, manual]
```

`pass_filenames: false` and `always_run: true` matter: cargo gates are workspace-wide, not per-file, so we don't want `prek` to pass the staged file list to `check.sh` or skip the run when nothing Rust changed.

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

- `prek run --all-files` — runs all gates (~60s on a warm `target/`; first-run cold build can be 3–5 min on a medium workspace) — prescribed entry point
- `./check.sh --fix` — auto-fix path (prek doesn't pass flags through)
- `prek install` — wire up git hooks (one-time per checkout)

Gates: rustfmt · cargo check · clippy · cargo build · cargo doc · cargo-machete (+ cargo test / nextest if present).
```

Do **not** create `CLAUDE.md` just to document the gates. That's agent-clutter the user didn't ask for; the `check.sh` header comment and `justfile`/`Makefile` are self-documenting.

## Step 11: First run

Run `prek run --all-files` and fix anything that comes up. Expect:

- `prek: command not found` — install per Step 3 (`cargo install --locked prek` or `brew install prek`).
- Missing tools — `cargo-machete`, `cargo-nextest` not installed. Install with `cargo install --locked <tool>` from Step 3.
- `clippy` failures on a fresh setup — the default config is strict (`unwrap_used`, `expect_used`, `panic`). If the volume is large, either fix in batches or relax specific lints in `Cargo.toml` rather than disabling clippy wholesale. For test-only relaxations, put `#[cfg_attr(test, allow(clippy::unwrap_used))]` on the affected modules.
- Workspace members missing `[lints] workspace = true` — `[workspace.lints]` is opt-in per crate. Add the table to each member's `Cargo.toml`.
- `cargo doc` failing on intra-doc links — usually `[Foo]` references to renamed/removed items. Fix by adjusting the link or removing the doc.
- `cargo-machete` flagging crates used only via proc macros (`serde`, `tracing`, `async-trait`) — add to `[package.metadata.cargo-machete] ignored = [...]`.
- Build failures from mutually-exclusive features — drop `--all-features`, or switch the gate to `cargo hack --feature-powerset` (Step 12).
- Stale `Cargo.lock` after first run — commit the changes; this is normal when adding new dev tools.

## Step 12: Advanced patterns (propose for larger repos; don't apply unprompted)

These are proven production patterns for Rust workspaces and larger services. They cost setup time, so pitch them and get buy-in before applying.

### Parallel orchestrator instead of sequential bash

A sequential `check.sh` with 6+ gates commonly hits 2–4 min wall time. A Rust orchestrator (or `cargo make`, or `just` with `parallel` flags) that fans gates out compresses that to the slowest single gate (usually tests). The simplest pure-Rust orchestrator:

```rust
// xtask/src/main.rs — invoke via `cargo xtask check`
// Requires the standard `xtask` pattern: add an `xtask` crate to the workspace
// and an alias in `.cargo/config.toml`: `[alias] xtask = "run --package xtask --"`

use std::process::{Command, Stdio};
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

struct Gate {
    name: &'static str,
    argv: Vec<&'static str>,
}

fn main() -> std::io::Result<()> {
    let gates = vec![
        Gate { name: "fmt",      argv: vec!["cargo", "fmt", "--all", "--", "--check"] },
        Gate { name: "check",    argv: vec!["cargo", "check", "--workspace", "--all-targets", "--all-features"] },
        Gate { name: "clippy",   argv: vec!["cargo", "clippy", "--workspace", "--all-targets", "--all-features", "--no-deps", "--", "-D", "warnings"] },
        Gate { name: "doc",      argv: vec!["cargo", "doc", "--workspace", "--no-deps", "--all-features"] },
        Gate { name: "machete",  argv: vec!["cargo", "machete"] },
        Gate { name: "test",     argv: vec!["cargo", "nextest", "run", "--workspace", "--all-features"] },
    ];

    let (tx, rx) = mpsc::channel();
    let n = gates.len();

    for g in gates {
        let tx = tx.clone();
        thread::spawn(move || {
            let out = Command::new(g.argv[0])
                .args(&g.argv[1..])
                .env("RUSTDOCFLAGS", "-D warnings -D rustdoc::broken_intra_doc_links")
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .output();
            let _ = tx.send((g.name, out));
        });
    }
    drop(tx);

    // Collect with a global deadline — a hung gate can't pin the whole run.
    let mut failed = Vec::new();
    for _ in 0..n {
        let (name, out) = rx.recv_timeout(Duration::from_secs(600))
            .expect("gate timed out (>10 min)");
        match out {
            Ok(o) => {
                println!("── {name} ──");
                std::io::Write::write_all(&mut std::io::stdout(), &o.stdout)?;
                std::io::Write::write_all(&mut std::io::stderr(), &o.stderr)?;
                if !o.status.success() {
                    failed.push(name);
                }
            }
            Err(e) => {
                eprintln!("── {name} ── failed to spawn: {e}");
                failed.push(name);
            }
        }
    }

    if !failed.is_empty() {
        for n in &failed { eprintln!("FAIL: {n}"); }
        std::process::exit(1);
    }
    Ok(())
}
```

Note: for a more polished experience, wrap each gate's stdout/stderr in a per-gate `Write` that prefixes every line with `[name]` and streams live; that's worth the complexity once the orchestrator is your daily driver. The version above is the minimal correct shape — parallel, bounded, deterministic output.

Keep `check.sh` as a thin wrapper that calls `cargo xtask check` so external consumers (CI, IDEs, hooks) still see a stable entry point.

### Feature-matrix testing with `cargo-hack`

Crates with several optional features have a combinatorial test space. `--all-features` only proves the all-on combination compiles; it says nothing about the all-off, default-only, or pairwise combinations. `cargo hack` solves this:

```bash
# Every feature individually, plus none — catches most issues, fast
cargo hack check --workspace --feature-powerset --depth 1 --all-targets

# Pairwise combinations — much slower but catches feature interactions
cargo hack check --workspace --feature-powerset --depth 2 --all-targets
```

Run `--depth 1` on every push; reserve `--depth 2+` for nightly CI. Cost grows quadratically — for a crate with N features, depth-2 builds roughly N + C(N,2) combinations. That's manageable at 6–8 features (~30 builds) but punishing at 15 (~120 builds). Above ~8 features, restrict depth-2 to scheduled runs only.

### `cargo-deny` for supply chain

`cargo-deny` is a strict superset of `cargo-audit`: licenses, security advisories, banned crates, source policy (only crates.io, only certain git remotes). Add `deny.toml`:

```toml
[advisories]
db-urls = ["https://github.com/rustsec/advisory-db"]
yanked = "deny"
unmaintained = "warn"

[licenses]
allow = ["MIT", "Apache-2.0", "Apache-2.0 WITH LLVM-exception", "BSD-3-Clause", "ISC", "Unicode-DFS-2016"]
confidence-threshold = 0.93

[bans]
multiple-versions = "warn"  # several copies of `syn`, `hashbrown`, etc. is normal but worth eyeballing
wildcards = "deny"          # `*` version requirements are a footgun

[sources]
unknown-registry = "deny"
unknown-git = "deny"
```

Run `cargo deny check` in CI on every push for everything except advisories; run advisories on a daily schedule so an upstream CVE disclosure doesn't fail every PR until you bump.

### MSRV verification with `cargo-msrv`

If the crate publishes a `rust-version = "1.X"` in `Cargo.toml`, verify it actually builds against that version. `cargo-msrv verify` does this. Slow (downloads a toolchain), so run nightly in CI, not on every push.

### Coverage the reliable way

```bash
cargo llvm-cov --workspace --all-features --lcov --output-path lcov.info
cargo llvm-cov report --fail-under-lines 80   # tune the threshold per repo
```

Make generating `lcov.info` part of the gate, not conditional on its presence. Per-crate thresholds (via `cargo-llvm-cov`'s `--fail-under` per-package or a follow-up script) prevent one well-tested crate from masking the rest.

### Public-API drift for libraries (`cargo-semver-checks`)

For library crates published to crates.io, accidental breaking changes are a real cost. Add `cargo semver-checks check-release` as a release-gate (not every-push) — it diffs the current crate against the latest published version and fails on undeclared breaking changes.

### `miri` for unsafe-heavy crates

If the crate has `unsafe` blocks, run the test suite under `miri` to catch undefined behavior:

```bash
cargo +nightly miri test --workspace
```

Slow (10–100× normal test time). Run as a separate `miri.sh` script invoked nightly in CI, not in `check.sh`.

### Pre-commit / pre-push split

Pre-commit must be <15s or developers start using `--no-verify`. Split:

- **pre-commit (~10s)**: `cargo fmt --check` on staged files, `cargo clippy --workspace --no-deps -- -D warnings` scoped to changed crates only (`cargo clippy -p <changed-crate>`).
- **pre-push (~60–180s)**: the full orchestrator — fmt, check, clippy, build, doc, machete, tests.

`cargo check` and `cargo clippy` benefit massively from a warm target dir, so set `CARGO_TARGET_DIR=$HOME/.cache/cargo-target-shared` in the dev profile if it isn't already.

### Project-specific gates belong in the orchestrator

Mature Rust repos often need custom checks the template doesn't cover: schema migration freshness, protobuf regen, OpenAPI contract drift, generated bindings (`bindgen`, `tonic-build`), cross-compile smoke (`cargo check --target aarch64-unknown-linux-gnu` on an x86 dev box), license header presence. Add them as additional gates in the `xtask` orchestrator — don't try to cram them into `check.sh`.

## Customization options

Ask the user if they want to adjust:

- **Lint strictness** — `unwrap_used`/`expect_used`/`panic` are on by default; relax to `allow` for binary crates or research code where pragmatic panics are common.
- **Complexity thresholds** — defaults in `clippy.toml` are 25 cognitive, 7 args, 250 type-complexity; tune per repo.
- **Feature matrix depth** — none / `--all-features` / `cargo hack --depth 1` / `cargo hack --depth 2`.
- **Test runner** — `cargo test` (stdlib) vs `cargo nextest` (faster, better output, retry support).
- **Coverage minimum** — only if adopting Step 12's coverage pattern.
- **Additional gates** — `cargo audit` / `cargo deny`, `miri`, `cargo-mutants`, `cargo-semver-checks`, MSRV verification.
- **Workspace vs single crate** — single-crate repos don't need `[workspace.lints]`; put lints directly in the crate's `Cargo.toml [lints]` table.
- **Stable vs nightly toolchain** — nightly unlocks `udeps`, unstable rustfmt options, and `miri` but adds churn from compiler regressions.
