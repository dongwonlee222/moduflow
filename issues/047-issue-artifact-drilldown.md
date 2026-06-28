# Issue: `047-issue-artifact-drilldown`

**Status: backlog** — created 2026-06-28. Part of goal `visual-workbench`, Axis A (view). This is the L2 layer of the documented L0–L3 IA.

## Goal

Let a human click one issue and see **that issue's** planning artifacts in one place: spec, benchmark, user scenario, IA, customer journey, screen plan, diagrams, plus its history — per project. This is the "추후 문제가 생기면 사람이 산출물을 확인한다" surface.

## Distinct from 045 (do not conflate)

- `045` = issue **graph**: nodes = issues, edges = relationships, color = status. A *relationship* view across issues.
- `047` = issue **artifact panel**: drill *into* a single issue's `specs/<issue>/` contents. A *depth* view of one issue.

They compose (graph → click node → 045 hands off to 047), but they are different features. 045 as written does not satisfy this.

## Core principle: show what exists

Render only the artifacts that are actually present in `specs/<issue>/` (and related `memory/`/`workspace/` entries). Never force empty sections — consistent with `046`'s selective-artifact principle. An issue with only `spec.md` shows just that.

## Scope

- A per-issue view listing/linking the issue's existing artifacts (`spec.md`, `plan.md`, `tasks.md`, `status.md`, and — when present — `design-brief.md`, `prototype.md`, `analysis.md`, `metrics.md`, benchmark, diagrams) with its lifecycle history.
- Reuse the `042`/`044` generation pattern (Python → self-contained HTML, zero backend) and surface via `product:dashboard` or a sibling command.
- Per-project by construction (reads the project's own `specs/`).

## Out of Scope

- The issue graph itself (→ `045`).
- Producing the artifacts (→ `046`).
- Interactive editing/creation (later goal stage).

## Open question (decide in spec)

- Standalone command vs a mode of `product:dashboard` vs the click-target of the `045` graph. Likely: 045 graph node → opens 047 panel.

## Reference (benchmarked)

Visualization libraries benchmarked for this view: `memory/evidence/2026-06-28-visualization-library-benchmark.md` — decision: drill-down needs **no JS library** (Python markdown→HTML), Chart.js only when a metrics artifact is present, Mermaid code-fences render natively on GitHub/Obsidian.

## Related

- Goal `visual-workbench` (Axis A)
- `042-decision-graph-dashboard`, `044-product-dashboard-command` (pattern + command surface reused)
- `045-issue-graph-visualization` (the graph that hands off to this panel)
- `046-planning-artifact-templates` (produces what this renders)
- Evidence: `memory/evidence/2026-06-28-visualization-library-benchmark.md`
