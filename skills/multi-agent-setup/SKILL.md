---
name: multi-agent-setup
description: Share repository instructions and skills across coding agents. Use for "set up multi-agent", "share skills between agents", "unify agent configs", migrating CLAUDE.md to AGENTS.md, or sharing `.agents/skills` and `.claude/skills`. Use AGENTS.md as the shared instruction file and symlink shared skill directories without duplicating content.
---

# Multi-agent setup

Make the current repo usable by Claude Code and other agent systems without duplicating skills or top-level instructions. Choose the instruction-file arrangement and canonical skills directory independently.

## Instruction files

[Claude Code 2.1.277](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#21277) added an AGENTS.md fallback for projects with no CLAUDE.md. The release also added a **Project instructions** choice in `/config` and excluded Bedrock, Vertex, and Foundry at launch. An existing CLAUDE.md takes precedence under the default behavior; do not assume both files are combined.

Use **AGENTS.md as the canonical instruction file**. If CLAUDE.md exists, migrate its content into AGENTS.md and remove the old CLAUDE.md file or link after preserving its content. **Never create CLAUDE.md**, including a compatibility symlink. Older versions or unsupported providers do not change this rule; report a known compatibility limitation instead of creating the file.

Inspect AGENTS.md and CLAUDE.md, including symlink targets, before changing them:

| Existing state | Action |
| --- | --- |
| AGENTS.md only | Keep it. Do not create CLAUDE.md. |
| CLAUDE.md is a real file; AGENTS.md is absent | Move CLAUDE.md to AGENTS.md. |
| Neither file | Use AGENTS.md for new shared instructions. If writing instructions is outside the request, report the missing file and continue with skills. |
| `CLAUDE.md -> AGENTS.md`, with a real AGENTS.md | Keep AGENTS.md and remove only the CLAUDE.md symlink. |
| `AGENTS.md -> CLAUDE.md`, with a real CLAUDE.md | Remove the AGENTS.md symlink, then move the real CLAUDE.md to AGENTS.md. |
| Both are real files | Merge their instructions into AGENTS.md, preserving unique content and consolidating duplicates. Remove CLAUDE.md only after verifying the merge. Ask only if contradictory instructions require the user's decision. |
| Broken, cyclic, or unexpected link | Inspect the target before migrating. Preserve readable instruction content in AGENTS.md and remove only the obsolete CLAUDE.md entry, without deleting an external target. If the intended content cannot be recovered or identified, report the unresolved migration. |

Never delete the only real copy or leave AGENTS.md pointing at a removed CLAUDE.md. Do not infer support for user-global or nested instruction files, or `.agents/skills` discovery, from the project-level release note. This workflow targets the repository's top-level instruction files.

## Shared skills

Native AGENTS.md support does not replace skill-directory sharing. Select the canonical skills directory from the skills already on disk, independently of which instruction file exists:

- `.agents/skills/` has the real content: link `.claude/skills -> ../.agents/skills`.
- `.claude/skills/` has the real content: link `.agents/skills -> ../.claude/skills`.
- Neither has content: default to `.agents/skills/` as canonical.
- Both have real content: inspect and reconcile the contents before linking. Ask only when a content conflict or ownership choice needs the user's decision.
- An existing link resolves correctly: preserve its direction. Inspect broken or unexpected links before retargeting; do not create a symlink cycle.

For another convention such as `.codex/skills`, follow the user's stated choice; otherwise establish the intended source before linking.

Once the source and destination are established, set these variables (swap the paths and target for a Claude-first skills directory):

```bash
CANON_SKILLS=.agents/skills
CONSUMER_SKILLS=.claude/skills
CONSUMER_SKILLS_TARGET=../.agents/skills
```

Then link safely:

```bash
# The canonical path must be a real directory or absent.
if [ -L "$CANON_SKILLS" ] || { [ -e "$CANON_SKILLS" ] && [ ! -d "$CANON_SKILLS" ]; }; then
  echo "Inspect the canonical skills path before proceeding: $CANON_SKILLS"
  exit 1
fi

mkdir -p "$CANON_SKILLS" "$(dirname "$CONSUMER_SKILLS")"

if [ -L "$CONSUMER_SKILLS" ]; then
  if [ "$(readlink "$CONSUMER_SKILLS")" != "$CONSUMER_SKILLS_TARGET" ]; then
    echo "Inspect the existing consumer symlink before retargeting: $CONSUMER_SKILLS"
    exit 1
  fi
elif [ -d "$CONSUMER_SKILLS" ]; then
  # rmdir succeeds only for an empty directory, including hidden entries.
  rmdir "$CONSUMER_SKILLS" || exit 1
elif [ -e "$CONSUMER_SKILLS" ]; then
  echo "Consumer path is not a directory: $CONSUMER_SKILLS"
  exit 1
fi

ln -sfn "$CONSUMER_SKILLS_TARGET" "$CONSUMER_SKILLS"
```

## Verify and report

- Confirm AGENTS.md is readable, the migrated instructions are preserved, and CLAUDE.md is absent (including dangling symlinks). If no instructions existed and authoring them was outside the request, report that instead. Do not report a migration as complete while conflicts or broken links remain.
- Confirm the consumer skills link resolves to the canonical directory and exposes its skill files. Re-running should preserve a working setup.
- Report the instruction arrangement, canonical skills directory, and any known compatibility limitations or unresolved conflicts. Do not claim Claude Code loaded AGENTS.md based only on filesystem checks; verify through Claude Code's Project instructions setting when runtime confirmation is needed.

Use relative links so they travel with the repo. Never overwrite unique files or non-empty directories without resolving their contents within the user's authorization. Do not change `.gitignore`, stage, or commit unless requested. The shared instructions and any required symlinks can be committed so collaborators inherit the setup.
