---
name: frontend-organization
description: Review or refactor frontend file layout, naming, and feature boundaries so route ownership, screen ownership, and public APIs are obvious. Use when the code feels AI-organized, when screen/container ownership is unclear, or when feature barrels and shared UI boundaries need cleanup.
context: fork
---

# Frontend Organization

Use this skill when the problem is structural discoverability rather than broken behavior.

This skill is for code that works, but is difficult to navigate because:

- screen owners are hard to identify
- route files and feature files have muddled responsibilities
- feature barrels expose too much or too little
- generic UI and feature UI are mixed together
- naming reflects implementation tiers instead of UI responsibility

This skill is the canonical policy for organization work in this repo.

## Primary Goal

Optimize for fast navigation and obvious ownership.

A developer opening a screen should be able to answer these questions quickly:

1. Which route file owns the URL?
2. Which feature component owns the screen implementation?
3. Which files are part of that screen versus reusable leaf modules?
4. Which imports are part of the feature's supported public API?

If the folder layout does not answer those questions, the structure is wrong even if the code works.

## What To Audit

For the target route or feature, answer these questions first:

1. Which file in `src/routes` owns the URL contract?
2. Which feature component owns the mounted screen or layout?
3. Which files own major sections inside that screen?
4. Which modules under that feature are screen-level, section-level, domain-level, and leaf-level?
5. Which imports should be public through the feature barrel?
6. Which components are truly reusable and belong in `src/core/ui`?

If you cannot answer those quickly, the organization needs work.

Treat these as three distinct ownership layers:

- route owner
- mounted screen or layout owner
- section or module owners

Do not collapse those into one generic idea of a "container." In practice, that is where most structural ambiguity comes from.

## Boundary Audit Before Moves

Before moving or renaming files, inspect boundary leaks first.

Check for:

1. route files deep-importing feature internals
2. other features importing `components/...` or other internal paths directly
3. missing barrel exports for legitimate cross-feature usage
4. namespace re-exports that expose too much of the feature by default

Fixing the boundary is often more valuable than moving files around.

## Core Rules

### 1. Keep route ownership in `src/routes`

- route files own URL contracts, loaders, auth gates, and route-level bootstrap
- features own mounted screen implementations
- do not create parallel route hierarchies inside feature folders

Examples:

- `src/routes/projects.tsx` owns the `/projects` route contract
- `src/routes/projects.lazy.tsx` mounts the screen
- `src/features/projects/components/ProjectsLandingView/ProjectsLandingView.tsx` owns the screen implementation

### 2. Prefer domain-first folders

Use names like:

- `ProjectsLandingView`
- `ProjectCard`
- `CreateProjectModal`
- `table`
- `rows`
- `controls`
- `overlays`

Do not default to abstract buckets like `elements` or `modules` unless they genuinely improve clarity.

When a feature needs internal structure for ownership clarity, prefer these buckets:

- `layout/` for route-mounted shells, navigation chrome, or outer page scaffolding
- `screens/` for mounted screen owners
- `sections/` for major content blocks within a screen

Keep existing domain subfeatures when they already represent a coherent subsystem, for example:

- `apiTokens/`
- `mcpIntegration/`
- `providerCredentials/`

Do not reorganize stable subfeatures just to make the tree look uniform.

### 3. Use naming to resolve ambiguity, not to enforce ideology

- `*View` is useful for full screens and major panels when it improves discoverability
- `*Screen` is also acceptable when already established
- `*Widget`, `*Connected`, and `*Container` are not default naming tools
- `use*Controller` is reserved for genuinely complex coordination logic
- `use*ViewModel` is appropriate when a hook shapes data for one screen

Use names that clarify responsibility. Do not build a naming bureaucracy.

Screen components:

- prefer consistency inside a feature
- do not mass-rename stable files just to force one suffix everywhere

Leaf and mid-level UI components:

- use noun-based names tied to UI responsibility
- examples: `ProjectCard.tsx`, `ListHeader.tsx`, `GroupingRow.tsx`, `DeleteProjectOverlay.tsx`
- avoid names that only describe implementation tier unless they resolve a real ambiguity

Hooks and controllers:

- use `use*Controller` for interaction-heavy coordination, state machines, focus management, drag/drop, or dense table/board behavior
- use `use*ViewModel` when the hook shapes screen data for one view
- use ordinary `use*` names for straightforward data derivation or local behavior

### 4. Curate feature barrels

Feature `index.ts` files should export the supported public API:

- mounted screens
- supported hooks
- shared types and schemas
- cross-feature utilities that are intentionally public

Do not:

- `export *` from every internal subtree by default
- force consumers to deep-import internals
- expose leaf renderers casually

The rule is not "export only one View." The rule is "export only what other layers should rely on."

Prefer curated named exports over broad namespace exports when that improves clarity, but do not force everything into one export style in a single pass if the namespace is already a stable API.

Other features should import from a feature barrel, not from that feature's internals.

Bad:

```ts
import { ProjectCard } from '@/features/projects/components/ProjectCard/ProjectCard'
```

Good:

```ts
import { useProjectsListQuery } from '@/features/projects'
```

If another feature needs a leaf UI component directly, one of these is usually true:

1. The component should move to `src/core/ui`.
2. The consuming feature needs a different abstraction.
3. The feature barrel is missing a legitimate export.

### 5. Promote only true primitives

Move code to `src/core/ui` only when:

- the name is feature-agnostic
- the props are generic
- the behavior is reusable across features

Leave thin adapters in the feature when the shared primitive still needs feature-specific wiring.

### 6. Organize feature folders by domain responsibility

Preferred pattern inside a feature:

```text
src/features/<feature>/
├── api/
├── hooks/
├── store/
├── schemas/
├── utils/
├── components/
│   ├── <ScreenName>/
│   │   ├── <ScreenName>.tsx
│   │   ├── <ScreenName>.stories.tsx
│   │   ├── use<ScreenName>ViewModel.ts
│   │   └── <supporting files>
│   ├── <DomainModule>/
│   │   ├── <DomainModule>.tsx
│   │   └── <supporting files>
│   ├── layout/
│   ├── controls/
│   ├── rows/
│   ├── table/
│   └── overlays/
└── index.ts
```

Rules:

- use folder-per-component when the component has stories, tests, hooks, or multiple support files
- use flat files when a component is small and truly standalone
- prefer domain buckets like `table`, `rows`, `header`, `cards`, `overlays`, `controls`
- avoid generic junk-drawer buckets like `elements` unless the feature genuinely benefits from them

## Choose The Smallest Fix

Do not default to file moves.

For each ambiguity, ask which change actually solves it:

1. A folder move?
2. A barrel export change?
3. A rename of the real owner?
4. A promotion into `src/core/ui`?
5. A comment/docstring clarifying ownership?

Prefer the smallest change that materially improves discoverability.

## File Move Rule

When a refactor does require moving files, use `git mv` so file history stays intact.

- do not delete and recreate the same file at a new path when it is logically a move
- preserve rename tracking whenever possible
- only fall back to manual delete/add when the move is inseparable from a full rewrite
- after moving, update imports and barrels in the same pass so the tree is never half-migrated

## Refactor Workflow

1. Identify the route owner, mounted screen/layout owner, and section owners separately.
2. Audit external deep imports and route-to-feature boundary leaks.
3. Decide whether the real fix is exports, naming, promotion, or file moves.
4. Shrink or reshape the feature barrel to match the intended public API.
5. Reorganize only the noisy or ambiguous subtrees by domain responsibility.
6. Rename only the files that materially improve discoverability.
7. Move true shared primitives to `src/core/ui` if needed.

Prefer small passes over broad churn.

## Smartness Rules

Do not enforce a fake "dumb components only" policy.

Use this split instead:

- route/app boundary owns URL contracts, auth gates, and global bootstrap
- feature screen owns feature orchestration
- leaf modules own rendering and local interaction
- heavy cross-cutting coordination moves into hooks, controllers, or services when that materially improves clarity

A component may call a query hook if that is the clearest ownership boundary. Do not add a wrapper component just to preserve purity theater.

## Red Flags

These are strong signals that a refactor is justified:

- multiple files look like they might own the same screen
- the mounted route owner and the actual screen owner are hard to distinguish
- feature barrels export many unrelated leaf modules
- another feature imports `components/.../Thing.tsx` directly
- component names describe architecture tier instead of UI job
- generic UI primitives remain trapped in one feature
- route logic and screen logic are duplicated in different places

## Recommended Enforcement

Prefer lightweight enforcement over rigid ceremony.

Recommended checks:

- ESLint restriction against cross-feature deep imports
- require feature barrels for supported public APIs
- require colocated comments/docstrings when touching ambiguous ownership files
- review naming changes for actual clarity gains before accepting them

## Migration Strategy

Apply these rules incrementally.

1. Fix the public API first.
   Reduce deep imports and curate `index.ts` files.
2. Clarify screen ownership next.
   Make the route file, mounted screen, and screen view-model obvious.
3. Reorganize noisy component trees by domain.
   Prefer small, readable moves over broad folder churn.
4. Promote true shared primitives to `src/core/ui`.
5. Rename only where names actively obscure ownership.

Do not rewrite entire features just to achieve aesthetic symmetry.

## Litmus Test

A feature is organized well when a new engineer can:

1. open the route file and identify the mounted screen immediately
2. open the feature folder and identify the mounted screen or layout owner immediately
3. identify major section owners without reading half the tree
4. distinguish public API from internals without guessing
5. find related modules by domain, not by memorizing arbitrary bucket names

If that is true, the structure is doing its job.

## Applied Heuristics

Use these heuristics during real passes:

- identify route owner, mounted screen owner, and section owners separately
- fix cross-feature deep imports before moving files
- prefer the smallest change that improves discoverability
- use `layout`, `screens`, and `sections` when they clarify ownership
- preserve coherent domain subfeatures instead of reorganizing for symmetry
- curate public exports without flattening every stable namespace in one pass

## Output Expectations

When using this skill:

- state the current route owner, mounted screen owner, section owners, and public API boundary
- explain why each rename or move improves discoverability
- call out any boundary leaks you fixed
- avoid churn that only makes the tree look symmetrical
- preserve working behavior; this is an organization pass, not a product rewrite
