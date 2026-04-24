# TypeScript for stories

Use Storybook's built-in `Meta` and `StoryObj` utility types. Zero config needed.

## The canonical shape

```ts
import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "./Button";

const meta = {
  component: Button,
} satisfies Meta<typeof Button>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Basic = {} satisfies Story;

export const Primary = {
  args: { primary: true },
} satisfies Story;
```

Two reasons this shape is preferred:

1. **`satisfies Meta<typeof Button>` preserves the precise type** of `meta`. With `const meta: Meta<typeof Button> = ...` the type widens to the annotation, and `StoryObj<typeof meta>` can no longer tell which args are already provided at the meta level — you get spurious "required arg missing" errors at the story level.
2. **`type Story = StoryObj<typeof meta>`** — always derive from `typeof meta`, never from the component type directly. That connection is what lets TS know meta-level args satisfy story-level requirements.

## Meta generic parameter

`Meta<typeof Button>` and `Meta<ButtonProps>` both work. Use `typeof Component` when possible — it's less noisy and keeps automatic tracking when the component's type changes.

## Typing custom args (args that aren't real props)

If a story adds args that aren't real component props (e.g., a `footer` string the story renders into a slot), use an intersection type and pass it to `Meta` explicitly:

```tsx
type PagePropsAndCustomArgs = React.ComponentProps<typeof Page> & {
  footer?: string;
};

const meta = {
  component: Page,
  render: ({ footer, ...args }) => (
    <Page {...args}>
      <footer>{footer}</footer>
    </Page>
  ),
} satisfies Meta<PagePropsAndCustomArgs>;

export default meta;

type Story = StoryObj<typeof meta>;

export const CustomFooter = {
  args: { footer: "Built with Storybook" },
} satisfies Story;
```

Note: `Meta<PagePropsAndCustomArgs>` instead of `Meta<typeof Page>`. The `render` function destructures the extra arg and passes only the real props through.

## Stories typed `: Story` vs `satisfies Story`

Both work. `satisfies Story` gives stricter checks (e.g., helps TypeScript know the play function is defined when composing stories); `: Story` is shorter. Either is fine; pick one per project.

## When TS inference breaks

- **You used `:` instead of `satisfies` on `meta`.** Switch to `satisfies Meta<typeof Component>`.
- **`Story` derived from the component type.** Must be `StoryObj<typeof meta>`.
- **Custom args trigger errors.** Use an intersection type and pass it to `Meta<...>` explicitly.
- **Angular/Web Components: `satisfies` doesn't improve things.** Their class+decorator model doesn't expose required-vs-optional metadata at compile time. Use plain `Meta<typeof Component>` annotation.
