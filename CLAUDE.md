# Skills Repository

This is a collection of agent skills. Each skill is in `skills/{skill-name}/SKILL.md`.

## Available Skills

- **typeql** - TypeQL language reference for TypeDB 3.8+. Schema definition, CRUD, queries, functions, and pitfalls.
- **type-bridge** - Python ORM for TypeDB. Entities, relations, attributes, CRUD, queries, expressions, schema management.
- **ai-testing** - Guidelines for writing robust tests. Test design, assertions, mocking, debugging strategies.

## Usage

Skills are loaded on-demand based on their description. When a task matches a skill's description, the full SKILL.md is loaded into context.
