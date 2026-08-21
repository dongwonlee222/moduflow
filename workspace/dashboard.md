# ModuFlow Dashboard

## Current Phase

Goal `trustworthy-execution-and-project-knowledge`: Issues 109 and 110 are merged. Issue 103 specification, implementation plan, and readiness gate are complete; execution approval is next.

## Active Goal

- `trustworthy-execution-and-project-knowledge`: make execution repository-safe and project knowledge reproducible. See `workspace/goal.md`.

## Active Issue

- `103-atomic-lifecycle-state-transaction` (phase: execute). Canonical: `issues/103-atomic-lifecycle-state-transaction.md`.

## Priority Queue — 2026-08-21

- Merged: `109` canonical project-context consumer convergence — PR #41 merged as `9df5f02` after local and GitHub CI verification.
- Merged: `110` project operation capability enforcement — [PR #42](https://github.com/dongwonlee222/moduflow/pull/42) passed CI and merged as `5f173f4`; post-merge source release check passed.
- Now: `103` atomic lifecycle state transaction — P0; specification and eight-task implementation plan are ready, readiness gate passed, explicit execution approval next.
- Parallel before next release: `111` runtime provenance and validation-mode separation — P1, does not block 103.
- Verified intake: four Issue 102 findings accepted and mapped to exactly three non-duplicate issues in `workspace/reviews/2026-08-21-issue-102-post-release-validation.md`.
- Shipped: `102` project registry/resolver merged as `010eee8`; 1,225 tests and source release check passed, package source version 0.3.49.
- Shipped: `098` selective Spec Kit validation adapter merged via PR #37 as `513e08f`, installed locally as ModuFlow 0.3.48, and remains project-opt-in only.
- Shipped: `097` merged via PR #36 as `46f98c0`; routing simulation and CI passed.
- Shipped: `095` merged via PR #33 as `f4029f3`; post-merge release check passed.
- Then: `086` project-aware production/playbook dashboard.
- Also ready: `087` Korean GitHub PR review surface, `090` project knowledge registry — both independent.
- Later: `090` → `091` → `092`; `082` before `083`/`084` (081's review found worker prompts carry OpenAI guidance on every host).

## Recently Completed

- `110-project-operation-capability-enforcement`: project resolution is separated from authorization; 64 mutation surfaces are centrally classified and guarded, 1,339 tests plus CI passed, and PR #42 merged as `5f173f4`.

- `109-canonical-project-context-consumer-convergence`: all project-aware consumers now use one validated canonical context; the repository guard reports 22 reviewed fixed/default literals and zero runtime, unclassified, prohibited, or stale exceptions. Full discovery passed 1,248 tests and the release check is green.

- `093-frontmatter-issue-schema-readiness-gate`: one shared issue parser (`scripts/project_issue_schema.py`, 2,545 lines) now feeds lifecycle, loop, doctor, validation, MCP, and dashboard; `ready` became a computed result instead of a field an issue can assert. Reviewed 2026-07-25 with verdict approve-with-conditions (both cleared) and merged as `11190b4` via PR #31. The review refuted its own fail-open hypothesis but found and fixed a real crash: non-file `*.md` sources were silently skipped, so a directory-shaped issue file raised `IsADirectoryError` out of the loop. Spun off `095`.
- `081-gpt-5-6-model-tier-guidance`: GPT-5.6 tier examples documented against the durable `deep`/`balanced`/`fast` schema; merged as `1e5144a` via PR #32. Recovered from an uncommitted working tree where it had been marked done since 2026-07-10 and was silently absent from the 0.3.26 release. Spun off `082`, `083`, `084`.

- `030-project-memory-layer`: legacy prototype audit completed on 2026-07-21; foundation commit `5929502` retained and remaining registry/migration scope superseded by Issue 090.
- `080-reference-improvement-backlog`: PR #16 merged with successful CI on 2026-07-09; missing human-approval and release evidence were reconciled with Dongwon Lee approval on 2026-07-21.
- `079-plan-discipline-skill-matrix`: PR #13 merged with successful CI on 2026-07-09; lifecycle and release evidence were reconciled on 2026-07-21.
- `078-frontend-qa-template-pack`: PR #15 merged with successful CI on 2026-07-09; lifecycle and release evidence were reconciled on 2026-07-21.
- `077-implementation-readiness-gate`: PR #14 merged with successful CI on 2026-07-09; lifecycle and release evidence were reconciled on 2026-07-21 after fresh 582-test verification.
- `089-verified-code-review-intake-and-remediation-routing`: implementation and staged review passed; four important review findings were fixed by TDD, and Dongwon Lee approved PR #26 for merge on 2026-07-16.
- `088-canonical-repository-remote-identity-gate`: implementation and staged review passed; Dongwon Lee approved PR #25 for merge on 2026-07-16 after CI and canonical identity checks passed.
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

- `085-project-production-records-and-playbooks`: done; PR #17 merged and version 0.3.23 released after Korean-first human approval.
- `086-project-aware-production-library-dashboard`: ready; global project selector plus project-scoped production/playbook views are unblocked for `product:design 086-project-aware-production-library-dashboard`.
- `087-korean-github-pr-review-surface`: make GitHub PR bodies, review comments, and approval summaries Korean-first when a Korean review packet exists. Next: `product:spec 087-korean-github-pr-review-surface`.
- `071-spec-code-converge-check`: post-implementation code-vs-spec divergence check (P3).
- `072-lifecycle-hooks-automation`: SessionStart state injection + auto lifecycle sync hooks (P4).
- `073-project-constitution-steering`: standing versioned project principles replacing per-plan Global Constraints re-authoring (P5).

## Blockers

- None.

## Verification

- Issue `095` corrective implementation (2026-07-27 at `4f5d14a`): Task 1
  focused suite `92/92 PASS`; five-module focused suite `195/195 PASS`; zero
  expected failures. Independent Task 1/Task 2 spec and quality reviews passed
  after two Important base-selection findings were fixed and re-reviewed in
  `4f5d14a`. Artifact validation is `valid: true` with `errors: []`; lifecycle
  drift is `[]`; `git diff --check` is clean. Full unittest discovery, release
  check, and final whole-branch review remain F4.
- Issue `095` redesign trigger (2026-07-27 at `bfa4157`): focused resolver
  tests reached `221/221 PASS`, but full discovery failed 2 of 885 because an
  unrelated historical octopus ambiguity reached the release gate. Independent
  review separately reproduced a normal trunk advance being treated as an
  ambiguous base. The approved fix is per-issue merge-base fork points plus
  diagnostics projected to the caller's commit/issue range. Twenty failure
  families are now preserved in an append-only corpus; future requirements,
  invariant tests, and Critical/Important findings must trace to `FH-*` ids.
- Issue `095` redesign plan (2026-07-27): six guarded TDD streams now replace
  the global-base patch loop. Execution starts by isolating the Git graph
  snapshot, then lands per-topic fork points before any consumer migration.
- Issue `095` execution start (2026-07-27): repository identity and
  implementation readiness passed. Worker analysis selected sequential
  host-subagent execution T01→T09 due shared graph/resolver state.
- Issue `095` T01 (2026-07-27 at `8068f98`): graph snapshot and Git failure
  semantics completed. Four direct consumer suites passed 105/105; separate
  spec and quality reviews approved with no open findings. `FH-021` and
  `FH-022` are regression-captured.
- Issue `095` T02 (2026-07-27 at `d25bbdd`): per-issue historical fork-point
  derivation completed. Review caught and closed snapshot ref drift,
  criss-cross incomplete merge bases, and a missing comparable-candidate
  invariant as `FH-023`–`FH-025`. Four direct consumer suites passed 117/117;
  final review has no open finding.
- Issue `095` T03 (2026-07-28 at `2a000c0`): historical topic deltas, stacked
  exclusions, publication recovery, cached diagnostic replay, and independent
  range projection completed. The cumulative five-module gate passed 231/231
  to terminal exit; independent spec and quality reviews have no open finding.
- Issue `095` T04 (2026-07-28 at `24bfd3c`): merge boundary and content claims
  are separate, complex side ownership requires graph corroboration, and
  overlapping topic intervals are partitioned independently of subject,
  parent, or issue-id order. The cumulative gate passed 267/267; final spec
  and quality reviews have no open finding.
- Issue `095` T05 (2026-07-28 at `8221ea0`): fatal errors and scoped
  diagnostics are structured, compatibility errors are stable and deduplicated,
  and bare/indexed lookups use one policy without per-commit `git show`.
  The cumulative gate passed 279/279; final reviews have no open finding.
- Issue `095` T06 (2026-07-28 at `d5da824`): release linkage scopes one shared
  attribution result to behavior SHAs; out-of-range ambiguity is excluded,
  in-range ambiguity remains fail-closed, and neutral-only ranges build no
  attribution. The cumulative gate passed 281/281 with clean final reviews.
- Issue `095` T07 (2026-07-28 at `94ca3d4`): converge requests one issue-scoped
  result, preserves legacy payloads, and carries structured diagnostics/fatal
  errors. Prebuilt indexes are safely reprojected without Git rebuild. The
  six-module gate passed 335/335.
- Issue `095` T08 (2026-07-29 through `8209855`): all 36 failure records map
  to an independent executable manifest and all 70 required-component
  deletions are detected. The behavior gate passed 351/351 to terminal exit;
  independent spec and quality reviews approved with no Critical or Important
  finding. Current task is T09 full verification and whole-branch review.
- Issue `095` T09 pre-review (2026-07-29 at `a1616d5`): the first full
  discovery preserved `FH-037` after 1016 tests failed twice because mutation
  injection crossed two unittest module identities. `5d1509a` fixed the owner
  module boundary and independent FH-037 spec/quality reviews approved 0/0/0.
  Fresh discovery passed 1018/1018 in 288.945 seconds; spec findings are
  0/0/0, release/project are valid with empty errors, lifecycle drift is `[]`,
  and diff check is clean. Read-only Issue 093 evidence is 56 commits/46 files
  with the schema included and no diagnostics/fatal/errors. Historical
  octopus ambiguity remains in the unscoped corpus, stays outside current
  release errors, and fails closed when explicitly scoped. This was the
  pre-review checkpoint before the final whole-branch approval below.
- Issue `095` T09 final (2026-07-29 at `f19762d`): whole-branch review findings
  `FH-038`–`FH-040` and the FH-029/FH-035 recurrences were preserved and
  corrected. Publication recovery now uses the captured graph with constant
  external calls, unrelated side refs cannot silently move a topic fork, and
  terminal evidence requires positive counts and duration. Independent final
  spec and quality reviews both approved 0/0/0. Controller verification passed
  1035/1035 in 417.627 seconds; spec is 0/0/0, release/project are valid with
  empty errors, lifecycle drift is `[]`, and diff/status are clean.
- Issue `095` PR review (2026-08-03): verified branch pushed and PR #33 is
  ready for review at `https://github.com/dongwonlee222/moduflow/pull/33`.
  Fresh release check and GitHub CI passed; the merge state is clean/mergeable.
  Korean review packet and PR handoff are current; merge still requires human
  approval.
- Issue `095` release (2026-08-03): Dongwon Lee approved proceeding in the
  Korean Codex review flow. PR #33 merged as `f4029f3`; a fresh release check
  on merged `main` returned `valid: true`, `errors: []`. Repository-source
  integration is complete; plugin/cache publication remains held for Issue 096.
- Proposed Issue `096` handoff: explicit evidence writes, issue-id traversal,
  repo-external symlinks, and write announcements. Issue 095 does not modify
  Issue 096; before execution its canonical issue must add these acceptance
  criteria, its dependency on 095, and the plugin-update gate. Installed plugin
  update remains on hold until both issues are safe.
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
- Issue `093` E2 (2026-07-25): spec consistency `0/0/0` with 12/12 coverage, full unittest `732/732`, project validation valid, lifecycle drift `[]`, release check valid, and `git diff --check` clean at implementation HEAD `ab682e3`.

## Next Command

`product:status`
