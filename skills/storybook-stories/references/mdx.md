# MDX for docs

MDX mixes Markdown + JSX, letting you write prose around live stories and Doc Blocks. Use it for documentation pages that need structure beyond what Autodocs produces — onboarding guides, design tokens, usage do/don'ts, richer per-component pages.

## When MDX vs CSF

- **CSF (`.stories.tsx`)** — succinctly defines stories (component examples). Typed, terse. Use for every component state.
- **MDX (`.mdx`)** — structured prose _around_ stories. Use when you need markdown, links, tables, or curated layout.

They work together: MDX files reference stories via the `Meta` block and embed them with Doc Blocks.

## Register the glob

MDX files only appear if the `stories` glob in `.storybook/main.ts` matches them:

```ts
const config: StorybookConfig = {
  framework: "@storybook/your-framework",
  stories: ["../src/**/*.mdx", "../src/**/*.stories.@(js|jsx|mjs|ts|tsx)"],
  addons: ["@storybook/addon-docs"],
};
export default config;
```

## Attached MDX (tied to a story file)

Docs page that displays alongside a component's stories. Use the `Meta` Doc Block with `of={ComponentStories}`:

```mdx
{/* Button.mdx */}
import { Meta, Controls, Primary, Stories } from '@storybook/addon-docs/blocks';
import \* as ButtonStories from './Button.stories';

<Meta of={ButtonStories} />

# Button

A button is a clickable interactive element that triggers a response.

## Usage

<Primary />
<Controls />

## Variants

<Stories />
```

Critical: **pass the whole star-import (`ButtonStories`) to `of`, not the component itself**. `of={Button}` won't work.

## Unattached MDX (standalone docs page)

`Meta` with no `of` — the page stands alone in the sidebar:

```mdx
<Meta title="Design System/Typography" />

# Typography

...
```

Use for design tokens, onboarding, guidelines, changelog.

If you omit `Meta` entirely, Storybook infers the title from the file path (like CSF auto-titles). Works well for pure-markdown pages with no Doc Blocks.

## Anatomy gotchas

- **Blank lines separate blocks.** MDX mixes languages; missing blanks around JSX → cryptic parse errors.
- **Comments are JSX**: `{/* like this */}`.
- **Imports sit at the top.** The `Meta` Doc Block and any imported MDX or components.
- **Markdown (CommonMark) by default.** Tables and footnotes (GFM) need `remark-gfm` enabled in addon-docs `mdxPluginOptions` (see "Troubleshooting" below).
- **MDX Provider sandboxing.** If you override MDX components (`h1`, `p`, etc.) via `MDXProvider`, overrides apply only to Markdown-produced tags (`# Hi`), not native JSX tags (`<h1>`). This is MDX behavior, not Storybook's.

## Embedding stories and composing docs

Besides `of`, you can render individual stories:

```mdx
<Story of={ButtonStories.Primary} />
<Canvas of={ButtonStories.Primary} />
```

`Canvas` = toolbar + story + auto-generated Source snippet. `Story` = just the story.

## Multiple components on one page

```mdx
<Meta title="Layout" />
import * as PageStories from './Page.stories'; import * as ListStories from
'./List.stories';

# Page

<Primary of={PageStories} />
<Controls of={PageStories} />

# List

<Primary of={ListStories} />
<Controls of={ListStories} />
```

## Importing markdown

```mdx
import { Markdown } from "@storybook/addon-docs/blocks";
import Readme from "../README.md?raw";

<Markdown>{Readme}</Markdown>
```

Useful for rendering a README or CHANGELOG as part of the docs.

## Linking between pages/stories

URL pattern — `?path=/docs/<id>` for a docs page, `?path=/story/<id>` for a story:

```md
[Go to the docs page](?path=/docs/components-button--docs)
[Anchor inside a docs page](?path=/docs/components-button--docs#usage)
[Go to a specific story](?path=/story/components-button--primary)
```

Note: on Canvas pages, URL anchors (`#...`) are ignored because Storybook uses the URL for args tracking.

## Troubleshooting

### Tables not rendering

Default MDX is CommonMark (no GFM tables). Enable `remark-gfm`:

```ts
addons: [
  {
    name: '@storybook/addon-docs',
    options: {
      mdxPluginOptions: {
        mdxCompileOptions: {
          remarkPlugins: [remarkGfm],
        },
      },
    },
  },
],
```

Install `remark-gfm` as a dev dependency (not bundled by default).

### MDX page not showing

- Check the `stories` glob includes `'../src/**/*.mdx'`.
- If you're overriding an Autodocs page with MDX, remove the `autodocs` tag on that component to avoid duplicate entries / errors.
- In monorepos, `npx @hipster/mdx2-issue-checker` can locate malformed files.

### Controls not driving the story

Only a problem if `parameters.docs.story.inline: false` is set. Known limitation.

### VS Code support

Install the MDX extension (`unifiedjs.vscode-mdx`) and add:

```json
{ "mdx.server.enable": true }
```

for linting, type checking, auto-completion.
