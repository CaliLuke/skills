# Maintainability enforcement

Use this when setting up or auditing Go maintainability gates. The goal is to prevent unreviewed deterioration while exposing existing debt. Function scores and structural cohesion are different dimensions; measure both.

## Initial inspection

1. Inventory owned production code under the actual build tags. Separate generated/vendor source and test code explicitly; do not exclude hand-written transport wiring or design declarations merely because they are large.
2. Run the chosen function and structural analyzers. Check exit status, package-load errors, scope, and toolchain compatibility before interpreting findings. A partial audit can identify leads, but it cannot establish a complete baseline.
3. Inspect the largest receiver method sets, highest function complexities/lowest maintainability indices, and largest files/packages with disconnected responsibilities. Read representative callers, not just declarations. A service holder used only in startup wiring differs from one passed throughout business code; a lookup table differs from a file mixing lifecycle operations.
4. Classify important findings as actionable debt, justified exception, or unconfirmed signal. Report the confirmed hotspots to the user before saying the setup is complete. Do not turn a tool's severity label into a claim of production failure.

For a tiny cohesive module, a lightweight scope/size check plus initial inspection may be proportionate. For large services, use receiver/package analysis (for example Lagotto) and enforce known layer boundaries where the repository defines them. Record the limits of whichever approach is chosen.

## Function-level policy

Use maintainability index as the default function-level measure, with a starting floor of 20 and higher scores indicating better maintainability. Preserve an explicitly chosen repository policy and calibrate with actual functions. Cognitive/cyclomatic complexity can remain supporting evidence; do not enable several correlated gates merely to increase their count.

New functions below the selected score floor fail. Existing violations may be baselined after review, with their measured values retained. A function already above the complexity limit must fail when its complexity increases; a baselined maintainability index must fail when it declines. Compare stable function identity (module/package, receiver, function) rather than line number alone.

A diagnostic-presence/count baseline is insufficient: it can hide a function growing from complexity 30 to 60 while remaining “one known warning.” Extract numeric values from supported analyzer output, or retain a source/body fingerprint and require renewed review when that flagged implementation changes. Document the latter as a review trigger rather than a numeric comparison. Fail clearly when output cannot be parsed; never assume the old value still applies.

A score already at zero cannot decline further. Require explicit review of changes to those declarations (or conservatively their files) using a source fingerprint, and describe this as a review trigger rather than a measured regression.

Line-diff lint modes alone can also miss a worsening function whose diagnostic points at an unchanged declaration. The full gate must inspect the complete affected declaration/package and compare it with the accepted baseline.

## Structural policy

Use a reviewed rule set and severity threshold for automatic blocking. It should cover the repository's material risks: large multi-responsibility receivers, disconnected file/package responsibilities, broad dependency holders, and forbidden cross-layer dependencies where defined. Lower-severity naming advice may remain informational, clearly separated from enforcement.

New findings under that policy require resolution or a narrow documented exception. Known debt must not worsen without explicit review. For measured findings, retain relevant dimensions (for example receiver method count and concern groups); a stable finding ID alone must not grant unlimited growth. If the analyzer cannot express numeric worsening, use a reviewed fingerprint of the implicated declarations/files to trigger inspection. Avoid global average or total-count comparisons that let an unrelated improvement hide a regression.

Do not invent layer rules for a repository that has not defined them. Do not mandate a package per receiver, split coherent lookup tables, or move methods just to satisfy a size limit. A refactor should clarify responsibility and callers' dependencies, with transaction, authorization, and durable-effect boundaries preserved.

## Baselines and exceptions

Store stable identities, measured values or reviewed fingerprints, rule/tool versions, build scope, and a short rationale. Keep accepted debt distinct from a false-positive suppression. Confirmed large refactors should have a follow-up reference when ticket creation is authorized; otherwise retain an actionable local description and disclose it.

Normal checks are read-only. A baseline refresh must show additions, removals, metric increases/decreases, and scope changes for review; it must never run automatically to make a failing command pass. A move/rename is reviewed as an identity change, not an excuse to lose the old obligation. Tighten accepted values after improvements through the repository's explicit update workflow. Flag stale exceptions so they do not silently cover future unrelated code.

Do not baseline new defects from the current implementation as historical debt. Do not hide findings by broadening source exclusions, weakening thresholds, or treating a tool crash as an empty result. When tooling is blocked, state that the corresponding maintainability gate is incomplete and continue independent work.

## Rejection fixtures

For a new comparator or policy, use a small temporary Go module or analyzer-output fixture as appropriate. Verify:

- A new function below the maintainability floor fails.
- A known function with a declining score fails even when the diagnostic count and declaration line stay unchanged; changed zero-score code triggers review.
- Unchanged reviewed debt passes; an improvement passes and is visible for ratchet tightening.
- A growing receiver or newly disconnected responsibility fails the chosen structural policy or triggers its documented review path.
- A narrow justified suppression does not hide the same defect elsewhere.
- A missing tool, analyzer execution failure, package-load error, malformed/partial report, or missing owned package cannot be reported as clean. Handle a documented findings-only exit through the comparator; verify reviewed debt can pass without masking execution failures.

Use real analyzer execution for representative triggering examples; test comparison logic with fixtures where that is faster and more deterministic. Do not repeatedly run the application integration suite merely to validate this infrastructure.
