# Coverage ratchet

Do not use a fixed low threshold for every repository. Preserve a stricter existing policy. Otherwise, record current per-file coverage and reject regressions.

Official references:

- [Vitest coverage guide](https://v4.vitest.dev/guide/coverage)
- [Vitest 4 coverage migration](https://v4.vitest.dev/guide/migration.html#removed-options-coverage-all-and-coverage-extensions)
- [Vitest coverage reporter configuration](https://vitest.dev/config/coverage.html#coverage-reporter)

## Produce a complete artifact

The full test command must emit `coverage/coverage-summary.json`. Remove that generated file before the test run. The coverage gate must fail if the runner does not recreate it, or if the result is empty or invalid.

For Vitest, configure the JSON summary reporter and include owned source files that tests do not load:

```ts
coverage: {
  reporter: ['text', 'json-summary'],
  include: ['src/**/*.{ts,tsx}'],
  exclude: ['**/*.d.ts', '**/*.test.*', '**/generated/**'],
}
```

Vitest 4 removed `coverage.all`. Use `coverage.include` to put uncovered source files in the report.

Adapt `include` and `exclude` to the repository. Exclude generated, vendored, fixture, test, and setup files. Do not exclude owned production code to hide missing coverage.

## Record and enforce the baseline

Copy [../scripts/check-coverage-ratchet.mjs](../scripts/check-coverage-ratchet.mjs) into the target repository, for example as `tools/check-coverage-ratchet.mjs`. Then use it from the project root:

```text
node tools/check-coverage-ratchet.mjs --write-baseline --new-file-min 80
node tools/check-coverage-ratchet.mjs --new-file-min 80
```

Commit `.quality/coverage-baseline.json`. Generate it only after the team reviews the full report.

The check enforces these rules:

- Every existing file must keep or improve its line, statement, function, and branch percentages.
- A newly covered source file must meet `--new-file-min` for every metric.
- A baseline entry can disappear only when its source file no longer exists.
- Missing coverage or baseline artifacts fail the gate.

Use a small `--tolerance` only for reporter rounding. Tighten the baseline by writing it again after intentional improvements. Review the baseline diff before commit.
