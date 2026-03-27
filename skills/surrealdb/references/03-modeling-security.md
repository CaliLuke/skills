# Modeling Security

## Multi-Model Framing

The docs present SurrealDB as document-first underneath, with graph, relational-style, time-series, search, vector, and geospatial patterns built into the same system.

Use:

- nested objects/arrays for document-style data
- record IDs and `RELATE` for graph edges
- tables/fields/indexes/assertions/permissions for stricter relational-style schema

## Schema Strategy

- `SCHEMALESS`: default flexibility
- `SCHEMAFULL`: strict field enforcement
- `FLEXIBLE`: escape hatch for object fields inside strict tables

Practical guidance from the docs:

- put type and length constraints on arrays/sets where possible
- define nested object structure explicitly in strict tables
- use `ASSERT` for validation
- use `THROW` inside `ASSERT` blocks when a clearer custom error helps
- use `DEFINE PARAM` for shared constants

For the full upstream guide kept intact, use:

- `references/reference-guides/schema-creation-best-practices.mdx`

## Auth Model

### System users

- created with `DEFINE USER`
- scope: `ROOT`, `NAMESPACE`, or `DATABASE`
- roles: `OWNER`, `EDITOR`, `VIEWER`

Example:

```surql
DEFINE USER john ON ROOT PASSWORD "VerySecurePassword!" ROLES OWNER;
DEFINE USER mary ON DATABASE PASSWORD "VerySecurePassword!" ROLES EDITOR;
```

### Record users

- created through `DEFINE ACCESS ... TYPE RECORD`
- use signin/signup logic over normal records
- do not inherit RBAC roles
- effectively have no access unless table/field permissions allow it

Example pattern:

```surql
DEFINE TABLE user SCHEMAFULL
  PERMISSIONS
    FOR select, update, delete WHERE id = $auth.id;

DEFINE FIELD name ON user TYPE string;
DEFINE FIELD email ON user TYPE string ASSERT string::is_email($value);
DEFINE FIELD password ON user TYPE string;
DEFINE INDEX email ON user FIELDS email UNIQUE;

DEFINE ACCESS user ON DATABASE TYPE RECORD
  SIGNIN (
    SELECT * FROM user
    WHERE email = $email
      AND crypto::argon2::compare(password, $password)
  )
  SIGNUP (
    CREATE user CONTENT {
      name: $name,
      email: $email,
      password: crypto::argon2::generate($password)
    }
  );
```

## Security Defaults

- hash passwords with password-hashing functions such as Argon2
- do not use general-purpose hashes like MD5/SHA* for passwords
- shorten token duration where possible
- set session duration intentionally for direct-client use
- bind parameters instead of interpolating user input
- encode or sanitize user HTML before rendering
- prefer asymmetric JWT verification when SurrealDB only needs to verify tokens

## Capabilities

Docs emphasize that SurrealDB is secure by default and that sensitive capabilities should be allowed narrowly.

Main controls mentioned:

- `--allow-all` / `--deny-all`
- `--allow-funcs` / `--deny-funcs`
- `--allow-net` / `--deny-net`
- `--allow-scripting` / `--deny-scripting`
- `--allow-guests` / `--deny-guests`
- `--allow-experimental`

Rule priority from docs:

- more specific rules beat less specific rules
- at equal specificity, deny beats allow

Safer example:

```bash
surreal start --deny-all \
  --allow-funcs "array, string, crypto::argon2, http::get" \
  --allow-net api.example.com:443
```

## Query Safety

Always prefer parameter binding.

Good:

```js
await db.query('CREATE person CONTENT name = $name;', { name });
```

Bad:

```js
await db.query(`CREATE person CONTENT name = "${name}";`);
```

## Modeling Defaults

- If requirements are evolving, start schemaless then tighten later.
- If auth is application-facing, use record access plus explicit permissions.
- If data is security-sensitive, make permissions explicit and conservative.
- If a field must be unique, define an index for it.

## Intact Reference Guides Worth Checking

- `references/reference-guides/schema-creation-best-practices.mdx`
- `references/reference-guides/sample-industry-schemas.mdx`
- `references/reference-guides/real-time-best-practices.mdx`
