# Cloud Tooling And Recipes

## Cloud

Use Cloud docs when the request is about managed instances rather than self-hosting.

Main topics covered in the sampled docs:

- account creation
- organisation creation
- instance creation
- connecting via CLI / HTTP / SDK / Surrealist
- network access
- export and backup
- logs and metrics
- billing and support

## Surrealist

Use Surrealist docs when the request is about GUI workflows.

Main topics:

- install / get started
- local database serving
- querying in the editor
- schema exploration
- GraphQL sending
- access management
- connection templates
- search/shortcuts/settings

## Integrations

Use integration docs when the request is framework-first, not language-SDK-first.

Examples explicitly covered in sampled docs:

- LangChain
- LlamaIndex
- Pydantic AI
- CrewAI
- Agno
- OpenAI embeddings
- Mistral embeddings
- FastEmbed
- Airbyte
- Fivetran
- n8n

## Tutorials

Use tutorials when the user wants a worked example or a starting implementation.

Sampled topics:

- define a schema
- realtime presence via live queries
- semantic search in Rust
- minimal LangChain
- AI chatbot
- Postman over HTTP
- Auth0 / AWS Cognito integration

## Heuristics

- “How do I run/query/manage this visually?” -> Surrealist
- “How do I do this on managed infra?” -> Cloud
- “How do I integrate framework X?” -> Integrations
- “Show me an end-to-end example” -> Tutorials

## Default Advice

- Prefer core SDK docs for exact client API behavior.
- Prefer tutorials for architecture/examples, not for definitive syntax.
- Prefer Cloud docs only when the user is actually on Cloud; otherwise answer from self-hosted/runtime fragments.
