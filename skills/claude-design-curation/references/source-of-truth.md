# What the repo side must get right

`/design-sync` owns the build, but several of its defaults produce a project
that *looks* synced and is not usable. Each of these shipped green.

## Comments only survive into `tokens/`

Everything shipped is minified. A palette with 89 comments in source reaches
`_ds_bundle.css` with **zero**. So a per-token annotation the Design app is
meant to read — `/* @kind other */` and the like — cannot travel that way, and
annotating the source alone changes nothing.

`cfg.tokensGlob` is the one path that copies a file **verbatim** into `tokens/`
and has `styles.css` import it. That is where annotations survive.

Two traps in using it:

- `copyTokens` returns early unless `cfg.tokensPkg` is also set. For a repo that
  is its own package, the `node_modules` self-link resolves — set
  `tokensPkg` to the package name and give `tokensGlob` a repo-relative path.
- **`styles.css` imports `tokens/` unlayered**, and unlayered beats every
  layered rule. Palette files are usually tokens *plus* global element rules
  (`body`, `h1`–`h3`, `code`, `:focus-visible`). Copying one whole lets those
  defaults override the component layer in every rendered design. Publish an
  extract of the `:root` block alone, generated at build time so it cannot
  drift from the source, and fail the build if a nested rule ever appears in it.

Verify it changed nothing: render hashes should be untouched and every grade
should carry forward. If they do, the tokens file is purely additive.

## The converter never runs `cfg.buildCmd`

`buildCmd` is a recorded config key and nothing more — `grep -rn buildCmd`
across the tool finds it only in the list of known keys. The same goes for any
declaration build. `package-build.mjs` on its own will happily ship yesterday's
CSS and yesterday's `.d.ts`, and the only symptom is a fix that "didn't apply".

Run the CSS build, then the declaration build, then `package-build.mjs`, in that
order, every time styles or prop types changed. When a style fix seems not to
land, check the mtime of the `cssEntry` file before anything else.

## Contracts that reference types they never define

Upstream `lib/dts.mjs` always returns `prelude: ''`, so an emitted contract can
say `invite: InviteOut` with `InviteOut` defined nowhere in the file. The agent
learns the prop's name and nothing about its shape — the same wall a human hits.

Fill the prelude in a `.design-sync/overrides/dts.mjs` fork. Three things are
load-bearing and each was a separate bug:

- Resolution is a **fixpoint**. An inlined type names types of its own.
- Placeholders carry **arity and namespace structure**. `ComponentRenderFn<A, B>`
  needs two parameters; `SheetPrimitive.Handle<T>` needs `declare namespace`.
- Opaque bodies are **`Record<string, unknown>`, not `unknown`**, because
  `keyof unknown` is `never` and `Pick<Opaque, "k">` is a real prop shape.

Gate it with a type-check over the emitted `.d.ts` files, and set
**`skipLibCheck: false`** — every input is a declaration file, so the usual
`true` makes the check inert and it passes on a bundle with dozens of broken
contracts. Inject a deliberately-broken canary each run and fail if the canary
does not error.

## Data-bound components need the bundle's own providers

A preview cannot supply React Query or Router context by importing those
libraries itself: it bundles its own copy while the component runs from the copy
inlined in `_ds_bundle.js`, so the two context objects differ and the component
throws.

Export the providers from a small module merged onto the same global via
`cfg.extraEntries`. Then two follow-ons: they are PascalCase, so exclude them
with `cfg.componentSrcMap` or they get cards of their own; and they must appear
in the declaration tree or every preview importing them fails type-check.

## A story may not build context the published component consumes

The same two-copies rule bites from the other side, and this one renders blank
rather than throwing, so nothing in the build says why.

A preview module resolves **component** imports to the published global; every
other import is bundled fresh into that module. So a story that mounts a
provider it imported directly — `<Toast.Provider>`, a theme provider, any
library context — hands the published component a context object from a
*different* copy of that library. The component reads an empty context and
renders nothing. Storybook, where there is only one copy, renders it perfectly,
so the two panels disagree permanently and the fix looks like a CSS problem.

Tell it apart from a genuine blank by dumping the rendered DOM: the provider's
own side-effects are there (a live region holding the toast text) while the
component's output is empty. That is the signature.

The fix is to move the provider-mounting surface *into* the component module
and publish it, so both halves resolve through one copy. That is a real export
in application code, so give it a name and a doc comment that say it documents
the component — it is the seam that makes the card honest, not a test hook.

## Serve fixtures at the `fetch` boundary

Seeding the query cache does not work — generated query options carry their own
`queryFn`, so a client-level default never runs, and the generated key embeds
the client's base URL, which is guesswork to reconstruct.

Stubbing `fetch` sidesteps both and is higher fidelity: the request goes through
the real client, its interceptors and the generated response validators, so a
fixture that does not match the server contract fails loudly instead of looking
fine. Expect it to catch invented ids, invented enum values and missing required
fields on the first run — that is the check working, not an obstacle.
