# Issue: `046-planning-artifact-templates`

**Status: done** — created 2026-06-28, completed 2026-06-28. Part of goal `visual-workbench`, Axis C (planning-artifact depth). Supersedes the dropped "spec mermaid embed" scope.

## Outcome

- `commands/product-spec.md` enhanced with the 4 benchmarked elements: clarify-first (AI asks 3-5 questions), required `## Non-Goals` + `## Alternatives Considered`, default Mermaid block (renders on GitHub/Obsidian), prev/next pipeline pointers. Selective-depth note keeps heavier artifacts demand-driven.
- `specs/046-planning-artifact-templates/spec.md` written as the dogfood — first spec under the new template (core 3: requirements/solution/diagram).
- Fixed a GitHub-rendering bug: 4-backtick outer fence so the inner mermaid fence nests correctly.
- Closed at spec stage by design: the deliverable *is* the template + its first exercised use. No separate plan/execute needed.
- Deferred (demand-driven): scenario / IA / journey / screen templates and the same clarify-first treatment for `product:design`/`analyze` — pull when an issue warrants it.

## Goal

Make ModuFlow's planning-artifact chain *real* — but **selectively, never forced per issue**. The commands (`product:opportunity`/`research`/`benchmark`/`design`/`prototype`/`analyze`) are defined, yet across 32 spec folders there are **0** `design-brief.md`, **0** `prototype.md`, **0** `analysis.md`. The chain has never been exercised, so its templates are unvalidated.

## Why this matters

A PM should be able to take an issue to planning depth — requirements→benchmark→solution, scenario→IA→journey→screens→diagrams — when the issue warrants it. Today that depth has no proven templates to reach for. The decision-graph and drill-down views (Axis A) are empty without these artifacts behind them.

## Core principle: selective, not mandatory

Per the owner: **do not create every artifact on every issue — produce them only when judged necessary.** A UX feature warrants screens and a journey; a refactor or infra issue does not. The work is a good template + a judgment guide, not a forced pipeline that dirties every issue with empty sections.

## Scope

1. **Template quality** — harden the templates for the planning chain, benchmarked against strong external references (this is the ModuFlow way: absorb known-good patterns):
   - requirements / pain-point analysis
   - case benchmarking
   - solution definition
   - user scenario
   - information architecture (IA)
   - customer journey
   - detailed screen plan
   - diagrams (sequence / flow)
2. **Judgment guide** — a short rubric for which artifacts an issue warrants, so the depth is opt-in and proportional.
3. **Wire to existing commands** — templates land where the commands already write (`specs/<issue>/design-brief.md`, `prototype.md`, `analysis.md`, etc.); do not invent a parallel artifact tree.

## Out of Scope

- Forcing artifacts on every issue.
- The L2 view that renders these artifacts (→ `047`).
- A new artifact taxonomy — reuse the existing `specs/<issue>/` layout and adapter `writes` targets.

## Open question (decide in spec)

- External references to benchmark templates against: which sources (the planning-harness write-up, plus other well-known PM/UX artifact standards) and how to credit them in `memory/benchmark/`.

## Reference (benchmarked)

External templates benchmarked for this issue: `memory/evidence/2026-06-28-planning-artifact-templates-benchmark.md` — planning-harness skill chain, ai-dev-tasks PRD (★7.7k), ml-design-docs, Mermaid journey, utext IA. Use it as the source for template patterns; the 5 recommendations there are the spec's starting point.

## Related

- Goal `visual-workbench` (Axis C)
- `047-issue-artifact-drilldown` (renders what this produces)
- `043-memory-relationship-capture-prompts` (sibling: data quality, Axis B)
- Adapters `product-design`, `spec-kit`, `data-analytics` (where the chain's skills are vendored)
- `docs/visual-workbench-and-planning-harness.md` (planning-harness analysis, L0–L3 IA)
- Evidence: `memory/evidence/2026-06-28-planning-artifact-templates-benchmark.md`
