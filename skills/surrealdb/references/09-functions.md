# Functions

## Function Categories

The docs split SurrealQL functions into:

- database functions
- embedded JavaScript functions
- SurrealML functions

For most day-to-day work, database functions are the main surface.

## Database Function Families

The sampled docs list these database families:

- `api`
- `array`
- `bytes`
- `count`
- `crypto`
- `duration`
- `encoding`
- `file`
- `geo`
- `http`
- `math`
- `meta` (docs note deprecation in favor of `record` functions)
- `not`
- `object`
- `parse`
- `rand`
- `record`
- `search`
- `sequence`
- `session`
- `set`
- `sleep`
- `string`
- `time`
- `type`
- `value`
- `vector`

## High-Value Families

### `string::`

Use for text normalization, validation, splitting/joining, regex checks, HTML safety, semver, and string distances.

Notable functions surfaced in sampled docs:

- `string::contains`
- `string::ends_with`
- `string::join`
- `string::len`
- `string::lowercase`
- `string::matches`
- `string::replace`
- `string::slice`
- `string::slug`
- `string::split`
- `string::starts_with`
- `string::trim`
- `string::uppercase`
- `string::words`
- `string::html::encode`
- `string::html::sanitize`
- `string::is_email`
- `string::is_url`
- `string::is_domain`
- `string::is_record`

Useful examples:

```surql
RETURN string::slug("Hello SurrealDB");
RETURN string::is_email("user@example.com");
RETURN string::html::encode("<script>alert(1)</script>");
```

### `time::`

Use for current time, extraction, formatting, rounding, grouping, unix conversions, and timestamp construction.

Notable functions surfaced in sampled docs:

- `time::now`
- `time::format`
- `time::group`
- `time::ceil`
- `time::floor`
- `time::round`
- `time::year`
- `time::month`
- `time::day`
- `time::hour`
- `time::minute`
- `time::second`
- `time::unix`
- `time::from_secs`
- `time::from_millis`
- `time::from_nanos`

Useful examples:

```surql
RETURN time::now();
RETURN time::format(time::now(), "%Y-%m-%d");
RETURN time::hour();
```

### `crypto::`

Use for password hashing and secure auth flows first; use raw hashes only when the task genuinely needs a general hash.

Hash functions surfaced:

- `crypto::blake3`
- `crypto::joaat`
- `crypto::md5`
- `crypto::sha1`
- `crypto::sha256`
- `crypto::sha512`

Password-hash helpers surfaced:

- `crypto::argon2::generate`
- `crypto::argon2::compare`
- `crypto::bcrypt::generate`
- `crypto::bcrypt::compare`
- `crypto::pbkdf2::generate`
- `crypto::pbkdf2::compare`
- `crypto::scrypt::generate`
- `crypto::scrypt::compare`

Security rule:

- prefer Argon2/Bcrypt/PBKDF2/Scrypt for passwords
- do not use MD5/SHA* for password storage

Useful examples:

```surql
RETURN crypto::argon2::generate("MyPaSSw0RD");
RETURN crypto::argon2::compare(password, $password);
RETURN crypto::sha256("payload");
```

### `vector::`

Use for embedding math, distance, similarity, and vector search helpers.

Operations surfaced:

- `vector::add`
- `vector::subtract`
- `vector::multiply`
- `vector::divide`
- `vector::dot`
- `vector::cross`
- `vector::magnitude`
- `vector::normalize`
- `vector::project`
- `vector::scale`
- `vector::angle`

Distance/similarity surfaced:

- `vector::distance::euclidean`
- `vector::distance::manhattan`
- `vector::distance::chebyshev`
- `vector::distance::minkowski`
- `vector::distance::hamming`
- `vector::distance::knn`
- `vector::similarity::cosine`
- `vector::similarity::jaccard`
- `vector::similarity::pearson`

Useful examples:

```surql
RETURN vector::dot([1,2,3], [1,2,3]);
RETURN vector::similarity::cosine($a, $b);
SELECT id, vector::distance::knn() AS distance
FROM actor
WHERE embedding <|2,40|> $person_embedding
ORDER BY distance;
```

### `http::`

Use for outbound HTTP calls from SurrealQL, but only when capabilities allow it.

Methods surfaced:

- `http::head`
- `http::get`
- `http::put`
- `http::post`
- `http::patch`
- `http::delete`

Behavior surfaced in docs:

- non-2XX responses fail
- JSON responses are parsed as values
- non-JSON responses are treated as text
- optional headers object can be passed
- use requires network capability allowance

Useful examples:

```surql
RETURN http::get("https://surrealdb.com");
RETURN http::post("https://example.com/hook", { id: 1 }, { Authorization: "Bearer token" });
```

### `search::`

Use with full-text search indexes and the `@@` / matches operator.

Functions surfaced:

- `search::analyze`
- `search::highlight`
- `search::linear`
- `search::offsets`
- `search::rrf`
- `search::score`

Common uses:

- inspect analyzer output
- retrieve BM25 relevance
- highlight hits
- fuse lexical and other rankings

Example:

```surql
SELECT id, search::highlight('<b>', '</b>', 1) AS title
FROM book
WHERE title @1@ 'rust web';
```

## Other Very Useful Families

- `array::`: array shape and transformations
- `object::`: object construction and manipulation
- `record::`: preferred record-id metadata helpers
- `parse::`: parse URL/email-like values
- `rand::`: random values and fake/test data style helpers
- `geo::`: geospatial calculations
- `math::`: numeric stats and transforms
- `type::`: type coercion and type helpers
- `value::`: generic value handling
- `duration::`: duration conversions and extraction
- `encoding::`: especially base64
- `file::`: file/bucket operations
- `session::`: current session metadata
- `api::`: API endpoint middleware
- `sleep()`: deliberate pauses

## Embedded JavaScript Functions

Docs note that SurrealDB supports embedded JavaScript functions with ES2020 support.

Use when:

- logic is significantly more complex than is comfortable in pure SurrealQL
- async/generator/JS-style transformations are helpful

Example shape:

```surql
CREATE person SET scores = function() {
  return [1,2,3].map(v => v * 10);
};
```

## SurrealML Functions

The docs also expose a SurrealML function category. Treat it as a specialized area and escalate to the ML section if the task is specifically model-serving or ML-function related.

## Selection Heuristics

- text cleanup/validation -> `string::`
- timestamps/windows/bucketing -> `time::`
- password/auth hashing -> `crypto::argon2::*` and related password helpers
- semantic/vector math -> `vector::`
- outbound webhooks/fetches -> `http::`
- full-text score/highlights/hybrid fusion -> `search::`
- array/object manipulation -> `array::`, `object::`

## Safety Notes

- `http::` depends on capability allowlists
- password hashing should use password-specific crypto helpers
- `string::html::encode` is the safer default over sanitization when rendering untrusted content
