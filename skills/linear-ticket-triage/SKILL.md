---
name: linear-ticket-triage
description: Audit Linear issues against the current codebase and close only those clearly done or no longer relevant. Use to triage backlog tickets, clean up stale backend issues, or reconcile Linear with recent implementation work.
---

# Linear Ticket Triage

## Overview

Use this skill when a repo has drifted from Linear and the user wants an evidence-based cleanup pass. The job is to verify tickets against the current codebase, not to guess from memory or close issues optimistically.

## Workflow

1. Pin the scope before touching tickets.
   Confirm the team, label, project, or issue set from the user request.
   Capture any explicit exceptions such as "leave immutable image work alone."

2. Load the Linear surface first.
   Use Linear tools to list the candidate issues.
   If status names matter, fetch the team's statuses first so you use real workflow states instead of guessing.
   Read each issue before deciding anything.

3. Verify against the repo.
   Inspect the codebase, tests, and recent commits for direct evidence.
   Prefer `rg`, focused file reads, and targeted tests over broad speculation.
   If the ticket is about behavior that could live outside the repo, distinguish "done in code" from "blocked on external config" or "no longer a repo issue."

4. Classify each ticket into one of four buckets.
   `Done`: the ticket scope is clearly implemented in the repo.
   `No longer relevant`: the original ticket no longer reflects useful work for this repo, is superseded, or belongs to external configuration/operations instead of code.
   `Still relevant`: the ticket scope is still materially open.
   `Partial / superseded`: some work landed, but the original ticket is not fully complete or should be rewritten rather than closed.

5. Only close the clear cases.
   Close `Done` issues when the repo evidence is strong.
   Close `No longer relevant` issues only when the remaining gap is clearly outside the repo or the ticket is stale enough to be misleading.
   Do not close partial tickets just to reduce backlog count.

6. Leave evidence on every closed issue.
   Add a short Linear comment before changing state.
   Include the key proof:
   file paths, test names, commit hashes, or a precise reason the ticket is obsolete.
   Keep comments factual and short.

7. Report the outcome to the user.
   Group by `closed done`, `closed stale`, `left open`, and `needs rewrite`.
   Call out any tickets you intentionally did not close because the evidence was incomplete.

## Decision Rules

- Default to keeping the ticket open if the evidence is ambiguous.
- Treat external console setup, infra toggles, and third-party configuration as distinct from repo implementation.
- If a ticket asks for a cleanup tail and the repo still contains the targeted production path, keep it open.
- If the user gives an exemption, never close those tickets during the pass.
- If a ticket is "mostly done" but not fully aligned with its acceptance criteria, leave it open and explain why.

## Linear Update Pattern

For each issue you close:

1. Add a comment with the decisive evidence.
2. Move it to the appropriate closed state used by the team.
3. Avoid rewriting issue history unless the user asked for that too.

If a ticket should stay open but the scope is stale, suggest a rewrite in your summary instead of silently mutating it.

## Evidence Standards

Strong evidence:

- A live production code path exists or is deleted in the expected place.
- Tests cover the claimed behavior.
- The implementation landed in a recent commit and matches the ticket scope.
- The repo clearly no longer owns the concern described by the ticket.

Weak evidence:

- "We probably already did this."
- Similar code exists somewhere else.
- The issue title sounds old.

Do not close tickets on weak evidence.

## Recommended Response Shape

When using this skill, return:

- The issues closed as done.
- The issues closed as no longer relevant.
- The issues left open because they are still real.
- The issues left open because they are partial, superseded, or need rewrite.

Keep the explanation short, but always include the core reason for each non-obvious decision.
