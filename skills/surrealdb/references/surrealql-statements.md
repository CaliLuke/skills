# SurrealQL Statements Pack

Use this file when the task needs a denser statement-level reference than `02-surrealql.md`.

## Statement Families

### Resource / schema / admin

- `DEFINE`
- `ALTER`
- `REMOVE`
- `REBUILD`
- `ACCESS`
- `USE`
- `INFO`
- `SHOW`

### Control flow / transaction

- `BEGIN`
- `COMMIT`
- `CANCEL`
- `FOR`
- `CONTINUE`
- `BREAK`
- `IF ELSE`
- `SLEEP`
- `RETURN`
- `THROW`

### Query / record lifecycle

- `CREATE`
- `INSERT`
- `RELATE`
- `UPDATE`
- `UPSERT`
- `SELECT`
- `LIVE SELECT`
- `DELETE`
- `KILL`
- `LET`

## Core Resource Statements

### `DEFINE`

Used for namespaces, databases, users, tables, fields, params, functions, indexes, analyzers, sequences, access methods, events, and modules/buckets in related sections.

High-value shapes:

```surql
DEFINE NAMESPACE app;
DEFINE DATABASE prod;
DEFINE USER app_user ON DATABASE PASSWORD "..." ROLES EDITOR;

DEFINE TABLE person SCHEMAFULL
  PERMISSIONS
    FOR select, update, delete WHERE id = $auth.id;

DEFINE FIELD email ON TABLE person
  TYPE string
  ASSERT string::is_email($value);

DEFINE INDEX email_idx ON TABLE person FIELDS email UNIQUE;
DEFINE PARAM $MONTHS VALUE ["Jan", "Feb", "Mar"];
DEFINE FUNCTION fn::normalize($input: string) { RETURN string::lowercase($input); };
```

### `ALTER`

Used for changing certain defined resources. In practice, docs note that `DEFINE ... OVERWRITE` is often the more common route.

### `REMOVE`

Used to remove resources such as tables, indexes, events, users, and more.

### `REBUILD`

Used to rebuild indexes and related resources.

### `ACCESS`

Used to manage access grants after access methods have been defined.

### `USE`

Changes current namespace/database context.

```surql
USE NAMESPACE app;
USE DATABASE prod;
```

### `INFO`

Use to inspect current definitions and metadata.

```surql
INFO FOR ROOT;
INFO FOR NAMESPACE;
INFO FOR DATABASE;
INFO FOR TABLE person;
```

### `SHOW`

Use to inspect changefeeds for a table or database.

## Control Flow / Transaction Statements

### `BEGIN` / `COMMIT` / `CANCEL`

Use when multiple statements must behave as a manual transaction.

```surql
BEGIN;
LET $id = person:one;
UPDATE $id SET active = true;
COMMIT;
```

Use `CANCEL` instead of `COMMIT` to abort.

### `FOR`

Loop over values or query output.

### `CONTINUE` / `BREAK`

Loop control.

### `IF ELSE`

Branching inside expressions or statement blocks.

### `RETURN`

Use to emit a final value from a block/function/transaction or for readability in simple expressions.

### `THROW`

Use to abort execution with a custom error, especially inside `ASSERT` logic.

## Record / Query Statements

### `CREATE`

- create one or more records
- can create a specific record id or random ids
- in non-STRICT behavior, may define missing resources implicitly for some write paths

```surql
CREATE person CONTENT { name: "Tobie" };
CREATE person:one CONTENT { name: "Tobie" };
```

### `INSERT`

- create one or more records or graph edges
- useful for batch-style insertion

```surql
INSERT INTO person [
  { name: "Tobie" },
  { name: "Jaime" }
];
```

### `RELATE`

- create a graph edge between two records
- edge is a real table and can store properties

```surql
RELATE person:one->likes->thing:two CONTENT { strength: 10 };
RELATE person:brian->order->product:crystal_cave SET quantity = 2;
```

### `UPDATE`

- mutate matching records

```surql
UPDATE person SET active = true WHERE last_seen > time::now() - 7d;
```

### `UPSERT`

- update existing or create missing
- use when that semantics is explicit, not just as a shortcut

```surql
UPSERT person:one CONTENT { name: "Tobie" };
```

### `SELECT`

- retrieve records or ad-hoc values
- supports graph traversal, clauses, functions, and shaped output

```surql
SELECT * FROM person WHERE age > 18 ORDER BY age LIMIT 10;
SELECT ->wrote->post.* AS posts FROM user:alice;
```

### `LIVE SELECT`

- stream changes from a table

### `DELETE`

- delete records

```surql
DELETE person WHERE active = false;
```

### `KILL`

- cancel a `LIVE SELECT`

### `LET`

- bind a reusable parameter/value in the current script

```surql
LET $id = person:one;
LET $query_vec = [0.1, 0.2, 0.3];
```

## Statement Choice Heuristics

- need relationship row with metadata -> `RELATE`
- need simple pointer/reference -> record link, not necessarily `RELATE`
- need “create if absent else update” -> `UPSERT`
- need multi-step atomic flow -> `BEGIN`/`COMMIT`
- need reusable intermediate value -> `LET`
- need schema/resource config -> `DEFINE`

## Version-Sensitive Note

The sampled docs note that current versions return errors for many undefined-resource reads/writes where older versions sometimes returned empty arrays. Avoid assuming old behavior.
