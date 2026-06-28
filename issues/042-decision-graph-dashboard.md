# Issue: `042-decision-graph-dashboard`

**Status: done** — created 2026-06-28. Supersedes `041-decision-graph-native-mermaid-rendering` (static Mermaid hardening absorbed into an interactive dashboard).

## Goal

Turn the chat-only decision-graph into an interactive, openable dashboard the user can actually use — drag, zoom, click a node to its source `.md` — while staying Git-native (no npm, no build, no server).

## Decision (spine)

Render with **Cytoscape.js**, pinned via CDN, not d3 (too raw) and not React Flow (pulls a full React app stack into a pure-Python repo).

- The graph engine is **adopted, not built**: Cytoscape draws; ModuFlow emits only node/edge data from `memory/` frontmatter.
- `source-adapter-policy` (vendor/overlays/adapters) targets **skills/plugins**, not a single render library — so a CDN version pin is the whole "adoption". No vendoring ceremony for one `<script src>`.
- "Keep getting updates" = a deliberate, tracked CDN/version refresh, not silent auto-update.
- Tier 2 (React Flow + elkjs webapp) stays gated behind proven intuitiveness bottleneck; data layer carries over if it ever happens.

Background: `docs/dashboard-visualization-research.md`.

## Scope (done)

- `parse_frontmatter`: read YAML block-list relationships (`key:` then `  - item`), not just inline `[...]`. Fixed the silent edge-drop that made the graph look empty.
- `_collect_graph(root) -> (nodes, edges)`: extracted shared helper; `generate_memory_graph` Mermaid output kept byte-identical.
- `_normalize_target`: drop external URLs, strip file-path targets to node ids — removes URL-node noise, connects path-style references.
- `--dashboard` CLI flag → writes self-contained `memory/dashboard.html` (Cytoscape CDN + injected elements JSON, cose layout, click-to-source).
- Edge conventions carried over: supersedes solid, references/depends_on dashed.
- Relationship backfill: added real `gitcanon supersedes portable` to frontmatter (content-verified).
- Tests: +3 (block-list parser, target normalization, dashboard embed). Full suite green.

## Out of Scope

- Drag-to-writeback editing (WYSIWYG → frontmatter). Click-through-to-md edit is enough at this stage.
- React Flow / elkjs webapp (Tier 2).
- fcose layout (optional follow-up if disconnected-node spread needs more than cose tuning).

## Related Issues

- `041-decision-graph-native-mermaid-rendering` (superseded — its edge-extraction logic lives on in `_collect_graph`)
- `037-delegation-level-gate-and-memory-context-graph` (foundation — original Mermaid graph)
- `030-project-memory-layer` (memory frontmatter source)

## Related Artifacts

- `scripts/project_memory.py` (`_collect_graph`, `render_dashboard_html`, `--dashboard`)
- `memory/dashboard.html` (generated)
- `docs/dashboard-visualization-research.md`
