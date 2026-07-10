# ModuFlow Dashboard

## Current Phase

Goal `team-visibility-onboarding`: make work visible to non-local collaborators (GitHub Issues projection, `054`) and give first-time users a ranked entry path (`055`). Previous goal `visual-workbench` closed 2026-07-05 with all three axes shipped.

## Active Goal

- `team-visibility-onboarding`: external collaborators see progress from the GitHub UI; new users get a small ranked entry path. See `workspace/goal.md`.

## Active Issue

- `085-project-production-records-and-playbooks`: implementation, dogfood, and independent review complete; ready for PR handoff.

## Recently Completed

- `070-spec-consistency-analyze`: `scripts/spec_consistency.py` runs a deterministic pre-execution check over spec↔plan↔tasks — AC coverage (token-overlap "possibly uncovered" warns), vague-term lint (no-digit bullets), structural stream tracing — report-only JSON, recommended in `product:plan`/`product:execute`. Also fixed a pre-existing gate false positive (placeholder paths in issue prose treated as real links). Dogfood on specs/069: clean.
- `069-issue-dependency-priority-model`: issues now carry `**Priority: p0-p3**` and `**Blocked-by:**` metadata (blocked_by canonical, blocks derived); `ready_issues`/`--ready`/`moduflow_ready` answer "지금 시작 가능한 일" priority-sorted; dangling refs, cycles, and active-with-unmet-blocker are drift-gate errors. Also repaired the pre-048 schema still emitted by the issue template and the orphaned generator. Verification caught 4 real findings (prose false-parse, RecursionError on deep chains, generator landmine, silent active-blocked state) — all fixed with regression tests.
- `068-machine-query-surface`: `scripts/mcp_server.py` is now a real persistent stdio MCP server (4 read-only tools: status/issues/issue_get/doctor, payloads versioned `moduflow.mcp.v1`), registered in `.mcp.json` via `${CLAUDE_PLUGIN_ROOT}`; `project_lifecycle.py` gained `--issues` JSON. Independent verification caught and we fixed a real path-traversal disclosure, a crash-on-non-object-JSON, a schema clobber, and a duplicated parser — 21 module tests, 248 total.
- `054-github-issue-sync`: `scripts/project_github_issues.py` projects a git-file issue to a GitHub Issue (opt-in, one-way): title + `moduflow:<status>` label + canonical-source link, URL written back into the issue's `## Links` as the create-vs-update discriminator; wired into the `061` done-flow as a post-push label refresh. Built subagent-TDD + independently verified (SPEC pass; 8 of 11 quality findings fixed, 3 accepted with rationale). Live projection not yet run — ask-first.
- `055-command-surface-onboarding`: first issue of goal `team-visibility-onboarding` — `product:start` now ends with a 3-command core path (goal → issue → status) instead of the command wall, `product:status` closes with ranked ≤3 next commands from loop state, and README's flat 37-command list is regrouped into Core path / Build cycle / On-demand. Doc-only; no command renamed or removed.
- `065-installed-plugin-staleness-detection`: `product:doctor` now reports (soft warning, exit unchanged) when the installed Claude Code plugin (`installed_plugins.json`) or Codex personal cache is behind the repo's own `.claude-plugin/plugin.json` version, with the exact update commands — the tool that detects everyone else's drift can now see its own. Built via implementation subagent + independent verification subagent; 2 reviewer-reproduced defects (lexicographic version sort, missing name guard) fixed with regression tests.
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

## Queue (post-benchmark, 2026-07-05 — goal `team-visibility-onboarding` issues complete)

- `085-project-production-records-and-playbooks`: project-local recurring production records and human-approved playbooks implemented and reviewed. Next: `product:pr 085-project-production-records-and-playbooks`.
- `086-project-aware-production-library-dashboard`: spec complete for a global project selector plus project-scoped production/playbook views. Next: `product:design 086-project-aware-production-library-dashboard`; implementation blocked by `085`.
- `071-spec-code-converge-check`: post-implementation code-vs-spec divergence check (P3).
- `072-lifecycle-hooks-automation`: SessionStart state injection + auto lifecycle sync hooks (P4).
- `073-project-constitution-steering`: standing versioned project principles replacing per-plan Global Constraints re-authoring (P5).

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
