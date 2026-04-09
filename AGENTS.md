# Skills Repository

This is a collection of agent skills. Each skill is in `skills/{skill-name}/SKILL.md`.

## Available Skills

- **typeql** - TypeQL language reference for TypeDB 3.8+. Schema definition, CRUD, queries, functions, and pitfalls.
- **type-bridge** - Python ORM for TypeDB. Entities, relations, attributes, CRUD, queries, expressions, schema management.
- **ai-testing** - Guidelines for writing robust tests. Test design, assertions, mocking, debugging strategies.
- **fowler-refactoring** - A practical, task-oriented implementation of Martin Fowler's refactoring approach, used when improving design without changing behavior.
- **go-1-25-review** - Review and refactor Go code to leverage Go 1.25 features, new standard-library APIs, and new tooling guidance.
- **go-1-26-review** - Review and refactor Go code to leverage Go 1.26 features, new language and standard-library APIs, modern `go fix` workflows, and newly deprecated or tightened behaviors.
- **surrealdb** - SurrealDB documentation router. Covers SurrealDB core concepts, SurrealQL, schema design, security, deployment, SDKs, SurrealDB Cloud, Surrealist, integrations, and tutorials.

## Usage

Skills are loaded on-demand based on their description. When a task matches a skill's description, the full SKILL.md is loaded into context.
