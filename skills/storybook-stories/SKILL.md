---
name: storybook-stories
description: Author or edit `.stories.ts(x)`/`.mdx`, configure `.storybook/` (main/preview/manager), restructure sidebar/hierarchy, debug missing stories or single-story hoisting, write play functions, or use `composeStories` in Vitest/Jest/Playwright. Also triggers on `Meta<typeof ...>`, `StoryObj`, or `@storybook/*` imports. Scope: CSF3, React + TS, v10.3.
---

# Storybook stories (v10.3, React + TS, CSF3)

This skill encodes Storybook's official guidance for authoring stories and docs the way the tooling expects. Follow it whenever you're touching `.stories.tsx`, `.mdx`, or files in `.storybook/`.

**In scope**: Component Story Format 3 (CSF3), React renderer, TypeScript, Storybook v10.3.

**Out of scope** (fall back to Storybook's docs for these):

- **CSF Next** (`preview.meta(...)`, `meta.story(...)`) — a preview syntax the docs also describe. Don't mix it with CSF3; humans and type inference both get confused.
- **Authoring addons/presets** — `@storybook/addon-kit`, `managerEntries`, `previewAnnotations` for third-party distribution. Storybook's addon-development docs are the right source.

## The mental model

A story file has two things:

1. A **default export** (the `meta`) that describes the component being documented and applies to all stories in the file.
2. **Named exports** — each one is a story: a specific state or example of the component.

Storybook discovers these via the `stories` glob in `.storybook/main.ts`, usually `../src/**/*.stories.@(js|jsx|mjs|ts|tsx)`. It builds the sidebar from the meta's `title` (or the file path, if `title` is omitted) and renders each named export as a story under it.

## Canonical story file

This is the shape to reach for. It uses `satisfies` on both meta and each story — that's what gives you type errors on missing or invalid args:

```ts
// Button.stories.tsx

import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "./Button";

const meta = {
  component: Button,
  // title is optional — omit it to let the file path generate the sidebar location
  // include it only when you want to override the implicit location (e.g., grouping)
} satisfies Meta<typeof Button>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Basic: Story = {};

export const Primary: Story = {
  args: { primary: true },
};
```

Key points (why, not just what):

- **`satisfies Meta<typeof Button>`** rather than `const meta: Meta<typeof Button> = ...`. `satisfies` preserves the precise type so `StoryObj<typeof meta>` can tell that args defined at the meta level satisfy story-level required-arg checks. With `:` annotation you lose that inference and get false errors.
- **`type Story = StoryObj<typeof meta>`** — always derive from `typeof meta`, not from the component type directly. This is what lets TypeScript know which args are already provided at the meta level.
- **Each story typed `: Story`** (not `satisfies Story`) works, but using `satisfies Story` gives stricter checks on play functions and other fields; either is acceptable.
- **Custom args that aren't real props** (e.g., a `footer` string the story passes to a child) need an intersection type, not just `Meta<typeof Component>`. See `references/typescript.md`.

## Sidebar hierarchy and `title`

There are **two ways** stories land in the sidebar:

- **Implicit (preferred)**: omit `title`, rely on the file path. `src/components/Button/Button.stories.tsx` becomes `Components/Button`. This keeps filesystem and sidebar in sync and avoids drift.
- **Explicit**: set `title: 'Design System/Atoms/Button'`. Use `/` as the group separator. Reach for this only when the sidebar structure intentionally differs from the filesystem (e.g., a curated "Design System" grouping).

Don't mix: either the whole project uses implicit titles, or you set titles on every file. Half-and-half produces a sidebar that's hard to reason about.

### Single-story hoisting (common gotcha)

If a file has **exactly one story** whose exported name matches the last segment of the title (or the component name, for implicit titles), Storybook **hoists** the story up to replace its parent in the sidebar. So `title: 'Design System/Atoms/Button'` with a lone `export const Button` renders as `Design System/Atoms/Button` (one item), not nested.

When this bites you:

- You add a second story and the sidebar structure changes. This is expected — the story is no longer the only sibling.
- Story export names are start-cased: `myStory` → `"My Story"`. So a lone story named `button` won't hoist under title `.../Button`; either rename the export to `Button` or set `Button.storyName = 'Button'`.

### Sorting

Default is import order. For deterministic/curated order, set `storySort` in `.storybook/preview.ts`'s `parameters.options`. Supports `method: 'alphabetical'`, a custom `order` array with nested arrays for 2nd-level kinds, and `'*'` as a "rest" placeholder to pin categories to the end. See `references/naming-hierarchy.md` for the full shape.

## Documenting components: tags over configuration

Storybook v10 drives docs with **tags**, not per-file flags. The important ones:

- `'autodocs'` — generate an auto-documentation page for this story/component. Usually set project-wide in `preview.ts`:

  ```ts
  const preview: Preview = { tags: ["autodocs"] };
  ```

  Opt out per-file with `tags: ['!autodocs']`.

- `'!autodocs'` on a single story — keep the component docs page, but exclude this specific story from it.
- `'manifest'` / `'!manifest'` — controls whether a story or docs page is included in the AI manifests that tools like Storybook's MCP server consume. Default is in; remove to exclude instructional or deprecated examples.

### When to reach for MDX instead of CSF

Rule of thumb: if you'd write a README, write an MDX file. If you're describing a component state, write a story. See `references/mdx.md` and `references/doc-blocks.md`.

## Writing stories that also serve AI agents

Storybook generates manifests (JSON descriptions of components and docs) that MCP-based agents consume. The same patterns that make stories readable to humans make them useful to agents:

- **One concept per story.** `Primary`, `Disabled`, `WithIcon` — not `SizesAndVariantsAndStates`. A story demonstrating six different things teaches neither humans nor agents anything specific.
- **JSDoc on component and props.** Extracted verbatim into the manifest. Prefer `react-docgen-typescript` over `react-docgen` in `.storybook/main.ts` (`typescript.reactDocgen`) — slower but much richer.
- **JSDoc on stories explaining _why_.** "Primary buttons are used for the main action in a view. There should not be more than one primary button per view." — this is the kind of rule an agent can actually follow.
- **`@summary` tags** for short blurbs: `@summary for the main action in a view`.
- **Use `tags: ['!manifest']`** to hide anti-pattern demos, deprecated components, or instructional-only stories from agents.

See `references/ai.md` for full guidance on manifests and curation.

## Building and publishing docs

`storybook dev --docs` / `storybook build --docs` render the published docs experience: toolbar hidden, stories flattened under their Docs page. Add them as `package.json` scripts when you need to review or deploy docs separately. See `references/doc-blocks.md`.

## Reference files

Load these when you need depth on a topic:

- `references/naming-hierarchy.md` — titles, grouping, roots, hoisting, sort order (full detail + examples).
- `references/typescript.md` — `Meta`/`StoryObj` generics, `satisfies`, typing custom args via intersections.
- `references/args-parameters-decorators-loaders.md` — global/component/story inheritance for all four; `useArgs`, `mapping`, arg composition, URL args; parameter merge semantics; decorator order and context; when loaders are and aren't appropriate.
- `references/autodocs.md` — enabling/disabling per project/component/story, custom templates, table of contents, subcomponents, monorepo gotchas.
- `references/mdx.md` — MDX syntax, `Meta` block (attached vs unattached docs), setting up the `stories` glob, linking, troubleshooting.
- `references/doc-blocks.md` — every available block (`ArgTypes`, `Canvas`, `Controls`, `Primary`, `Stories`, `ColorPalette`, `Typeset`, etc.), Code panel, and docs build/publish. Customization via `parameters.docs.*`.
- `references/ai.md` — manifests (components + docs), curation via `'manifest'` tag, JSDoc best practices, prop-type extraction, debugging at `/manifests/components.html`.
- `references/testing.md` — play functions (interaction tests), portable stories (`composeStories` in Vitest/Jest/Playwright CT), visual tests (Chromatic), snapshot tests, E2E via story iframe URLs.
- `references/configure.md` — `.storybook/main.ts` / `preview.ts` / `manager.ts`: stories glob, addons, docs config, env vars, theming, sidebar/toolbar customization, story layout, telemetry opt-out, permalink control.

## Common failure modes

- **Story file not appearing** → check `stories` glob in `.storybook/main.ts`. Most common cause.
- **Sidebar nesting looks wrong after adding a second story** → single-story hoisting stopped applying. Expected. Either live with the new structure or rename exports so the original continues to hoist.
- **Types red on `args` the meta already provides** → you used `: Meta<...>` instead of `satisfies Meta<...>`, or derived `Story` from the component type instead of `typeof meta`.
- **Autodocs page missing in a monorepo** → import components from their file directly, not from the package root; may also need `typescript.reactDocgen: 'react-docgen'` and `check: false` in `main.ts`. See `references/autodocs.md`.
- **MDX page not picked up** → `stories` glob must include `'../src/**/*.mdx'` (or wherever). Autodocs won't cover `.mdx` by itself.
- **`Meta` block in MDX passing the component instead of the story exports** → always pass the full set of exports (`of={ButtonStories}`), not the component.
