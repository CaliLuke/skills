---
name: design-docs
description: Write engineering design documents for architecture, API, framework, or product-contract decisions before implementation planning. Use when the user asks for a design doc, proposal, RFC-style design, contract design, or wants to debate system shape. Not for execution plans, milestone checklists, progress trackers, or implementation task breakdowns.
---

# Design Docs

Use this skill when the user wants to define, critique, or refine the shape of a system before implementation work is planned. The output is a design artifact for discussion and review, not a task list.

The goal is to settle the contract: what problem is being solved, what design is chosen, what behavior follows from it, what is rejected, and what proof obligations must hold. Implementation sequencing belongs in the execution-plans skill after the design is accepted.

## When To Use

Use this skill for:

- engineering design documents
- architecture proposals
- API, DSL, protocol, data-model, runtime, or framework contract designs
- design reviews where the main question is "is this the right shape?"
- design artifacts that should be reviewed before implementation tasks are written

Do not use this skill for:

- implementation plans
- milestone checklists
- progress trackers
- commit, branch, or rollout plans
- test-first execution plans
- documents whose main purpose is assigning files, commands, and tasks

If the user asks for both design and implementation planning, write or refine the design doc first, then hand off to the execution-plans skill only after the design contract is stable.

## Default Shape

Prefer these sections unless the user gives a different section list:

```md
# <Title>

## Summary

## Problem Statement

## Goals

## Non-Goals

## Current State

## Proposed Design

## API / Contract Changes

## Detailed Behavior
```

Optional sections are allowed only when they materially improve design review:

- `Alternatives Considered`
- `Risks And Tradeoffs`
- `Open Questions`
- `Proof Obligations`

Do not add implementation milestones, checkboxes, owner assignments, or commit/push steps.

## Design Discipline

- Keep implementation tasks out of the design doc.
- Treat the design-owned contract as the center of the document.
- Turn vague intentions into invariants, decision rules, rejection rules, or future-work boundaries.
- Prefer exact defaults, validation rules, routing rules, naming rules, and compatibility rules over broad prose.
- Use pseudocode, decision tables, and small examples when they make behavior more precise and shorter.
- Make unsupported cases explicit. Say whether they are rejected now, future work, or intentionally unsupported.
- State backward compatibility as an observable rule when existing behavior must not change.
- Include proof obligations, not execution steps. It is fine to say a golden fixture or schema-equivalence test is required; do not write the implementation checklist for creating it. Proof obligations must name the property to prove, not the file edits, test names, command sequence, or milestone needed to prove it.
- Avoid placeholder nouns once code inspection reveals real owners.
- Do not invent code paths, files, or module names. If you did not inspect the repo, phrase owner details as design-level responsibilities instead of fake specifics.
- For repo-backed designs, inspect current docs and source before naming existing files, modules, APIs, generators, or ownership boundaries. If inspection is not possible, keep ownership at the responsibility level.
- Preserve the difference between design-time permission and deployment/runtime enablement.
- For generated-code systems, name the source of truth and every projection surface.

## Detailed Behavior Pattern

Detailed behavior should read like executable policy. For complex designs, use this shape:

1. One sentence naming the invariant.
2. Pseudocode or a decision table for defaults and validation.
3. Pseudocode or a small diagram for projection/routing.
4. A short proof-obligation list.

Example:

```go
func validate(input) error {
    if input.Has(FeatureA) && !input.Has(RequiredOwner) {
        return error("FeatureA requires RequiredOwner")
    }
    if input.Mode == Legacy && input.Has(NewOnlyOption) {
        return error("NewOnlyOption is unsupported in legacy mode")
    }
    return nil
}
```

Use prose for why the rule exists; use pseudocode for what the rule is.

## Design Completeness Gate

Before a design doc is ready for execution planning, every V1 capability must be expressible as a testable contract matrix. If a row cannot be filled without guessing, the design is not done.

For each capability, surface, mode, or generated artifact, define:

- `Supported`: what works in V1
- `Rejected`: what fails fast in V1
- `Deferred`: what is explicitly future work
- `Default`: what happens when new metadata or configuration is absent
- `Source Of Truth`: where the canonical authored contract lives
- `Ownership / Placement`: where generated, runtime, protocol, or catalog artifacts live
- `Routing`: which execution or dispatch path is used
- `Naming`: exposed names, aliases, and collision behavior
- `Equivalence`: schemas, results, or behavior that must match across projections
- `Proof Obligations`: properties that fixtures, tests, or review evidence must prove

Use this table shape when it makes the design shorter or clearer:

```md
| Capability | Supported | Rejected | Default | Source Of Truth | Placement | Routing | Naming | Equivalence | Proof |
|------------|-----------|----------|---------|-----------------|-----------|---------|--------|-------------|-------|
| <name> | <V1 support> | <fail-fast cases> | <default> | <owner> | <placement> | <path> | <names/collisions> | <matching rule> | <property> |
```

### Completeness Heuristics

Use these sniff tests to catch gaps that the general matrix can hide:

- If the design says "preserve existing behavior", it must say what output remains byte-for-byte or contract-equivalent and what proof locks that down.
- If the design exposes one contract through multiple surfaces, it must name the canonical source and define projection equivalence for payloads, results, errors, and visibility.
- If the design adds placement metadata, it must define valid owners, invalid owners, missing placement behavior, and whether cross-owner placement is supported.
- If the design adds routing, adapters, dispatchers, or generated glue, it must say where the shared path lives, who can call it, and what duplicate paths are forbidden.
- If the design names an unsupported feature, it must say whether V1 rejects it, defers it, or intentionally supports it, and where that decision is enforced.
- If the design creates externally visible names, it must define the default name, collision scope, collision behavior, and whether aliases are future work.
- If the design changes catalog, discovery, search, visibility, permissions, or registration behavior, it must define how the new artifact participates in every existing discovery path.
- If deployment configuration can suppress or enable behavior, it must distinguish design-time permission from runtime registration.
- If a feature is internal-only, external-only, or dual-surface, it must define both the positive availability rule and the negative non-exposure rule.
- If proof obligations mention tests or fixtures, they must state the property being proved, not the implementation sequence for proving it.

## Review Loop

For non-trivial design docs, expect one or more critique-and-tighten passes before the doc is ready. Review findings should be applied to the design, not converted into implementation tasks.

For non-trivial design docs, read `references/review-prompts.md` and use the prompt that matches the main risk:

- use `Design Contract Review Prompt` for most design docs
- use `Behavior Precision Review Prompt` when validation, routing, projection, compatibility, or defaults are complex
- use `Source Of Truth Review Prompt` for generated-code, adapter, schema, protocol, or multi-surface designs
- use `Focused Design Re-Check Prompt` after applying blocker fixes

Ask reviewers to critique only:

- missing invariants
- ambiguous ownership
- unsupported cases that are asserted but not routed
- compatibility gaps
- naming, placement, or schema rules that can be interpreted more than one way
- behavior that would be clearer as pseudocode, a decision table, or an explicit state transition
- proof obligations that are too vague to test later

Do not ask design reviewers to create implementation tasks. Do not let review loops drift into milestone planning.

The design is not ready until blocker findings are applied or explicitly rejected with rationale, and a focused re-check returns ready.

## Handoff To Execution

A design doc is ready to hand off when:

- v1 scope is explicit
- default behavior is locked
- source of truth is clear
- placement, routing, naming, and validation semantics are defined
- unsupported combinations fail fast or are clearly deferred
- proof obligations are concrete enough to become tests later
- remaining open questions are true design decisions, not missing implementation work

At that point, use the execution-plans skill to translate the accepted design into milestones, checklists, exact files, and commands.
