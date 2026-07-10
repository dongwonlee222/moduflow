# ModuFlow Roadmap

## Now

Team visibility and onboarding: make work visible to non-local collaborators (GitHub Issues projection) and give first-time users a small, ranked entry path instead of a 20+ command wall.

Active goal: `team-visibility-onboarding`

Previous goal `visual-workbench` closed 2026-07-05 — all three axes (View / Data quality / Planning-artifact depth) shipped: `042`–`047`, `049`, plus follow-ons `056`/`057`. See `workspace/goal.md` history note.

## Current Execution Queue

### `076-product-context-interview-and-readiness-loop`

- Outcome: ModuFlow keeps the fast issue path fast, while routing vague/risky/strategic requests through short shaping or panel-assisted questioning before issue/spec creation.
- Reason: The clearest product promise is not "more commands"; it is keeping AI agents aligned with product context without forcing every request through a long interview.
- Confidence: high
- Dependency: 020 simple loop UX, 046 planning templates, 075 AI-first issue fields.
- Next command: `product:spec 079-plan-discipline-skill-matrix`
- Status: done; merged via PR #12 and released locally in `specs/076-product-context-interview-and-readiness-loop/release.md`.

### `079-plan-discipline-skill-matrix`

- Outcome: `product:plan` shows which Superpowers disciplines and ModuFlow adapter skills each issue/task should use, such as writing-plans, TDD, product-design, data-analysis, Storybook/MSW, Playwright/QA, review, and verification.
- Reason: ModuFlow already contains Superpowers, but users should not have to know when each discipline should be activated.
- Confidence: high
- Dependency: 067 upstream adapter absorption, 073 constitution steering.
- Next command: `product:pr 079-plan-discipline-skill-matrix`
- Status: in_progress

### `077-implementation-readiness-gate`

- Outcome: `product:execute` checks implementation readiness before worker dispatch, including API contracts, test strategy, frontend fixtures, smoke checks, permissions, and release conditions.
- Reason: Agent execution fails most often when the plan lacks concrete contracts, not when the agent lacks coding ability.
- Confidence: high
- Dependency: 079 plan discipline matrix, 070 spec consistency analyzer.
- Next command: `product:pr 077-implementation-readiness-gate`
- Status: pr

### `078-frontend-qa-template-pack`

- Outcome: ModuFlow ships reusable templates for Storybook required states, MSW fixture catalogs, API contract mapping, Playwright smoke matrices, and QA evidence checklists.
- Reason: Frontend work needs state/fixture/test evidence before implementation and review can be trusted.
- Confidence: medium
- Dependency: 077 implementation readiness gate, 046 planning templates.
- Next command: `product:pr 078-frontend-qa-template-pack`
- Status: pr

### `080-reference-improvement-backlog`

- Outcome: Improvements discovered in reference repositories or templates are captured in a separate backlog and can be promoted later without polluting the active product issue queue.
- Reason: Reference repo insights appear during real work and currently risk disappearing or getting mixed into the wrong issue.
- Confidence: medium
- Dependency: 075 issue-less context capture.
- Next command: `product:pr 080-reference-improvement-backlog`
- Status: review

### `085-project-production-records-and-playbooks`

- Outcome: Each project preserves recurring production outputs, decisions, failures, reusable patterns, and approved playbooks without forcing existing asset folders into a central structure.
- Reason: Issue completion records what happened, but recurring banner, PR, proposal, Alimtalk, SMS, and Push work must improve the next production cycle.
- Confidence: high
- Dependency: existing project memory and candidate-promotion foundations (`030`, `040`, `043`).
- Next command: `product:release 085-project-production-records-and-playbooks` after merge
- Status: PR #17 automated review and CI passed; awaiting human merge approval.

### `086-project-aware-production-library-dashboard`

- Outcome: One global project selector controls Issue DB, production records, playbooks, knowledge, decisions, roadmap, and status across the dashboard.
- Reason: Projects have different folders and brand knowledge, so the dashboard must use registered project metadata without mixing project context or crawling arbitrary paths.
- Confidence: high
- Dependency: `085-project-production-records-and-playbooks`, `056-dashboard-database-list-view`, `047-issue-artifact-drilldown`.
- Next command: `product:design 086-project-aware-production-library-dashboard`
- Status: spec complete; design can proceed while implementation remains blocked by `085`.

### `074-sync-fetch-sandbox-handling`

- Outcome: Approval-sensitive hosts can run a top-level `git fetch` and then `project_sync.py --no-fetch`, avoiding misleading `.git/FETCH_HEAD` warnings from Python subprocess fetches.
- Confidence: high
- Next command: `product:spec 075-issue-less-context-capture`
- Status: done; hotfix, tests, review, release notes, version bump, and follow-up issue complete.

### `075-issue-less-context-capture`

- Outcome: ModuFlow gains first-class issue-less context tiers (`session`, `inbox`, `note`, `decision`, `issue`) with promotion gates so exploratory work does not disappear but also does not require premature issues.
- Confidence: high
- Dependency: 074 recovery case, 069 ready issue model, memory/decision capture.
- Next command: `product:spec 075-issue-less-context-capture`
- Status: backlog (next up)

### `071-spec-code-converge-check`

- Outcome: Post-implementation review compares actual code against spec/plan/tasks and reports missing, partial, contradictory, or unrequested behavior.
- Confidence: high
- Dependency: 070 spec consistency analyzer.
- Next command: `product:spec 071-spec-code-converge-check`
- Status: backlog

### `072-lifecycle-hooks-automation`

- Outcome: SessionStart/Stop hooks inject current state and run lifecycle sync when issue files change, reducing manual state/dashboard drift.
- Confidence: medium
- Dependency: 048 lifecycle sync, 065 installed plugin staleness detection.
- Next command: `product:spec 072-lifecycle-hooks-automation`
- Status: backlog

### `073-project-constitution-steering`

- Outcome: A versioned project constitution centralizes shared engineering principles so plans reference one governed source instead of restating house rules.
- Confidence: medium
- Dependency: 070 spec analyzer, 060 output convention.
- Next command: `product:spec 073-project-constitution-steering`
- Status: backlog

### `055-command-surface-onboarding`

- Outcome: `product:start`/`product:status` name 2-3 concrete next commands; command reference groups core path vs on-demand.
- Confidence: high
- Next command: `product:execute 055-command-surface-onboarding`
- Status: done; released on `origin/main`.

### `054-github-issue-sync`

- Outcome: opt-in one-way projection of `issues/*.md` to GitHub Issues with status labels, so external collaborators see progress in the GitHub UI.
- Confidence: high
- Dependency: design decisions recorded in the issue (mapping storage, trigger, explicit `-R` repo, label bootstrap)
- Next command: `product:spec 054-github-issue-sync` after 055
- Status: done; implementation complete, live projection remains ask-first.

### `050-repo-sync-preflight`

- Outcome: `product:sync` and `product:status` warn when local Git-file artifacts are stale because the current branch is gone, behind `origin/main`, or missing issue files that exist remotely.
- Reason: A deleted stale branch made Issue 040 appear missing locally even though GitHub `main` already contained issues through 049.
- Confidence: high
- Dependency: Git-file issue model, lifecycle drift checks, and repo preflight behavior
- Next command: `product:status`
- Status: done; repo sync preflight helper, docs, tests, and review complete.

### `051-autonomous-execute-review-visual-handoff`

- Outcome: Development handoff now continues into review, verification, and dashboard-backed issue inspection instead of stopping after implementation.
- Reason: ModuFlow's previous execute/review flow depended on manual continuation and did not automatically surface the visual artifact panel.
- Confidence: high
- Dependency: worker routing, host subagent availability, issue artifact drill-down, lifecycle sync
- Next command: `product:status`
- Status: done; handoff helper, docs, tests, subagent review, and visual handoff complete.

### `052-draft-pr-review-handoff`

- Outcome: Draft PR / local PR-ready state is now the early human review surface, with review, verification, dashboard, and issue drill-down evidence refreshed into `specs/<issue>/pr.md`.
- Reason: GitHub-native workflows make PRs visible before final review, while human approval, required reviews, and status checks still control merge.
- Confidence: high
- Dependency: autonomous review handoff, team issue branch PR workflow, dashboard drill-down
- Next command: `product:status`
- Status: done; PR handoff helper, docs, tests, review notes, and visual handoff complete.

### `034-memory-capture-and-sync-workflow`

- Outcome: ModuFlow can suggest, approve, store, retrieve, and mirror durable project memories while keeping full deliverables separate from memory summaries.
- Reason: The memory prototype works, but users need clear save triggers, a reviewable capture flow, search/retrieval behavior, and Google Drive or similar mirror options that do not replace Git as the source of truth.
- Confidence: high
- Dependency: project memory layer, business document workflow, artifact schema gates, and external memory pattern review
- Next command: `product:spec 056-dashboard-database-list-view`
- Status: released via PR #5; release notes written to `specs/034-memory-capture-and-sync-workflow/release.md`.

### `056-dashboard-database-list-view`

- Outcome: Dashboard gains a Notion/Jira/Linear-inspired DB/list view alongside the issue graph, so users can scan, filter, sort, and triage issues without relying only on node topology.
- Reason: The graph is useful for relationships, but PM workflow also needs dense list/table views for status, next action, missing artifacts, review readiness, and operational triage.
- Confidence: medium
- Dependency: 045 issue graph, 047 issue drill-down, 049 bilingual sidecars, current dashboard generator
- Next command: `product:status`
- Status: done; released locally with `specs/056-dashboard-database-list-view/release.md` after human approval.

### `057-korean-human-review-packet`

- Outcome: PR/review/release gates produce a compact Korean human-review packet so Korean-speaking reviewers can approve work without reading every English canonical artifact.
- Reason: English canonical artifacts are useful for tools, but human approval is currently uncomfortable when PR handoff and review notes are English-heavy.
- Confidence: high
- Dependency: 049 bilingual sidecars, 051 review handoff, 052 PR handoff
- Next command: `product:status`
- Status: done; released locally after human approval with release note, approval record, PR handoff, Korean packet, and passing gates.

### `058-git-write-fallback-via-github-api`

- Outcome: ModuFlow detects when local `.git` writes are blocked and automatically routes commit/push handoff through GitHub API before asking the user to run terminal commands.
- Reason: Issues 056 and 057 needed API-created commits because Codex could edit files but could not create `.git/index.lock`; this should be a standard flow, not ad hoc recovery.
- Confidence: high
- Dependency: 050 repo sync preflight, 052 PR handoff, 057 Korean human review packet
- Next command: `product:execute 058-git-write-fallback-via-github-api`
- Status: done; commit-capability classification and GitHub API fallback guidance shipped.

### `035-team-issue-branch-pr-workflow`

- Outcome: Small teams and TFs can create, assign, start, review, and complete work through ModuFlow while developers use Git branches and PRs underneath.
- Reason: PMs should be able to run team work in natural language, while developers need deterministic issue, branch, PR, review, and memory-capture state.
- Confidence: high
- Dependency: Git binding, intake-to-goal graph, worker routing, artifact validation, and memory candidate workflow
- Next command: `product:status`
- Status: complete and versioned as 0.2.14.

### `037-delegation-level-gate-and-memory-context-graph`

- Outcome: Control AI delegation safety with delegation_level checks, and visualize memory connections using depends_on and references relations rendered via Mermaid.
- Reason: High-trust collaboration requires humans to approve critical agent steps, and Neo4j-style context graphs help developers inspect project memory relations.
- Confidence: high
- Dependency: 034-memory-capture-and-sync-workflow
- Next command: `product:plan`
- Status: planning phase, implementation plan created.

### `038-worker-context-memory-path-injection`

- Outcome: Dynamically inject relevant memory references and short summaries into task worker prompts, keeping context windows lightweight.
- Reason: Workers need previous architectural context and guidelines without causing prompt bloat or attention drift.
- Confidence: high
- Dependency: 037-delegation-level-gate-and-memory-context-graph
- Next command: `product:status`
- Status: completed.

### `040-automatic-memory-candidate-capture`

- Outcome: Automatic capture of decisions and deliverables on release/research events into a candidate memory directory with approval/promotion workflow.
- Reason: Avoid manual capture friction and build structured project memory iteratively with low human toil.
- Confidence: high
- Dependency: 030-project-memory-layer, 039-automated-review-checklists-and-safety-lint-gates
- Next command: `product:status`
- Status: ✅ done, released.

### `039-automated-review-checklists-and-safety-lint-gates`

- Outcome: AI-driven spec-diff comparison checklist inside status.md and linting/security validation gates inside release_check.py.
- Reason: Improve human discernment during reviews and enforce code quality/security compliance before PR creation.
- Confidence: high
- Dependency: 038-worker-context-memory-path-injection
- Next command: `product:status`
- Status: ✅ done, released.

### `036-portfolio-team-dashboard`

- Outcome: Portfolio dashboards show each project's active work, review queue, blockers, and next command from project-local state.
- Reason: Small teams and TFs need a cross-project 현황판, not only per-project team state.
- Confidence: high
- Dependency: team issue branch PR workflow
- Next command: `product:status`
- Status: complete and versioned as 0.2.15.

### `033-business-document-workflow`

- Outcome: ModuFlow business documents become project-local, source-backed, decision-ready artifacts, starting with market-entry analysis.
- Reason: Users need more than issues; project work also needs durable deliverables, decisions, calculations, validation results, and polite executive-report style.
- Confidence: high
- Dependency: project memory layer and business-plan skill
- Next command: `product:status`
- Status: review complete, with skill routing, templates, test artifact, validation, and local plugin cache deployment in place.

### `032-multi-language-goal-benchmarking-and-core-mcp-server-integration`

- Outcome: Extend benchmarking with English-to-Korean translation and build light MCP server layer.
- Reason: Reduce terminal command execution friction and support multi-lang insights.
- Confidence: high
- Dependency: 031-goal-driven-autonomous-benchmarking-and-issue-generation
- Next command: `product:status`
- Status: complete.

### `031-goal-driven-autonomous-benchmarking-and-issue-generation`

- Outcome: AI agent can autonomously search, benchmark, and generate structured issues from a high-level goal.
- Reason: Enable self-driven product design and issue tracking.
- Confidence: high
- Dependency: none
- Next command: `product:status`
- Status: complete.

### `025-lightweight-project-adoption`

- Outcome: Normal projects adopt ModuFlow in light mode with only state and PM artifacts in the project; tool commands, scripts, skills, and templates stay central.
- Reason: The current dogfooding repo shape makes ModuFlow feel too invasive when users imagine applying it to every project.
- Confidence: high
- Dependency: project migration/profile flows and artifact schema gates
- Next command: `product:status`
- Status: complete.

### `026-simplify-command-and-folder-surface`

- Outcome: Users see a small default command/folder model first, with advanced internals available only when needed.
- Reason: Many folders and commands are maintainable internally but uncomfortable as the first user experience.
- Confidence: high
- Dependency: simple loop UX and `/moduflow` hub command
- Next command: `product:status`
- Status: complete.

### `027-reduce-approval-popup-friction`

- Outcome: Approval prompts become predictable, batched where possible, and routine validation can run through importable/tool-call paths instead of repeated shell prompts.
- Reason: Repeated prompts during Git/GitHub cleanup and validation checks make otherwise normal workflows feel noisy.
- Confidence: medium
- Dependency: Git binding and doctor/preflight checks
- Next command: `product:status`
- Status: complete.

### `028-real-subagent-execution-backend`

- Outcome: Worker plans can dispatch safe independent tasks to real host-provided subagents when available.
- Reason: Static worker plans are useful, but host environments such as Antigravity may support actual parallel coding agents.
- Confidence: medium
- Dependency: worker routing/isolation and host API verification
- Next command: `product:status`
- Status: complete.

### `029-antigravity-artifact-sync-connector`

- Outcome: Antigravity-native artifacts and ModuFlow Git artifacts stay synchronized without duplicate writing.
- Reason: Duplicate `task.md`/`implementation_plan.md` and ModuFlow issue/spec/status files fragment the record.
- Confidence: medium
- Dependency: artifact schema gates and host artifact model verification
- Next command: `product:status`
- Status: ✅ done, released.

### `030-worker-cognitive-demand-model-routing`

- Outcome: Define and integrate cognitive demand routing (deep, balanced, fast) on task workers.
- Reason: Avoid executing heavy LLM orchestration where simple syntax parsing or lightweight changes are requested.
- Confidence: high
- Dependency: superpowers-execution-bridge
- Next command: `product:status`
- Status: ✅ done, released.

## Backlog / Existing Capabilities

### `024-artifact-schema-and-doctor-gates`

- Outcome: Doctor validates artifact relationships, state drift, Git binding, intake records, worker plans, and next-command consistency, not only file existence.
- Reason: A richer loop model needs stronger consistency checks.
- Confidence: high
- Dependency: loop state from 019, Git binding from 021, intake routing from 022, and worker routing from 023
- Next command: `product:status`

### `023-worker-routing-and-isolation`

- Outcome: Worker assignment and parallel execution are now deterministic, file/dependency aware, and sequential by default when unsafe.
- Reason: Workers should help only when work can be safely split and merged.
- Confidence: high
- Dependency: Git binding from 021 and intake routing from 022
- Next command: `product:status`

### `022-intake-to-goal-graph`

- Outcome: Loose requests classify into active issue attachment, new issue candidates, goal graph candidates, or inbox routing records.
- Reason: This is the main product value beyond Spec Kit and coding agents.
- Confidence: high
- Dependency: simple UX from 020 and goal graph from 019
- Next command: `product:status`

### `021-git-binding-and-execution-backend`

- Outcome: Issues and loop steps are tied to branches, commits, PRs, releases, and optional execution backends such as Copilot Cloud Agent, Codex, Claude Code, OpenHands, or manual work.
- Reason: ModuFlow should orchestrate execution rather than compete with coding agents.
- Confidence: high
- Dependency: loop state model from 019
- Next command: `product:status`

### `020-user-facing-simple-loop-ux`

- Outcome: Simple aliases shipped for `상태`, `다음`, `이거 해줘`, and guarded `완료` while preserving direct `product:*` commands.
- Reason: Internal loop complexity must not increase user complexity.
- Confidence: high
- Dependency: loop state model from 019
- Next command: `product:status`

### `019-loop-kernel-and-state-model`

- Outcome: Durable goal-loop state model shipped for Goal 1:N Issue, active cursor, attempts guard, and drift-aware validation.
- Reason: This is the core foundation for making ModuFlow a PM loop orchestrator instead of a collection of workflow commands.
- Confidence: high
- Dependency: current artifact tracking and doctor gates
- Next command: `product:status`
