# Code Layout Smell Catalog

Detailed detection criteria, examples, and remediation for each smell. Language-agnostic principles with Python and TypeScript specifics.

## 1. Prefix Cluster

**Definition:** Three or more files in the same directory sharing a name prefix.

**Detection:**

- Group files by longest common prefix (ignoring extensions)
- Flag groups of 3+ files sharing a prefix of 4+ characters
- Exclude `test_` / `*.test.` / `*.spec.` prefixes (test naming convention, not a smell)
- Exclude `__init__` / `index` files

**Python examples:**

```text
backend/
  agent.py
  agent_helpers.py
  agent_loop.py
  agent_session.py
  agent_tools.py
```

**TypeScript examples:**

```text
src/components/
  ChatMessage.tsx
  ChatInput.tsx
  ChatHeader.tsx
  ChatState.ts
  ChatTypes.ts
```

**Remediation:** Promote the prefix to a directory. The prefix-stripped names become the filenames inside:

```text
backend/agent/
  __init__.py    # public API (replaces re-exports)
  loop.py
  helpers.py     # (ideally renamed to what it actually does)
  session.py
  tools.py
```

**Why it matters:** The prefix IS the package — the developer already grouped these mentally. The file system should reflect that grouping so navigation, imports, and ownership boundaries are visible at a glance.

---

## 2. Shim Facade

**Definition:** A file whose primary purpose is re-exporting symbols from sibling files to preserve old import paths.

**Detection signals:**

- File docstring or comments mention "re-export", "backward compat", "back-compat"
- More than 50% of top-level symbols are imported-and-re-exported (not defined locally)
- `# noqa: F401` annotations on imports (Python — suppressing "imported but unused")
- `export { X } from './sibling'` comprising most of a TypeScript file
- Barrel `index.ts` files that only re-export

**Python example:**

```python
"""Re-exports symbols so that existing ``from backend.corpus import X`` statements continue to work."""
from backend.corpus_context import _build_context_filter  # noqa: F401
from backend.corpus_briefing import build_full_corpus_context  # noqa: F401
```

**TypeScript example:**

```typescript
// src/utils/index.ts — barrel re-export
export { formatDate } from "./formatDate";
export { parseQuery } from "./parseQuery";
export { validateInput } from "./validateInput";
```

**Remediation:** If this file exists because of a prefix cluster, promote to a package and use `__init__.py` / `index.ts` as the public API. If the re-exports serve no current consumer, delete them.

**Why it matters:** Shim facades are scar tissue from mechanical splitting. They add indirection, obscure where code actually lives, and signal that the split didn't restructure the module interface.

---

## 3. Junk Drawer

**Definition:** A file named with a generic term (`core`, `utils`, `helpers`, `common`, `shared`, `misc`, `lib`, `base`) containing unrelated functions/classes.

**Detection:**

- Filename matches: `core`, `utils`, `helpers`, `common`, `shared`, `misc`, `lib`, `base`, `general`, `stuff`
- File contains 3+ top-level definitions (functions, classes) that serve different callers or domains
- Low internal cohesion: the definitions don't call each other

**Python example:**

```python
# core.py — "shared leaf utilities"
# Contains: LLM client builder, HTTP client singleton, conversation logger
# These three things are unrelated; they live together because they're all "shared"
```

**TypeScript example:**

```typescript
// utils.ts
export function formatDate(...) { }   // used by UI components
export function retryFetch(...) { }   // used by API layer
export function slugify(...) { }      // used by routing
```

**Remediation:** Split by actual domain or responsibility. Name files by what they contain, not by their role relative to callers:

- `core.py` with HTTP client + LLM builder + logger → `http_client.py`, `llm.py`, `conversation_log.py`
- Or group into an infrastructure package: `infra/http.py`, `infra/llm.py`

**Why it matters:** Junk drawers are gravity wells. Every "where should I put this?" gets answered with "just put it in utils." They grow without bound and obscure the actual dependency structure.

---

## 4. Import Magnet

**Definition:** A single file imported by more than 50% of its directory siblings, mixing multiple unrelated responsibilities.

**Detection:**

- Count how many sibling files import from each file
- Flag files imported by >50% of siblings
- Cross-reference with responsibility count: does the file export symbols serving different domains?
- A settings/config file imported everywhere is NOT a smell (single responsibility, just widely needed)
- The smell is when a widely-imported file mixes concerns

**Python example:**

```text
request_context.py — imported by 10 of 18 siblings
  Contains: ContextVar definitions (infrastructure)
  AND: OpenSearch wrapper functions (data access)
  AND: Scope-tracking helpers (business logic)
```

**TypeScript example:**

```text
context.ts — imported by 12 of 15 siblings
  Contains: React context definitions
  AND: API fetch wrappers
  AND: Type definitions for multiple features
```

**Remediation:** Split by responsibility. Each responsibility becomes its own module. The widely-needed parts (like ContextVar definitions or type exports) remain in a focused file.

**Why it matters:** Import magnets create hidden coupling. Changing one responsibility in the file risks affecting all importers. They also resist refactoring — moving anything out breaks many import sites.

---

## 5. Shadow Name

**Definition:** A file named by its relationship to another file rather than by what it contains. Suffixes: `_helpers`, `_utils`, `_data`, `_types`, `_support`, `_extra`, `_impl`, `_internal`.

**Detection:**

- Filename matches pattern: `{something}_{suffix}` where suffix is in the shadow-name list
- The "something" part matches another file in the same directory
- Exception: `_types` / `_schemas` files in TypeScript ARE a convention (though they can still be a smell if they cover multiple domains)
- Exception: `_test` / `_spec` suffixes are test convention, not a smell

**Python examples:**

```text
corpus_helpers.py     — helper to what? Actually contains: entity lookup, NER formatting, filter injection
search_helpers.py     — helper to what? Actually contains: hit deduplication, snippet extraction
document_helpers.py   — helper to what? Actually contains: parent-doc fetching, content parsing
agent_helpers.py      — helper to what? Actually contains: agent config builder, input assembler, token estimator
```

**TypeScript examples:**

```text
chatUtils.ts          — what utils? Actually contains: message formatting, scroll management
authHelpers.ts        — what helpers? Actually contains: token refresh, permission checking
```

**Remediation:** Rename to describe the content, not the relationship:

- `corpus_helpers.py` → `entity_formatting.py` or fold into corpus package
- `search_helpers.py` → `hit_processing.py` or fold into search module
- `agent_helpers.py` → `agent_config.py` or `agent/config.py` in a package

**Why it matters:** Shadow names hide content behind a relationship. You must open the file to know what's inside. They also become secondary junk drawers — "it doesn't fit in the main file, so dump it in helpers."

---

## 6. Orphan Module

**Definition:** A file that is not imported by any other file in the project (excluding entry points, tests, scripts, and config).

**Detection:**

- For each non-test, non-entry-point file, check if any other file imports from it
- Exclude known entry points: `main.py`, `app.py`, `manage.py`, `index.ts`, `App.tsx`
- Exclude test files, config files, migration scripts
- Exclude files that are dynamically imported or loaded by framework convention

**Remediation:** Verify whether the file is truly unused (it may be dynamically loaded). If unused, delete it.

**Why it matters:** Dead modules add cognitive load. Readers wonder about their purpose and hesitate to delete them. They accumulate during refactors when imports are moved but old files aren't cleaned up.

---

## 7. Layering Violation

**Definition:** A flat directory mixing files at different abstraction levels — high-level orchestration alongside low-level infrastructure — with no visible hierarchy.

**Detection:**

- In the same directory, identify files that are "leaf" dependencies (imported by many, import few siblings) vs. "root" orchestrators (import many siblings, imported by few)
- If both coexist in the same flat directory with no subdirectories separating them, flag it
- Heuristic: if the import graph has 3+ layers of depth within a single directory, the directory is hiding its internal architecture

**Example:**

```text
backend/                         # all flat, no subdirectories
  routes.py                      # layer 3: HTTP interface
  agent.py                       # layer 2: orchestration
  agent_loop.py                  # layer 2: orchestration
  compaction.py                  # layer 1: domain logic
  corpus_context.py              # layer 1: domain logic
  request_context.py             # layer 0: infrastructure
  settings.py                    # layer 0: infrastructure
  ttl_cache.py                   # layer 0: infrastructure
  opensearch_client.py           # layer 0: infrastructure
```

**Remediation:** Introduce subdirectories that reflect the layers:

```text
backend/
  routes.py                      # stays at top (entry point)
  agent/                         # orchestration layer
  corpus/                        # domain logic layer
  infra/                         # infrastructure layer
```

**Why it matters:** When everything is flat, you can't tell from `ls` whether a file is a high-level orchestrator or a low-level utility. The dependency direction is invisible. New contributors (and AI agents) have to read import statements to understand the architecture.

---

## 8. Infrastructure Sprawl

**Definition:** Five or more leaf-node files (high in-degree, low out-degree, no domain logic) sitting ungrouped in the same flat directory. Each file is individually well-named and single-responsibility, but together they form an unlabeled layer.

**Detection:**

- **Classify by content first, not degree.** Read each file and check: does it contain domain logic (business rules, orchestration) or only plumbing (transport, config, protocol definitions, caching, tracing, middleware)? Plumbing files are infra regardless of their import degree.
- Degree heuristics (in-degree >= 2, out-degree <= 2) are a starting point but miss cases: a transport file with context-var wrappers may have high out-degree; a tracing file may have low in-degree. Content classification catches these.
- If 5+ infra files coexist in a flat directory without a grouping subdirectory, flag it
- This smell specifically survives prefix-cluster fixes because each infrastructure file has a unique, descriptive name — no shared prefix triggers grouping

**Key distinction from Layering Violation:** A layering violation is about mixing abstraction levels (orchestrators next to leaf utilities). Infrastructure sprawl is about having too many leaf-node files at the same level with no grouping. You can fix layering violations (by promoting orchestrators into packages) and still have infrastructure sprawl left over.

**Python example:**

```text
backend/
  http_client.py           # shared HTTP client + retry
  llm.py                   # LLM client builder
  opensearch_client.py     # OpenSearch transport
  request_context.py       # ContextVar definitions
  settings.py              # config
  ttl_cache.py             # async TTL cache
  conversation_log.py      # event logger
  langsmith_http_context.py # tracing context
  stream_protocol.py       # typed event classes
  # 9 infrastructure files — no shared prefix, each well-named, but ungrouped
```

**TypeScript example:**

```text
src/
  apiClient.ts             # HTTP fetch wrapper
  authContext.ts           # auth state context
  eventBus.ts              # pub/sub event system
  logger.ts                # structured logging
  storage.ts               # localStorage abstraction
  websocket.ts             # WebSocket connection manager
  # 6 infrastructure files sprawled across src/
```

**Remediation:** Group into an infrastructure package. The package name should describe the layer, not the contents:

```text
backend/
  infra/
    __init__.py
    http_client.py
    llm.py
    opensearch_client.py
    request_context.py
    settings.py
    ttl_cache.py
    conversation_log.py
    langsmith_http_context.py
    stream_protocol.py
```

Or in TypeScript:

```text
src/
  infra/
    index.ts
    apiClient.ts
    authContext.ts
    eventBus.ts
    logger.ts
    storage.ts
    websocket.ts
```

**Why it matters:** Individually well-named files create a false sense of organization. Each file is clear in isolation, but `ls` shows a flat soup of 15+ files with no visible grouping. The infrastructure layer is invisible — you have to read imports to discover it exists. Grouping makes the layer explicit: "these are plumbing, not domain logic, and you rarely need to touch them."

---

## 9. Misplaced Module

**Definition:** A file that lives outside a package but >70% of its importers are inside that package. The file is functionally part of the package but hasn't been moved in.

**Detection:**

- For each file outside a package directory, count its importers across the entire project (not just siblings — include imports from within packages)
- Group importers by package. If one package accounts for >70% of all importers, the file is misplaced
- Exclude entry points (`main.py`, `routes.py`) — they legitimately import from everywhere
- Exclude files with only 1 importer (too little signal)

**Python example:**

```text
backend/
  compaction.py       # 5 importers: agent/__init__.py, agent/config.py,
                      #   agent/loop.py, routes.py, tools/cognitive_toolkit.py
                      # 3/5 = 60% from agent/ — borderline
                      # But the 3 agent importers use it heavily (token counting
                      # is core to the agent loop), while routes uses it once
                      # for the compress endpoint
```

**TypeScript example:**

```text
src/
  messageFormatter.ts  # 4 importers: chat/ChatApp.tsx, chat/ChatMessage.tsx,
                       #   chat/ChatInput.tsx, utils/export.ts
                       # 3/4 = 75% from chat/ — misplaced
```

**Remediation:** Move the file into the package that consumes it most. If the remaining external consumers need it, they can import across the package boundary — that's a cleaner dependency than having the file float outside.

**Why it matters:** A misplaced module obscures coupling. The file system says "this is general-purpose" but the import graph says "this belongs to package X." Moving it in makes the coupling visible and reduces the number of files a newcomer has to scan at the top level.

---

## 10. Coupled Pair

**Definition:** Two files with a clear parent/satellite relationship — one contains the main logic, the other contains supporting definitions (schemas, queries, data) — that aren't grouped into a subdirectory.

**Detection:**

- Identify file pairs where one imports heavily from the other and they share a naming relationship (e.g., `search.py` + `search_queries.py`, `entities.py` + `entity_schemas.py`, `cognitive.py` + `cognitive_toolkit.py`)
- The satellite file is imported only by its parent (or by very few others)
- The pair isn't part of a larger prefix cluster (which would be smell #1)
- Flag when 2+ such pairs exist in the same directory — individually each pair is fine, but multiple pairs signal that the directory wants to be split into subdirectories

**Python example:**

```text
tools/
  search.py             # main tool definitions
  search_queries.py     # query builders, hit processing (satellite)
  documents.py          # main tool definitions
  document_extraction.py # fetch, parse, NER (satellite)
  entities.py           # main tool definitions
  entity_schemas.py     # schema definitions (satellite)
  # 3 coupled pairs in one directory — each pair is a mini-package
```

**TypeScript example:**

```text
components/
  UserProfile.tsx       # main component
  UserProfileUtils.ts   # helper functions (satellite)
  Dashboard.tsx         # main component
  DashboardTypes.ts     # type definitions (satellite)
```

**Remediation:** When multiple coupled pairs coexist, consider promoting each pair to a subdirectory. For a single pair in an otherwise well-organized directory, leave it alone.

**Why it matters:** Coupled pairs are prefix clusters that didn't quite reach the 3-file threshold. Individually harmless, but 3+ pairs in one directory means the directory has hidden internal structure. The pairs are doing the grouping mentally — the file system should reflect it.

---

## 11. Import-Tree Cluster

**Definition:** A root file and 5 or more of its descendants (children, grandchildren) all sitting flat in the same directory, forming a hidden feature tree that isn't reflected in the file system.

**Detection:**

- From the import graph, pick each file that has 3+ sibling imports (potential root)
- Recursively trace its imports: children, then their children, counting only files in the same directory
- If the tree totals 5+ files (including the root), it's an import-tree cluster
- This catches functional groupings that name-based prefix detection misses — files may have completely different names but form a tight feature tree

**Key distinction from Prefix Cluster:** Prefix clusters are detected by naming convention (`Chat*`, `Agent*`). Import-tree clusters are detected by actual dependency relationships. A `ChatApp` component that imports `ContextBar`, `ReportDialog`, and `ChatTimeline` (which imports `ToolSteps`) forms a 6+ file tree, but only 2 files share the `Chat` prefix.

**React/TypeScript example:**

```text
components/                       # 19 files flat
  ChatApp.tsx          (421L)     # root — imports 5 siblings
  ├── ChatInput.tsx    (87L)      # imports ContextDoughnut
  │   └── ContextDoughnut.tsx (108L)
  ├── ChatTimeline.tsx (155L)     # imports ToolSteps, MarkdownMessage, CoverageBadge
  │   └── ToolSteps.tsx (436L)    # imports ToolCards, ReasoningCard
  │       ├── ToolCards.tsx (329L)
  │       └── ReasoningCard.tsx (86L)
  ├── ContextBar.tsx   (111L)
  ├── ContextViewer.tsx (411L)
  └── ReportDialog.tsx (125L)
  # 10-file tree hidden in a 19-file flat directory
```

**Python example:**

```text
handlers/                         # 15 files flat
  request_handler.py   (300L)     # root — imports 4 siblings
  ├── auth_checker.py  (150L)
  ├── rate_limiter.py  (100L)
  ├── response_builder.py (200L)  # imports formatter, serializer
  │   ├── formatter.py (120L)
  │   └── serializer.py (90L)
  └── error_handler.py (80L)
  # 7-file tree hidden in a 15-file flat directory
```

**Remediation:** Promote the tree to a subdirectory named after the root's domain concept. Shared files imported by multiple trees (e.g., `MarkdownMessage` used by 6 importers across different features) stay in the parent or move to a `shared/` subdirectory.

**Why it matters:** Name-based prefix detection catches groups where the developer named things consistently. Import-tree detection catches groups where the developer didn't — the grouping exists in the dependency graph but is invisible in `ls`. This is especially common in React codebases where components are named by UI responsibility (not by feature prefix) but form tight feature trees.

---

## 12. Premature Package

**Definition:** A directory containing only 1 source file. The directory adds a level of navigation without providing any grouping value.

**Detection:**

- For each subdirectory, count source files (excluding `index.ts`, `__init__.py`, config files)
- If the count is 1, flag it
- Exception: directories that are framework conventions (e.g., `pages/` in Next.js with a single index route) — don't flag these

**TypeScript example:**

```text
src/
  hooks/
    useSession.ts        # only file — directory is premature
  services/
    api.ts               # only file — directory is premature
  components/
    ChatApp.tsx           # 19 files — directory is justified
    ...
```

**Python example:**

```text
backend/
  middleware/
    cors.py              # only file — directory is premature
  validators/
    schema.py            # only file — directory is premature
```

**Remediation:** Either move the file up to the parent directory, or wait until 2+ related files exist before creating the directory. A single file named `hooks/useSession.ts` communicates the same information as `useSession.ts` in the parent — the `hooks/` directory is pure overhead.

**Why it matters:** Premature packages are the inverse of too-many-files-flat. They add navigation depth without providing grouping. Each directory in the path is a decision point for a reader: "do I need to go in here?" A directory with 1 file always answers "yes" — making the directory pointless. They also signal over-engineering: the developer anticipated growth that hasn't materialized.
