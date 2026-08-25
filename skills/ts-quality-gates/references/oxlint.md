# Oxlint configuration and migration

Use Oxlint as the only lint runner. Use native rules first. Then use type-aware rules and ESLint-compatible JavaScript plugins.

## Contents

- [Install](#install)
- [Select a configuration format](#select-a-configuration-format)
- [Use one typed pass](#use-one-typed-pass)
- [Migrate ESLint without keeping an ESLint gate](#migrate-eslint-without-keeping-an-eslint-gate)
- [Migrate another lint runner](#migrate-another-lint-runner)
- [Handle compatibility honestly](#handle-compatibility-honestly)
- [Gate and diagnose](#gate-and-diagnose)

Official references:

- [Oxlint overview](https://oxc.rs/docs/guide/usage/linter.html)
- [Configuration](https://oxc.rs/docs/guide/usage/linter/config.html)
- [Type-aware linting](https://oxc.rs/docs/guide/usage/linter/type-aware.html)
- [Built-in plugins](https://oxc.rs/docs/guide/usage/linter/plugins)
- [JavaScript plugins](https://oxc.rs/docs/guide/usage/linter/js-plugins)
- [ESLint migration](https://oxc.rs/docs/guide/usage/linter/migrate-from-eslint.html)

## Install

Install both packages as development dependencies:

```text
oxlint
oxlint-tsgolint@7
```

Keep `oxlint-tsgolint` aligned with the native TypeScript version. Its version encodes the TypeScript release it embeds.

## Select a configuration format

Use `.oxlintrc.json` or JSONC for broad runtime compatibility.

If Node can execute TypeScript files, you can use `oxlint.config.ts`. The repository must use the Node-based Oxlint package.

Oxlint discovers nested configuration. Put `typeAware` and `typeCheck` only in the root configuration.

If a `plugins` array is present, list every required plugin. This array replaces the default set.

The default native plugins are `eslint`, `typescript`, `unicorn`, and `oxc`. If the repository uses other native plugins, add them.

## Use one typed pass

For a gate with separate fast and full modes, keep the root configuration syntax-only and enable both typed features on the full command:

```text
oxlint --type-aware --type-check --deny-warnings
```

Oxlint and `tsgolint` share the TypeScript programs between type-aware rules and compiler diagnostics. The fast command remains:

```text
oxlint --deny-warnings
```

Do not use `--type-aware=false` or `--type-check=false`; current Oxlint does not accept those arguments.

If the repository has no syntax-only fast mode and every Oxlint invocation should be typed, configure the root instead:

```jsonc
{
  "options": {
    "typeAware": true,
    "typeCheck": true
  }
}
```

The `typeAware` and `typeCheck` options can only appear in the root configuration. CLI flags can enable them but cannot disable root-enabled modes.

Type-aware mode enables high-signal correctness rules by default. Add explicit rules only to define additional policy.

In a monorepo, build declaration outputs that the typed pass requires. Keep root solution configurations scoped with `files: []`.

Do not use `include: ["**/*"]` in an aggregate configuration.

## Migrate ESLint without keeping an ESLint gate

For flat configs, run the package-manager equivalent of:

```text
npx @oxlint/migrate --type-aware
```

Then:

1. Compare every rule, severity, option, ignore, override, environment, and global.
2. If a native Oxlint rule is available, prefer it.
3. Add non-native npm or local rules through `jsPlugins`.
4. If a JavaScript plugin name conflicts with a native plugin, add an alias.
5. Verify representative files with `oxlint --print-config`.
6. Run fixes and compare diagnostics before deleting ESLint configuration and dependencies.

Example JavaScript plugin fallback:

```jsonc
{
  "jsPlugins": [
    {
      "name": "company",
      "specifier": "./tools/eslint-plugin-company/index.js"
    }
  ],
  "rules": {
    "company/no-unsafe-boundary": "error"
  }
}
```

Do not add `eslint-plugin-oxlint` or a second `eslint` command. Those support a dual-run migration, which this skill intentionally avoids.

## Migrate another lint runner

Oxlint must own the lint row after migration. Treat existing tools as migration inputs, not permanent second lint gates.

| Existing runner | Migration action |
| --- | --- |
| Oxlint | Extend its root configuration and verify representative files. |
| ESLint | Run `@oxlint/migrate --type-aware`. Map native rules first and JavaScript plugins second. |
| Biome | Keep Biome formatting if it is established. Move lint policy to Oxlint. Remove Biome lint commands only after parity checks pass. |
| `deno lint` | Map ordinary JavaScript and TypeScript policy to Oxlint. Inspect Deno-specific rules separately. Report an exact unsupported semantic instead of silently keeping two general lint gates. |

Oxlint owns `complexity`, `max-lines`, and other policy rules in all four cases. Exclude generated files with Oxlint ignore patterns or overrides.

## Handle compatibility honestly

Oxlint's JavaScript plugin API targets ESLint v9+ and implements almost all of that API.

JavaScript plugins do not support type-aware rules or custom file parsers. This limit applies to full Vue, Svelte, and Angular templates.

Use native Oxlint/tsgolint rules for type-aware policy. Use framework checks for embedded templates.

If no replacement exists, identify the exact rule and file scope. Do not delete the rule silently.

## Gate and diagnose

Use these commands through the detected package manager:

```text
oxlint --deny-warnings
oxlint --type-aware --type-check --deny-warnings
oxlint --fix
oxlint --print-config src/example.ts
oxlint --debug timings
```

Use only safe fixes in the routine fix path. Before you apply behavior-changing fixes, get explicit user authorization.
