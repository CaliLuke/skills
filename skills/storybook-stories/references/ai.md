# Stories and docs for AI agents

Storybook v10+ generates JSON **manifests** describing the components and docs in your Storybook. Tools like Storybook's MCP server consume these to give AI agents knowledge about your UI library. The two manifests are:

- **Components manifest** — `/manifests/components.json` — from static analysis of CSF files + component prop types.
- **Docs manifest** — `/manifests/docs.json` — from static analysis of MDX files.

Both manifests are available at those paths in a running dev server (default `http://localhost:6006/manifests/...`) and in a built Storybook. Debugger at `/manifests/components.html` shows both in a human-readable form with any warnings encountered.

Currently React-only and in preview; schema is not yet stable.

## Writing stories the agent can use

Agents consume stories as _examples of when and why to use a component_. A story demonstrating five unrelated things teaches nothing specific. Prefer one concept per story:

```ts
// ✅ One concept: the default
export const Basic: Story = {};

// ✅ One concept: the primary variant
export const Primary: Story = {
  args: { primary: true },
};

// ✅ One concept: disabled — even though it renders two buttons,
// both demonstrate the same idea
export const Disabled: Story = {
  render: () => (
    <>
      <Button disabled>Disabled</Button>
      <Button disabled primary>Disabled Primary</Button>
    </>
  ),
};

// ❌ Kitchen sink — teaches nothing specific
export const SizesAndVariants: Story = {
  render: () => (
    <>
      <Button size="sm">Small</Button>
      <Button size="md">Medium</Button>
      <Button size="lg">Large</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="text">Text</Button>
    </>
  ),
};
```

## JSDoc that ends up in the manifest

### Component description

```ts
// Button.tsx
/**
 * Button is used for user interactions that do not navigate to another route.
 * For navigation, use Link instead.
 *
 * @summary for user interactions that do not navigate to another route
 */
export const Button = (props: ButtonProps) => {
  /* ... */
};
```

Agent receives the `@summary` if present, otherwise a truncation of the description.

### Prop descriptions

```ts
export interface ButtonProps {
  /** The icon to render before the button text */
  icon?: ReactNode;
  /** Optional click handler */
  onClick?: () => void;
}
```

Pair this with `react-docgen-typescript` in `main.ts` for rich type extraction:

```ts
typescript: {
  reactDocgen: "react-docgen-typescript";
}
```

Slower than `react-docgen` but much richer output. Only downgrade to `react-docgen` if manifest generation is painfully slow.

### Story description and summary

```ts
/**
 * Primary buttons are used for the main action in a view.
 * There should not be more than one primary button per view.
 *
 * @summary for the main action in a view
 */
export const Primary: Story = {
  args: { primary: true },
};
```

Explain **why**, not **what**. The story itself shows what; the JSDoc is the prose an agent needs to pick the right component for the task.

### MDX docs summary

Unattached MDX (design tokens, guidelines) should carry a summary on the `Meta`:

```mdx
<Meta
  title="Design System/Colors"
  summary="color tokens and how to pick them"
/>
```

## What doesn't end up in the manifest

The docs manifest is **static analysis** of MDX — the MDX is not executed. So:

```mdx
import { colors } from "./tokens";

# Colors

<ColorPalette>
  {colors.map((c) => (
    <ColorItem key={c.name} {...c} />
  ))}
</ColorPalette>
```

The color values never appear in the manifest because they're computed at render time. If an agent needs them, include them literally in the MDX (`red: #f00`, `blue: #00f` ...).

## Curating the manifest

Every story and docs page implicitly has the `manifest` tag. Remove it to exclude from the manifest — valuable for anti-pattern demos, deprecated components, or instructional-only stories that would confuse an agent.

Per story:

```ts
export const ForInstructionOnly: Story = { tags: ["!manifest"] };
```

Per component (excludes all stories in the file):

```ts
const meta = {
  component: MyComponent,
  tags: ["!manifest"],
} satisfies Meta<typeof MyComponent>;
```

Per MDX page:

```mdx
<Meta title="Internal Guide" tags={["!manifest"]} />
```

## Debugging

Run Storybook, open `http://localhost:6006/manifests/components.html`. The debugger shows every component/docs entry, any extraction warnings, and lets you filter to the problematic entries.

If an agent isn't using a component well, check the debugger — usually the issue is missing JSDoc, missing prop descriptions, or a too-cute "kitchen sink" story the agent is trying to emulate.
