---
name: design-docs-execution-plans
description: Write a compact, decision-first design doc or execution plan — "implementation plan", "milestone checklist", "execution tracker", "design doc for X". Not for RFCs, ADRs, research memos, post-mortems, or open-ended "what could we do" questions. Execution plans render a sibling HTML progress tracker via `render_plan.py`.
---

# Design Docs And Execution Plans

Use this skill when the user wants a design document or an execution plan.

The goal is not to produce a broad analysis memo. The goal is to produce a short working document that can drive implementation, define exit conditions, and be checked off as work progresses.

## Design Doc vs Execution Plan

Both share the same shape (chosen design + milestones + acceptance criteria + checklists). They differ in how the document gets used after it is written:

- A **design doc** states the chosen design and how the code will look. It is written once and read by reviewers; checkboxes are aspirational.
- An **execution plan** is a design doc that gets worked through iteratively, with checkboxes flipped as tasks land. If the user wants progress tracking, will update the doc as work proceeds, or asked for a "tracker", "checklist", or "plan I can check off", treat it as an execution plan and render the sibling HTML tracker described in `Live HTML Tracker` below.

When in doubt, default to execution-plan shape — the HTML tracker is cheap to render and easy to ignore if it turns out the doc was read-once.

## Default Shape

Prefer a single document with:

1. A short opening paragraph stating the chosen design
2. Milestones
3. For each milestone:
   - what it is achieving
   - acceptance criteria to exit the milestone
   - a flat checklist

Default to this shape unless the user explicitly asks for something else.

For execution plans (as opposed to pure design docs), also render a sibling HTML tracker from the start so a human can follow progress visually. See the `Live HTML Tracker` section below.

## Non-Negotiables

- Do not pad the document with summary, background, current understanding, frontend note, decisions, risks, open questions, or follow-up sections if the same content can be folded into the main design paragraph or milestone tasks.
- Do not create multiple adjacent sections that restate the same thing in different words.
- Do not leave "open questions" in the document if a reasonable decision has already been made in the conversation.
- Do not create a separate "decisions" section if those decisions can be embedded directly in the design or milestones.
- Do not turn a plan into a changelog or essay.
- Do not use nested bullets.
- Do not treat milestones as loose buckets of tasks. Each milestone must have a goal and exit criteria.
- Do not put tests after implementation when the change can be protected by writing tests first.
- Do not hide process discipline in a final catch-all milestone if it belongs to an earlier milestone.
- Do not write branchy checklist items with `if`, `or`, `and/or`, or fallback phrasing unless the branch is a real explicit decision the user still needs to make.
- Do not write vague checklist items like `verify`, `confirm`, or `investigate` without stating the concrete artifact or outcome they must produce.
- Do not write checklist items that depend on conversation-only context. A fresh agent reading the plan should have enough information to start from the repo and act.
- Do not write review prompts that ask for plan critique without explicitly telling the reviewer to inspect the relevant code and verify that the tasks are actionable against the repo as it exists now.
- Do not name a file, module, package, test, route, or behavior owner unless you inspected it in the current repo or explicitly mark it as unknown.
- Do not include cross-repo work unless the checklist names the repo path and the verification command or concrete proof artifact.
- Do not use placeholder nouns like `queue/store/cache`, `handler/path`, or `module` once code inspection reveals the concrete owner type and file path.
- Do not use `targeted tests`, `verification`, or `checks` without naming the exact command from the correct repo root.
- Do not mark a non-trivial execution plan complete until a required peer review has been performed and reconciled in the plan status/checklist, or the plan explicitly states why the review was skipped under the small-plan exception.
- Do not let smoke checks satisfy parity, contract, or behavior acceptance criteria unless the plan names them as smoke checks and states the weaker assertion target.

## Writing Rules

- Compress aggressively. The document should read like an execution note, not a review artifact.
- State the chosen design directly. If delete is a hard delete, say that once and move on.
- Turn ambiguity into concrete tasks whenever possible.
- If a technical nuance matters for implementation, encode it in the relevant task.
  Example: "Resolve canonical display ID before cleanup" belongs in the backend milestone, not in a separate decisions appendix.
- Prefer milestone names that describe outcomes, not phases of thinking.
  Good: `Backend Cleanup`
  Bad: `Current Understanding`
- Prefer milestone goals that describe a completed state, not an area of investigation.
- Checklist items should be concrete and markable.
  Good: `Add a regression test for create -> delete -> entry removed from list query`
  Bad: `Think through testing`
- Checklist items should describe one chosen action, not a menu of options.
  Good: `Add frontend store test for evicting cached rows on entity.deleted`
  Bad: `Add a failing repro, targeted test, or otherwise reproducible verification`
- Checklist items should name the concrete locus of change or inspection when it is knowable from the repo.
  Good (Go backend example): `Add a regression test in internal/store/entries_test.go for create -> delete -> entry removed from list query`
  Bad: `Add a backend regression test`
- Checklist items should name the concrete command to run when the step is execution, not design.
  Good (Go backend example): `Run go test -run TestDeleteEntries -v ./internal/store/...`
  Bad: `Run the targeted backend tests`
- If an adjacent test already covers the same path, name that test file explicitly and extend it instead of writing `add or update a test`.
- If code inspection shows the behavior already exists, the plan should switch from presumed implementation to explicit verification.
  Good: `Add a frontend test proving entity.deleted invalidates the cache query that lists entries`
  Bad: `Implement eviction on entity.deleted` when the repo already does that
- Acceptance criteria should be stated as observable truths, not intentions.
  Good: `Deleting an entry with a pending change removes both from backend queries`
  Bad: `Backend seems correct`
- Acceptance criteria should state what makes them true.
  Good (Go backend example): `internal/store/entries_test.go contains a regression test where create -> delete removes both the entry and its pending change from backend queries`
  Bad: `The behavior is covered by tests`
- Acceptance criteria should name the proof artifact when it is knowable.
  Good (Go backend example): `A service-level test in internal/service/entries asserts that delete publishes entity.deleted`
  Bad: `Event coverage proves delete still emits entity.deleted`
- Acceptance criteria should name the exact observable or assertion target, not just the area of behavior.
  Good: `GetEntry returns no entry and ListPendingChanges omits the deleted entry's pending change`
  Bad: `Backend queries are correct`
- Process steps belong where they happen.
  Good: targeted tests immediately after the implementation they verify
  Bad: all validation deferred to the end
- Discovery tasks must name the output they produce.
  Good: `Identify the pending-changes store owner and record the concrete module to change`
  Bad: `Identify the pending-changes store`
- A fresh agent should not have to guess where to start.
  Include file paths, package names, commands, event names, stores, routes, or tests whenever those are already discoverable.
- For route-sensitive work, record both the client callsite and the server route/handler path when both are knowable.

## Milestone Contract

Every milestone should contain exactly these three elements:

1. `Goal`
   - One short sentence describing what the milestone achieves.
2. `Acceptance Criteria`
   - One to three bullets describing the conditions to exit the milestone.
   - Each bullet must be testable or directly checkable.
   - Each bullet should identify the proof artifact when it is already knowable: test file, command, manual check, route, store, event, or output.
   - Avoid vague words like `covered`, `verified`, `handled`, or `works` unless the bullet also states what concrete observation makes that claim true.
3. `Checklist`
   - Flat checkbox list for the work inside the milestone.

If a milestone lacks one of these, the plan is incomplete.

Acceptance criteria are exit conditions, not work items. They should answer:

1. What exact behavior or state must be true?
2. How would a fresh agent prove that it is true?
3. Where does that proof live?

## Ordering Rules

- Put discovery before implementation only when it is truly unresolved.
- If discovery is small, make it an explicit prerequisite milestone or the first checklist items in the relevant milestone.
- Write tests before code when the behavior can be captured in a regression or contract test.
- Run targeted tests immediately after the implementation they verify.
- Put commit, review, and push steps in the milestone where handoff actually happens.
- Do not use a generic final milestone like `Validation` as a dumping ground for unrelated steps.
- If an acceptance criterion depends on a test, the checklist should include writing or updating that test before the implementation step it protects.
- If a branch must exist, make it a named decision outside the checklist before writing the plan. Do not leave execution branches inside checklist items.
- If a fresh reviewer is asked to critique the plan, instruct them to inspect the current code and judge whether each checklist item is executable without hidden context.
- Preserve current public contracts explicitly when a plan changes internal mechanics.
  If IDs, return values, event payloads, or route behavior already have tests, state whether the plan preserves or changes them.
- If the plan preserves an existing outward contract while changing internals, say that explicitly in the milestone acceptance criteria.
- Before marking checklist items complete, inspect the changed code and make sure each acceptance criterion's named assertion, command, or proof artifact exists at the named file path.

## Default Document Template

This is the canonical template. It is also the exact shape `render_plan.py` parses, so an execution plan and a design doc both start from it. `## Status` and `Toc:` are required only when rendering the HTML tracker; a read-once design doc can omit them.

```md
# <Title>

<One short paragraph describing the chosen design and any critical constraints.>

## Status

- 2026-05-11 — Plan created.

## Milestones

### Milestone 1: <Outcome>

Toc: <short sidebar label>

Goal: <What this milestone achieves>

Acceptance Criteria

- <Observable exit condition>
- <Observable exit condition>

Checklist

- [ ] <Concrete task>
- [ ] <Concrete task>

### Milestone 2: <Outcome>

Goal: <What this milestone achieves>

Acceptance Criteria

- <Observable exit condition>

Checklist

- [ ] <Concrete task>
- [ ] <Concrete task>
```

## What To Fold Into Tasks

Fold these into the relevant milestone instead of creating separate sections:

- identifier handling details
- event contract details
- backend vs frontend ownership
- validation requirements
- "we are not changing X" constraints
- test-first sequencing
- commit/review/push discipline
- chosen file or module targets when discovery is already complete
- concrete commands or tests when they are already known
- cross-repo repo paths and proof artifacts when work spans repos
- adjacent test files that should be extended instead of invented from scratch

Example:

- Instead of a separate decision section saying "delete remains a hard delete," write:
  `Keep entry delete as a hard delete`
- Instead of a separate ambiguity section saying "cleanup must use public ID, not internal ID," write:
  `Resolve each delete input to the canonical public ID before explicit cleanup`
- Instead of putting review and push in a generic footer, write them in the final delivery milestone checklist
- Instead of saying "we should add tests," write:
  `Write failing regression test for create -> delete -> entry removed from list query`
- Instead of writing `cover both X and Y, or cover Z if canonical`, decide the contract first and write the exact test to add
- Instead of writing `verify whether the pending-changes store is already invalidated`, write:
  `Inspect the pending-changes store event handler and record whether entity.deleted already evicts cached rows`
- Instead of writing `update the frontend handler`, write:
  `Update <store/module path> to evict cached rows on entity.deleted`
- Instead of asking a reviewer to `check the plan`, ask:
  `Inspect the referenced code paths and judge whether each task names a concrete locus, output, and verification step`
- Instead of writing acceptance criteria like `backend event coverage proves delete still emits entity.deleted`, write:
  `internal/service/<test file> contains a test that asserts deleting an entry publishes entity.deleted`
- Instead of writing acceptance criteria like `canonical ID handling is covered`, write:
  `A delete-by-internal-ID regression test proves Delete resolves the canonical public ID before cleanup`
- Instead of assuming missing frontend behavior, write:
  `Inspect <frontend repo path> and choose between verification work and implementation work based on the current cache invalidation code`
- Instead of writing `run targeted frontend checks`, write (JS frontend example):
  `Run pnpm vitest <exact test file> from <frontend repo root>`

## When To Add Extra Structure

Add one extra section only if it materially changes implementation:

- `Scope` when the user explicitly wants in/out boundaries
- `Acceptance Criteria` when the user needs approval gates
- `Rollout` when deployment sequencing matters

If you add one of these, keep it short.

Do not add a document-level `Acceptance Criteria` section if the same contract is already expressed at the milestone level.

## Style And Discipline

- Favor milestone checklists over narrative prose.
- Treat milestone structure as mandatory, not optional.
- Use the host repo's real terminology from code and routes.
- Keep the document short enough that a human can scan it quickly and start implementation.
- If the user criticizes the format, simplify further instead of defending the original structure.
- A meticulous plan chooses actions. It does not preserve avoidable branches for later.

## Live HTML Tracker

For execution plans, render a live HTML tracker alongside the Markdown from the moment the plan exists so a human can follow iterations visually. The Markdown is the source of truth. The HTML is regenerated from it. The rendered HTML auto-reloads every 30 seconds, so an open browser tab picks up new renders without manual refresh.

Workflow:

1. Author the plan in Markdown at the repo root (e.g. `FOO_PLAN.md`) using the Default Document Template above.
2. Render the HTML sibling by running `render_plan.py`. See `Renderer CLI` below for the exact invocation.
3. Re-render after every plan edit or progress update.
4. Update progress by editing the Markdown only: toggle `- [ ]` to `- [x]` on completed tasks and append a dated bullet to `## Status`. Never hand-edit the HTML.
5. When the work concludes, move both files to a `plans/` directory (create it if missing) to archive them.

The rendered HTML recomputes hero stats, milestone progress bars, status badges (`Pending` vs `Complete`), and ToC counts at page load from checkbox state. Do not pre-compute these in the Markdown.

The renderer is intentionally a constrained subset, not a full Markdown engine. If you find yourself wanting nested bullets, callouts, or rich formatting, the skill's writing rules are telling you to simplify the plan, not extend the renderer.

### Renderer CLI

Invocation: `python3 "<skill-dir>/render_plan.py" PLAN.md [-o OUTPUT.html]`, where `<skill-dir>` is the directory containing this `SKILL.md` (resolve it from wherever the host has installed the skill — do not hardcode a user-specific path).

- **Positional arg**: path to the Markdown plan.
- **`-o`/`--output PATH`**: write HTML to PATH instead of the default sibling `.html`. Useful for diffing renders against a committed reference without clobbering it.
- **Python**: requires 3.10+ (PEP 604 union syntax). Stdlib only — no third-party dependencies.
- **Exit codes**: `0` success, `1` Markdown parse error (the script prints the reason to stderr), `2` plan file not found.
- **Idempotence**: re-running on the same Markdown produces the same HTML byte-for-byte.

If the renderer rejects the file, fix the Markdown until it parses; do not hand-edit the HTML.

### Renderer-Specific Rules

These supplement the Default Document Template above. They are constraints the parser enforces, not style choices:

- Use `### Milestone N: <Title>` for every milestone. The `N:` is mandatory; `N` can be any single token (typically a digit).
- The literal lines `Goal:`, `Acceptance Criteria`, and `Checklist` are mandatory and case-sensitive inside each milestone block.
- `Toc:` is optional. If present, the renderer uses the short label in the sidebar; otherwise it falls back to the milestone title. Keep ToC labels short enough to fit the sidebar (~2-3 words).
- `## Status` bullets must be of the form `- YYYY-MM-DD — body` to render as a timeline entry. Bullets without a leading date render as plain text.
- Inline backticks render as `<code>`. No other Markdown features are supported (no bold, italic, links, images, tables, headings inside milestones).
- No nested bullets. No `if`/`or` branchy phrasing in checklist items (already covered by the writing rules above).

### Attached Command Disclosure

A checklist item can be followed by an indented fenced code block. The renderer turns it into a collapsible "show command" disclosure attached to that item. Use this only for commands too long to read inline (e.g. peer-review invocations); short commands belong inline in backticks.

Required shape: blank line after the checklist item, then a fence indented by **2+ spaces**, matching closing fence at the same indent.

````md
- [ ] Run the peer-review script

  ```bash
  /path/to/long-script --name foo --basis "..." --focus "..."
  ```
````

The fence language tag is optional but recommended (`bash`, `text`, etc.) so the source Markdown passes lint hooks that enforce MD040. The renderer ignores it.

## Review Prompt Rule

When asking another agent to critique a plan produced with this skill, the prompt should explicitly require all of the following:

1. Inspect the relevant code, not just the plan text.
2. Check whether each checklist item is actionable by a fresh agent with no conversation context.
3. Call out vague tasks that do not name a file, package, module, event, command, or test when that detail is already discoverable.
4. Call out checklist items whose acceptance criteria are not backed by a named verification step.
5. Call out plan items that assume missing behavior when the inspected code already implements that behavior.
6. Critique only. No delegation, no implementation, no meta-summary.

Use a review pass by default for non-trivial plans. A single planner should not trust themselves to catch all structural defects unaided.

## When To Use Review Prompts

Run an external review prompt when any of these are true:

- the plan spans more than one milestone
- the plan touches more than one layer or repo
- the plan includes backend plus frontend work
- the plan names specific files, tests, routes, stores, or events
- the plan will be used as an execution artifact for someone other than the planner
- the planner had to make architectural or contract decisions while drafting it

You may skip the external review only for very small plans where all of these are true:

- one milestone only
- one repo only
- one obvious implementation locus
- no cross-layer coordination
- no ambiguity about tests, commands, or ownership

If you skip the review, do a local self-check against the same standards before finalizing.

## How To Use Review Prompts

Use this loop:

1. Draft the plan using this skill.
2. Choose the review prompt type that matches the plan shape.
3. Give the reviewer:
   - the plan path
   - the skill path
   - the repo path or repo paths
   - the concrete code paths they must inspect
4. Ask for critique only.
5. Update the plan first to fix plan-local defects.
6. Update the skill if the reviewer found a weakness the skill should have prevented.
7. If the changes were substantial, run one fresh review pass again.

Do not outsource the loop itself to the reviewer. The reviewer critiques; the planner integrates.

## Which Review Prompt To Choose

- Use `Plan Review Prompt` for most non-trivial plans in a single repo.
- Use `Actionability-Focused Review Prompt` when the main risk is that checklist items or acceptance criteria are still too vague for a fresh agent.
- Use `Cross-Repo Review Prompt` when the plan spans multiple repos or names work outside the current repo.

If in doubt:

- start with `Plan Review Prompt`
- switch to `Actionability-Focused Review Prompt` if the first review says the plan is still vague
- use `Cross-Repo Review Prompt` as soon as the plan includes another repo path

## Review Prompt Templates

The three ready-to-use templates live in `references/review-prompts.md` (in this skill's directory). Read that file when you are about to send a review prompt, copy the appropriate template, fill in the bracketed placeholders (`<repo path>`, `<plan path>`, `<skill path>`), and send it.

You do not need to read the templates file to decide _whether_ to run a review or _which_ prompt to pick — that decision guidance is in the `When To Use Review Prompts` and `Which Review Prompt To Choose` sections above. Load the reference file only when you have decided to send a prompt.
