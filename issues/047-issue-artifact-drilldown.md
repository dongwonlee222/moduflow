# Issue: `047-issue-artifact-drilldown`

**Status: done** — created 2026-06-28, started 2026-06-28, done 2026-06-28. Part of goal `visual-workbench`, Axis A (view). This is the L2 layer of the documented L0–L3 IA.

## Outcome

- Built `render_issue_panel()` + `_collect_issue_artifacts()` + `_resolve_issue_slug()` in `scripts/project_memory.py`; new `--issue <id>` flag emits `memory/issue-<id>.html` (derived, `.gitignore`d).
- **Architecture (reversed spec Alternatives #4 at plan stage):** all-CDN — `marked` 12.0.2 + `mermaid` 11.4.1 pinned, Python collects+assembles only, **zero Python dependency**; reuses the 042/044 render path. Rationale + reversal documented in `plan.md`, spec Alternatives #4, and the visualization benchmark evidence (no silent change).
- Surfaced as a **mode of `product:dashboard`** (`--issue <id>`), per spec Goal #2 — no new command. `commands/product-dashboard.md` documents it.
- Renders **only existing artifacts** (Issue header + spec/plan/tasks/status + any warranted *.md), in fixed order; missing artifacts omitted, no empty stubs; no-spec-folder degrades to a "no artifacts yet" panel. Accepts bare number or full slug.
- Tests: 3 added (present-only / number↔slug parity / graceful degrade) → 24 pass. Render integrity verified (JSON round-trip, Mermaid fence preserved, no `</script>` leak, CDN pins present). `release_check` exit 0.

## Progress

- Spec written: `specs/047-issue-artifact-drilldown/spec.md` (under the 046-enhanced spec template).
- Decisions (clarify-first): entry = **mode of `product:dashboard`** (`--issue <id>`); first scope = **single-issue panel**; display = **section embed + Markdown/Mermaid render, existing artifacts only**.
- Plan: `specs/047-issue-artifact-drilldown/plan.md`; tasks: `specs/047-issue-artifact-drilldown/tasks.md`.

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
