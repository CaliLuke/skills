# Naming, hierarchy, and sort order

Storybook builds the sidebar from two sources: the file path (implicit) or the meta's `title` (explicit). Pick one scheme and stick to it.

## Hierarchy anatomy

Sidebar from top to bottom:

- **Root** — the top-level grouping, rendered uppercased and non-expandable by default. Disable via sidebar config (see [Roots](https://storybook.js.org/docs/configure/user-interface/sidebar-and-urls.md#roots)) if you want a flatter look.
- **Category** / **Folder** — intermediate groupings created by `/` in the title (or nested directories).
- **Component** — one per story file.
- **Docs** — an auto-generated docs page (when `autodocs` tag applies).
- **Story** — one per named export.

## Implicit titles (preferred)

Omit `title`. Storybook infers it from the file path per the `stories` glob in `.storybook/main.ts`. `src/components/Button/Button.stories.tsx` → `Components/Button` (exact mapping depends on [auto-title config](https://storybook.js.org/docs/configure/user-interface/sidebar-and-urls.md#csf-30-auto-titles)). Advantages: filesystem and sidebar stay in sync, renames are free, no duplicated source of truth.

## Explicit titles

```ts
const meta = {
  title: "Design System/Atoms/Button",
  component: Button,
} satisfies Meta<typeof Button>;
```

Use `/` to nest. Reach for this only when your sidebar structure should intentionally diverge from the filesystem — e.g., curating a public "Design System" view, or grouping cross-package components.

Don't mix implicit and explicit in the same project; it produces unpredictable sidebar layouts.

## Single-story hoisting

Rule: if a file exports **exactly one** named story and that story's display name (start-cased export name) matches the **last segment of the title** (or the component name for implicit titles), Storybook hoists the story to replace its parent in the sidebar.

```ts
const meta = {
  title: "Design System/Atoms/Button",
  component: ButtonComponent,
} satisfies Meta<typeof ButtonComponent>;

// Lone export named Button → title resolves to `Design System/Atoms/Button`
// (one leaf), not `Design System/Atoms/Button/Button` (nested).
export const Button: Story = {};
```

Consequences:

- Adding a second story **undoes** hoisting. Expected; not a bug.
- Export names are start-cased: `myStory` → `"My Story"`. A lone story `button` under title `.../Button` won't hoist — either rename the export or override via `button.storyName = 'Button'`.
- Component name (from `component:`) is usually what you want the lone story export to match.

## Sorting

Default: import order. Customize in `.storybook/preview.ts` via `parameters.options.storySort`.

### Function form

Full control. Receives two entries with `{ id, title, name, importPath }`.

```ts
const preview: Preview = {
  parameters: {
    options: {
      storySort: (a, b) =>
        a.id === b.id
          ? 0
          : a.id.localeCompare(b.id, undefined, { numeric: true }),
    },
  },
};
```

### Object form

```ts
storySort: {
  method: 'alphabetical',      // or omit for import order
  order: ['Intro', 'Pages', ['Home', 'Login', 'Admin'], 'Components', '*', 'WIP'],
  includeNames: false,         // include story name (not just kind) in ordering
  locales: 'en-US',            // locale for alphabetical sort
}
```

Fields:

- `method` — `'alphabetical'` or omit for import order.
- `order` — custom list. Entries not in the list land wherever `'*'` is (or at the end if `'*'` is absent). Nested arrays sort 2nd-level kinds: `['Pages', ['Home', 'Login']]` puts Home/Login in that order under Pages.
- `includeNames` — by default, sorting considers the kind (title path) only; set `true` to include story name.
- `locales` — defaults to system locale.

`order` and `method` are independent: order runs first, then `method` (or import order) fills in the gaps.

Common pattern — pin `'WIP'` to the bottom:

```ts
order: ["Intro", "Components", "*", "WIP"];
```
