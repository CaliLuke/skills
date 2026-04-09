---
name: functional-ui-refactor
description: Refactor UI architecture by collapsing distinctions without difference, naming components by UI responsibility instead of schema entities, pushing data sourcing out of UI components, and promoting generic primitives into shared UI. Use when a UI surface feels over-specialized, duplicated by entity names, or too smart about data fetching.
context: fork
---

# Functional UI Refactor

Use this skill when the goal is not just to "clean up" UI code, but to make the UI architecture functionally correct:

- one component per real UI responsibility
- no fake distinctions driven by backend nouns
- data loading outside UI components
- generic primitives in `src/core/ui`
- feature adapters thin and explicit

This skill is for refactors where the current structure slows down feature work, multiplies bugs, or creates naming and ownership confusion.

## Design Lessons For Complex Tables And Boards

When refactoring a rich table or board, do not stop at naming cleanup. Use these structural rules:

- keep one canonical source of truth for columns/cards/items
- derive displayed layout state separately from canonical state
- derive viewport-visible state separately from displayed layout state
- keep render coordination in one owner instead of scattering redraw logic across components
- treat focus and selection as semantic interaction state, not DOM trivia
- keep drag highlight state separate from drop commit state
- make scrollbar and viewport state explicit when layout depends on them

For tables, the highest-value pipeline is:

- `canonical columns -> displayed columns -> viewport columns`

For rows/items, the equivalent rule is:

- canonical item order is not the same thing as rendered window or drag preview state

If a refactor leaves those concerns collapsed together, the architecture is still too entangled.

For overlays, forms, and any async surface that appears/disappears, use the same idea:

- one owner decides `loading | error | ready` before the real surface mounts
- keep a stable outer frame mounted while inner state changes
- swap content inside that frame instead of letting the container size/structure thrash
- loading/error shells should preserve the same basic footprint as the ready state whenever possible

If a surface "grows in" because the container only acquires structure after data arrives, the render pipeline is still under-designed.

## Core Rules

### 1. Name by UI responsibility, not schema entity

Default assumption:

- entity-named **leaf renderers** can be valid
- entity-named **selectors, overlays, controllers, wrappers, smart components** are usually wrong

Bad smells:

- `EpicSelect`, `MilestoneSelect`
- `ConnectedEpicOverlay`, `ConnectedMilestoneOverlay`
- `EpicController`, `MilestoneController` when behavior is config-driven

Prefer:

- `GroupingSelect`
- `ConnectedArtifactOverlay`
- `SectionGroupedController`
- `RelationFilterInput`

If the only difference is entity type, labels, or query source, the name is wrong and the abstraction is probably split too early.

### 2. Collapse distinctions without difference

If two UI components differ only by:

- copy
- icon
- artifact/entity type
- query hook
- mutation hook
- test ID suffix
- one or two config fields

then they should usually be one configurable component.

Do not preserve parallel component families just because the product has multiple entity types.

### 3. Keep data sourcing out of UI components

UI components should receive data and render it.

They should not decide:

- which query hook to call
- which project scope to derive
- which backend noun they represent
- which source registry to branch on

The caller or a dedicated hook owns data sourcing.

Good boundary:

- shared UI primitive: renders
- feature adapter: maps value shape / visuals
- caller or hook: fetches data

### 4. Promote true primitives into `src/core/ui`

If a component is reusable beyond one feature, it does not belong under a feature just because it was born there.

Promote to `src/core/ui` when the component:

- has generic behavior
- has no feature-specific data loading
- is configurable by render props / accessors / options
- can support multiple features without renaming

Leave only thin feature adapters behind.

### 5. Smart wrappers are suspect

Patterns like:

- `ConnectedXOverlay`
- `XOverlay`
- `XForm`

often hide one reusable controller plus one presentational shell.

Check whether the "smart" wrappers all perform the same steps:

- invalidate
- fetch data
- build initial values
- build submit handler
- build delete handler
- render type-specific shell

If yes, extract one configurable orchestration layer.

### 6. Configuration belongs in data, not branching

Prefer:

- config objects
- accessors
- render callbacks
- source adapters

Avoid:

- `if entity === 'epic'`
- `switch (artifactType)` inside UI components
- duplicate component files with noun swaps

If branching survives after refactor, ask whether it reflects a real behavioral difference. If not, move it into config.

### 7. Derived layout state deserves its own layer

Do not let leaf components recompute layout decisions ad hoc.

For dense surfaces, create an explicit derived-state layer for:

- displayed columns or lanes
- pinned vs scrollable regions
- header/group structure
- viewport-visible subsets
- scrollbar visibility and viewport measurements when layout depends on them

The canonical data model should not also be the render-layout model.

### 8. One owner for render and interaction coordination

Complex surfaces degrade when scroll, resize, focus restore, selection, and redraw each live in separate leaf hooks.

Prefer one coordinator per responsibility:

- one render/viewport coordinator
- one interaction controller for focus, keyboard nav, and selection
- one drag controller for drop semantics

Leaf cells, rows, cards, and headers should mostly dispatch and render.

### 9. Preserve semantics, not DOM instances

When a surface rerenders, regroups, virtualizes, or reorders, preserve:

- focused row/cell/card identity
- selection range/root/anchor
- editing state

Do not treat focus or selection as something the DOM will "naturally" keep stable. Persist semantic identity first, then restore DOM bindings after refresh.

### 10. Virtualization and scrolling are separate from content rendering

If a surface is large enough to need virtualization, do not fold that into generic row components.

Keep separate concerns for:

- viewport measurement
- rendered window + overscan
- recycled row/item identity
- pinned regions or always-mounted regions
- scroll-source coordination

If virtualization logic is leaking into row/cell/card components, the split is wrong.

### 11. The Headless Controller Pattern (Comp vs Ctrl)

For dense interactive surfaces, decouple structural rendering from behavioral control using a Controller/Component pair.
- The **Component** strictly manages DOM elements/framework templates and implements a granular, explicit interface for visual updates (e.g., `setTopHeight(h)`, `setColumnMovingCss(on)`).
- The **Controller** owns the logical state, observes events, and drives the component via its interface.
This prevents the UI tree from becoming a dumping ground for interaction logic and keeps coordination fully testable and framework-agnostic.

### 12. Feature Isolation over Monolithic Hooks

Stop stuffing drag-and-drop, focus management, and scroll synchronization into one giant component or monolithic hooks.
Decouple complex layout and interaction behaviors into standalone "Features" or "Services" (e.g., `FocusService`, `ViewportSizeFeature`). These isolated modules listen to domain events and manipulate state or controllers independently, keeping feature code cohesive and bypassing standard render cycles.

### 13. PubSub / Event Bus over Deep Prop Drilling

For massively complex surfaces, unified state atoms or deep prop-drilling can trigger too many expensive re-renders across the entire tree.
Introduce an internal Event Bus for the surface (e.g., `columnMoved`, `scrollVisibilityChanged`). Let leaf-node controllers subscribe directly to the granular events that affect them, rather than passing structural diffs down through a massive component tree.

### 14. Inversion of Control for Framework Bindings (The Proxy Pattern)

Instead of the core UI logic being tied to React's `useEffect` or VDOM diffing, define an explicit, framework-agnostic Proxy interface for UI mutations (e.g., `IView.setTopHeight(val)`, `IView.toggleDraggingCss(true)`). The React component implements these methods by wrapping `setState` or DOM refs, and passes itself to the vanilla Controller. This isolates state-mutation policies from the VDOM reconciler and prevents React rendering quirks from dictating feature logic.

### 15. Direct Ref Escapes for High-Frequency State

Do not pipe high-frequency, continuous state changes (drag coordinates, column moving, selection outlines, scroll syncs) through React's `useState` or prop-drilling. VDOM diffing is too slow and structurally expensive for 60fps interaction on dense surfaces. Utilize a `CssClassManager` or direct `useRef` manipulation to bypass the Reconciler entirely for styling and structural adjustments during interactions.

### 16. Atomic Update Isolation (Flattening the Blast Radius)

In complex boards or tables, a state change to a single atom (a cell or a card field) should never trigger a re-render of its parent row or the entire list. Controllers should maintain direct reference to the leaf node (e.g., `CellCtrl` drives `CellComp` directly) and command it to update its local state. Propagating granular data changes down from the top-level parent guarantees performance failure at scale.

### 17. Differentiate Smart and Stateless Renderers Architecturally

Be explicit about which leaf nodes are "Smart" (requiring async coordination, lifecycle management, or external data fetching) versus "Stateless" (pure functions of data). For surfaces rendering hundreds or thousands of elements, fast-track the initialization and lifecycle of pure functional components to avoid paying unnecessary mount/coordination overhead.

### 18. DOM Order Preservation over Blind Re-rendering

When dealing with large sets of dynamic elements (like columns or rows), do not rely purely on React's reconciler to handle array reordering, as ripping elements out of the DOM and re-inserting them will immediately break CSS transitions and animations. Introduce a manual flag or mechanism (like AG Grid's `domOrder` flag and `getNextValueIfDifferent`) to check if the structural order actually needs to change. If DOM order is not strictly required for accessibility, preserve the previous array reference and let CSS transform/translate handle the visual reordering.

### 19. FlushSync Restraint and Rendering Batching

Using `ReactDOM.flushSync` is necessary for certain critical visual updates to avoid tearing, but it is catastrophic if used blindly in high-frequency streams (like scrolling). Wrap framework-level sync calls with strict checks to avoid executing them during existing render cycles. Always provide a parameter (`useFlushSync`) so the Controller can deliberately dictate when a DOM change must be synchronous versus when it can be batched by the framework.

### 20. Pre-Paint DOM Manipulation (Layout Effects)

To avoid visual "jerking" or layout thrashing when dynamic components (like cells or popups) mount, execute structural DOM manipulations before the browser repaints. In React, use `useLayoutEffect` instead of `useEffect` when appending framework-agnostic vanilla JS components to a React ref, or when making initial size/position measurements. This ensures the component is fully styled and positioned before the user ever sees it.

### 21. Animation Frame Batching for Structural Updates

For complex surfaces that render hundreds of elements during scroll or interactions, do not execute every DOM creation/destruction task synchronously. Instead, implement a centralized `AnimationFrameService` that queues and batches UI tasks (`requestAnimationFrame`). Sort these tasks geometrically (e.g., rendering rows in the direction of the scroll, and cells left-to-right) and cap the execution time per frame (e.g., 16ms) to guarantee a smooth 60fps experience without locking the main thread.

### 22. The `afterGuiAttached` Lifecycle for Measurement & Focus

Do not attempt to measure DOM nodes, calculate absolute positioning, or grab focus while a component is still spinning up its internal state. Introduce a distinct `afterGuiAttached` (or equivalent) lifecycle callback that only fires *after* the component's root element has been physically appended to the active DOM document. Rely on this strict lifecycle step to trigger focus drops and layout calculations to prevent premature reflows.

### 23. CSS Translates for Virtualized Row Positioning

When building virtualized lists or grids, never rely on standard block layout (margin, padding, or flow) to position rows. Doing so causes the browser to recalculate the layout of every subsequent element when a row is added or resized. Instead, use `position: absolute` for all rows and position them using hardware-accelerated CSS transforms (`transform: translateY(px)`). This completely isolates the layout recalculation to the single row being modified, which is a hard requirement for scroll performance in large datasets.

## Review Heuristics

Use these smells aggressively:

### Entity-name smell

If a UI component is named after a schema entity, ask:

1. Is this a pure renderer for that entity?
2. Or is it actually a selector / controller / shell / wrapper that should be generalized?

If it is the second, it is probably wrong.

### Query-in-component smell

If a component calls a query hook and then immediately renders a generic picker/table/dropdown/surface, it is probably owning too much.

Move the query to the caller unless the component's actual responsibility is "data-aware surface."

### Barrel-cycle smell

When refactoring toward generalization, do not introduce new feature-barrel dependencies just to satisfy lint rules.

If the barrel is unsafe:

- use the leaf import
- document the exception narrowly in ESLint
- never reintroduce the cycle for stylistic consistency

### "Two files, same story" smell

If two files read like the same component with nouns replaced, collapse them.

Typical targets:

- paired selects
- paired overlays
- paired mutation hooks
- paired regroup/assignment UIs

### Canonical-vs-derived-state smell

If one hook or component owns all of these at once:

- raw columns/items
- display ordering
- pinned/grouped structure
- viewport-visible subset
- scroll calculations

then the surface is under-factored.

Split canonical state from derived layout state and from viewport/render state.

### DOM-led interaction smell

If focus, keyboarding, selection, or drag behavior depends on whichever DOM node happened to survive rerender, the interaction model is too implicit.

Promote those concerns into semantic state owned above the render layer.

### Mount-thrash smell

If a modal, overlay, form shell, or panel:

- mounts an empty container first
- adds header/body/footer structure only after async data resolves
- changes height dramatically between loading and ready
- lets loading/error/ready branches each define their own outer shell

then the render pipeline is too unstable.

Refactor to:

- one state owner above the presentational surface
- one stable outer frame
- inner branches for loading/error/ready

Borrow this pattern from the best table/board pipelines: state selection happens first, then rendering happens inside a predictable frame.

## Refactor Workflow

1. Identify the real UI responsibility.
   Replace entity nouns with the actual role:
   `EpicSelect` -> `GroupingSelect`

2. List differences between the parallel components.
   Separate:
   - true behavioral differences
   - data-source differences
   - naming/copy differences

3. Move data sourcing out first.
   Do not generalize a component while it still owns query branching.

4. Promote the generic behavior into `src/core/ui` if it is truly reusable.
   Otherwise keep it in the feature as a thin adapter.

5. Separate canonical state from derived layout state.
   For tables/boards, explicitly decide:
   - canonical columns/items
   - displayed layout structure
   - viewport/rendered subset
   - semantic interaction state

6. For async surfaces, define the render pipeline explicitly.
   Decide:
   - who owns `loading | error | ready`
   - what outer frame stays mounted across states
   - which inner branches swap inside that frame
   - how loading/error states preserve footprint and focus expectations

7. Leave only feature-specific adapters where necessary.
   Adapters should map:
   - value shape
   - labels
   - icon/rendering config
   - domain-specific mutation or submit config

8. Delete the old specialized wrappers.
   Do not keep compatibility shims or alias exports.

9. Re-run:
   - targeted tests
   - `bun run typecheck`
   - targeted `eslint`
   - `ui-testability-contract` scan for touched UI
   - FTA cap check on changed UI files

## Output Standard

A successful refactor should leave the code in this shape:

- generic primitive has generic name
- feature adapter has feature meaning but minimal logic
- caller owns data fetching
- async surfaces keep a stable outer frame while inner state changes
- no duplicate entity-named variants remain without a true behavioral reason
- selector/test ID contract remains stable

If you cannot collapse two components, explicitly state the real behavioral difference that justifies keeping them separate.

If you cannot articulate that difference, they should probably be one component.
