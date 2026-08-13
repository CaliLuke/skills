# Safe adoption

Use this sequence when the gate introduces a new tool, broad formatting, or new enforcement.

Official references:

- [Knip gradual adoption](https://knip.dev/guides/adopt-gradually)
- [Knip rules and filters](https://knip.dev/features/rules-and-filters)
- [Knip issue types](https://knip.dev/reference/issue-types)

## Before changes

1. Inspect `git status --short` and identify active work.
2. Run the old canonical gate and record its result.
3. Measure each proposed gate before you enforce it.
4. Decide which current findings become baselines and which must be fixed now.

Do not run a hook that stashes unstaged files while agents, editors, watchers, or generators are changing the tree.

## Separate changes by purpose

Use this order when possible:

1. Add or migrate configuration without broad automatic fixes.
2. Apply a formatter in a formatting-only change. It must contain zero behavior changes.
3. Apply reviewed lint fixes. Separate behavior-changing fixes from safe mechanical fixes.
4. Commit coverage and other measured baselines.
5. Enable hook and CI enforcement.

Do not mix product logic with repository-wide formatting or gate infrastructure.

## Calibrate enforcement

- Preserve a stricter working policy.
- For legacy findings, use a committed ratchet or a measured issue limit.
- Set complexity, file-size, and duplication limits at or just above current reality. Tighten them deliberately.
- Exclude generated, vendored, fixture, snapshot, and build output by path. Do not exclude owned source only to make a gate green.

For Knip, start with unused files and dependencies as errors. Keep unused exports, types, and enum members as warnings while teams remove the backlog. Knip supports `error`, `warn`, and `off` rules. Its `--max-issues` option can ratchet a large existing backlog.

Example starting policy:

```json
{
  "rules": {
    "files": "error",
    "dependencies": "error",
    "devDependencies": "error",
    "unlisted": "error",
    "unresolved": "error",
    "exports": "warn",
    "types": "warn",
    "enumMembers": "warn",
    "duplicates": "off"
  }
}
```

Review entry points and framework plugins before you trust the first Knip result.
