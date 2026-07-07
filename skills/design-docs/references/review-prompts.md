# Design Review Prompt Templates

Ready-to-use prompts for asking another agent to critique a design document produced with the `design-docs` skill. Pick one per the selection guidance in the main `SKILL.md`, fill in the bracketed placeholders, and send it to the reviewer.

Each prompt enforces the same baseline contract: inspect relevant current code or docs when the design names existing loci, critique only, and return concrete design blockers or fixes. These prompts review design quality. They must not convert design findings into implementation tasks, milestones, owners, commits, or rollout steps.

## Design Contract Review Prompt

Use for most non-trivial design docs.

```text
Review the design contract in <design doc path> against the current code/docs in <repo path>.

Requirements:
- Inspect current code/docs for any existing APIs, modules, generated surfaces, adapters, schemas, or ownership boundaries named by the design.
- Judge whether the design is ready for implementation planning, not whether implementation tasks are complete.
- Check whether every V1 capability can be expressed as a contract matrix row: supported, rejected, deferred, default, source of truth, ownership/placement, routing, naming, equivalence, and proof obligations.
- Call out missing invariants, ambiguous ownership, unclear source of truth, undefined defaults, missing rejection rules, compatibility gaps, and unsupported cases that are asserted but not routed.
- Flag any implementation checklist, milestone, owner assignment, commit step, or task breakdown that belongs in an execution plan instead.
- Critique only. Do not edit files. Do not delegate. Do not create implementation tasks.

Return exactly these sections:
1. Design blockers
2. Ambiguous contract points
3. Implementation-planning leakage
4. Specific design doc fixes to apply next
```

## Behavior Precision Review Prompt

Use when validation, routing, projection, compatibility, defaults, state transitions, or failure behavior are the main risk.

```text
Review behavioral precision in <design doc path> against the current code/docs in <repo path>.

Requirements:
- Inspect current code/docs for any behavior the design claims to preserve, route through, project from, or reject.
- Check whether defaults, validation rules, routing rules, naming rules, compatibility behavior, and unsupported combinations are stated as executable policy.
- Check whether each complex behavior has either precise pseudocode, a decision table, a state transition table, or an explicit contract matrix row.
- Flag prose that should be replaced or supplemented by pseudocode, a decision table, a state transition table, or explicit rejection rules.
- Check that pseudocode names conditions, branches, errors, and outputs precisely enough that two implementers would build the same behavior.
- Check that proof obligations name properties to prove, not file edits, test names, commands, or milestones.
- Critique only. Do not edit files. Do not delegate. Do not create implementation tasks.

Return exactly these sections:
1. Behavior ambiguities
2. Missing pseudocode or decision tables
3. Unsupported or failure cases not defined
4. Specific design doc fixes to apply next
```

## Source Of Truth Review Prompt

Use for generated-code, adapter, schema, protocol, DSL, or multi-surface designs.

```text
Review source-of-truth and projection semantics in <design doc path> against the current code/docs in <repo path>.

Requirements:
- Inspect current generator, adapter, schema, protocol, or DSL ownership where the design names existing loci.
- Check that the canonical authored contract is explicit.
- Check that every projection surface is named and that schema/result/behavior equivalence requirements are testable as properties.
- Check that placement, routing, naming, collision behavior, discovery/catalog participation, and design-time-vs-runtime enablement are defined for every projection surface.
- Flag any duplicated contract, adapter-specific glue, unclear registration owner, ambiguous placement rule, naming collision gap, or deployment/runtime enablement confusion.
- Flag any unsupported feature that is claimed as preserved without an explicit route or rejection rule.
- Critique only. Do not edit files. Do not delegate. Do not create implementation tasks.

Return exactly these sections:
1. Source-of-truth blockers
2. Projection or routing ambiguities
3. Compatibility and equivalence gaps
4. Specific design doc fixes to apply next
```

## Focused Design Re-Check Prompt

Use after integrating review findings. This should be narrow and should not restart a full broad critique unless the patch changed the design contract.

```text
I applied fixes for these previous design blockers in <design doc path>:
- <blocker fixed>
- <blocker fixed>
- <blocker fixed>

Please do a focused re-check only of those blockers and design readiness.

Requirements:
- Inspect the changed design text and current code/docs only where needed to confirm the blockers are fixed.
- Do not re-review unrelated sections unless the fix introduced a new design blocker.
- Critique only. Do not edit files. Do not delegate. Do not create implementation tasks.

Return exactly these sections:
1. Blockers remaining
2. Ready for execution planning? yes/no with one sentence
```
