# Claude Design Prompt Template

Use this as a starting point when drafting a prompt for Claude Design. Delete irrelevant sections, but keep hard domain rules and negative constraints.

## Template

```text
Design [surface] for [product].

This is [app/tool context], not a marketing page. The primary user is [role]. The screen is [route/workflow/state].

Hard domain rules:
- [Rule the design must not violate.]
- [Taxonomy, lifecycle, permission, or safety rule.]
- [What actions are allowed, disabled, or forbidden in this state.]

Target state to show:
- [Selected object, focused workflow, or current mode.]
- [Counts, queue state, sync state, timestamps, statuses.]
- [What is enabled, disabled, pending, or blocked.]

Layout:
- [Region 1 and purpose.]
- [Region 2 and purpose.]
- [Region 3 and purpose.]

Data examples:
- [Concrete row/card/item labels.]
- [Example field values.]
- [Evidence, confidence, status, or audit values.]

Interaction semantics:
- [Key/button/action] means [specific product action].
- Disabled: [action] when [state] because [reason].
- Destructive or external writes require [confirmation/review behavior].

Visual style:
- [Density, palette, typography, platform, component style.]
- [What should feel prominent or quiet.]

Avoid:
- Do not invent [categories/actions/policies].
- Do not show [forbidden or impossible state].
- Do not use [generic UI pattern that would weaken the workflow].

Review checklist:
- [Domain rule check.]
- [Action/state consistency check.]
- [Data consistency check.]
```

## Example: Contact Cleaner Proposal Review

```text
Design a terminal-style desktop UI mockup for Contact Cleaner.

This is a dense, keyboard-driven operational tool for reviewing proposed contact-cleanup changes before they can write to Google Contacts. It is not a landing page and not a generic CRM. The primary user is a human reviewer who needs to inspect evidence, convert safe cleanup proposals, reject bad proposals, and keep external writes controlled.

Hard domain rules:
- The proposal taxonomy must be D1 inverted-name, D2 same-email, D3 normalized-identical-name, D4 fuzzy, and Q7 whitespace field-fix.
- D1-D4 are review-only in this screen. They can be inspected, rejected, edited, or converted into an explicit cleanup proposal, but they must not be shown as already approved for automatic Google writes.
- Q7 whitespace field-fix is the only visible policy-eligible group in this state.
- External Google writes are never automatic. They require explicit human approval or confirmation and move through a serialized write queue.
- The UI must distinguish review-only proposals from policy-eligible cleanup proposals.

Target state to show:
- Header: "16 proposals · 12 review · 4 policy-eligible".
- Selected row: "D1.042 Acuña, María ↔ María Acuña" with .94 confidence and "review-only" status.
- The selected item detail pane shows raw snapshots for contact a and contact b, normalized fields, detector evidence, and draft field winners.
- The command bar shows "c convert" enabled, "a approve" disabled for the selected review-only item, "r reject" enabled, and "e edit" enabled.
- Top status shows Google ready, sync time 14:23, contacts 4,821, open 16, queue idle.

Layout:
- Left navigation with dashboard, findings, proposals, contacts, audit, setup.
- Main proposal list grouped by detector class with compact rows, confidence, status, and group counts.
- Right inspector with selected proposal id, confidence, raw snapshots, normalized comparison, detector evidence, and draft field winners.
- Bottom command bar with keyboard shortcuts.

Visual style:
- Monospace terminal UI, compact spacing, sharp grid lines, high-contrast dark surface, red review-only status, teal policy-eligible status, and muted inactive text.
- Keep the interface information-dense and work-focused.

Avoid:
- Do not label D1-D4 as policy-eligible in this state.
- Do not use "auto" for proposals that still require review.
- Do not show "approve" as available for D1.042 unless it is first converted.
- Do not invent detector categories, merge policies, CRM pipeline concepts, or marketing content.
- Do not make a decorative dashboard or card-heavy SaaS landing page.

Review checklist:
- The selected row and detail pane refer to the same proposal id.
- The header counts add up to the visible groups.
- Review-only and policy-eligible states are visually distinct.
- Google write behavior is clearly gated.
- The command bar matches the selected item's lifecycle state.
```
