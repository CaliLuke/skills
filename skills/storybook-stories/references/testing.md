# Testing stories

Stories are reusable as test fixtures. Four places they show up as tests:

1. **Play functions** — post-render interaction scripts, run in Storybook UI.
2. **Portable stories** — import stories as React elements in Vitest / Jest / Playwright CT.
3. **Visual tests** — Chromatic takes pixel snapshots of every story.
4. **E2E** — Cypress / Playwright hit the story iframe URL directly.

## Play functions

A `play` function runs after the story renders. Use for interaction tests and setup-heavy stories (filled forms, open dialogs).

```ts
export const FilledForm: Story = {
  play: async ({ canvas, userEvent }) => {
    await userEvent.type(canvas.getByLabelText("email"), "a@b.com", {
      delay: 100,
    });
    await userEvent.type(canvas.getByLabelText("password"), "pw", {
      delay: 100,
    });
    await userEvent.click(canvas.getByRole("button"));
  },
};
```

### Querying

- `canvas` is a Testing-Library scoped to the story root. Use `canvas.getByRole`, `canvas.getByLabelText`, etc.
- For elements rendered outside the story root (a dialog portaled to `body`, a toast root), import `screen` from `storybook/test` to query the whole document.

```ts
import { screen, expect } from "storybook/test";

export const Open: Story = {
  play: async ({ canvas, userEvent }) => {
    await userEvent.click(canvas.getByRole("button", { name: "Open dialog" }));
    const dialog = screen.getByRole("dialog");
    await expect(dialog).toBeVisible();
  },
};
```

### Composing play functions

Reuse by calling another story's `play` with the current context:

```ts
export const FirstStory: Story = {
  play: async ({ canvas, userEvent }) => {
    await userEvent.type(canvas.getByTestId("an-element"), "example-value");
  },
};

export const CombinedStories: Story = {
  play: async ({ context, canvas, userEvent }) => {
    await FirstStory.play(context);
    await SecondStory.play(context);
    await userEvent.type(canvas.getByTestId("another-element"), "random value");
  },
};
```

Pattern: small leaf stories for single steps, composed stories for full flows. Keeps the flow discoverable in the sidebar while avoiding duplicated code.

## Portable stories — running stories in Vitest/Jest/Playwright CT

Storybook exports `composeStories` / `composeStory` from the framework package (e.g., `@storybook/react`). They compose your raw CSF exports with meta, global annotations, decorators, and args, producing runnable React elements.

### Setup — global annotations

Before composing stories, apply your `preview.ts` annotations once per test project. This is what makes global decorators, parameters, and loaders available:

```ts
// vitest.setup.ts
import { setProjectAnnotations } from "@storybook/react";
import * as preview from "../.storybook/preview";

setProjectAnnotations([preview]);
```

Without this step, stories render in isolation from your Storybook config and decorators won't apply.

### Using composed stories in tests

```ts
// Form.test.tsx
import { composeStories } from "@storybook/react";
import { fireEvent, screen } from "@testing-library/react";
import * as stories from "./Form.stories";

const { InvalidForm, ValidForm } = composeStories(stories);

test("Invalid form shows error", async () => {
  await InvalidForm.run();
  fireEvent.click(screen.getByRole("button", { name: "Submit" }));
  expect(screen.getByLabelText("invalid-form")).toBeInTheDocument();
});
```

`Story.run()` mounts the story (applying decorators, loaders, args, play function). Returns a promise — `await` it.

### Single story

```ts
const ValidForm = composeStory(ValidFormStory, Meta);
```

Always pass `Meta` (the default export) so the story inherits component-level config.

### Per-test overrides

Both `composeStories` and `composeStory` accept a third argument to override `decorators`, `parameters`, `globalTypes` for tests only:

```ts
const { ValidForm } = composeStories(stories, {
  decorators: [
    /* test-only wrappers */
  ],
  parameters: {
    /* ... */
  },
});
```

### Composed stories carry their metadata

The composed result exposes `.args`, `.parameters`, etc., so assertions can reference story values directly — no duplication:

```ts
render(<Primary />);
expect(screen.getByRole('button').textContent).toEqual(Primary.args.label);
```

### Snapshot testing

Snapshot tests are best kept narrow — DOM snapshots are noisy and hard to review (the class-name-only-diff problem). Useful for _non-visual_ invariants:

```ts
const { Primary } = composeStories(stories);

test("renders", async () => {
  await Primary.run();
  expect(document.body.firstChild).toMatchSnapshot();
});
```

Visual tests are strictly better for appearance regressions. Reserve snapshots for error-boundary checks and similar non-visual cases.

### Asserting a thrown error

To test an error-throwing story, exclude it from sidebar (`!dev`) and from auto-run (`!test`):

```ts
export const ThrowError = {
  tags: ["!dev", "!test"],
  args: { doNotUseThisItWillThrowAnError: true },
};
```

```ts
test("throws", async () => {
  await expect(ThrowError.run()).rejects.toThrowError("I tried to tell you...");
});
```

## Visual tests — Chromatic

Install the addon, and every story becomes a cross-browser visual test:

```bash
npx storybook@latest add @chromatic-com/storybook
```

First run sets baselines; subsequent runs diff against them. Accept intentional changes in the Visual Tests panel; push to sync baselines. Use the addon in local dev for quick catch-and-fix; wire Chromatic into CI for the authoritative gate. Accepted baselines from local auto-accept in CI.

Configure in `./chromatic.config.json`:

```json
{
  "projectId": "Project:abc123",
  "buildScriptName": "build-storybook",
  "zip": true
}
```

## E2E — Cypress / Playwright

Stories have stable URLs like `http://localhost:6006/iframe.html?id=components-login-form--filled-form`. Hit those directly from E2E tests. If the story has a `play` function, the app is already in the post-play state by the time your E2E script starts asserting.

Cypress:

```js
describe("Login Form", () => {
  it("has valid credentials pre-filled", () => {
    cy.visit("/iframe.html?id=components-login-form--filled-form");
    cy.get("#email").should("have.value", "email@provider.com");
  });
});
```

Playwright:

```js
test("Login form pre-filled", async ({ page }) => {
  await page.goto(
    "http://localhost:6006/iframe.html?id=components-login-form--filled-form",
  );
  await expect(await page.inputValue("#email")).toBe("email@provider.com");
});
```

Rule of thumb for picking a test kind:

- **Play function + Storybook Test/Interactions** — interaction correctness.
- **Portable stories in Vitest/Jest** — unit/integration assertions; deep DOM queries.
- **Visual tests** — appearance.
- **Snapshot tests** — non-visual invariants (errors, specific DOM structure).
- **E2E** — flows that cross pages/services; use portable stories first if you can.
