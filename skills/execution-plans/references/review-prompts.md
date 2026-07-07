# Execution Plan Review Prompt Templates

Ready-to-use prompts for asking another agent to critique an execution plan produced with the `execution-plans` skill. Pick one per the selection guidance in the main `SKILL.md`, fill in the bracketed placeholders, and send it to the reviewer.

Each prompt enforces the same baseline contract: inspect real code, critique only, and return concrete blockers or fixes. These prompts review execution readiness. If the accepted design cannot be executed as written, reviewers should report a design blocker instead of resolving the design inside the execution plan.

## Plan Review Prompt

Use for most non-trivial plans in a single repo.

```text
Review execution readiness for these files in <repo path>:
1. <skill path>
2. <plan path>

Requirements:
- Inspect the current code where the plan points. Do not review the plan text in isolation.
- Judge whether the plan is executable by a fresh agent with no conversation context.
- Call out vague checklist items, weak acceptance criteria, missing file/module specificity, sequencing defects, wrong behavior loci, missing commands, and places where the skill still allows weak plans.
- Do not reopen accepted design decisions. If a task is impossible or contradictory, report it as a design blocker.
- Critique only. Do not edit files. Do not delegate. Do not spawn sub-agents.

Return exactly these sections:
1. Execution blockers
2. Non-actionable or under-specified tasks
3. Missing proof commands or artifacts
4. Specific skill or plan fixes to apply next
```

## Actionability-Focused Review Prompt

Use when the main risk is that a fresh agent still would not know where to act.

```text
Inspect <plan path> against the current code in <repo path> for actionability.

Requirements:
- Inspect the concrete files, tests, commands, routes, stores, and modules referenced by the plan.
- Check whether each checklist item is directly actionable by a fresh agent without hidden conversation context.
- Flag any task that does not name a concrete locus of work or a concrete proof artifact when that detail is already discoverable.
- Flag any acceptance criterion that does not state what makes it true.
- Critique only. No edits, no delegation, no implementation.

Return exactly these sections:
1. Non-actionable checklist items
2. Weak acceptance criteria
3. Missing repo-specific detail
4. Exact prompt or skill rules needed to prevent those defects next time
```

## Cross-Repo Review Prompt

Use when a plan spans multiple repos.

```text
Inspect <plan path> against these repos:
- <repo path A>
- <repo path B>

Requirements:
- Verify every cross-repo checklist item names the repo path, concrete module or test locus, and the proof artifact or command that closes it.
- Flag any milestone that cannot be executed from the named repos alone.
- Flag any plan item that assumes missing behavior without checking the current code first.
- Flag any design decision that is being reopened as ambiguous execution work. If the accepted design is impossible or contradictory, report it as a design blocker.
- Critique only. No edits, no delegation, no implementation.

Return exactly these sections:
1. Broken cross-repo assumptions
2. Missing repo-path or module specificity
3. Missing verification steps
4. Skill rules to add or tighten
```

## Parallel Slice Review Prompt

Use for broad plans where several independent risk slices can be reviewed at the same time. Send one prompt per reviewer, changing `<slice>` and `<slice-specific paths>` for each reviewer.

```text
Review the <slice> execution slice of this plan in <repo path>:
1. <skill path>
2. <plan path>

Planner-owned inventory for this slice:
- <inventory fact or rg result>
- <inventory fact or rg result>

Slice-specific code paths to inspect:
- <slice-specific path>
- <slice-specific path>

Requirements:
- Inspect the current code for this slice. Do not review the plan text in isolation.
- Judge whether this slice is executable by a fresh agent with no conversation context.
- Call out wrong owners, sequencing defects, missing tests, missing commands, stale assumptions, and checklist items that do not reconcile the inventory.
- Stay inside this slice unless you find a blocker that crosses slice boundaries.
- Critique only. Do not edit files. Do not delegate. Do not spawn sub-agents.

Return exactly these sections:
1. Slice blockers
2. Slice ambiguities
3. Missing inventory reconciliation
4. Exact plan or skill fixes for this slice
```

## Focused Readiness Re-Check Prompt

Use after integrating review findings. This should be narrow and should not restart a full broad critique unless the patch changed architecture or milestone boundaries.

```text
I applied fixes for these previous blocker findings in <plan path>:
- <blocker fixed>
- <blocker fixed>
- <blocker fixed>

Please do a focused re-check only of those blockers and readiness.

Requirements:
- Inspect the changed plan text and the current code only where needed to confirm the blockers are fixed.
- Do not re-review unrelated slices unless the fix introduced a new blocker.
- Critique only. Do not edit files. Do not delegate. Do not spawn sub-agents.

Return exactly these sections:
1. Blockers remaining
2. Ready to execute? yes/no with one sentence
```
