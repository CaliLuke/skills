# Args, parameters, decorators, loaders

These four concepts share the same structure: each can be defined at **global** (`.storybook/preview.ts`), **component** (meta default export), or **story** level, with later (more specific) levels overriding earlier ones. Learn the pattern once, apply it to all four.

## Args — the data that drives a story

Args are a JSON-serializable object whose keys match component props (plus any custom args). Changing an arg re-renders the component, which is what powers Controls, Actions, and URL sharing.

```ts
// Story-level (most specific)
export const Primary: Story = {
  args: { primary: true, label: "Button" },
};

// Component-level (defaults for all stories in the file)
const meta = {
  component: Button,
  args: { primary: true },
  argTypes: { backgroundColor: { control: "color" } },
} satisfies Meta<typeof Button>;

// Global (defaults for every story in the project)
// .storybook/preview.ts
const preview: Preview = {
  args: { theme: "light" },
};
```

### Composing args between stories

```ts
export const Primary: Story = { args: { primary: true, label: "Button" } };

export const Secondary: Story = {
  args: { ...Primary.args, primary: false },
};
```

Note: when using `satisfies` the `.args` property is typed precisely, so `...Primary.args` spreads cleanly.

### Custom args (not real props)

Use an intersection type and a `render` that destructures — see `typescript.md`.

### URL-driven args

`?args=size:100;variant:primary` overrides initial args for the active story. Limited to alphanumerics, spaces, `_`, `-`. Special forms: `!null`, `!undefined`, `!date(ISO)`, `!hex(RRGGBB)`, `!rgba(...)`, `!hsla(...)`. Nested keys via `obj.key:val`, arrays via `arr[0]:one`.

### `useArgs` — mutating args from inside a story

For interactive stories (e.g., a controlled checkbox), the render function needs to update args so Storybook reflects the change:

```tsx
import { useArgs } from "storybook/preview-api";

export const Example: Story = {
  args: { isChecked: false, label: "Try Me!" },
  render: function Render(args) {
    const [{ isChecked }, updateArgs] = useArgs();
    return (
      <Checkbox
        {...args}
        isChecked={isChecked}
        onChange={() => updateArgs({ isChecked: !isChecked })}
      />
    );
  },
};
```

Don't mix Storybook's `useArgs`/`useState`/`useEffect` (from `storybook/preview-api`) with React's hooks of the same name inside a story render — re-renders bypass Storybook's hook context and will throw.

### `mapping` for complex arg values

JSX or non-serializable values can't travel through Controls or the URL. Keep the control values simple strings, then map to the real value:

```ts
argTypes: {
  label: {
    control: { type: 'select' },
    options: ['Normal', 'Bold', 'Italic'],
    mapping: {
      Bold: <b>Bold</b>,
      Italic: <i>Italic</i>,
    },
  },
}
```

Keys in `mapping` are arg **values**, not indexes. Unmapped values pass through unchanged.

## Parameters — static metadata for features/addons

Unlike args, parameters are not serialized into URL or Controls; they configure _how_ Storybook renders or behaves — backgrounds, viewport, docs, addon settings.

```ts
// Story
export const Primary: Story = {
  parameters: {
    backgrounds: { options: { red: { name: "Red", value: "#f00" } } },
  },
};

// Component
const meta = {
  component: Button,
  parameters: { layout: "centered" },
} satisfies Meta<typeof Button>;

// Global — .storybook/preview.ts
const preview: Preview = {
  parameters: {
    backgrounds: { options: { light: { name: "Light", value: "#fff" } } },
  },
};
```

### Merge semantics

Parameters are **merged**, not replaced. A story-level `docs: { toc: { disable: true } }` overrides just that sub-key; all other docs parameters from component and global levels remain. Keep this in mind when designing addon APIs — don't rely on full-object replacement.

## Decorators — wrap stories with context or markup

Decorators take the rendered `Story` and return wrapped JSX. Used for layout padding, theme providers, router contexts, mocked services.

```tsx
// Story decorator — innermost
export const Primary: Story = {
  decorators: [
    (Story) => (
      <div style={{ margin: "3em" }}>
        <Story />
      </div>
    ),
  ],
};

// Component decorator
const meta = {
  component: Button,
  decorators: [
    (Story) => (
      <ThemeProvider>
        <Story />
      </ThemeProvider>
    ),
  ],
} satisfies Meta<typeof Button>;

// Global decorator — outermost
const preview: Preview = {
  decorators: [
    (Story) => (
      <QueryProvider>
        <Story />
      </QueryProvider>
    ),
  ],
};
```

### Running order

Global → component → story, with story decorators innermost. If you define multiple decorators at the same level, they apply in the order listed (innermost first within each level).

### Reading context to parameterize a decorator

The second argument is the story context: `{ args, argTypes, globals, parameters, viewMode, hooks }`. Common pattern — a conditional layout based on a parameter:

```tsx
decorators: [
  (Story, { parameters }) => {
    switch (parameters.pageLayout) {
      case "page":
        return (
          <div className="page-layout">
            <Story />
          </div>
        );
      case "page-mobile":
        return (
          <div className="page-mobile-layout">
            <Story />
          </div>
        );
      default:
        return <Story />;
    }
  },
];
```

This pattern — decorator reads a parameter — is how most themable/contextual Storybook features work.

### Pure stories + decorators

Keep the story render function a clean rendering of the component under test. Move wrapper markup into decorators so Doc Blocks like `Source` show code the user would actually write, not your Storybook harness.

## Loaders — async data fetched before render

Loaders run before the story renders. Their return values are merged into `context.loaded`, which render functions and decorators can read.

```tsx
export const Primary: Story = {
  loaders: [
    async () => ({
      todo: await (await fetch("/api/todos/1")).json(),
    }),
  ],
  render: (args, { loaded: { todo } }) => <TodoItem {...args} todo={todo} />,
};
```

### Scoping and precedence

Global / component / story loaders **all run, in parallel**, not just the most specific one. Results merge; on key conflicts, specificity wins (story > component > global).

### When NOT to use loaders

Loaders are an escape hatch. If the data can be an arg, use an arg — args participate in Controls, URL sharing, Autodocs, visual tests, and portable stories. Loaders don't integrate with any of that. Typical valid uses: genuinely remote data you can't embed, asset preloading, lazy-loading a heavy dependency.
