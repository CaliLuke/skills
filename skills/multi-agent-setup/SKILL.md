---
name: multi-agent-setup
description: Share skills and top-level instructions across coding agents (Claude Code and others) via symlinks. Use for "set up multi-agent", "share skills between agents", "link AGENTS.md to CLAUDE.md", "unify agent configs", or pointing `.agents/skills` and `.claude/skills` at the same place. Treats `.agents/` as canonical, `.claude/` as consumer.
---

# Multi-agent setup

Make the current repo usable by both Claude Code and other agent systems without duplicating skills or top-level instructions.

## Convention

- `.agents/skills/` is the canonical skills directory. All shared skills live here.
- `AGENTS.md` is the canonical top-level instructions file.
- `.claude/skills/` and `CLAUDE.md` are symlinks into the canonical paths.

## Steps

Run from the repository root. Use relative symlink targets so the links survive the repo being moved.

### 1. Link `CLAUDE.md` → `AGENTS.md`

```bash
# Preconditions: AGENTS.md exists. CLAUDE.md must not be a regular file with unique content.
test -f AGENTS.md || { echo "AGENTS.md missing — create it first"; exit 1; }

if [ -e CLAUDE.md ] && [ ! -L CLAUDE.md ]; then
  echo "CLAUDE.md exists as a regular file. Stop and ask the user before overwriting."
  exit 1
fi

if [ -L CLAUDE.md ] && [ "$(readlink CLAUDE.md)" != "AGENTS.md" ]; then
  echo "CLAUDE.md is already a symlink to $(readlink CLAUDE.md). Confirm with the user before retargeting."
  exit 1
fi

ln -sfn AGENTS.md CLAUDE.md
```

### 2. Link `.claude/skills` → `.agents/skills`

```bash
mkdir -p .agents/skills .claude

# If .claude/skills already exists as a real directory, do not destroy it.
if [ -d .claude/skills ] && [ ! -L .claude/skills ]; then
  if [ -z "$(ls -A .claude/skills 2>/dev/null)" ]; then
    rmdir .claude/skills
  else
    echo ".claude/skills is a non-empty directory. Stop and ask the user how to merge into .agents/skills."
    echo "To migrate manually: mv .claude/skills/* .agents/skills/ && rmdir .claude/skills, then re-run."
    exit 1
  fi
fi

# If .claude/skills is already a symlink pointing somewhere other than the canonical target, confirm first.
if [ -L .claude/skills ] && [ "$(readlink .claude/skills)" != "../.agents/skills" ]; then
  echo ".claude/skills is already a symlink to $(readlink .claude/skills). Confirm with the user before retargeting."
  exit 1
fi

ln -sfn ../.agents/skills .claude/skills
```

### 3. Verify

```bash
ls -l CLAUDE.md .claude/skills
readlink CLAUDE.md
readlink .claude/skills
test -e CLAUDE.md && test -e .claude/skills/. && echo "OK: both symlinks resolve"
```

Both `readlink` calls should print the canonical relative targets, and the final line should print `OK`.

## Committing the symlinks

The two symlinks are tiny and use relative targets, so they travel with the repo. Typical setup is to commit both `CLAUDE.md` and `.claude/skills` so collaborators inherit the wiring on checkout — no need to gitignore them. Leave staging to the user.

## Safety rules

- Never overwrite a real `CLAUDE.md` file or a non-empty `.claude/skills/` directory without explicit user confirmation — they may contain unique content the user has not migrated yet.
- Use `ln -sfn` (force + no-dereference) so re-running the skill is idempotent on existing symlinks but does not follow into the target directory.
- Use relative link targets (`AGENTS.md`, `../.agents/skills`) so the repo remains portable.
- Do not touch `.gitignore` or commit anything; leave staging decisions to the user.

## When NOT to use

- The repo already has both symlinks resolving correctly — running again is harmless but unnecessary; just report status.
- The user uses a different convention (e.g. `.codex/` as canonical). Confirm the canonical directory before linking.
