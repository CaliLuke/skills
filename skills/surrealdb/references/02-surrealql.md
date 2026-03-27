# SurrealQL

## Statement Taxonomy

### Resource / schema

- `DEFINE`
- `ALTER`
- `REMOVE`
- `REBUILD`
- `ACCESS`
- `USE`
- `INFO`
- `SHOW`

### Control flow / transactions

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

### Query / record operations

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

## High-Value Syntax Skeletons

### DEFINE

```surql
DEFINE NAMESPACE name;
DEFINE DATABASE name;
DEFINE USER user ON ROOT|NAMESPACE|DATABASE PASSWORD "..." ROLES OWNER|EDITOR|VIEWER;
DEFINE TABLE table_name [SCHEMAFULL|SCHEMALESS] [PERMISSIONS ...];
DEFINE FIELD field_name ON TABLE table_name [TYPE ...] [VALUE ...] [ASSERT ...] [PERMISSIONS ...];
DEFINE INDEX index_name ON TABLE table_name FIELDS field1, field2 [UNIQUE];
DEFINE PARAM $name VALUE ...;
DEFINE FUNCTION fn::name($arg: type) { ... };
DEFINE ACCESS access_name ON DATABASE TYPE RECORD
  SIGNIN (...)
  SIGNUP (...)
  [DURATION FOR TOKEN ... FOR SESSION ...];
```

### CRUD / graph

```surql
CREATE person CONTENT { name: "Tobie" };
INSERT INTO person [{ name: "Tobie" }, { name: "Jaime" }];
RELATE person:one->likes->thing:two CONTENT { strength: 10 };
SELECT * FROM person WHERE age > 18 ORDER BY age LIMIT 10;
UPDATE person SET active = true WHERE last_seen > time::now() - 7d;
UPSERT person:one CONTENT { name: "Tobie" };
DELETE person WHERE active = false;
```

### Manual transaction

```surql
BEGIN;
LET $id = person:one;
UPDATE $id SET active = true;
COMMIT;
```

## Data Model Highlights

- Records have record IDs like `person:one`.
- Objects and arrays are first-class.
- Record references / graph links are central, not bolted on.
- The docs cover arrays, objects, records, IDs, references, ranges, UUIDs, datetimes, bytes, files, literals, idioms.

## Query Shaping Clauses

- `WHERE`
- `FETCH`
- `GROUP BY`
- `ORDER BY`
- `LIMIT`
- `SPLIT`
- `OMIT`
- `EXPLAIN`
- `WITH`

## Practical Guidance

- Use `RELATE` for graph edges.
- Use `UPSERT` when “update if exists else create” is the real intent.
- Use `LET` for reusable values inside larger scripts.
- Use `RETURN` inside blocks/functions/transactions when the return value matters.
- Use SDK variable binding instead of interpolating untrusted strings.

## Version-Sensitive Gotcha

Sampled docs note that from `3.0.0` onward many statements return an error when a resource is undefined, where older versions sometimes returned empty arrays. Do not assume old empty-array behavior on current versions.

## Common Modeling Statements

```surql
DEFINE TABLE user SCHEMAFULL
  PERMISSIONS
    FOR select, update, delete WHERE id = $auth.id;

DEFINE FIELD email ON user TYPE string ASSERT string::is_email($value);
DEFINE INDEX email ON user FIELDS email UNIQUE;
```

## Default Advice

- Reach for SurrealQL first when the question is about exact behavior or expressive querying.
- Reach for SDK helpers when the question is mostly connection lifecycle or type wrappers.
