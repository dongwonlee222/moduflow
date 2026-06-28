# Issue: `045-issue-graph-visualization`

**Status: done** — created 2026-06-28, started 2026-06-28, done 2026-06-28. Part of goal `visual-workbench`, Axis A. Scope **expanded** (2026-06-28, user decision) from "issue graph only" to the **L1 project view**: issue graph + memory graph, cross-linked, per project.

## Outcome

`product:dashboard` now generates a **two-tab project view** (`memory/dashboard.html`) — `이슈 그래프` + `지식 그래프` — plus pre-generated per-issue (`issue-<id>.html`) and per-memory (`mem-<id>.html`) detail panels (all derived/`.gitignore`d). Built in `scripts/project_memory.py`: `_collect_issue_graph` (status + supersedes + related parsing, no issue-file frontmatter), `_issue_linked_memory`, `_issue_elements` (goal-box compound grouping), `render_project_view`, `render_memory_panel`. Delivered, beyond the original graph scope, through iterative user feedback:

- **Cross-link (3 layers)**: issue node `🧠N` badge (toggle), click-preview of linked memory (kind icons), and the 047 panel's "연결된 지식" section. Memory node → "출처 이슈" jump. Powered by `memory.issue_id` (sparse → `043`).
- **flow = goal boxes**: issues grouped into compound goal boxes, number-ordered inside (preset layout). `supersedes` (solid) + `related` (dashed, **toggle, default on**) edges. Related parsed from `## Related` sections only, undirected-deduped.
- **Standalone viewing**: tab = full-screen single graph; `#issues`/`#memory` deep-link; badge + relation toggles.
- **Korean UI**, label-wrap fix (long titles wrap inside the box), light drag motion (border pop→ease-back), **active issue highlight + auto-zoom** (current issue = orange border, centered on tab open).
- **지식 상세**: memory nodes get a "상세 열기" panel rendering the entry body (Markdown/Mermaid), like the issue panel.

Tests: 29 pass (issue-graph status/supersedes, linked-memory map, goal grouping, project-view two tabs, 047 linked-memory section). `release_check` exit 0. Spun off `049-bilingual-artifact-view` (Korean artifact bodies) to keep scope tight.

## Goal

Do for issues what `042` did for memory: a read-only graph where nodes = issues, edges = supersedes/related/depends, color = status. See how the 44+ issues actually relate.

## Scope expansion — L1 project view (user decision, 2026-06-28)

The user asked for **both node graphs — 지식(memory) + 이슈(issue) — viewable per project, navigable between each other**. This is exactly the documented L1 layer (`project = goal + issue graph + memory graph`). So 045 delivers a per-project view that holds both graphs under one `product:dashboard` entry, cross-linked via `memory.issue_id`.

Decisions (clarify-first, settled with the user):
- **Container**: simplest that satisfies "see both, navigate between" — issue graph (new) beside the existing 042 memory graph under one per-project surface. **Not** a merged single canvas, not a new app (P12 / selective).
- **Relationship source (start cheap, reliable subset)**: parse `**Status:**` line for node color; **`supersedes` edges first** (status line + "Supersedes `NNN`" prose) — clean. Dense `## Related Issues` prose edges are noisy (22× `## Related Issues`, 5× `## Related`, each issue cites several) → added later, scoped/toggleable to avoid a 49-node hairball. **No frontmatter added to issue files** (forbidden without a 024-scoped decision).
- **Cross-links (the integration = what 047 deferred)**: issue node → its 047 panel; **047 panel → that issue's linked memory** (un-defers 047's linked-memory cut); memory node → source issue. Powered by `memory.issue_id` (already present on 5 of 8 entries — sparse, honest; ties to `043`).
- **Korean UI surface** (labels/help text only, not artifact bodies) — match 042's existing Korean help tone.

## Decision (spine)

Reuse the `042` generator pattern (Python emits node/edge JSON → Cytoscape, single self-contained HTML). The hard part is the relationship source, because issues have no frontmatter.

## Relationship Source — fork (decide in spec)

- **Cheap**: parse the `## Related Issues` section + `**Status:**` line. Brittle text parsing, zero schema change.
- **Proper**: give issues frontmatter (like memory) — `supersedes`/`depends_on`/`related`/`status`. A change to the Git-native artifact model; touches `024-artifact-schema-and-doctor-gates`, doctor/validation, and templates. Bigger, but makes issue relationships first-class and machine-readable.

Do not start adding frontmatter to issue files outside a dedicated decision.

## Scope

- Read-only issue graph rendered the same way as the memory dashboard.
- Status-colored nodes (done / backlog / superseded / active).

## Out of Scope

- Interactive editing/creation (later goal stage).
- The artifact-model schema change itself (separate issue if the "proper" path is chosen).

## Scope boundary vs 047

This issue is the issue **graph** — a relationship view across issues (nodes + edges + status color). It is **not** the per-issue artifact panel; clicking a node to see that issue's spec/benchmark/journey/screens is `047-issue-artifact-drilldown`. Expected composition: this graph's node click hands off to the `047` panel.

## Related

- Goal `visual-workbench` (Axis A)
- `042-decision-graph-dashboard` (pattern reused)
- `047-issue-artifact-drilldown` (the drill-down this graph hands off to — distinct feature)
- `024-artifact-schema-and-doctor-gates`, `git-native-artifact-model` (if frontmatter path chosen)
- Evidence: `memory/evidence/2026-06-28-visualization-library-benchmark.md` (Cytoscape confirmed for the graph)
