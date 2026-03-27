# Navigation

## Decision Table

- “What is SurrealDB / how do I run it / what storage or deployment mode should I use?” -> `01-core-and-operations.md`
- “How do I write or debug this query?” -> `02-surrealql.md`
- “I need a denser SurrealQL reference” -> `surrealql-statements.md`, `surrealql-clauses.md`, `surrealql-types-and-values.md`, `09-functions.md`
- “How should I model this / set up auth / permissions / security?” -> `03-modeling-security.md`
- “How do I do this in JS / Python / Rust / Go / Java / .NET / PHP?” -> `04-sdks.md`
- “How do Cloud / Surrealist / LangChain / OpenAI / tutorials fit in?” -> `05-cloud-tooling-and-recipes.md`
- “How do extensions/plugins/Surrealism modules work?” -> `06-extensions.md`
- “How do I run SurrealDB embedded/in-process/in-browser?” -> `07-embedding.md`
- “Which data model should I use: document, graph, vector, search, time-series, geospatial?” -> `08-data-models.md`
- “Which SurrealQL function should I use?” -> `09-functions.md`
- “What are the recommended best practices for schema, performance, real-time, observability, or sample schemas?” -> `references/reference-guides/`

## Product Map

- Core DB docs: `doc-surrealdb`
- Query language: `doc-surrealql`
- Current SDKs: `doc-sdk-javascript`, `doc-sdk-python`, `doc-sdk-rust`, `doc-sdk-golang`, `doc-sdk-java`, `doc-sdk-dotnet`, `doc-sdk-php`
- Legacy SDKs: `doc-sdk-*-1x`
- Cloud: `doc-cloud`
- GUI: `doc-surrealist`
- Integrations: `doc-integrations`
- Tutorials: `doc-tutorials`

## What The Fragments Already Cover

- Core product positioning and architecture
- Runtime modes and storage engines
- CLI surface and common startup commands
- SurrealQL statement taxonomy
- Dense SurrealQL pack: statements, clauses, types/values, functions
- Common schema, auth, permissions, and security patterns
- Current SDK quickstart flows
- Cloud / Surrealist / integrations / tutorial routing
- Extensions / Surrealism plugin workflow
- Embedding in Rust, Python, JS/browser/server
- Data model selection and tradeoffs
- Function families and lookup surface
- Intact reference guides from upstream

## Escalation Rule

Escalate only for one of these:

- exact statement syntax not already summarized
- niche SDK method behavior
- version-specific discrepancy
- unusual integration/tutorial detail

Before escalating beyond the skill, check `references/reference-guides/` if the request is about best practices or operational guidance.

## Last-Resort Upstream Path Rules

Use only if a fragment is insufficient.

- `/docs/surrealdb/...` maps to `src/content/doc-surrealdb/...`
- `/docs/surrealql/...` maps to `src/content/doc-surrealql/...`
- `/docs/sdk/javascript/...` maps to `src/content/doc-sdk-javascript/...`
- `/docs/sdk/python/...` maps to `src/content/doc-sdk-python/...`
- `/docs/sdk/rust/...` maps to `src/content/doc-sdk-rust/...`

Raw GitHub rule of thumb:

- section page: `.../path.mdx`
- landing page: `.../path/index.mdx`

Repo: `https://github.com/surrealdb/docs.surrealdb.com`
