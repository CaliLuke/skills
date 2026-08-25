# Skills Repository

This is a collection of agent skills. Each skill is in `skills/{skill-name}/SKILL.md`.

## Available Skills

- **typeql** - TypeQL language reference for TypeDB 3.8+. Schema definition, CRUD, queries, functions, and pitfalls.
- **type-bridge** - Python ORM for TypeDB. Entities, relations, attributes, CRUD, queries, expressions, schema management.
- **ai-testing** - Guidelines for writing robust tests. Test design, assertions, mocking, debugging strategies.
- **design-docs** - Write design-only architecture, API, framework, or contract documents before implementation planning.
- **execution-plans** - Write requested implementation plans, milestone checklists, execution trackers, and handoff plans from accepted designs.
- **fowler-refactoring** - A practical, task-oriented implementation of Martin Fowler's refactoring approach, used when improving design without changing behavior.
- **go-modern-review** - Review and refactor Go code for Go 1.25 and 1.26 features, new language/stdlib APIs, `go fix` workflows, and newly deprecated or tightened behaviors.
- **surrealdb** - SurrealDB documentation router. Covers SurrealDB core concepts, SurrealQL, schema design, security, deployment, SDKs, SurrealDB Cloud, Surrealist, integrations, and tutorials.
- **ts-quality-gates** - Set up TypeScript 7 quality gates with Oxlint linting and type diagnostics, formatting, duplicates, dead code, coverage, and `prek` orchestration.
- **go-quality-gates** - Set up Go quality gates (build, vet, golangci-lint, goimports, duplicates, dead code, complexity, mod tidy drift, coverage) in any Go repo, wired through `prek` with a `check.sh` orchestrator.
- **py-quality-gates** - Set up Python quality gates (ruff lint/format, type checking, pytest + coverage, complexity, dead code, duplicates, file length) in any Python repo, wired through `prek` with a `check.sh` orchestrator.
- **rust-quality-gates** - Set up Rust quality gates (cargo check/build, clippy, rustfmt, dead code, unused deps, doc build) in any Rust repo, wired through `prek` with a `check.sh` orchestrator.
- **storybook-stories** - Authoring `.stories.ts(x)` / `.mdx`, configuring `.storybook/`, sidebar hierarchy, play functions, and `composeStories`. Scoped to CSF3, React + TS, Storybook v10.3.
- **sqlite-debug-logging** - Token-efficient SQLite-based debug logging for frontend projects: local log server, structured logs, AI-friendly triage that survives page refreshes.
- **log-hunt** - Triage frontend issues by querying the SQLite debug log database produced by `sqlite-debug-logging`.

## Usage

Skills are loaded on-demand based on their description. When a task matches a skill's description, the full SKILL.md is loaded into context.
