# SurrealQL Types And Values Pack

Use this file when the task is about the data model, literal forms, value semantics, or type-oriented query behavior.

## Core Value Shapes

The docs call out support for:

- arrays
- booleans
- bytes
- datetimes
- durations
- files
- geometries
- idioms (path expressions)
- record IDs
- literals
- numbers
- objects
- ranges
- records / references
- regex
- sets
- strings
- UUIDs
- generic values

## High-Value Types

### Record IDs

SurrealDB uses record IDs like:

```surql
person:one
product:apple
```

They function as first-class references and are central to both record links and graph relations.

### Objects

Objects are first-class and commonly nested.

```surql
{
  created_at: time::now(),
  metadata: {
    source: "import",
    score: 10
  }
}
```

### Arrays / Sets

Used for multi-valued fields and embeddings.

Schema guidance from docs:

- constrain array element type and size when possible
- define individual indices when the shape is fixed and meaningful

### Datetimes / Durations

Core for time-series and lifecycle logic.

Typical usage:

```surql
time::now()
d'2024-09-04T00:32:44.107Z'
7d
90h30m
```

### Strings / Regex

Use string functions and regex matching for validation, parsing, and search-like logic.

### UUIDs / ULIDs / Special IDs

Handled as typed values, not just plain strings.

## Type-Oriented Modeling Notes

### `SCHEMALESS` vs `SCHEMAFULL`

- `SCHEMALESS`: permits flexible structure
- `SCHEMAFULL`: strict field enforcement

Inside strict schemas:

- unexpected fields error out
- nested objects need deliberate shape
- `FLEXIBLE` can loosen nested object fields

### Literal Object Types

Docs note that literal structure can force schemaful object behavior even in otherwise looser contexts.

### Record References

Use direct record references when you want efficient pointer-like links.

Use graph edges when:

- the relationship needs its own properties
- traversal semantics are central

## Value Manipulation Helpers

Relevant families:

- `array::`
- `object::`
- `record::`
- `type::`
- `value::`
- `string::`
- `time::`

## Common Patterns

### Strict user table

```surql
DEFINE TABLE user SCHEMAFULL;
DEFINE FIELD name ON user TYPE string;
DEFINE FIELD metadata ON user TYPE object;
DEFINE FIELD metadata.created_at ON user TYPE datetime;
DEFINE FIELD metadata.age ON user TYPE int;
```

### Array with constrained size/type

```surql
DEFINE FIELD small_bytes ON data TYPE array<int, 8>
  ASSERT $value.all(|$int| $int IN 0..=255);
```

### Fixed-shape vector-like field

```surql
DEFINE FIELD rgb ON colour TYPE <array, 3>;
DEFINE FIELD rgb[0] ON colour TYPE int ASSERT $value IN 0..=255;
DEFINE FIELD rgb[1] ON colour TYPE int ASSERT $value IN 0..=255;
DEFINE FIELD rgb[2] ON colour TYPE int ASSERT $value IN 0..=255;
```

## Practical Advice

- When the question is “what kind of value is this and how should I store/query it?”, start here.
- When the question is more about query syntax, use `surrealql-statements.md` or `surrealql-clauses.md`.
- When the question is about operations on the value, use `09-functions.md`.
