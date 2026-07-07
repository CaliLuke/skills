# Skills

A personal collection of agent skills I've built for Claude Code. These are tools and instructions that I find useful — feel free to browse, copy, or adapt anything that helps you.

## What's Here

Each folder in [`skills/`](./skills) is a self-contained skill with a `SKILL.md` file containing instructions Claude can follow. Some have helper scripts or reference docs.

Current skills include:

- `design-docs` - Write architecture, API, framework, or contract design documents before implementation planning.
- `execution-plans` - Write requested implementation plans, milestone checklists, execution trackers, and handoff plans from accepted designs.
- `ai-testing` - Guidelines for writing robust tests, including test design, assertions, mocking, and debugging strategies.
- `fowler-refactoring` - Practical refactoring guidance based on Martin Fowler's approach for improving design without changing behavior.
- `frontend-organization` - Refactor frontend structure so route ownership, screen ownership, feature boundaries, and public APIs are easier to navigate.
- `functional-ui-refactor` - Refactor UI architecture by simplifying over-specialized components, separating data loading from rendering, and promoting real primitives into shared UI.
- `go-modern-review` - Review and modernize Go code using Go 1.25 and 1.26 features, APIs, `go fix` workflows, and newer behavior changes.
- `surrealdb` - Documentation router for SurrealDB concepts, SurrealQL, schema design, deployment, SDKs, and tooling.
- `type-bridge` - Reference for the TypeDB Python ORM covering schema management, CRUD, queries, and expressions.
- `typedb` - TypeQL reference for TypeDB 3.8+, including schema definition, queries, functions, and common pitfalls.

Browse around and grab what you need.

## Installation

```bash
npx skills add CaliLuke/skills
```

Or copy a skill folder into your project's `.claude/skills/` directory.

## License

MIT — do whatever you want with these.
