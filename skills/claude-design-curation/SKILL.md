---
name: claude-design-curation
description: Decide how a component library presents itself in a claude.ai/design project — which pane section each component belongs to, and which card presentation (grid / column / single + viewport) its stories get — and upload it without stale paths or false-green gates. Also holds how feedback travels back: the project is a readable shared filesystem, so a design agent's changes come back as FILES, never as instructions the user copy-pastes between chats. Use alongside /design-sync, which owns the build and transport; use this when a user relays something a design agent told them, when cards look wrong (squashed, clipped, overlapping, showing one story when states matter), when sections duplicate or misfile components, when adopting a declared-kind policy, or before an upload that moves card paths.
---

# Curating a design system in claude.ai/design

`/design-sync` builds the bundle and moves the bytes. It does not decide what
the pane should look like, and its warnings do not catch the most common way a
design system reads as broken. That judgment is this skill.

Everything here was learned by shipping a 48-component system and measuring
what went wrong. Numbers come from that system; the mechanisms are general.

## Feedback comes back as files, not chat

The project is a **shared filesystem**, not a one-way publish. `DesignSync` has
`list_files` and `get_file`, and the design agent can write into the project. So
a change it wants made in the repo travels as a file you read.

If a user is pasting a design agent's instructions into a coding chat, the loop
is broken. Fix it rather than working around it — the agent defaults to asking
for a relay because nothing tells it otherwise, and it will keep doing so.

**Picking it up:** `list_files` on the `projectId` in `.design-sync/config.json`,
then `get_file` on everything under `templates/**` and `feedback/**`. Implement,
re-sync, delete consumed `feedback/**` notes. Leave `templates/**` — those are
the user's designs, not a queue.

**Telling the other side:** `cfg.readmeHeader` points at a repo file stitched to
the top of the project README, which is the first thing the design agent reads.
The protocol belongs there. Explaining it in chat does not persist.

**What comes back is a proposal, not an instruction.** It was written by an agent
that cannot see the repo, cannot run the build, and is inferring from a compiled
snapshot. Check it before implementing and say plainly when it is wrong — that is
the whole value over a relay. A real one: a design agent asked for
`/* @kind other */` on ten token declarations "in the source repo, then
re-sync". Right intent, impossible as written, because the build strips comments
everywhere except one file. See `references/source-of-truth.md`.

## Two axes, decided separately

| axis | comes from | answers |
| --- | --- | --- |
| **section** | the story title's prefix (`Editor/Thing`) | where a reader looks for it |
| **presentation** | `cfg.overrides.<Name>` (`cardMode` + `viewport`) | how the card shows its stories |

They are independent and allowed to disagree: a page layout can be an
`Editor/` component and still be presented as a full-width screen. Do not make
one follow from the other.

## The decision, in one table

Declare what each component represents as a tag on its story `meta`, and
generate `cfg.overrides` from it. Never hand-tune the overrides: entries
accumulate reactively, nobody can state the rule, and new components silently
take the grid default — which is wrong for anything that is not small.

| tag | represents | card |
| --- | --- | --- |
| `ds:tile` | a repeating catalog item, several visible at once | grid |
| `ds:control` | one control or surface, shown as a stack of its variants | column |
| `ds:panel` | an instrument-width composite | column |
| `ds:fragment` | a slot with exactly one state worth showing | single |
| `ds:overlay` | the visible experience *is* the floating thing (dialog, toast) | single |
| `ds:screen` | a whole page or the app shell | column at a desktop viewport |

Modifiers: `ds:viewport:WxH`, `ds:primary` on the story the card leads with,
`ds:escapes` for content that leaves its own box. Then a `--check` mode in the
repo's quality gate fails on any untagged component and on config that
disagrees with the tags, so the grid default can never be reached by accident.

## Five things that will bite you regardless

Read these even if you read nothing else. Each is expanded in a reference file.

1. **The validator cannot see the worst failure.** `[GRID_OVERFLOW]` measures
   whether a story is *wider* than its cell. A responsive layout reflows into a
   320px track instead, reports `gridOverflow: null`, and reads as broken with
   every check green — which is how five whole-screen states shipped as three
   narrow columns. → `references/card-modes.md`
2. **Never decide `ds:escapes` by reading the component.** A component in
   `grid`/`column` that has never flagged is verified; one in `single` is
   unverified permanently, because the check is gated on card mode. The
   plausible argument ("its portal only opens on interaction, and a static card
   never interacts") was tested on two components and the validator flagged
   both. → `references/escapes.md`
3. **`skip` is hand-written and nothing derives it.** A generator that rebuilds
   `overrides` from tags deletes every `skip` on its first run, silently. It is
   the only mistake here that destroys work rather than reporting a false
   green. → `references/generator.md`
4. **Touching a story file re-grades its component; touching `cfg.provider`
   re-grades all of them.** Know the cost before you edit, and batch.
   → `references/economics.md`
5. **A title change moves the card path**, so the old directory lingers in the
   project unless the upload deletes it. Seven moved components left 28 stale
   files. → `references/upload.md`

## Reference files

| file | covers |
| --- | --- |
| `references/card-modes.md` | the three cards, the blind spot, choosing a kind, which distinctions never reach the pane |
| `references/escapes.md` | the two escape mechanisms, and the evidence rule that settles them |
| `references/viewports.md` | width vs height, the fold arithmetic, when to set one |
| `references/sections.md` | slug derivation, filing by consumer, primitives vs feature components |
| `references/economics.md` | the grade key: what re-grades what, and what is free |
| `references/upload.md` | the upload sequence, the anchor, deletes, verifying the artifact |
| `references/overlays.md` | portalled dialogs need a canvas or the oracle goes blind; grading from sheets |
| `references/generator.md` | ten holes that let a gate report green on a mis-declared component |
| `references/source-of-truth.md` | what the repo side must get right for the project to be usable at all: comments, tokens, contracts, providers, fixtures |

Each file stands alone. Where one disagrees with this summary the reference
file wins, and measured output wins over both — go and read the emitted card.
