# Portalled overlays, and grading from sheets

Tagging a dialog `ds:overlay` gives it a correct-looking card and can still
leave verification permanently red, for a reason no kind can imply.

A dialog that portals to `<body>` leaves the story root **literally empty**.
The comparison harness waits for a visible element inside that root before it
shoots, that wait can never succeed, and it reports `sb-error "no storybook
root content"` having taken **no screenshot on either side**. The component is
fine; the oracle cannot see it.

The fix is one decorator on `meta.decorators`: a single empty block with
`min-height: 100vh` around the story. It works because a screenshot captures
the page pixels inside an element's rectangle, not an isolated render of its
subtree — so the root only needs a visible child and a big enough rectangle,
and the body-portalled dialog lands in the picture anyway.

**The decorator must stay inert.** No `position`, background, `transform`,
`contain` or `isolation`: any of those creates a containing block or stacking
context and changes how the overlay composites, which is the very fidelity the
comparison exists to check.

**Do not reach for `skip` here.** It is the obvious-looking remedy and it is a
trap: `skip` removes the story's cell, and skipping every story leaves the
component a floor card with no visual at all. `sb-error` on an overlay means
"nothing visible in the render root", not "the component is broken" — confirm
with a full-page screenshot before believing otherwise.

### Grading from sheets: what is a defect and what is framing

Judge from the paired screenshots. Some differences are the harness, not the
component, and should be graded `close` with a note rather than chased:

- the preview page's own padding (a ~24px gutter the storybook canvas lacks),
  which can also reveal an off-screen skip-link chip;
- a deliberately deferred toast that the reference shot takes before it fires;
- a trailing marker just outside the frame — widen the `viewport`, which moves
  both panels equally.

A real defect looks different: wrong values, missing states, overlapping text,
content clipped at a cell edge.
