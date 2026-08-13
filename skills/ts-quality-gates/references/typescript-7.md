# TypeScript 7 migration reference

If you adopt native TypeScript 7 or type-aware Oxlint, use this reference.

## Contents

- [TypeScript 7.0 toolchain facts](#typescript-70-toolchain-facts)
- [Choose a package layout](#choose-a-package-layout)
- [Migrate configuration](#migrate-configuration)
- [Verify framework and API constraints](#verify-framework-and-api-constraints)
- [Verify the transition](#verify-the-transition)

## TypeScript 7.0 toolchain facts

- Install the stable native compiler from `typescript@^7`. The executable is `tsc`.
- Treat `@typescript/native-preview` and the `tsgo` command as pre-release-era names. Do not add them to a new stable setup.
- Expect the TypeScript 7 CLI and language service to be native Go programs.
- TypeScript 7.0 has no stable programmatic compiler API. Verify current tool support before you replace TypeScript 6 for API consumers.
- Match `oxlint-tsgolint` to the TypeScript 7 release it tracks. Type-aware Oxlint requires a TypeScript 7-compatible configuration.

Official references:

- [TypeScript 7.0 announcement](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/)
- [TypeScript 6.0 transition notes](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-6-0.html#preparing-for-typescript-70)
- [Oxlint type-aware linting](https://oxc.rs/docs/guide/usage/linter/type-aware.html)

## Choose a package layout

### Native-only

If no dependency imports the TypeScript compiler API, use this layout:

```json
{
  "devDependencies": {
    "typescript": "^7.0.2"
  }
}
```

### Native CLI plus TypeScript 6 API compatibility

If a tool imports `typescript`, use this layout. The repository can still run the native compiler for project checking.

```json
{
  "devDependencies": {
    "@typescript/native": "npm:typescript@^7.0.2",
    "typescript": "npm:@typescript/typescript6@^6.0.2"
  }
}
```

This layout supplies native `tsc`, compatibility `tsc6`, and the TypeScript 6 API. Preserve versions that the repository pins.

Before you edit scripts, verify the binary that the package manager resolves.

## Migrate configuration

Run TypeScript 6 without `ignoreDeprecations` first. Fix every deprecation before switching the canonical compiler to TypeScript 7.

Review these TypeScript 7 default changes. A successful project compile does not complete this review.

- `strict: true`
- `module: esnext`
- `target`: the stable ECMAScript version immediately before `esnext`
- `noUncheckedSideEffectImports: true`
- `libReplacement: false`
- `stableTypeOrdering: true`
- `rootDir: ./`
- `types: []`

Keep runtime intent explicit. If the configuration is above the source directory, set `rootDir`.

List required ambient packages in `types`. Do not restore `types: ["*"]` without evidence.

Remove or migrate these TypeScript 7 errors:

- Remove `target: es5`. Use ES2015 or newer. If necessary, use an external downlevel transform.
- `downlevelIteration`.
- Remove `moduleResolution: node`, `node10`, or `classic`. Use `nodenext` for Node. Use `bundler` for a bundler or Bun.
- Remove `module: amd`, `umd`, `systemjs`, or `none`. Use an ESM mode that matches the runtime.
- Remove `baseUrl`. Make `paths` targets relative to the project root.
- `esModuleInterop: false` or `allowSyntheticDefaultImports: false`.
- `alwaysStrict: false`.
- `outFile` and legacy namespace/import constructs removed during the 6-to-7 transition.
- Do not pass CLI file arguments beside a discovered `tsconfig`. Use a project configuration. Use `--ignoreConfig` only for an intentional bypass.

For `baseUrl` and `rootDir`, consider the focused migration tool and review its diff:

```text
npx @andrewbranch/ts5to6 --fixBaseUrl .
npx @andrewbranch/ts5to6 --fixRootDir .
```

If the repository does not use npm, use its package runner instead of `npx`.

## Verify framework and API constraints

TypeScript 7.0 does not expose the old programmatic API. Inspect actual current support before changing any of these:

- Angular template checking
- Vue/Volar and `vue-tsc`
- Svelte and `svelte-check`
- Astro checks
- MDX language tooling
- custom transformers or language-service plugins
- tools that import compiler API types or functions

Use the supported framework checker for embedded files. Oxlint can gate ordinary JavaScript and TypeScript.

If a required framework check uses TypeScript 6, document the split. Do not claim full TypeScript 7 adoption.

## Verify the transition

1. Run the old compiler and configuration once. Record the baseline.
2. Run native `tsc --version` and verify that it reports 7.x.
3. Run every production `tsconfig`, not only the root configuration.
4. Compare diagnostics with the TypeScript 6 baseline.
5. Run framework checks and emit/declaration builds separately.
6. Run Oxlint type-aware mode only after every selected `tsconfig` is TypeScript 7 compatible.
