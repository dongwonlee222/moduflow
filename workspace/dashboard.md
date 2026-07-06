# ModuFlow Dashboard

## Current Phase

Goal `visual-workbench`: moving ModuFlow toward a visual workbench (graphs + per-issue artifact drill-down) while keeping Git-native Markdown canonical. Organized into 3 axes — View / Data quality / Planning-artifact depth.

## Active Goal

- `visual-workbench`: see and (eventually) act on issues, relationships, memory, and planning artifacts through a visual surface, per project. See `workspace/goal.md`.

## Active Issue

- `058-git-write-fallback-via-github-api` (phase: execute). Canonical: `issues/058-git-write-fallback-via-github-api.md`.

## Recently Completed

- `056-dashboard-database-list-view`: released locally after human approval; dashboard now has an `이슈 DB` list view, Korean descriptions, issue detail Korean overview, Korean PR review packet generation, and GitHub PR preflight.
- `057-korean-human-review-packet`: released locally after human approval; Korean human-review packets are now a release gate with approval evidence.
- `034-memory-capture-and-sync-workflow`: released via PR #5; memory capture workflow now has review, PR, release, and Korean human-review packet artifacts, with follow-ups 056/057 registered.
- `052-draft-pr-review-handoff`: PR flow now supports early Draft PR / local PR-ready state, refreshes `specs/<issue>/pr.md` after review, and carries dashboard + issue drill-down evidence into the PR handoff before human approval.
- `051-autonomous-execute-review-visual-handoff`: execute/review flow now generates a review handoff, maps implementation/QA/PM-spec review to subagent-ready sections, requires verification, and surfaces the dashboard plus issue drill-down HTML for human visual inspection.
- `050-repo-sync-preflight`: repo freshness preflight for `product:sync`/`product:status`; detects gone upstream branches, local branches behind `origin/main`, remote-only issue files, no-upstream work branches, and dirty worktrees before trusting local Git-file artifacts.
- `049-bilingual-artifact-view`: English stays canonical; the 047 panel gains an `English / 한글` toggle that renders a `<name>.ko.md` sidecar when present (per-artifact EN fallback, hidden when none). New-artifacts-forward policy in `product-spec.md`. Dogfooded via `spec.ko.md`.
- `048-artifact-lifecycle-sync`: lifecycle drift detection + single propagation. `scripts/project_lifecycle.py` (`--state/--drift/--sync`); issue `Status:` is canonical; `validate`/`doctor` gate off `.moduflow/state.json` (loop-state retired); drift is a hard gate after reconcile. Dogfooded (synced this repo's divergence).
- `043-memory-relationship-capture-prompts`: write-time relationship capture (guided, not inferred) — `--list-ids` candidates, command-doc capture step (`--supersedes/--depends-on/--references/--issue-id`), `project_doctor` isolated-node soft hint (exit 0). Fills 045's sparse cross-links habitually.
- `045-issue-graph-visualization`: **L1 project view** — `product:dashboard` → two-tab `이슈 그래프` + `지식 그래프` (`memory/dashboard.html`) + per-issue/per-memory detail panels (derived). Goal-box grouping, supersedes+related edges (toggle), `issue_id` cross-links, active-issue highlight/zoom, light drag motion, Korean UI. Spun off `049` (Korean artifact bodies).
- `047-issue-artifact-drilldown`: L2 per-issue artifact panel — `product:dashboard --issue <id>` → `memory/issue-<id>.html` (derived/`.gitignore`d). All-CDN (`marked`+`mermaid`, zero Python dep), renders only existing artifacts. Reversed spec Alternatives #4 at plan stage (documented).
- `046-planning-artifact-templates`: enhanced `product:spec` template (clarify-first, required Non-Goals + Alternatives, default Mermaid, pipeline pointers); dogfooded via `specs/046/spec.md`. Core 3 first; heavier artifacts demand-driven.
- `044-product-dashboard-command`: exposed the decision graph as ModuFlow-native `product:dashboard` (`/moduflow 그래프`); routed in `moduflow.md` + `skills/index/SKILL.md`; `dashboard.html` is derived/`.gitignore`d.
- `042-decision-graph-dashboard`: interactive Cytoscape memory-graph dashboard generated from `memory/` frontmatter (supersedes static-Mermaid `041`).
- `040-automatic-memory-candidate-capture`: automatic memory candidate capture with `--candidates/--approve/--reject/--capture`, 14-day stale pruning, released-status auto-capture.

## Queue (goal `visual-workbench`)

- `058-git-write-fallback-via-github-api`: make ModuFlow automatically fall back to GitHub API commits when local `.git` writes are blocked, so users are not asked to run terminal Git commands.

## Blockers

- None.

## Verification

- `python3 scripts/release_check.py` passed (exit 0) after each of issues 042/044/046/047/045/043/048/049.
- `python3 -m unittest discover -s tests` passed (157 tests).
- `python3 -m unittest tests.test_project_sync -v` passed (4 tests) for Issue 050 RED/GREEN coverage.
- `python3 -m unittest tests.test_project_execution -v` passed (2 tests) for Issue 051 handoff coverage.
- `python3 -m unittest tests.test_project_pr -v` passed (2 tests) for Issue 052 PR handoff coverage.
- `python3 scripts/release_check.py .` passed for Issue 052 after PR evidence and subagent review fixes.
- `python3 scripts/project_memory.py . --dashboard` generated `memory/dashboard.html`.
- `python3 scripts/project_memory.py . --issue 051-autonomous-execute-review-visual-handoff` generated `memory/issue-051-autonomous-execute-review-visual-handoff.html`.
- `python3 scripts/project_memory.py . --issue 052-draft-pr-review-handoff` generated `memory/issue-052-draft-pr-review-handoff.html`.
- Lifecycle drift is now an automated gate (`048`); the Active Issue section + state.json are regenerated by `project_lifecycle.py --sync`.

## Next Command

`product:execute 058-git-write-fallback-via-github-api`
