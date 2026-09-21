# Writing the generator: ten holes to close

A gate that reports green while a component is mis-declared is worse than no
gate. Every one of these produced a false green in review:

1. **Scan what Storybook scans.** Its glob is usually `*.stories.@(ts|tsx)`;
   reading only `.tsx` lets an untagged `.ts` story ship unseen.
2. **Reject tag arrays you cannot fully read.** Filtering non-literals out of
   `["ds:control", ...spread]` silently accepts a second, hidden kind.
3. **Resolve the default export.** Storybook reads `export default`, so a local
   `const meta` that is not the exported object describes nothing.
4. **Handle every export form** — `export { Story }` lists and parenthesized
   initializers, not just `export const`.
5. **Validate tags by scope and spelling.** A misspelled story tag must not read
   as "nothing declared", and a meta-level story tag must be an error.
6. **Derive the component key exactly as the consumer does.** It strips
   whitespace, applies `titleMap`, and walks *earlier* title segments against
   the set of real exports. An override under a key no card reads is silent.
7. **Reject two files claiming one key.** The consumer merges their stories into
   one card; your generator would pick one policy and drop the other.
8. **Require `primaryStory` exports to be PascalCase** — the preview exporter
   capitalizes story keys, and the card matches case-sensitively before
   silently falling back to the first story.
9. **Look kinds up with `Object.hasOwn`.** `ds:constructor` and `ds:toString`
   reach `Object.prototype` and read as valid kinds.
10. **Carry `skip` forward.** `cfg.overrides.<Name>.skip` is hand-written and
    records that a story cannot render statically — a capability fact, not a
    presentation choice, so nothing in your tag vocabulary can derive it. A
    generator that rebuilds `overrides` from tags alone **deletes every `skip`
    on its first run**, silently. This is the only hole on this list that
    destroys someone's work rather than merely reporting a false green, so
    read the existing config and re-emit those entries untouched.

Prove each one: write the broken story to a temp file, run the gate, assert it
fails, delete the file.
