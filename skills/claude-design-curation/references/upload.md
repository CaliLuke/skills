# Upload and verification

Follow `/design-sync`'s sequence — sentinel first, chunked writes, deletes,
sentinel re-arm, anchor last — and add these:

- **Fetch the anchor fresh.** A cached `_ds_sync.json` from a previous session
  inflates the changed set: a 41-component anchor against a 48-component build
  marks everything changed and pushes the whole roster into grading.
- **Write everything, always.** The diff's component list is for verification,
  not for scoping writes. Re-uploading unchanged files is idempotent; an
  under-scoped write list desyncs the project permanently.
- **Deletes come verbatim from the diff.** Title changes move card paths, and
  the old directories linger in the project forever otherwise — they are not
  overwritten by the new ones. Seven moved components produced 28 stale files.
- **Verify with `list_files` afterwards** and read it for absences: the old
  section directories should be gone, the new ones present.
- **Never delete the server-generated files** (`_ds_manifest.json`,
  `_adherence.oxlintrc.json`). The app writes them; they are not in your plan.

- **`_ds_needs_recompile` IS the sentinel.** It looks like build scratch —
  a 24-byte `{"by":"design-sync-cli"}` sitting beside `.ds-build-meta.json`
  and `.sync-diff.json` — so it is easy to filter out when you build the
  upload list from a directory listing. Do not. It is the fence the app's
  self-check consumes to recompile `_ds_manifest.json`, which is what the
  Design System pane actually indexes. Without it every file uploads
  cleanly, `list_files` shows the new component directories, and the new
  cards never appear; the manifest still lists the old roster. It is absent
  from the remote listing between uploads *because the app consumed it* —
  its absence is not evidence you should not send it.
- **Build the write list from the sequence, not from `find`.** Sentinel
  first, chunked writes, deletes, sentinel re-arm, anchor (`_ds_sync.json`)
  last. A list assembled by filtering a directory drops the sentinel and
  usually puts the anchor in the first chunk, which is the opposite of what
  the ordering is for.
- **The self-check runs when the project is opened, not on upload.** After
  arming the sentinel, the manifest stays stale until someone loads the
  project. Re-reading `_ds_manifest.json` immediately proves nothing; check
  it for the new component names *after* a refresh.

- **Grade files key on the display story name, not the export.**
  `<Name>.grade.json` keys on the string the receipt prints under
  `grade keys:` — `"Title Only"`, not `"TitleOnly"`. Single-word stories match
  either way, so the mistake hides until a multi-word one appears, and then
  that component reports `needs-grade` after every rebuild forever. Nothing
  warns about a key matching no story. Read the expected keys from
  `.design-sync/.cache/compare/<Name>.json` (`stories[].story`) and assert set
  equality before writing the file; a component that keeps coming back
  ungraded is this, not a recapture loop.

### Verify the artifact, not the intent

Two failure modes cost real time, both invisible without an explicit check:

- **A build can silently use a stale config.** After any build, read the emitted
  card HTML and confirm the mode and viewport you intended:
  `head -1 <Component>.html` shows the `@dsCard` comment with the viewport, and
  `grep -o 'var MODE="[^"]*"'` shows the card mode. A config edit that lost a
  race with the build produces a green run that changed nothing.
- **Never run two builds at once.** Both wipe the output directory; the result
  is a half-written bundle that looks like a crash.
