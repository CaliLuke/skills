# `ds:escapes`: content that leaves its box

A component that positions content outside its own box wants `single`, but be
precise about why, because there are **two different failure modes** and they
look nothing alike:

- **`position: fixed` content is contained and cropped.** A grid cell is
  `overflow:hidden` *and* `transform:translateZ(0)` (`emit.mjs`'s `.ds-cell`),
  so it is already a containing block: a fixed descendant resolves against the
  cell, not the viewport, and is then clipped at its edge. A full-bleed bar
  sizes itself to a ~330px cell and gets cut off. The converter's own comment
  is explicit that clipping "degrades to a **cropped** preview instead of a
  broken card".
- **A portal to `<body>` is not in the cell at all.** Nothing contains or clips
  it, so it paints over the page and over neighbouring cells.

Both want `single`; only the second is destructive. Do not repeat the sloppy
version of this — "a cell clips and escaping content paints over its
neighbours" fuses the two and is self-contradicting, since content that clips
cannot also overpaint. An agent reasoning from the fused version mis-predicts
which components are affected.

This is a fact about how a component renders, not about what it represents, so
it is a modifier that forces `single` whatever the kind says. Expect to
discover members by measurement: tagging four components by what they
represented moved them to `column`, and the validator flagged all four the same
run with `[GRID_OVERFLOW] … (fixed/portal)`.

**Never decide this by reading the component. Only the validator knows.** The
overflow check runs only when the card mode is `grid` or `column`
(`package-validate.mjs` gates on `__dsMode`), which splits every component into
two states:

- **in `grid`/`column` and never flagged → verified.** The check ran and came
  back clean, repeatedly. Trust it.
- **in `single` → unverified, permanently.** The check never ran. A tag applied
  here is a one-way ratchet: no future run can contradict it.

So an `escapes` tag is only as good as a flag you can quote, and an inherited
one with no flag behind it is an assumption wearing a tag's clothes. To settle
it, remove the tag, rebuild, and read the validator — that is the whole
procedure, and it is cheap next to shipping the wrong card for months.

**The tempting shortcut is wrong, and this is the one to learn from.** "Its
popup is a portal that only opens on interaction, and a static card never
interacts, so it cannot escape" sounds airtight. Tested on two such components,
the validator flagged **both** — `gridOverflow: "escape"`, on every story of
one of them. Components position content outside their cell for reasons that
are not visible in the source you are reading: a positioner that measures on
mount, a thumb that renders fixed. Reason your way *into* a hypothesis if you
like, then go and measure it.

The converse has teeth too: a component with an obvious portal that has sat in
`column` across every run without flagging is *verified* safe, and should not
be tagged on the strength of the portal you can see in its source.
