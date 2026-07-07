---
name: execution-plans
description: Write requested implementation plans, milestone checklists, execution trackers, and handoff plans from an accepted design or exact implementation direction. Use for planning artifacts only, not for ordinary implementation requests or design debate.
---

# Execution Plans

Use this skill only when the user asks for a planning artifact: an implementation plan, milestone checklist, execution tracker, handoff plan, or similar document. Do not use it for ordinary requests to implement code.

Use this skill after the design contract is accepted, or when the user has supplied an exact implementation direction. If the document must choose API semantics, architecture, data model, validation behavior, compatibility rules, alternatives, or other design contract details, stop and use the design-docs skill first. Do not smuggle unresolved design debate into an execution checklist.

## Output Contract

An execution plan states:

- the accepted implementation direction
- ordered milestones
- concrete acceptance criteria for each milestone
- flat checklists with exact loci of work
- named proof commands and artifacts
- review, commit, push, or handoff steps when requested

Execution plans may include design context only when it is needed to execute correctly. They must not re-litigate the design.

## Default Shape

Use one Markdown file:

```md
# <Title>

<One short paragraph summarizing the accepted design and implementation boundary.>

## Status

- YYYY-MM-DD — Plan created.

## Milestones

### Milestone 1: <Outcome>

Toc: <short label>

Goal: <What this milestone achieves>

Acceptance Criteria

- The executing agent has recited the workflow on the record before any code edits.
- <Observable exit condition with proof artifact>

Checklist

- [ ] Read this plan end-to-end, read the linked skill at `<skill-path>`, then recite the workflow you will follow — milestone order, exit criteria, named commands in execution order, test-first rule, peer-review gate, commit/push handoff, and inherited repo constraints. Do not edit code before this recital is on the record.
- [ ] <Concrete task>
- [ ] <Concrete proof command>
```

Every milestone must contain exactly `Goal`, `Acceptance Criteria`, and `Checklist`.

## Mandatory First Step

The first checklist item in the first milestone must force the executing agent to recite the workflow before editing code. The recital must cover:

- milestone order
- exit criteria
- named commands in execution order
- test-before-implementation requirements
- review or self-check gate
- commit/push or handoff steps
- inherited repo constraints from `AGENTS.md`, `CLAUDE.md`, README, hooks, or local scripts

## Writing Rules

- Use flat checklists only. No nested bullets.
- Keep acceptance criteria observable and tied to proof artifacts.
- Name exact files, packages, commands, tests, routes, stores, generated outputs, or modules whenever current code inspection can identify them.
- Do not write vague tasks like `verify`, `investigate`, `update backend`, or `add tests` without naming the concrete output.
- Do not use branchy checklist items with `if`, `or`, or `and/or` unless the branch is an explicit decision still assigned to the user.
- Do not put tests after implementation when a regression or contract test can be written first.
- Put targeted proof commands immediately after the implementation they verify.
- Do not place all verification in a generic final milestone.
- Do not claim pre-existing failures are unrelated. A red required gate is a blocker unless the repo instructions define an explicit exception.
- Preserve existing user changes in dirty worktrees.
- Do not include cross-repo work unless the checklist names the repo path and proof command or artifact for that repo.
- Do not mark the document ready for execution until a review pass has been performed, unless it is a one-milestone, single-repo, obvious implementation with no cross-layer coordination.

## Inventory Rules

When the plan changes an interface, generated contract, datastore behavior, broad cleanup, or cross-layer API:

- include an initial inventory task that names the exact `rg` scope or code search to run
- reconcile every current match to a checklist item, false-positive category, or disposition artifact
- name compile-impact surfaces such as fakes, mocks, generated adapters, stream types, and test doubles
- sequence type/interface additions before tests or commands that import those symbols
- name generated DTO fields, nullability, pointer/slice semantics, and generated artifact assertions
- distinguish mapper/unit tests from real datastore integration tests when datastore traversal or mutation matters

## Acceptance Criteria Rules

Acceptance criteria are exit conditions, not work items. Each one should answer:

1. What exact behavior or state must be true?
2. How does a fresh agent prove it?
3. Where does the proof live?

Good:

- `internal/store/entries_test.go contains a regression where create -> delete makes GetEntry return not found and ListPendingChanges omit the deleted entry.`

Bad:

- `Backend delete behavior is covered.`

## Review Prompt Rule

For non-trivial execution plans, read `references/review-prompts.md` and use the prompt that matches the main risk:

- use `Plan Review Prompt` for most non-trivial single-repo plans
- use `Actionability-Focused Review Prompt` when the main risk is vague tasks or missing loci of work
- use `Cross-Repo Review Prompt` when the plan spans repositories
- use `Parallel Slice Review Prompt` when independent slices can be reviewed separately
- use `Focused Readiness Re-Check Prompt` after applying blocker fixes

Ask reviewers to critique execution readiness, not the accepted design. The prompt must require reviewers to inspect current code and return only blockers or concrete fixes.

Reviewers should check:

- every checklist item is actionable by a fresh agent
- acceptance criteria have named proof artifacts
- task order respects test-first and compile dependencies
- inventory items are reconciled
- named files and commands are real
- design assumptions are not being reopened as implementation ambiguity

The plan is not ready until blocker findings are applied or explicitly rejected with rationale, and a focused re-check returns ready. If implementation inspection proves the accepted design impossible or internally contradictory, record a `Design Blocker` and stop. Do not resolve the design inside the execution plan.

## Live HTML Tracker

When the user asks for a tracker, progress document, or check-off plan, render a sibling HTML tracker with `render_plan.py`. The Markdown remains the source of truth.

Workflow:

1. Author the Markdown execution plan at the repo root.
2. Render HTML with `python3 "<skill-dir>/render_plan.py" PLAN.md`.
3. Re-render after edits.
4. Update progress by editing Markdown checkboxes and `## Status` only.
5. Never hand-edit generated HTML.

Renderer constraints:

- Use `### Milestone N: <Title>` headings.
- Inside each milestone, include literal `Goal:`, `Acceptance Criteria`, and `Checklist` lines.
- `Toc:` is optional and should stay short.
- `## Status` dated bullets should use `- YYYY-MM-DD — body`.
- Attached long commands may use an indented fenced block directly under the checklist item.

## Handoff From Design Docs

When an accepted design doc exists, start by extracting:

- v1 scope
- source of truth
- validation/rejection rules
- routing or ownership rules
- compatibility requirements
- proof obligations

Translate those into milestones and checklist items. If implementation inspection proves the design is impossible or internally contradictory, record a `Design Blocker` and stop. Do not re-open or resolve the design inside the execution plan.
