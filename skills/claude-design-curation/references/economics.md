# Grade economics: what re-keys what

Verification grades each story by comparing the preview against the reference
storybook, and grades are keyed. Before any change, know which bucket it is in:

| change | cost |
| --- | --- |
| `cardMode`, `primaryStory` | **free** — not in the grade key; targeted preview rebuild, seconds, grades carry |
| `viewport` | **keyed** — full package build, that component re-grades |
| story title | **keyed and moves the card path** — re-grades, and the old path must be deleted on upload |
| any edit to a `*.stories.*` file | **keyed** — story source is in the component's key |
| `cfg.provider` | **keyed globally** — it sits in the grade contract's global slice, which mixes into *every* component's key; one edit re-grades the entire roster |

That last row is the one that surprises. Adopting a tag policy edits every
story file, so **every** grade clears at once: 48 components, all re-graded
from fresh sheets in one pass. Budget it as a single deliberate event rather
than discovering it mid-run, and keep the kind defaults free of `viewport`
(let the tool's own default apply) so later tag changes stay cheap.

## A clear that means nothing

The grade key hashes the toolchain and the emitted contract, not just the
render. Editing a converter override in `.design-sync/overrides/` clears every
grade even though every screenshot is byte-identical.

Before re-grading dozens of cards, diff the old and new `_ds_sync.json`. If only
`sourceKeys` moved and `renderHashes` did not, nothing renders differently and
the prior verdicts stand verbatim — re-stamp them. Keep a copy of the anchor
before a rebuild so the comparison is available:

```bash
cp ds-bundle/_ds_sync.json /tmp/anchor.before
# …rebuild…
diff <(jq -S .renderHashes /tmp/anchor.before) <(jq -S .renderHashes ds-bundle/_ds_sync.json)
```

Re-upload `_ds_sync.json` afterwards either way, or the next sync re-verifies
the whole roster against an anchor that no longer matches a fresh build.
