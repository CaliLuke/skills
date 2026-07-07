---
name: claude-design-prompt
description: Create, critique, or revise prompts for Claude Design and similar AI UI prototype generators. Use when the user wants a visual UI prototype prompt, wants to improve an existing design prompt, shares a generated design for review, or needs prompts that preserve product semantics, domain rules, workflow state, and negative constraints instead of producing generic UI.
---

# Claude Design Prompt

## Goal

Write prompts that make Claude Design generate useful product UI prototypes, not generic screens. Preserve product vocabulary, invariants, safety rules, and workflow state as hard constraints.

## Workflow

1. Gather product truth: domain entities, user role, target workflow, current screen state, realistic data examples, safety rules, business rules, allowed actions, and disabled actions.
2. Separate hard rules from visual preferences. Hard rules include taxonomy, lifecycle semantics, authorization policy, destructive action behavior, and data states.
3. Draft the prompt with these sections: product and surface, screen to create, domain rules, target state, layout, interaction semantics, visual style, avoid, and review checklist.
4. Use concrete labels, counts, row examples, payload snippets, and command names. Do not ask for "a dashboard" without giving state and data.
5. Add negative constraints for likely model drift. Ban invented categories, actions, policies, and states.
6. Review the generated image against the domain rules before accepting it. Revise the prompt when the design invents concepts, mislabels actions, or contradicts product policy.

## Prompt Requirements

- Make domain invariants explicit with "must" language.
- Include at least one populated, realistic state.
- Include enabled and disabled actions, plus the reason each matters.
- Include exact copy and label constraints when product language matters.
- Include negative constraints that ban plausible wrong outputs.
- For operational tools, prefer dense working views over landing pages or marketing-style compositions.
- For approval or cleanup workflows, show evidence, proposed changes, confidence, auditability, and rollback or rejection paths where relevant.

## Review Checks

Before treating a generated design as useful, check:

- Does the taxonomy match product rules?
- Are action labels consistent with lifecycle semantics?
- Are destructive, permissioned, or write actions gated?
- Are counts and status labels internally consistent?
- Does the selected item's detail pane match the selected row?
- Are disabled, loading, error, empty, draft, review-only, and policy-eligible states clear where relevant?
- Did the design invent product concepts that were not in the prompt?

For a reusable prompt skeleton and a Contact Cleaner example, read `references/prompt-template.md`.
