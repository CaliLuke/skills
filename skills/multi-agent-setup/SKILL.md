---
name: multi-agent-setup
description: Share skills and top-level instructions across coding agents (Claude Code and others) via symlinks. Use for "set up multi-agent", "share skills between agents", "link AGENTS.md to CLAUDE.md", "unify agent configs", or pointing `.agents/skills` and `.claude/skills` at the same place. Auto-detects which side (`.agents/`+`AGENTS.md` or `.claude/`+`CLAUDE.md`) already has content and makes the other a symlink into it; defaults to `.agents/` canonical when starting fresh.
---

# Multi-agent setup

Make the current repo usable by both Claude Code and other agent systems without duplicating skills or top-level instructions.

## Convention

One side is **canonical** (holds the real files), the other is a **consumer** (symlinks pointing in). Either direction is valid:

- `.agents/skills/` + `AGENTS.md` canonical, `.claude/skills` + `CLAUDE.md` as symlinks — preferred for greenfield.
- `.claude/skills/` + `CLAUDE.md` canonical, `.agents/skills` + `AGENTS.md` as symlinks — preferred when the repo is already Claude-first.

The skill picks the canonical side from what's already on disk. It only asks the user when there's a genuine conflict.

## Step 0: Detect canonical direction

Run this first. It sets `$CANON_MD`, `$CONSUMER_MD`, `$CANON_SKILLS_REL`, `$CONSUMER_SKILLS`, and `$CONSUMER_SKILLS_TARGET` (the relative path the consumer symlink should point at).

```bash
agents_md_real=0; claude_md_real=0
[ -f AGENTS.md ] && [ ! -L AGENTS.md ] && agents_md_real=1
[ -f CLAUDE.md ] && [ ! -L CLAUDE.md ] && claude_md_real=1

agents_skills_real=0; claude_skills_real=0
[ -d .agents/skills ] && [ ! -L .agents/skills ] && [ -n "$(ls -A .agents/skills 2>/dev/null)" ] && agents_skills_real=1
[ -d .claude/skills ] && [ ! -L .claude/skills ] && [ -n "$(ls -A .claude/skills 2>/dev/null)" ] && claude_skills_real=1

# Conflict: both sides have real content. Stop and let the user merge.
if { [ $agents_md_real -eq 1 ] && [ $claude_md_real -eq 1 ]; } \
   || { [ $agents_skills_real -eq 1 ] && [ $claude_skills_real -eq 1 ]; }; then
  echo "Both .agents/ and .claude/ have real content. Ask the user which side should be canonical and merge the other in before re-running."
  exit 1
fi

# Pick canonical: whichever side has real content; default to .agents when both empty.
if [ $claude_md_real -eq 1 ] || [ $claude_skills_real -eq 1 ]; then
  CANON_MD=CLAUDE.md;  CONSUMER_MD=AGENTS.md
  CANON_SKILLS=.claude/skills;  CONSUMER_SKILLS=.agents/skills
  CONSUMER_SKILLS_TARGET=../.claude/skills
else
  CANON_MD=AGENTS.md;  CONSUMER_MD=CLAUDE.md
  CANON_SKILLS=.agents/skills;  CONSUMER_SKILLS=.claude/skills
  CONSUMER_SKILLS_TARGET=../.agents/skills
fi

echo "Canonical: $CANON_MD + $CANON_SKILLS"
echo "Consumer:  $CONSUMER_MD -> $CANON_MD, $CONSUMER_SKILLS -> $CONSUMER_SKILLS_TARGET"
```

## Step 1: Link `$CONSUMER_MD` → `$CANON_MD`

Skip this step entirely if `$CANON_MD` doesn't exist yet — let the user create the canonical instructions file first, then re-run.

```bash
if [ ! -f "$CANON_MD" ]; then
  echo "$CANON_MD missing — skipping top-level link. Create it and re-run if you want CLAUDE.md/AGENTS.md unified."
else
  if [ -e "$CONSUMER_MD" ] && [ ! -L "$CONSUMER_MD" ]; then
    echo "$CONSUMER_MD exists as a regular file. Stop and ask the user before overwriting."
    exit 1
  fi
  if [ -L "$CONSUMER_MD" ] && [ "$(readlink "$CONSUMER_MD")" != "$CANON_MD" ]; then
    echo "$CONSUMER_MD is already a symlink to $(readlink "$CONSUMER_MD"). Confirm with the user before retargeting."
    exit 1
  fi
  ln -sfn "$CANON_MD" "$CONSUMER_MD"
fi
```

## Step 2: Link `$CONSUMER_SKILLS` → `$CANON_SKILLS`

```bash
mkdir -p "$CANON_SKILLS" "$(dirname "$CONSUMER_SKILLS")"

# If the consumer path is a non-empty real directory, do not destroy it.
if [ -d "$CONSUMER_SKILLS" ] && [ ! -L "$CONSUMER_SKILLS" ]; then
  if [ -z "$(ls -A "$CONSUMER_SKILLS" 2>/dev/null)" ]; then
    rmdir "$CONSUMER_SKILLS"
  else
    echo "$CONSUMER_SKILLS is a non-empty directory. Stop and ask the user how to merge into $CANON_SKILLS."
    echo "To migrate manually: mv $CONSUMER_SKILLS/* $CANON_SKILLS/ && rmdir $CONSUMER_SKILLS, then re-run."
    exit 1
  fi
fi

# If the consumer is already a symlink pointing somewhere else, confirm first.
if [ -L "$CONSUMER_SKILLS" ] && [ "$(readlink "$CONSUMER_SKILLS")" != "$CONSUMER_SKILLS_TARGET" ]; then
  echo "$CONSUMER_SKILLS is already a symlink to $(readlink "$CONSUMER_SKILLS"). Confirm with the user before retargeting."
  exit 1
fi

ln -sfn "$CONSUMER_SKILLS_TARGET" "$CONSUMER_SKILLS"
```

## Step 3: Verify

```bash
ls -l "$CONSUMER_MD" "$CONSUMER_SKILLS" 2>/dev/null
[ -L "$CONSUMER_MD" ] && readlink "$CONSUMER_MD"
readlink "$CONSUMER_SKILLS"
test -e "$CONSUMER_SKILLS"/. && echo "OK: skills symlink resolves"
[ -L "$CONSUMER_MD" ] && test -e "$CONSUMER_MD" && echo "OK: md symlink resolves"
```

Each `readlink` should print the canonical relative target. The skills `OK` line should always print; the md `OK` line only prints when Step 1 actually created a link.

## Committing the symlinks

The symlinks are tiny and use relative targets, so they travel with the repo. Typical setup is to commit both the top-level md symlink and the skills symlink so collaborators inherit the wiring on checkout — no need to gitignore them. Leave staging to the user.

## Safety rules

- Never overwrite a real consumer-side file or a non-empty consumer-side skills directory without explicit user confirmation — they may contain unique content the user has not migrated yet.
- Use `ln -sfn` (force + no-dereference) so re-running the skill is idempotent on existing symlinks but does not follow into the target directory.
- Use relative link targets so the repo remains portable.
- Do not touch `.gitignore` or commit anything; leave staging decisions to the user.

## When NOT to use

- The repo already has both symlinks resolving correctly — running again is harmless but unnecessary; just report status.
- Both `.agents/` and `.claude/` have real, unique content. Detection will stop; ask the user which side wins and merge the other in before re-running.
- The user uses a different convention (e.g. `.codex/` as canonical). Confirm the canonical directory before linking.
