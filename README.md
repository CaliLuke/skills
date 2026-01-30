# Skills

A personal collection of agent skills I've built for Claude Code. These are tools and instructions that I find useful — feel free to browse, copy, or adapt anything that helps you.

## What's Here

Each folder in [`skills/`](./skills) is a self-contained skill with a `SKILL.md` file containing instructions Claude can follow. Some have helper scripts or reference docs.

Browse around and grab what you need.

## Using a Skill

Copy the skill folder into your project's `.claude/skills/` directory, or reference it however works for your setup.

## Skill Format

```yaml
---
name: skill-name
description: When Claude should use this skill.
---
# Skill Name

Instructions for Claude to follow.
```

## Creating Your Own

Use the [`template/`](./template) folder as a starting point.

## License

MIT — do whatever you want with these.
