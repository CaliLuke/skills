# Embedding

## What “Embedding” Means Here

Embedding means running SurrealDB inside your application process instead of talking to a separate server.

The sampled docs explicitly support embedding guidance for:

- Rust
- JavaScript
- Python
- .NET

## Main Embedding Modes

- in-memory: fastest, ephemeral
- file-backed persistent local storage
- browser embedding for JavaScript via WASM/IndexedDB

## Browser Embedding

Docs call out two browser-side choices:

- local browser persistence using IndexedDB
- using the SDK to talk to a remote SurrealDB instance instead of local persistence

IndexedDB note from docs:

- SurrealDB serializes keys and values into `Uint8Array`
- IndexedDB is used as a binary key-value store

## JavaScript Embedding

The JavaScript embedding page points to SDK engine docs rather than carrying full detail itself.

Key split:

- browser: WASM engine, in-memory or IndexedDB persistence
- server: Node.js engine, embedded DB backed by in-memory, RocksDB, or SurrealKV

Heuristic:

- browser app with local-first data -> WASM + IndexedDB
- browser app with central backend data -> remote SDK connection
- Node/Bun/Deno-style server process wanting in-process DB -> Node.js engine

## Python Embedding

Docs explicitly call out:

- `mem://`: in-memory embedded DB
- `file://` or `surrealkv://`: persistent file-based embedded DB

Example shape:

```python
from surrealdb import AsyncSurreal

async with AsyncSurreal("mem://") as db:
    await db.use("test", "test")
    await db.create("person", {"name": "John Doe"})

async with AsyncSurreal("surrealkv://mydb") as db:
    await db.use("test", "test")
    await db.create("company", {"name": "TechStart"})
```

Use cases named in docs:

- desktop apps
- testing
- local development
- edge computing

## Rust Embedding

Docs explicitly call out:

- `Mem` for in-memory
- `RocksDb` or `SurrealKV` for persistent local storage

Example shape:

```rust
use surrealdb::engine::local::Mem;
use surrealdb::Surreal;

let db = Surreal::new::<Mem>(()).await?;
db.use_ns("test").use_db("test").await?;
```

Persistent example:

```rust
use surrealdb::engine::local::RocksDb;

let db = Surreal::new::<RocksDb>("./mydb").await?;
db.use_ns("test").use_db("test").await?;
```

Use cases named in docs:

- desktop apps
- testing
- local development
- edge computing

## Practical Selection Rules

- want a disposable embedded DB for tests -> in-memory embedding
- want local persistence in-process -> RocksDB or SurrealKV style embedded backend
- want browser-local persistence -> JS WASM + IndexedDB
- want shared multi-client state -> do not embed per client; use a server/cloud instance instead

## Default Advice

- prefer embedding for local tooling, tests, desktop, offline/local-first, or edge-style use
- prefer server mode when multiple clients must share authoritative state
- for JS embedding questions, answer via engine choice: WASM for browser, Node engine for server
