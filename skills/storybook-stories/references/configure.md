# Configuring Storybook

Three files do most of the work. Edit only the one that matches what you're changing.

| File                    | Purpose                                                                         | Runs in        |
| ----------------------- | ------------------------------------------------------------------------------- | -------------- |
| `.storybook/main.ts`    | Build/story-indexing config: framework, stories glob, addons, env, webpack/vite | Node           |
| `.storybook/preview.ts` | Story rendering: global decorators, parameters, args, loaders, global tags      | Preview iframe |
| `.storybook/manager.ts` | Storybook UI chrome: theme, toolbar visibility, sidebar options                 | Manager UI     |

Also:

- `preview-head.html` / `preview-body.html` — inject tags into the preview iframe (fonts, static CSS, `<div id="custom-root">`).
- `manager-head.html` — inject into the manager UI (favicon, ad-hoc CSS overrides).
- `.env` — `STORYBOOK_*` env vars, surfaced in the preview.

## main.ts

Stories glob, framework, addons. Also `viteFinal` / `webpackFinal` for build customization.

```ts
import type { StorybookConfig } from "@storybook/react-vite";

const config: StorybookConfig = {
  framework: "@storybook/react-vite",
  stories: ["../src/**/*.mdx", "../src/**/*.stories.@(js|jsx|mjs|ts|tsx)"],
  addons: ["@storybook/addon-docs", "@storybook/addon-a11y"],
  docs: { defaultName: "Docs" },
  typescript: { reactDocgen: "react-docgen-typescript" },
  viteFinal: async (config) => config,
};

export default config;
```

### Stories glob forms

- String glob: `'../src/**/*.stories.@(js|jsx|mjs|ts|tsx)'`
- Object (lets you prefix auto-titles):

  ```ts
  stories: [{ directory: "../src", titlePrefix: "Custom" }];
  ```

- Mixing is fine.

### Env vars

```ts
env: (config) => ({ ...config, EXAMPLE_VAR: 'value' }),
```

Access with `process.env.EXAMPLE_VAR` (Webpack) or `import.meta.env.EXAMPLE_VAR` (Vite). Any env var prefixed with `STORYBOOK_` is auto-exposed. Never put secrets here — they're embedded in the build.

## preview.ts — rendering every story

```ts
import type { Preview } from '@storybook/react';
import './global.css'; // global CSS, subject to HMR

initialize(); // library init that must run before components render

const preview: Preview = {
  tags: ['autodocs'],
  parameters: {
    layout: 'centered', // 'centered' | 'fullscreen' | 'padded' (default)
    backgrounds: {
      options: {
        light: { name: 'Light', value: '#fff' },
        dark:  { name: 'Dark',  value: '#333' },
      },
    },
    docs: { toc: true, codePanel: true },
  },
  args: { theme: 'light' },
  decorators: [
    (Story) => (
      <ThemeProvider theme={theme}>
        <Story />
      </ThemeProvider>
    ),
  ],
  loaders: [/* async data fetchers — escape hatch only */],
};

export default preview;
```

### Layout

`parameters.layout` — one of `'centered'`, `'fullscreen'`, `'padded'` (default). Override per component or per story:

```ts
const meta = {
  component: Button,
  parameters: { layout: "centered" },
} satisfies Meta<typeof Button>;
```

### Styles and fonts

- Import CSS modules / global CSS directly in `preview.ts` (HMR-friendly).
- Static CSS that shouldn't go through HMR (e.g., hosted webfont stylesheets): add `<link>` tags to `.storybook/preview-head.html`.
- Custom content roots (`<div id="modal-root">`): add to `.storybook/preview-body.html`.
- CSS modules / PostCSS / Sass / Less: work out of the box with Vite. With Webpack, install `@storybook/addon-styling-webpack`.

## manager.ts — the Storybook UI chrome

```ts
import { addons } from "storybook/manager-api";
import { themes } from "storybook/theming";

addons.setConfig({
  theme: themes.dark,
  navSize: 300,
  bottomPanelHeight: 300,
  rightPanelWidth: 300,
  panelPosition: "bottom", // or 'right'
  showToolbar: true,
  enableShortcuts: true,
  sidebar: {
    showRoots: false, // treat top-level nodes as folders instead of "roots"
    collapsedRoots: ["other"],
    // renderLabel: ({ name, type }) => /* ReactNode */,
  },
  toolbar: {
    zoom: { hidden: false },
    fullscreen: { hidden: false },
  },
  layoutCustomisations: {
    showSidebar: (state, defaultValue) =>
      state.storyId === "landing" ? false : defaultValue,
    showToolbar: (state, defaultValue) =>
      state.viewMode === "docs" ? false : defaultValue,
    showPanel: (state, defaultValue) => {
      const tags = state.index?.[state.storyId]?.tags ?? [];
      return tags.includes("kitchensink") ? false : defaultValue;
    },
  },
});
```

Theme for Docs is separate — set `parameters.docs.theme` in `preview.ts`:

```ts
parameters: {
  docs: {
    theme: themes.dark;
  }
}
```

Hiding the sidebar via `showSidebar` breaks navigation unless the page provides its own — only do it on landing/docs pages that have other nav.

## Story IDs and permalinks

Storybook generates each story's ID from the title and the export name: `Foo/Bar` + `Baz` → `foo-bar--baz`. URL is `?path=/story/foo-bar--baz`.

To rename a title/story without breaking inbound links, pin the ID explicitly:

```ts
const meta = {
  title: "NewTitle/Bar",
  component: Foo,
  id: "Foo/Bar", // or 'foo-bar' — preserves old URL
} satisfies Meta<typeof Foo>;

export const Baz: Story = {
  name: "Display name here", // overrides the export name in the UI
};
```

## Auto-title behavior (v6.5+)

- File name casing is preserved (no more `startCase`). `MyComponent.stories.tsx` → `MyComponent`.
- Redundant names are collapsed: `components/MyComponent/MyComponent.stories.tsx` → `Components/MyComponent`, not `Components/MyComponent/MyComponent`. `index.stories.tsx` also collapses.
- To force the old behavior per file, set `title:` explicitly.

## Theming quickstart

Generate a theme with `create()`:

```ts
// .storybook/YourTheme.ts
import { create } from "storybook/theming";

export default create({
  base: "light", // required
  brandTitle: "My Storybook",
  brandUrl: "https://example.com",
  brandImage: "https://…/logo.png",
  brandTarget: "_self",
  // colors, typography, etc.
});
```

```ts
// .storybook/manager.ts
import { addons } from "storybook/manager-api";
import yourTheme from "./YourTheme";

addons.setConfig({ theme: yourTheme });
```

Themes are replaced wholesale, not merged — include `base: 'light'` or `base: 'dark'` and override from there.

## Telemetry opt-out

Anonymous usage telemetry is on by default. Opt out:

```ts
// .storybook/main.ts
core: {
  disableTelemetry: true;
}
```

Or `STORYBOOK_DISABLE_TELEMETRY=1` env var / `--disable-telemetry` CLI flag.
