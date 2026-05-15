# Review Prompt Templates

Three ready-to-use prompts for asking another agent to critique a plan produced with the `design-docs-execution-plans` skill. Pick one per the selection guidance in the main `SKILL.md`, fill in the bracketed placeholders, and send it to the reviewer.

Each prompt enforces the same baseline contract: inspect real code (not just the plan text), critique only (no edits, no delegation), and return a fixed set of named sections so findings are easy to integrate.

## Plan Review Prompt

Use for most non-trivial plans in a single repo.

```text
Review these files in <repo path>:
1. <skill path>
2. <plan path>

Requirements:
- Inspect the current code where the plan points. Do not review the plan text in isolation.
- Judge whether the plan is executable by a fresh agent with no conversation context.
- Call out vague checklist items, weak acceptance criteria, missing file/module specificity, sequencing defects, wrong behavior loci, and places where the skill still allows weak plans.
- Critique only. Do not edit files. Do not delegate. Do not spawn sub-agents.

Return exactly these sections:
1. Remaining defects in the plan
2. Remaining ambiguity in the plan
3. Remaining gaps in the skill
4. Specific skill or plan fixes to apply next
```

## Actionability-Focused Review Prompt

Use when the main risk is that a fresh agent still would not know where to act.

```text
Inspect <plan path> against the current code in <repo path>.

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
- Critique only. No edits, no delegation, no implementation.

Return exactly these sections:
1. Broken cross-repo assumptions
2. Missing repo-path or module specificity
3. Missing verification steps
4. Skill rules to add or tighten
```
