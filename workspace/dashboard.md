# ModuFlow Dashboard

## Current Phase

Goal `visual-workbench`: moving ModuFlow toward a visual workbench (graphs + per-issue artifact drill-down) while keeping Git-native Markdown canonical. Organized into 3 axes — View / Data quality / Planning-artifact depth.

## Active Goal

- `visual-workbench`: see and (eventually) act on issues, relationships, memory, and planning artifacts through a visual surface, per project. See `workspace/goal.md`.

## Active Issue

- None active. Next suggested: `043-memory-relationship-capture-prompts` (Axis B) — `product:spec 043`. 045's cross-links are sparse until this lands.

## Recently Completed

- `045-issue-graph-visualization`: **L1 project view** — `product:dashboard` → two-tab `이슈 그래프` + `지식 그래프` (`memory/dashboard.html`) + per-issue/per-memory detail panels (derived). Goal-box grouping, supersedes+related edges (toggle), `issue_id` cross-links, active-issue highlight/zoom, light drag motion, Korean UI. Spun off `049` (Korean artifact bodies).
- `047-issue-artifact-drilldown`: L2 per-issue artifact panel — `product:dashboard --issue <id>` → `memory/issue-<id>.html` (derived/`.gitignore`d). All-CDN (`marked`+`mermaid`, zero Python dep), renders only existing artifacts. Reversed spec Alternatives #4 at plan stage (documented).
- `046-planning-artifact-templates`: enhanced `product:spec` template (clarify-first, required Non-Goals + Alternatives, default Mermaid, pipeline pointers); dogfooded via `specs/046/spec.md`. Core 3 first; heavier artifacts demand-driven.
- `044-product-dashboard-command`: exposed the decision graph as ModuFlow-native `product:dashboard` (`/moduflow 그래프`); routed in `moduflow.md` + `skills/index/SKILL.md`; `dashboard.html` is derived/`.gitignore`d.
- `042-decision-graph-dashboard`: interactive Cytoscape memory-graph dashboard generated from `memory/` frontmatter (supersedes static-Mermaid `041`).
- `040-automatic-memory-candidate-capture`: automatic memory candidate capture with `--candidates/--approve/--reject/--capture`, 14-day stale pruning, released-status auto-capture.

## Queue (goal `visual-workbench`)

- `043-memory-relationship-capture-prompts` (backlog, Axis B) — capture memory relationships at write time so both graphs aren't sparse (045's cross-links depend on this).
- `048-artifact-lifecycle-sync` (backlog) — auto-propagate issue lifecycle changes to derived views (dashboard.md, etc.); this very staleness is the motivation.

## Blockers

- None.

## Verification

- `python3 scripts/release_check.py` passed (exit 0) after each of issues 042/044/046/047/045.
- `python3 -m unittest tests.test_project_memory` passed (29 tests).
- Note: this dashboard was stale at `040` until 2026-06-28; resynced manually. Auto-sync tracked as `048`.

## Next Command

`product:status`
