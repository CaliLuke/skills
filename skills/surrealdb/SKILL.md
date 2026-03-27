---
name: surrealdb
description: Work with SurrealDB, SurrealQL, schema design, auth, permissions, deployment, SDKs, SurrealDB Cloud, Surrealist, and integrations. Use when implementing or debugging SurrealDB-backed systems, writing SurrealQL, modeling data, configuring security, or answering product and SDK questions.
---

# SurrealDB

Use the local reference fragments first. They are meant to answer most requests without re-reading upstream docs.

## Load Order

1. Pick the smallest relevant fragment set from `references/`.
2. Answer from one fragment when the question is narrow.
3. Combine fragments when the question spans multiple areas, such as SDK plus auth, embedding plus storage, or modeling plus security.
4. Only escalate beyond the fragments for exact edge syntax, version disputes, or missing coverage.

## Fragment Selection

- `00-navigation.md`: choose the right fragment fast; map product areas; last-resort upstream path rules
- `01-core-and-operations.md`: product model, storage/runtime choices, CLI, install/run/deploy defaults
- `02-surrealql.md`: statements, clauses, data model, CRUD, transactions, common syntax and gotchas
- `surrealql-statements.md`: denser statement reference for schema/resource/control/query statements
- `surrealql-clauses.md`: denser clause reference for query shaping and execution
- `surrealql-types-and-values.md`: denser value/type/data-model reference
- `09-functions.md`: SurrealQL function families, what each family is for, and high-value examples
- `03-modeling-security.md`: schema strategy, auth, permissions, capabilities, security-safe patterns
- `04-sdks.md`: current SDK choices and the common connect/auth/query flow by language
- `05-cloud-tooling-and-recipes.md`: Cloud, Surrealist, integrations, tutorials, and when to use each
- `06-extensions.md`: Surrealism plugins/extensions, module build/load flow, and experimental gating
- `07-embedding.md`: embedding SurrealDB in Rust, Python, JavaScript/browser/server, and storage/runtime choices
- `08-data-models.md`: document, graph, vector, full-text, time-series, and geospatial modeling choices
- `references/reference-guides/`: upstream reference guides kept intact for observability, performance, real-time, sample schemas, and schema best practices

## Working Rules

- Prefer current SDK guidance over `1.x` unless the user explicitly has legacy code.
- Prefer safe patterns over shortest patterns:
  - parameter binding over string interpolation
  - password hashing over storing passwords
  - deny-by-default capabilities
  - explicit permissions for record users
- Do not browse first if the fragment already covers the answer.
- If exact upstream wording or a niche page is required, use `00-navigation.md` to derive the likely upstream file path or URL.
- For best-practice questions, prefer the intact files in `references/reference-guides/` over paraphrasing from memory.
