---
name: identify-layout-smells
description: >-
  This skill should be used when the user asks to "review file organization",
  "check code layout", "identify layout smells", "audit folder structure",
  "review module organization", "check file naming", "find code structure
  issues", "review how code is organized", or mentions that AI-generated code is
  disorganized or hard to navigate. Works with Python and TypeScript codebases.
license: MIT
metadata:
  author: octostar
  version: '1.0.0'
---

# Identify Layout Smells

Analyze file and directory organization to find structural problems that make
a codebase hard to navigate for humans and AI. These smells arise when code
is split to meet mechanical constraints (line limits, linter rules) without
restructuring the module boundaries.

The core principle: **file system layout should communicate domain structure
at a glance, without reading the code.**

## Smell Catalog (quick reference)

| #   | Smell                     | One-line test                                                                       |
| --- | ------------------------- | ----------------------------------------------------------------------------------- |
| 1   | **Prefix Cluster**        | 3+ files share a name prefix in a flat directory                                    |
| 2   | **Shim Facade**           | File primarily re-exports symbols from siblings                                     |
| 3   | **Junk Drawer**           | File named `core`/`utils`/`helpers`/`common`/`misc` with unrelated contents         |
| 4   | **Import Magnet**         | File imported by >50% of siblings AND mixes responsibilities                        |
| 5   | **Shadow Name**           | File named by relationship (`_helpers`, `_utils`) not by content                    |
| 6   | **Orphan Module**         | File imported by nothing (excluding entry points, tests)                            |
| 7   | **Layering Violation**    | Flat directory mixes high-level orchestration with low-level infra                  |
| 8   | **Infrastructure Sprawl** | 5+ infra files (transport, config, protocol, caching) ungrouped in a flat directory |
| 9   | **Misplaced Module**      | >70% of a file's importers are in one package, but the file lives outside it        |
| 10  | **Coupled Pair**          | Two files with a clear parent/satellite relationship not grouped into a package     |
| 11  | **Import-Tree Cluster**   | A root file + 5 or more descendants all flat in one directory (hidden feature tree) |
| 12  | **Premature Package**     | A directory containing only 1 source file                                           |

For detailed detection criteria, examples, and remediation per smell, consult
**`references/smell-catalog.md`**.

## Analysis Workflow

### Step 1: Map the directory

List all source files in the target directory (non-test, non-config). Record
filenames and line counts. This is the raw material.

```bash
# Python
find <dir> -maxdepth 1 -name "*.py" ! -name "__init__.py" ! -name "conftest.py" | sort

# TypeScript
find <dir> -maxdepth 1 \( -name "*.ts" -o -name "*.tsx" \) ! -name "index.ts" | sort
```

### Step 2: Detect prefix clusters and import-tree clusters

**Name-based:** Group filenames by shared prefix (4+ chars, 3+ files).
Exclude `test_`/`.test.`/`.spec.`. Report each cluster with member files
and total line count. A cluster with high total lines (>500) is a strong
signal for package promotion.

**Import-tree-based:** For component directories (React, Vue, etc.), trace
import trees from root-level files. If a root file imports 3+ siblings, and
those siblings import further siblings, count the entire tree. If the tree
totals 5+ files all flat in one directory, that's an import-tree cluster —
a hidden feature that should be a subdirectory. This catches functional
groupings that name-based detection misses (e.g., `ChatApp` + `ChatInput`

- `ChatTimeline` + `ContextBar` + `ContextViewer` + `ReportDialog` form a
  chat feature tree, but only 3 share the `Chat` prefix).

### Step 3: Scan for junk drawers and shadow names

Check filenames against known patterns:

- **Junk drawer names:** `core`, `utils`, `helpers`, `common`, `shared`, `misc`, `lib`, `base`
- **Shadow suffixes:** `_helpers`, `_utils`, `_data`, `_support`, `_extra`, `_impl`
- Exclude `_types`/`_schemas` in TypeScript (convention), `_test`/`_spec` (tests)

For each match, read the file and list its top-level definitions to assess
whether the name hides what's actually inside.

### Step 4: Build the import graph

For each source file, extract its imports from sibling files. Produce an
adjacency list: `file -> [siblings it imports from]`.

```python
# Python: use ast.parse to extract ImportFrom nodes
# TypeScript: grep for import statements with relative paths
```

Use this graph to detect:

- **Import magnets** — files imported by >50% of siblings (cross-check: do
  they mix responsibilities?)
- **Orphan modules** — files with zero incoming edges (excluding entry points)
- **Shim facades** — files where >50% of top-level symbols are re-exports
- **Layering violations** — compute depth (leaf = imported by many, imports
  few; root = imports many, imported by few). If 3+ layers coexist in one
  flat directory, flag it.
- **Infrastructure sprawl** — classify by content, not just degree. If a
  file contains no domain logic (only transport, config, protocol, caching,
  tracing), it's infra regardless of in/out-degree. If 5+ such files sit
  ungrouped in the same flat directory, they should be a package. This smell
  survives prefix-cluster fixes because each file has a unique name.
- **Misplaced modules** — for each file outside a package, count what
  percentage of its importers live in a single package. If >70% come from
  one package, the file probably belongs in that package.
- **Coupled pairs** — two files with a clear parent/satellite relationship
  (e.g., `search.py` + `search_queries.py`, `entities.py` +
  `entity_schemas.py`) that aren't grouped into a subdirectory. Report as
  LOW severity — not actionable alone, but worth noting when multiple pairs
  coexist in the same directory.
- **Premature packages** — directories containing only 1 source file. The
  directory adds navigation overhead without providing grouping value. Flag
  as LOW; the fix is either to add more files or inline the file into the
  parent directory.
- **Dev/production layering** — when checking for layering violations, also
  look for dev-only files (log viewers, test harnesses, debug panels,
  storybook files) mixed into production component directories. Dev tools
  scattered across directories are a special case of misplaced module — they
  should be grouped together (e.g., `dev/` or `components/dev/`).

### Step 5: Produce the report

Output a structured findings list. For each smell found:

1. **Smell name** and severity (high/medium/low)
2. **Files involved** with line counts
3. **Evidence** — the specific pattern that triggered detection
4. **Suggested remediation** — concrete rename, move, or package promotion

Group findings by smell type. End with a summary count table.

### Severity guidelines

- **High:** Prefix clusters of 4+ files, import-tree clusters of 7+ files, junk drawers over 200 lines, import magnets with 3+ mixed responsibilities, infrastructure sprawl of 7+ files, misplaced modules with >90% single-package importers
- **Medium:** Prefix clusters of 3 files, import-tree clusters of 5-6 files, shadow names, shim facades, layering violations, infrastructure sprawl of 5-6 files, misplaced modules with 70-90% single-package importers
- **Low:** Orphan modules, small junk drawers (<100 lines), single shadow-name files, coupled pairs, premature packages

## What NOT to flag

- A `settings.py`/`config.ts` imported everywhere is fine (single responsibility, just widely needed)
- A `types.ts` file co-located with its feature module is convention, not a smell
- Test file prefixes (`test_`, `.test.`, `.spec.`) are naming conventions
- `__init__.py`/`index.ts` barrel files in a package that already IS a directory
- Small projects (<10 source files) rarely benefit from subdirectories

## Additional Resources

### Reference Files

- **`references/smell-catalog.md`** — Full catalog with detection criteria,
  language-specific examples (Python + TypeScript), and remediation patterns
  for all 7 smells
