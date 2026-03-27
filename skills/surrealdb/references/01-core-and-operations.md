# Core And Operations

## Product Facts

- SurrealDB is a Rust multi-model database.
- Primary data models emphasized in the docs: document, graph, relational-style, time-series, geospatial, vector, full-text/search, key-value.
- Primary query language: SurrealQL.
- Other access modes called out in docs: GraphQL, HTTP, RPC, SDKs.
- It can run as:
  - embedded / in-process
  - single-node server
  - distributed cluster
  - browser/WASM in some SDK paths

## Mental Model

- `namespace`: top-level tenant / org boundary
- `database`: lives inside a namespace
- `table`: collection of records
- `record`: row/document
- `field`: attribute path

This hierarchy matters for auth and permissions.

## Storage / Runtime Choices

- In-memory: simple local/dev and ephemeral use
- RocksDB: persisted local/single-node default choice
- SurrealKV: persisted storage option, marked beta in sampled docs
- TiKV: distributed deployments

## Querying Modes

- SurrealQL: native path
- GraphQL: supported
- HTTP `/sql`: stateless query path
- WebSocket / RPC: stateful low-latency path
- SDKs: language-native wrappers around query and CRUD flows

## CLI Surface

The docs call out these commands:

- `surreal start`
- `surreal import`
- `surreal export`
- `surreal sql`
- `surreal isready`
- `surreal validate`
- `surreal version`
- `surreal upgrade`
- `surreal module`

## CLI Quick Reference

- `surreal start`: run a server in memory, on disk, or in distributed mode
- `surreal sql`: open a REPL or pipe SurrealQL to a running instance
- `surreal import`: import SurrealQL into a local or remote database
- `surreal export`: export a dataset as SurrealQL
- `surreal isready`: readiness check for scripts/containers
- `surreal validate`: validate SurrealQL input
- `surreal version`: print CLI/server version information
- `surreal upgrade`: upgrade to a newer SurrealDB version
- `surreal module`: build, inspect, and run Surrealism module files

## `surreal start` Essentials

Important options surfaced in the docs:

- `-b`, `--bind`: listen address
- `-u`, `--user`: initial/master username
- `-p`, `--pass`: initial/master password
- `-l`, `--log`: log level
- `--import-file`: import a `.surql` file on startup
- `--unauthenticated`: allow unauthenticated access
- `--no-identification-headers`: suppress version/name headers
- `--temporary-directory`: temp file directory
- `--allow-experimental`: enable experimental capabilities

Storage/path behavior called out in docs:

- if no positional storage argument is given, startup defaults to in-memory storage
- prefer `rocksdb:` or `surrealkv:` over deprecated `file://`
- short forms like `rocksdb:/path` can become absolute paths unexpectedly; be careful with slash count

Safe default:

```bash
surreal start --user root --pass secret
```

## `surreal sql` Essentials

Important options surfaced in the docs:

- `-e`, `--endpoint`, `--conn`: server URL
- `-u`, `--user`: username
- `-p`, `--pass`: password
- `--ns`: namespace
- `--db`: database
- `--auth-level`: `root`, `namespace`, or `database`
- `-t`, `--token`: JWT auth instead of username/password
- `--pretty`: pretty-print output
- `--json`: emit JSON
- `--multi`: newline behavior when omitting semicolons

Behavior worth remembering:

- docs note that as of SurrealDB `3.0`, `surreal sql` defaults to namespace `main` and database `main`
- if using `--auth-level namespace`, `--namespace` is required
- if using `--auth-level database`, both `--namespace` and `--database` are required
- `--token` cannot be combined with username/password/auth-level flags

Quick examples:

```bash
surreal sql --username root --password secret --pretty
surreal sql --namespace ns --database db --username root --password secret --pretty
surreal sql --endpoint http://localhost:8000 --namespace test --database test --auth-level database --username user --password pass
```

## CLI Environment Variables

The docs note that many CLI flags also have corresponding `SURREAL_*` environment variables. Example: database selection can be configured through `SURREAL_DATABASE`.

For experimental features in CLI usage, docs call out `SURREAL_CAPS_ALLOW_EXPERIMENTAL`.

## `surreal module` Essentials

This is the CLI surface for Surrealism extensions/plugins.

High-value commands called out in the docs:

- `surreal module build --out demo.surli /path/to/rust/project`
- `surreal module sig <function> demo.surli`
- `surreal module run <function> --arg <value> demo.surli`

Use `06-extensions.md` for the full plugin flow.

## Practical Startup Commands

Minimal authenticated server:

```bash
surreal start --user root --pass secret
```

Docker, ephemeral:

```bash
docker run --rm --pull always -p 8000:8000 surrealdb/surrealdb:latest start
```

Docker, persisted RocksDB:

```bash
mkdir mydata
docker run --rm --pull always -p 8000:8000 --user $(id -u) \
  -v $(pwd)/mydata:/mydata \
  surrealdb/surrealdb:latest \
  start rocksdb:/mydata/mydatabase.db
```

## Operational Defaults

- Prefer authenticated startup.
- Prefer explicit namespace/database selection in clients.
- Prefer parameter binding rather than building query strings.
- Prefer capability allowlists in production.
- Prefer current docs/examples over old blog snippets.

## Useful Defaults For Answers

- “Start locally”: `surreal start --user root --pass secret`
- “Persist data”: choose RocksDB or another persisted engine explicitly
- “Need stateful client”: use WS/RPC or an SDK with long-lived connection support
- “Need quick manual query work”: Surrealist or `surreal sql`

## Intact Reference Guides Worth Checking

- `references/reference-guides/observability.mdx`
- `references/reference-guides/performance-best-practices.mdx`
- `references/reference-guides/real-time-best-practices.mdx`
