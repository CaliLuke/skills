# Card modes: the three cards and the wrong default

The pane offers exactly three (see the converter's `emit.mjs`):

- **grid** — one cell per story at `repeat(auto-fit, minmax(320px, 1fr))`, each
  cell `overflow: hidden` and `transform: translateZ(0)`. The default when a
  component has no override. The validator measures it with the grid
  constrained to **680px** — the product's ≤728px column less its body padding
  — so a real cell is ~330px, not the 320px the CSS floor suggests.
- **column** — one story per row at full card width. Still a grid
  (`grid-template-columns: 1fr`); a cell still clips at its edge.
- **single** — one story (`primaryStory`, else the first export) full-bleed in a
  transformed wrapper, at the card's declared `viewport`.

**The default is wrong for anything that is not small.** A grid cell is
320px-minimum, and the product renders the card live, often narrower than the
capture viewport.

### The blind spot that makes this urgent

The validator's `[GRID_OVERFLOW]` check measures whether a story renders
*wider* than its cell. A responsive layout does not: it reflows into a 320px
track, reports `gridOverflow: null`, and reads as broken anyway. In the system
this came from, five whole-screen editor states shipped as three narrow columns
with the song title overlapping a tab — every automated check green.

So: **do not wait for a warning to tell you a card is wrong.** Width is a
symptom. What the component *is* predicts the right card; measure only to catch
what you misjudged.

### Declare the kind, derive the knobs

Hand-tuning `cfg.overrides` per component rots: entries accumulate reactively,
nobody can state the rule, and new components silently take the grid default.
Instead declare what each component represents, next to the component — a tag
on its story `meta` — and generate the overrides from one table:

| tag | represents | card |
| --- | --- | --- |
| `ds:tile` | a repeating catalog item, several visible at once | grid |
| `ds:control` | one control or surface, shown as a stack of its variants | column |
| `ds:panel` | an instrument-width composite | column |
| `ds:fragment` | a slot with exactly one state worth showing | single |
| `ds:overlay` | the visible experience *is* the floating thing (dialog, toast) | single |
| `ds:screen` | a whole page or the app shell | column at a desktop viewport |

**`ds:fragment` is the tag most easily misapplied.** The tempting definition —
"only reads inside its parent" — is a composition fact, and it is true of far
more components than should carry it: every layer inside a timeline, every
label and error inside a field. Applied literally it maps nine such components
to a `single` card and hides their states, so a waveform viewport stops showing
Loading / Failed / Empty. The kind's only job is choosing how to show the
states, so select on the states: **`fragment` means there is one state worth
showing.** A slot with several meaningful states is a `control` or a `panel`
that happens to need a parent, and where it needs one belongs in its usage
docs, not in its card mode.

Modifiers: `ds:viewport:WxH`, `ds:primary` on the one story the card leads
with, and `ds:escapes` (below). Then a `--check` mode in the repo's quality
gate fails on any untagged component and on config that disagrees with the
tags, so the grid default can never be reached by accident.

Two warnings from experience:

- **`panel` becomes a catch-all** for "not obviously a form control". Audit it:
  a fader, a pair of mute/solo buttons and a section selector are controls, not
  composites. A vocabulary nobody polices stops carrying information.
- **`overlay` is about identity, not rendering.** A select or slider whose
  popup escapes its box is still a control. Reserve `overlay` for components
  whose whole point is the floating layer; use `ds:escapes` for the rendering
  fact.
- **Know which distinctions reach the card, and which are only vocabulary.**
  `control` and `panel` emit the same card, and so do `overlay` and
  `escapes`-forced `single`. A relabel across those pairs changes zero pixels
  while re-grading every component it touches, because story source is in the
  grade key. That is a real debt worth paying — a vocabulary that lies stops
  carrying information — but pay it inside a pass that is re-grading anyway,
  never as its own errand. It also means these distinctions **cannot be
  policed by looking at the output**: a mislabel here is invisible in the pane
  and only a reader can catch it.
