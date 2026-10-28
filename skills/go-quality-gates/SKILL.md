---
name: go-quality-gates
description: Set up or review Go quality gates for correctness, maintainability, tests, and coverage. Extend the repository's existing orchestrator and hook ownership; use Prek and check.sh when creating a new setup. Use for Go linting or quality-gate infrastructure, including missing enforcement and weak baselines, rather than ordinary Go implementation work.
---

# Go quality gates

Build a gate system that detects regressions and makes accepted debt visible. A passing build and test suite does not establish maintainability. Maintainability index is the default function-level measure; higher scores are better. Reports alone do not satisfy the maintainability gate.

Preserve the repository's canonical command, tool pins, hook manager, build tags, and environment setup. Extend an existing system instead of installing a competing one. For a new setup, use Prek as the entry point and a non-mutating `check.sh` underneath; keep formatting fixes separate.

## Inspect the existing setup

Read `go.mod` / `go.work`, repository instructions, checker scripts, linter config, CI and hooks, tool pins, generated-source boundaries, and existing baselines. Determine the actual module/package inventory, build tags, CGo/native prerequisites, and supported platforms. Apply that scope consistently to build, analysis, tests, and coverage. Reuse established invocations; ask only when an unresolved choice affects correctness.

Inspect what each check **enforces**, not whether a config or tool exists. Reuse recent applicable results rather than rerunning an unchanged full suite. An analyzer that detects a defect is working; distinguish that result from an analyzer crash or unsupported toolchain.

Record a concise inventory:

| Required area | Evidence of enforcement |
| --- | --- |
| Build and vet | Correct package/tag scope; nonzero exit propagates |
| Formatting | `goimports`/`gofmt` differences fail in check mode |
| Lint | Valid pinned config; new diagnostics fail |
| Module hygiene | Non-mutating tidy-drift check, e.g. supported `go mod tidy -diff` |
| Dead code | Reachability appropriate to executable entry points; exported library API is not assumed unused |
| Duplication | Findings are parsed and rejected or compared with a reviewed baseline; tool exit 0 alone is insufficient |
| Function maintainability | Enforced maintainability-score floors, including worsening existing findings |
| Structural maintainability | Inspected receiver/package/file hotspots, a working structural check, and explicit accepted debt |
| Tests and coverage | Relevant unit/integration tests run; fresh complete coverage is required before threshold comparison |
| Orchestration | Canonical command and CI/hooks invoke the same checks; missing tools and incomplete analysis fail |

Use statuses such as **enforced**, **baseline debt**, **report-only**, **missing**, and **blocked**. Do not label an area complete merely because its report was produced. List the substantive gaps and implement the requested delta within the user's scope.

For a full quality-gate setup, function and structural maintainability are required areas, not advanced opt-ins. A narrower user request may intentionally cover less; state that boundary.

## Establish maintainability policy

Read [references/maintainability.md](references/maintainability.md) when adding or reviewing these gates. It defines initial inspection, regression semantics, exceptions, and evidence required before calling setup complete.

At minimum:

- Enforce maintainability index by default, using `maintidx` or an equivalent existing score. Retain other complexity metrics when the repository needs them, but do not substitute a cyclomatic-complexity cap for a requested maintainability score. Metrics complement structural review; none proves good design by itself.
- Inspect large receivers, disconnected responsibilities in large files/packages, broad dependency holders, and cross-layer calls. Use an AST/type-aware tool such as Lagotto when compatible, alongside direct inspection of representative findings.
- Ratchet new and worsening violations. Do not grandfather unlimited growth in an already flagged function or receiver.
- Review and disclose legacy hotspots before establishing a baseline. Distinguish accepted debt from false positives, with narrow reasons and follow-up work for meaningful deferred refactors. File tickets when authorized; otherwise provide concrete drafts.
- A missing/unsupported structural analyzer leaves that area blocked. Complete independent gates, disclose the gap, and use an equivalent working checker when available. Do not replace failed analysis with an empty report or quietly call it optional.

Keep routine checks non-mutating. Baseline updates are explicit review operations, never automatic retries after a failure. Do not raise limits, broaden exclusions, or reset baselines to hide changes introduced by the task.

## Tools and lint configuration

Use repository pins. For new tools, select compatible releases and pin them in the repository's established tool mechanism (modern Go tool directives, existing tool module, or installation script). Do not paste `@latest` into reproducible setup commands. Verify support for the target Go version, including the analyzer's package loader/export-data reader; recompiling a binary with a newer Go version may not suffice.

Typical tools: golangci-lint, goimports, deadcode, dupl, and a structural analyzer. Avoid duplicate checks when one configured tool already provides the needed enforcement. A standalone complexity reporter is useful for inventory, but its output needs a comparator to become a ratchet.

For golangci-lint, validate the config against the installed version. Start with its supported baseline and add repository-relevant rules such as error/resource handling and maintainability. Keep formatters distinct from linters. Do not copy removed v1 `run.skip-dirs` / `run.skip-files` keys into v2 configs. Avoid blanket test exclusions that suppress correctness diagnostics.

A minimal maintainability addition for a new v2 config is below. Merge it into the existing config; do not replace unrelated policy. These numbers are starting points to inspect and calibrate, not universal quality scores. The example is a strict gate; a legacy repository needs the reviewed numeric ratchet described in the reference.

```yaml
version: "2"
linters:
  default: standard
  enable:
    - maintidx
  settings:
    maintidx:
      under: 20
  exclusions:
    generated: strict
    warn-unused: true
issues:
  max-issues-per-linter: 0
  max-same-issues: 0
  uniq-by-line: false
formatters:
  enable:
    - gofmt
    - goimports
```

This snippet covers function-level signals only. A package containing hundreds of individually simple methods can still violate the structural policy.

Use the pinned version's [configuration reference](https://golangci-lint.run/docs/configuration/file/) and [linter settings](https://golangci-lint.run/docs/linters/configuration/) to confirm supported keys and threshold semantics. Run `golangci-lint config verify` with the intended config.

## Orchestrator and hooks

Adapt implementation to the repository rather than copying a generic script wholesale.

- Separate fast checks from a full push/CI gate when useful. Put expensive structural and integration analysis in the full gate; fast mode must not be presented as full acceptance.
- Make missing required tools a failure. Avoid `if command -v tool; then ...; fi` that silently turns off a gate.
- Classify exit statuses using the pinned tool's documented contract. A findings-only exit may proceed through baseline comparison; crashes, package-load errors, and incomplete output must fail. An empty report from a failed command is not a pass. For tools that exit 0 on findings, parse their supported output or configure a failure threshold.
- If collecting failures, use explicit conditionals so `set -e` neither aborts before the intended summary nor masks errors inside helper functions. Keep per-gate logs and clear final statuses.
- Generate fresh coverage in the same test invocation; reject missing, truncated, or partial profiles. Use per-package floors (and targeted file floors where needed), not only a global average. A new package needs an explicit policy rather than disappearing from the denominator.
- Scope deadcode to real entry points and account for external library users. Do not delete exported API just to clear a reachability report.
- Exclude actual generated/vendor source with documented ownership boundaries. Directory names, large files, or difficult domains alone are not grounds for exclusion.
- Bound execution and clean up owned workers. Default to serial or resource-budgeted concurrency; do not launch every expensive analyzer in parallel on a saturated host. Compile caches may reuse source compilation, not substitute for running required tests.
- Emit progress and a final result per gate so a long run does not hide an earlier failure. Do not rerun completed checks on an unchanged tree without a concrete reason.

Where Prek is already invoked by Husky or another manager, extend that wiring. Do not install a second hook owner. In a new repository without an owner, configure the required stages explicitly, then install only those hooks. Preserve existing stage/group selection in the documented canonical command; `prek run --all-files` is not automatically the full gate in a grouped setup.

Use the existing checker for generated-code freshness. When adding one, regenerate in an isolated checkout or controlled scope so checking does not overwrite unrelated edits. Keep network-dependent vulnerability checks and cross-platform builds in the appropriate CI/release workflow.

## Verify the gates, not just the project

Use small isolated fixtures for new/changed comparison logic. Prove the intended failures, not merely that the config parses. Include cases from the maintainability reference: a new violation, worsening existing debt, an improvement, and an incomplete analyzer run.

Run targeted checks while implementing, then one applicable full pass after the changes are coherent. A passing unrelated test suite does not validate a new gate's rejection behavior. Avoid repeatedly running the whole project suite for documentation or comparator edits.

Before declaring setup complete, report:

- The canonical fast/full commands and which checks actually block.
- The largest confirmed legacy hotspots, measured debt, and narrow exceptions retained.
- What new/worsening behavior each maintainability gate rejects.
- Any analysis that is missing, partial, unsupported, or intentionally outside the requested scope.
- The checks run and their results, including representative rejection fixtures.

Use “configured checks pass with the following accepted debt” when appropriate. Do not imply the repository is structurally healthy or that every quality dimension is covered merely because the hook exits successfully. No analyzer eliminates the need for design review.
