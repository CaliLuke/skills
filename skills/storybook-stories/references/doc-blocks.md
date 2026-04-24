# Doc Blocks

Doc Blocks are React components imported from `@storybook/addon-docs/blocks`. Used in two places:

1. **Inside MDX files** — embed blocks in prose.
2. **In custom Autodocs templates** — define `parameters.docs.page` as a function returning JSX.

Doc Blocks **do not** work inside CSF story render functions. Using them there throws a cryptic error. If you need those visuals (e.g., a color palette) in a "story", write an MDX docs page instead.

## Customization via parameters

Most blocks accept customization through `parameters.docs.<blockName>.*` at global, component, or story level. For example, exclude a prop from all Controls tables:

```ts
// .storybook/preview.ts
const preview: Preview = {
  parameters: { docs: { controls: { exclude: ["style"] } } },
};
```

Within MDX, pass customizations as props:

```mdx
<Controls exclude={["style"]} />
```

Note: because `Canvas` internally renders a `Source` block, customizing `parameters.docs.source` also affects the auto-generated source in `Canvas`.

## Available blocks

### Structure / headers

| Block         | Purpose                                                                                                                    |
| ------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `Title`       | Primary heading (component/page name)                                                                                      |
| `Subtitle`    | Secondary heading                                                                                                          |
| `Description` | Component/story description from JSDoc                                                                                     |
| `Meta`        | In MDX: attach docs to a component's stories (via `of=`), or set sidebar location (via `title=`). Doesn't render anything. |

### Stories

| Block     | Parameters namespace | Purpose                                              |
| --------- | -------------------- | ---------------------------------------------------- |
| `Primary` | —                    | Renders the first (primary) story in a `Story` block |
| `Story`   | `docs.story`         | Render a single story with annotations applied       |
| `Canvas`  | `docs.canvas`        | `Story` + toolbar + auto `Source`                    |
| `Stories` | —                    | Render the full collection of stories in the file    |

### Interfaces

| Block      | Parameters namespace | Purpose                                      |
| ---------- | -------------------- | -------------------------------------------- |
| `ArgTypes` | `docs.argTypes`      | Static table of arg types                    |
| `Controls` | `docs.controls`      | Dynamic controls table that drives the story |
| `Source`   | `docs.source`        | Rendered source code snippet                 |

### Design system building blocks

| Block                             | Purpose                                  |
| --------------------------------- | ---------------------------------------- |
| `ColorPalette` (with `ColorItem`) | Document colors / swatches               |
| `IconGallery` (with `IconItem`)   | Grid of icons                            |
| `Typeset`                         | Document fonts at multiple sizes/weights |
| `Markdown`                        | Import/render a `.md` file inline        |

### Navigation / layout

| Block             | Parameters namespace | Purpose                                                    |
| ----------------- | -------------------- | ---------------------------------------------------------- |
| `TableOfContents` | `docs.toc`           | Fixed sidebar ToC on the right                             |
| `Unstyled`        | —                    | Disable Storybook's default MDX styles for wrapped content |

## Default Autodocs template

For reference, the default template is approximately:

```tsx
import {
  Title,
  Subtitle,
  Description,
  Primary,
  Controls,
  Stories,
} from "@storybook/addon-docs/blocks";

() => (
  <>
    <Title />
    <Subtitle />
    <Description />
    <Primary />
    <Controls />
    <Stories />
  </>
);
```

Override via `parameters.docs.page` in `preview.ts`.

## Making custom blocks

`useOf` hook from `@storybook/addon-docs/blocks` gives you the same CSF metadata the built-in blocks consume. Only reach for this when existing blocks can't cover the need — consuming the hook is lower-level than most docs tasks require.

---

## Code panel

Separate feature, closely related to the `Source` block. Code Panel shows a story's source (with args resolved) in the Canvas toolbar — a replacement for the removed Storysource addon.

Enable globally:

```ts
// .storybook/preview.ts
const preview: Preview = { parameters: { docs: { codePanel: true } } };
```

Or per component/story:

```ts
const meta = {
  component: Button,
  parameters: { docs: { codePanel: true } },
} satisfies Meta<typeof Button>;

export const Secondary: Story = {
  args: { variant: "secondary" },
  parameters: { docs: { codePanel: false } }, // opt this one out
};
```

Same `parameters.docs.source` config controls snippet generation (language, code transforms, etc.), so customizing `Source` also customizes Code Panel output.

---

## Building and publishing docs

`package.json`:

```jsonc
{
  "scripts": {
    "storybook-docs": "storybook dev --docs",
    "build-storybook-docs": "storybook build --docs",
  },
}
```

Docs mode:

- Hides the toolbar.
- Flattens stories under their Docs page in the sidebar.
- Outputs to `storybook-static/` for `build --docs`.

Deploy the static folder anywhere (Vercel, Netlify, S3).
