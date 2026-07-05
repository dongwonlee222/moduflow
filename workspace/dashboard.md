# ModuFlow Dashboard

## Current Phase

Goal `visual-workbench`: moving ModuFlow toward a visual workbench (graphs + per-issue artifact drill-down) while keeping Git-native Markdown canonical. Organized into 3 axes — View / Data quality / Planning-artifact depth.

## Active Goal

- `visual-workbench`: see and (eventually) act on issues, relationships, memory, and planning artifacts through a visual surface, per project. See `workspace/goal.md`.

## Active Issue

- None active. Run `product:status` to pick the next issue.

## Recently Completed

- `066-legacy-issue-status-migration`: the 10 pre-048 issue files with no canonical `Status:` line now carry one, evidence-judged per file (subagent-gathered): `012`/`013`/`030`/`033`/`040` done, `014`/`017`/`018` superseded-by-`019`, `015`/`016` superseded-by-`023` — every issue file now parses to its true state; `grep -L "Status:"` returns empty.
- `067-upstream-adapter-absorption`: adapters had been frozen since 2026-06-12 while upstream moved 100+ commits each; relevance-filtered reviews found spec-kit templates and kwp product-management/productivity trees unchanged, but superpowers v6 rewrote subagent review + plan-writing practices — absorbed into `product-review.md` (read-only reviewers, no finding suppression, dual verdicts) and `product-plan.md` (Global Constraints, Interfaces, task right-sizing). All github adapters now carry `reviewed:` blocks; `--sync` stamp now requires an actual review (`053`'s stamp-without-review hole closed).
- `058-git-write-fallback-via-github-api`: `scripts/project_git_handoff.py`'s `check_commit_capability()` classifies `local-git-write` / `github-api-commit` / `blocked` before any stage/commit/push, with a non-destructive `.git` write probe (never touches `index.lock`). `product:pr`/`product:release`/`product:sync` now instruct agents to use the GitHub API fallback instead of asking the user for terminal commands; `project_pr.py`'s PR handoff records the chosen `commit_mode`/`commit_reason`.
- `064-version-bump-policy-and-enforcement`: advisory review of `063` found its version-bump step was convention-only (an agent could skip it, same failure class it fixed) and that `feat`→minor changed cadence unasked. Corrected: `feat`/`fix` now both bump patch (matches this repo's pre-063 history), and `release_check.py` gained a `version_bump_gate` that fails the pre-push hook if a bump-worthy commit lands with no version change. Also ran `010`'s sync mechanism to clear a live desync (`.codex-plugin/plugin.json` was still `0.2.15`, now `0.3.0+codex...`).
- `063-version-bump-on-done`: `.claude-plugin/plugin.json`'s version now bumps automatically as part of `061`'s auto-commit-push-on-done flow, classified from the commit message's Conventional-Commit prefix (`feat`→minor, `fix`→patch, `!`/`BREAKING CHANGE`→major, else none) — closes the gap where 7 issues shipped this session with zero version bumps.
- `053-vendor-freshness-gate`: `scripts/vendor_freshness.py` compares `vendor.lock.json` GitHub sources against their actual latest commit (via `gh api`), same drift-gate pattern as `048`/`062` extended to external sources. Ran against the live lock file — all four sources had never been reviewed; `--sync` recorded current baselines.
- `062-detect-unmerged-branch-work`: `inspect_repo_sync()` now scans remote branches ahead of `origin/main` for `Status: done` issues that aren't done there, reporting via `unmerged_branch_work` — catches finished work sitting on a forgotten/other-tool branch (found this session: 056/057 were done on `codex/058-...`, invisible to `origin/main`-only comparison).
- `061-auto-commit-push-on-issue-done`: agents now commit+push immediately when an issue reaches `Status: done` and `release_check.py` passes, instead of waiting for a separate user request — fixes a cross-machine gap where completed work sat unpushed until noticed.
- `059-auto-fetch-in-repo-sync`: `inspect_repo_sync()` now fetches remote refs itself (5s timeout, non-interactive) before comparing, with `fetched`/`fetch_warning` fields and a stale-cache recommendation on failure; `product:sync`/`product:status` no longer need a manual `git fetch` step first.
- `060-cross-agent-output-format-convention`: added project-root `AGENTS.md` (read natively by Antigravity/Claude Code/Codex) codifying a situation → shape table and deliberate whitespace-rhythm rules, replacing per-agent improvisation; `docs/host-adapter-guidance.md` now points to it.
- `056-dashboard-database-list-view`: released (merged from `codex/058-...` branch, 2026-07-05); dashboard now has an `이슈 DB` list view, Korean descriptions, issue detail Korean overview, Korean PR review packet generation, and GitHub PR preflight.
- `057-korean-human-review-packet`: released (merged from `codex/058-...` branch, 2026-07-05); Korean human-review packets are now a release gate with approval evidence.
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

- `054-github-issue-sync`: opt-in sync from `issues/*.md` to actual GitHub Issues (status label, one-way local→GitHub).
- `055-command-surface-onboarding`: rank/stage the 20+ `product-*` commands for a first-time user instead of listing the full surface.
- `065-installed-plugin-staleness-detection`: doctor warning when the installed Claude Code/Codex plugin copy is behind the repo's own version (found live: 0.2.6 installed vs 0.3.2 repo).

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

`product:status`
