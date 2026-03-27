# SurrealQL Clauses Pack

Use this file for query-shaping and execution clauses.

## Main Clauses Called Out In Docs

- `EXPLAIN`
- `FETCH`
- `FROM`
- `GROUP BY`
- `LIMIT`
- `OMIT`
- `ORDER BY`
- `SPLIT`
- `WHERE`
- `WITH`

## Clause Roles

### `FROM`

Defines the source table, record, or value source.

```surql
SELECT * FROM person;
SELECT ->wrote->post.* FROM user:alice;
```

### `WHERE`

Primary filtering clause.

Use for:

- scalar conditions
- function-based checks
- vector search operators
- full-text match predicates
- permission-like record filtering in normal queries

```surql
SELECT * FROM person WHERE age > 18;
SELECT * FROM test WHERE text @1@ 'graph';
SELECT * FROM actor WHERE embedding <|2,40|> $person_embedding;
```

### `FETCH`

Use to pull linked records instead of leaving them as record IDs where appropriate.

Best when:

- record links exist
- caller needs expanded linked data

### `GROUP BY`

Use for aggregation/grouped output.

```surql
SELECT category, count() AS total
FROM product
GROUP BY category;
```

### `ORDER BY`

Use for deterministic ordering.

```surql
SELECT * FROM person ORDER BY age DESC;
```

### `LIMIT`

Use to cap output size.

```surql
SELECT * FROM person ORDER BY age DESC LIMIT 10;
```

### `SPLIT`

Use to split array-like values into separate rows/records in the result stream.

### `OMIT`

Use to exclude fields from shaped output without rebuilding the whole projection.

### `EXPLAIN`

Use to inspect execution planning/behavior when tuning performance or understanding index use.

### `WITH`

Use when query structure benefits from common subquery shaping or related advanced composition.

## Clause Heuristics

- need filter -> `WHERE`
- need top-N -> `ORDER BY` + `LIMIT`
- need aggregate -> `GROUP BY`
- need expanded references -> `FETCH`
- need trimmed output -> `OMIT`
- need execution diagnostics -> `EXPLAIN`

## Common Patterns

### Filter, sort, cap

```surql
SELECT name, price
FROM product
WHERE category = "fruit"
ORDER BY price
LIMIT 10;
```

### Full-text with score/highlight

```surql
SELECT id, search::score(1) AS score, search::highlight('<b>', '</b>', 1) AS title
FROM book
WHERE title @1@ 'rust web'
ORDER BY score DESC
LIMIT 10;
```

### Vector search with distance reuse

```surql
SELECT id, vector::distance::knn() AS distance
FROM actor
WHERE embedding <|2,40|> $person_embedding
ORDER BY distance;
```

### Grouping

```surql
SELECT status, count() AS total
FROM task
GROUP BY status;
```

## Practical Advice

- Prefer clause composition over overly clever nested logic when the query can stay readable.
- When mixing search/vector ranking with ordering, be explicit about score/distance handling.
- Use `EXPLAIN` when performance/index behavior matters.
