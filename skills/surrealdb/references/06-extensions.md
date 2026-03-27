# Extensions

## What Surrealism Is

- Surrealism is the SurrealDB plugin/extension feature.
- Sampled docs mark it as available since `v3.0.0`.
- It is explicitly described as active development / not yet stable.
- Extensions are written in Rust, compiled to WebAssembly, then loaded into SurrealDB as modules.

## Main Use Cases Mentioned In Docs

- fake/mock data generation for testing
- exposing niche Rust crate functionality without patching SurrealDB itself
- surfacing your own Rust code as callable functions inside SurrealQL

## End-To-End Flow

1. Write Rust functions.
2. Add `#[surrealism]` to functions you want to expose.
3. Add a `surrealism.toml` file.
4. Build a `.surli` module with `surreal module build`.
5. Start SurrealDB with experimental capabilities enabled.
6. `DEFINE BUCKET` pointing at the allowed folder.
7. `DEFINE MODULE mod::name AS f"bucket:/file.surli";`
8. Call functions as `mod::name::function(...)`.

## Minimal Rust Shape

Add this to `Cargo.toml` when needed:

```toml
[lib]
crate-type = ["cdylib"]
```

Add dependencies mentioned in the docs:

- `surrealism`
- `surrealdb-types`

Example:

```rust
use surrealism::surrealism;

#[surrealism]
fn can_drive(age: i64) -> bool {
    age >= 18
}
```

If returning custom structs, derive `SurrealValue` so SurrealDB can understand the value shape.

## `surrealism.toml`

The docs show a package block plus capabilities block. Example shape:

```toml
[package]
organisation = "surrealdb"
name = "demo"
version = "1.0.0"

[capabilities]
allow_scripting = true
allow_arbitrary_queries = true
allow_functions = ["fn::test"]
allow_net = ["127.0.0.1:8080"]
```

Docs note this file will be used more heavily for versioning/capabilities in future.

## Build / Inspect / Run Via CLI

Build:

```bash
surreal module build --out demo.surli /Users/my_name/my_rust_code
```

Inspect function signature:

```bash
surreal module sig can_drive demo.surli
```

Run directly:

```bash
surreal module run can_drive --arg 17 demo.surli
```

## Runtime Gating

Docs call out two important environment variables for using extensions through a DB instance:

```bash
SURREAL_CAPS_ALLOW_EXPERIMENTAL=files,surrealism
SURREAL_BUCKET_FOLDER_ALLOWLIST="/Users/my_name/my_rust_code/"
```

Start the server with them:

```bash
SURREAL_CAPS_ALLOW_EXPERIMENTAL=files,surrealism \
SURREAL_BUCKET_FOLDER_ALLOWLIST="/Users/my_name/my_rust_code/" \
surreal start --user root --pass secret
```

Connect CLI with same gating when needed:

```bash
SURREAL_CAPS_ALLOW_EXPERIMENTAL=files,surrealism \
SURREAL_BUCKET_FOLDER_ALLOWLIST="/Users/my_name/my_rust_code/" \
surreal sql --user root --pass secret
```

## Loading A Module In SurrealDB

Create a bucket:

```surql
DEFINE BUCKET test BACKEND "file:/users/my_name/my_rust_code";
```

Load the module:

```surql
DEFINE MODULE mod::test AS f"test:/demo.surli";
```

Call functions:

```surql
mod::test::parse_number("10");
CREATE user CONTENT mod::test::random_user();
SELECT mod::test::can_drive(age) FROM user;
```

## Useful Details

- `#[surrealism(name = "other")]` renames the function on the SurrealDB side.
- `#[surrealism(default)]` makes a function callable via the module path alone.
- Extensions require both `files` and `surrealism` experimental capabilities in the sampled tutorial flow.

## Default Advice

- Treat extensions as advanced and version-sensitive.
- Prefer regular SurrealQL or SDK logic unless a Rust/WASM extension is genuinely needed.
- When answering extension questions, include the capability gating and bucket/module setup, not just the Rust attribute.
