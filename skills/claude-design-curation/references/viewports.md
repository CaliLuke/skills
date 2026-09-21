# Viewports: width and height are different knobs

`viewport` is the single most consequential number on a card, and the one most
easily set by reflex. Three facts decide every choice:

1. **Both `single` and `column` default to `900x700`** — the harness's own
   capture viewport. Leave it alone unless the content demands otherwise: a
   kind default that diverges silently moves capture geometry under grades
   that were carried forward.
2. **The declared viewport also drives the per-story captures.** It is not
   just how the card looks; it is the frame both sides of the comparison are
   shot in. Widening it moves the reference panel and the preview panel
   equally, so it changes framing, never fidelity.
3. **The product fits the card to a ≤728px column and a ~500px fold by
   scaling**, with everything below the fold on hover-scroll. A wide viewport
   is scaled down, not cropped — but a tall one buries its lower stories.

From those, the rules:

- **Only `ds:screen` should carry a kind-level viewport.** A page rendered at
  900px wide is not a page; give it your product's desktop baseline (`1440x900`
  worked for a 1920×1080-targeted app — wide enough to be a real screen,
  scaled cleanly into the pane). Every other kind leaves it unset.
- **Width and height are different knobs with different rules.** Do not treat
  `WxH` as one decision.
  - **Width is for clipping, and only on evidence.** Widen when content is
    measurably cut off — a trailing marker outside the frame — and widen,
    rather than inventing a new pair of numbers. Width also sets the scale:
    728/W. Never narrow to "fit"; the card scales, it does not crop.
  - **Height is for fitting the card to its content, and you should set it
    often.** At the `700` default a card renders ≈566px tall (700 × 728/900),
    which overshoots the ~500px fold, so a component whose stories occupy
    120px ships a card that hover-scrolls to reveal nothing but whitespace.
    Measure the rendered stack and set the height just above it: a 14-component
    set of form primitives wanted `900x300` through `900x620`, every one of
    them a *reduction*, and every one an improvement.
  - The inverse still holds: too short crops, and a column card's later stories
    need enough height to reach them.
- **Never set a viewport casually.** It is grade-keyed: every change costs a
  full package build and re-grades that component, where a `cardMode` flip
  costs seconds and carries grades. Batch viewport changes into one deliberate
  pass.

The smell to watch for: reaching for a viewport to fix something a card mode
should fix. If a component's stories are squashed, it usually wants `column`,
not a wider box.
