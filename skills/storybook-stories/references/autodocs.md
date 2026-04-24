# Autodocs

Autodocs generates a documentation page automatically from a story file: header (title/subtitle/description), the primary story, a live Controls table, and all other stories.

## Enable

Autodocs is driven by the `autodocs` **tag**, not a flag. Most projects enable it globally in `preview.ts` and opt out per-file as needed:

```ts
// .storybook/preview.ts
const preview: Preview = {
  tags: ["autodocs"], // all files get a Docs page
};
export default preview;
```

Opt out per file:

```ts
const meta = {
  component: Page,
  tags: ["!autodocs"],
} satisfies Meta<typeof Page>;
```

Opt out per story (still keeps the component's Docs page, but hides this story from it):

```ts
export const UndocumentedStory: Story = { tags: ["!autodocs"] };
```

## Configure

Global options in `main.ts`:

```ts
const config: StorybookConfig = {
  addons: ["@storybook/addon-docs"],
  docs: {
    defaultName: "Documentation", // default is 'Docs'
    docsMode: true, // sidebar shows only docs pages, not stories
  },
};
```

## Custom template

Override the default page by providing a `page` function returning a React component (using Doc Blocks). Set it in `preview.ts`:

```tsx
import {
  Title,
  Subtitle,
  Description,
  Primary,
  Controls,
  Stories,
} from "@storybook/addon-docs/blocks";

const preview: Preview = {
  parameters: {
    docs: {
      page: () => (
        <>
          <Title />
          <Subtitle />
          <Description />
          <Primary />
          <Controls />
          <Stories />
        </>
      ),
    },
  },
};
```

This is approximately the default template; reorder or omit blocks to customize.

### MDX template

For non-React projects (or to write the template in Markdown), create an MDX file with `isTemplate` on its `Meta`:

```mdx
{/* DocumentationTemplate.mdx */}
import { Meta, Controls, Primary, Stories, Subtitle, Title } from '@storybook/addon-docs/blocks';

<Meta isTemplate />

<Title />
<Subtitle />

## Default implementation

<Primary />

## Inputs

<Controls />

## Additional variations

<Stories />
```

```ts
// preview.ts
import DocumentationTemplate from "./DocumentationTemplate.mdx";
const preview = {
  parameters: { docs: { page: DocumentationTemplate } },
} satisfies Preview;
```

## Table of contents

```ts
parameters: {
  docs: {
    toc: true;
  }
}
```

Options:

| Option | Description |
|---|---|
| `contentsSelector` | CSS selector for the container to search for headings |
| `disable` | Hide ToC for this scope |
| `headingSelector` | Which headings to include (`'h1, h2, h3'`) |
| `ignoreSelector` | Selectors to ignore; defaults to ignore content inside Story blocks |
| `title` | Caption (string / React element / null) |
| `unsafeTocbotOptions` | Raw [Tocbot](https://tscanlin.github.io/tocbot/) config |

Override per-component:

```ts
const meta = {
  component: MyComponent,
  tags: ["autodocs"],
  parameters: { docs: { toc: { disable: true } } },
} satisfies Meta<typeof MyComponent>;
```

Known limitations: ToC hides on screens under 1200px; doesn't render if only one matching heading; can't customize ToC on unattached MDX pages (lacks parameter support).

## Documenting multiple components

```tsx
const meta = {
  component: List,
  subcomponents: { ListItem },
} satisfies Meta<typeof List>;
```

Main component and subcomponents show up as tabs in the `ArgTypes` block. For richer grouped docs, prefer MDX.

## Custom theme

```ts
import { themes } from "storybook/theming";
import { ensure } from "@storybook/addon-docs/blocks";

const preview: Preview = {
  parameters: { docs: { theme: ensure(themes.dark) } },
};
```

## Addon options

```ts
addons: [
  {
    name: '@storybook/addon-docs',
    options: {
      csfPluginOptions: null, // disable CSF plugin if needed
      mdxPluginOptions: {
        mdxCompileOptions: { remarkPlugins: [] },
      },
    },
  },
],
```

## Monorepo gotchas

If Autodocs isn't generating for some components, two fixes:

1. **Import directly from the component file, not the package root**:

   ```ts
   // ❌ import { MyComponent } from '@my-package';
   // ✅ import { MyComponent } from '@my-package/dist/MyComponent';
   ```

2. **Switch the prop extractor** in `main.ts`:

   ```ts
   typescript: { reactDocgen: 'react-docgen', check: false }
   ```

   `react-docgen-typescript` is more detailed but struggles with some monorepo imports; `react-docgen` is faster and more forgiving.

## Not updating controls for non-inline stories

If `parameters.docs.story.inline: false` is set, Controls in the docs page don't drive the rendered story. Known limitation.
