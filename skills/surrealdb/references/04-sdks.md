# SDKs

Use current SDK guidance by default. Treat `*-1x` docs as legacy.

## Shared SDK Pattern

1. create client
2. connect
3. select namespace/database
4. authenticate
5. query or CRUD
6. close or keep alive depending on transport

## JavaScript

Good for Node, browser, and framework integrations.

Core docs themes:

- `connect()`
- `signin()`, `signup()`, `authenticate()`
- typed tables / record IDs
- query builder style CRUD
- bound queries and `surql`
- Node and WASM engines
- sessions, transactions, live queries, diagnostics

Quick pattern:

```ts
import Surreal, { Table, RecordId } from 'surrealdb';

const db = new Surreal();
await db.connect('ws://localhost:8000', {
  namespace: 'company_name',
  database: 'project_name',
  authentication: { username: 'root', password: 'root' },
});

const users = new Table('users');
await db.create(users).content({ name: 'John' });
await db.select(users);
await db.query('SELECT * FROM users WHERE age > $age', { age: 18 });
```

## Python

Good for sync/async app code and embedded modes.

Docs themes:

- `Surreal` and `AsyncSurreal`
- WS/HTTP/embedded protocols
- `connect()`, `use()`, `signin()`
- sync and async examples
- live queries, transactions, value wrappers

Quick pattern:

```python
from surrealdb import Surreal

db = Surreal("ws://localhost:8000")
db.connect()
db.use("company_name", "project_name")
db.signin({"username": "root", "password": "root"})
db.create("users", {"name": "John"})
db.query("SELECT * FROM users WHERE age > $age", {"age": 18})
db.close()
```

## Rust

Good for strongly typed backend code and embedded use.

Docs themes:

- feature flags for engines/protocols
- `Surreal::new`
- `signin`
- `use_ns().use_db()`
- typed structs / serialization
- transactions, concurrency, live queries, vector work

Quick pattern:

```rust
use surrealdb::engine::remote::ws::Ws;
use surrealdb::opt::auth::Root;
use surrealdb::Surreal;

let db = Surreal::new::<Ws>("127.0.0.1:8000").await?;
db.signin(Root {
    username: "root".into(),
    password: "secret".into(),
}).await?;
db.use_ns("test").use_db("test").await?;
db.query("SELECT * FROM person WHERE age > $age")
    .bind(("age", 18))
    .await?;
```

## Go / Java / .NET / PHP

Use the same mental model:

- connect
- authenticate
- select namespace/database if separate
- query or CRUD
- use language-specific value wrappers/types as needed

The docs for these SDKs are organized around:

- installation / start
- concepts / core
- methods / api
- value types / errors

## SDK Selection Heuristics

- Browser/web app -> JavaScript
- Python service / scripts / data workflows -> Python
- Rust backend / embedded / typed performance-sensitive code -> Rust
- Existing ecosystem lock-in -> matching language SDK

## Default Advice

- Use SDK variable binding rather than hand-built query strings.
- Prefer current SDK docs over older code examples.
- If the question is mostly SurrealQL semantics, answer from `02-surrealql.md` first and add SDK syntax second.
