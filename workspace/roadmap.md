# ModuFlow Roadmap

## Product Direction and Priority Refresh — 2026-09-02

- Owner / decision maker: Dongwon Lee.
- Source: requests in the current Codex task for project home/wiki/material discovery, continuity across projects and chats, company analysis/document standards, and replaceable automation runners; followed by the request to reorder priorities.
- Goal: `trustworthy-execution-and-project-knowledge`; 111/060 released as 0.3.56; Issue 090 spec/plan implementation approved 2026-09-02; 086 remains independent preparation only.
- This is the current execution order. It supersedes older ordering below, including the earlier instruction to start 112 immediately after 103. Issue status, declared P0/P1/P2/P3 priority, hard dependencies, and approved acceptance criteria remain unchanged.
- No duplicate issues are created. New requirements below must be reconciled with the existing issue/spec before implementation; a roadmap entry is not proof that the feature exists.

### Direction: A Small Project Control Plane

ModuFlow owns project identity, discoverable context, issues, artifact/run references, decisions, verification/approval evidence, and next actions. Humans and AI use the same short project home to find selected source material. Company standards and specialist execution stay outside the core behind explicit, replaceable contracts.

| Layer | Owns | Does not own |
|---|---|---|
| ModuFlow | Project home and indexes; issue/run/output links; policy selection; evidence, decisions and follow-up intent | A second execution engine, scheduler, document editor, analytical database, or copied raw source library |
| Company/project profiles and skills | Versioned analysis rules, approved document templates, terminology and applicable checks | Unreviewed weakening of privacy/access constraints or implicit cross-project data sharing |
| Specialist adapters and host | Analysis, documents, design and implementation; one selected execution path | Independent copies of ModuFlow's canonical issue/spec/plan state |
| External automation runner | Scheduling, execution, retry and operational events through an adapter | Authority to approve results or silently change project policy |

Keep Git-native records and the existing Issue DB/table/tab UI. A dashboard is a projection of those records, not another database. A new chat reads a short home, finds relevant index entries, then reads selected originals; it does not inherit another chat's hidden memory. Company data, credentials and private originals remain outside shared Git/plugin packages.

### Now — Knowledge Implementation and Remaining Host Observation

**Current execution decision:** the user approved the existing 090 spec/plan (`7779b42`, integrated at `5ff27e6`) for A1 → B1 → C1 → C2 → D1 → D2 inline implementation. The existing 090 task owns its plan's code/tests; the existing 086 task prepares only issue-scoped QA documents and synthetic inputs. Common overlapping implementation files have one writer (090); lifecycle/goal/roadmap and release decisions remain integration-owned. See [approval and ownership](../specs/090-project-knowledge-and-artifact-registry/implementation-approval.md). No new subagents, duplicate issues or release authorization are introduced.

**Lifecycle limitation:** 111 remains active for R01/R02. Starting 090 was rejected before canonical writes because the current lifecycle model permits only one active issue. Leave the canonical cursor and 111 completion evidence unchanged; the approval record and task-specific progress describe 090 execution until integration reconciles this limitation. Do not treat backlog in this projection as revoked implementation approval or claim that the start transaction succeeded.

| Issue | Outcome | Reason | Confidence | Dependency / gate | Next command |
|---|---|---|---|---|---|
| `111-runtime-provenance-and-validation-mode-separation` | Separate source/package/project checks and identify the actually loaded package, including explicit unknowns | Installation and current host prompt-skill loading must not be confused | High | PR #45/#46 merged; 0.3.56 published/installed; CLI/MCP pass; R01/R02 fresh-host observations remain | `product:status` in a fresh host task; record R01/R02 |

Current release authority: [0.3.56 joint release](../specs/060-cross-agent-output-format-convention/release.md). Dongwon Lee approved sequential #45/#46 merge and deployment on 2026-09-02. The 060 common output-rule follow-up remains separate from 090/086 implementation. Earlier approval-pending snapshots below are historical; implementation, merge, publication, installation and actual host loading are still separate evidence.

Deployment update: [v0.3.56](https://github.com/dongwonlee222/moduflow/releases/tag/v0.3.56) is published from `2d857dd`; main CI and merged-source release checks passed. Codex cache and the existing Claude local connection now use the validated distribution. Old caches and settings backups are retained. The held publication is finished; do not repeat it. Fresh-host observations, not implementation or another release, are the remaining Issue 111 verification step.

Issue 103 is complete and merged through PR #44; do not restart it. The authorized 0.3.56 release is finished; source version 0.3.54 alone is not deployment evidence. Issues 090–092 and 112 are not new prerequisites for that completed release. Any newly observed release safety failure must be triaged rather than waived.

### Next — Find, Reuse, and Continue Project Work

Default implementation order is **090 → 091 → 086 → 092**. Issue 086 can be planned independently of 091, but 092 cannot be called complete before all three declared dependencies are complete. This prioritizes the user's daily retrieval/continuity problem before richer execution orchestration.

| Issue | Outcome | Reason | Confidence | Dependency / gate | Next command |
|---|---|---|---|---|---|
| `090-project-knowledge-and-artifact-registry` | One project wiki and source-linked material catalog | All later views and run records need a durable, project-scoped place to find evidence | High | Existing spec/plan approved; integrated readiness ready; existing task executes inline, publication not authorized | `product:execute 090-project-knowledge-and-artifact-registry` |
| `091-reproducible-analysis-runs-and-template-pack` | Reproducible run history, five existing analysis templates, and a bounded company-standard integration pilot | Makes recurring analysis traceable without moving calculation into ModuFlow | Medium for added profile/gate scope; high for existing run contract | 090; review additions without silently dropping the five accepted templates | `product:spec 091-reproducible-analysis-runs-and-template-pack` |
| `086-project-aware-production-library-dashboard` | A consistent project selector across Issue DB, production records and playbooks | A project switch must not leave related tabs on a different project's data | High | Updated spec/design/plan prepared separately at `0f7aeb7`; combined review and implementation approval pending | `product:review 086-project-aware-production-library-dashboard` (spec/design/plan only) |
| `092-project-home-dashboard` | A compact project home for people and AI: current work, blockers, approvals, recent results and next actions | Provides the shared entry point once the underlying records are reliable | Medium until existing spec/design refresh | 086, 090 and 091; replace stale fixed counts with source-derived criteria | `product:plan 092-project-home-dashboard` after spec/design reconciliation |

#### Earlier Parallelism Review Snapshot — 2026-09-02

The following pre-release review snapshot is historical. The current implementation/preparation authority and ownership are stated under Now above; open PR and approval-pending statements below do not supersede it.

- **Why needed:** reduce avoidable waiting while retaining a small control plane and the approved delivery priorities.
- **Problem:** issue numbers and separate worktrees do not prove independence. The 090 and 086 plans share integration files, and PR #46 is stacked on PR #45.
- **Expected benefit:** independent preparation can continue during release review without duplicate parsers, conflicting shared-file changes or premature completion claims. No elapsed-time saving has been measured.
- Owner / decision maker: Dongwon Lee. Source: request to check parallel execution opportunities while proceeding in the current task. Phase: coordination and plan review; no new implementation, merge or deployment approval is recorded here.

Recheck at each work boundary: **approved scope → producer/consumer contract → exact file overlap → shared state/side effects → independent verification → integration order**. Reuse the existing separate tasks; do not create duplicate tasks or dispatch subagents. A design sketch, acceptance gate or approval decision is not an executable worker. Recheck changed files against the latest integration base before future implementation; worktree isolation alone is insufficient.

| Lane / owning issue | Can proceed concurrently now | Must remain ordered / held | Next action |
|---|---|---|---|
| Integration: 111 and 060 follow-up | Inspect review/CI evidence while 090 and 086 review their plans | Approval → merge PR #45 → retarget PR #46 to main and revalidate → approved merge/publication/install → fresh-host verification | `product:review 111-runtime-provenance-and-validation-mode-separation`; keep PR #46 separate |
| Knowledge: 090 | Read-only contract, file-scope and synthetic-scenario review in its existing task | Future A1 → B1 → C1 → C2 → D1 → D2 stays inline; transaction changes and common integration files have one writer | Combined spec/plan review; do not rerun completed baseline tests merely for planning |
| Dashboard: 086 | Read-only selector/projection, privacy and navigation-scenario review in its existing task | Future A → B → C → D stays inline around the shared renderer; optional 090/091 consumption waits for its owning contract | Combined spec/design/plan review; preserve the existing Issue DB/table design |
| Analysis: 091 | Identify the fields and evidence it needs from 090; no implementation dispatched | Registry-backed implementation follows 090; no invented registry API or separate parser | `product:spec 091-reproducible-analysis-runs-and-template-pack` after contract review |
| Home: 092 | Retain existing requirements and dependency map | Integrated home completion depends on 086, 090 and 091 | Reconcile spec/design after producer contracts; no new implementation lane now |

**Concrete collision set from the two prepared plans:** `scripts/validate_moduflow.py`, `scripts/release_check.py`, `config/project-operation-entrypoints.json`, `tests/test_project_memory.py`, `tests/test_project_operation_audit.py`, and `tests/test_validation_distribution.py`. The 090 Doctor/validator integration must also be checked against merged 111 changes. Issue 090 alone owns its proposed registry parser and bounded 103 transaction extension; 086 must not add a second registry parser or transaction engine. Version manifests, release evidence and common lifecycle state remain integration-owned.

**Evidence snapshot, not implementation approval:** PR #45 at `d5e143b` and PR #46 at `c6ed2ab` are open drafts with successful CI. PR #46 currently targets the 111 branch, not main. Source 0.3.56 is prepared, not published or verified in a fresh host. The 090 plan commit `7779b42` (7 files) and 086 plan commit `0f7aeb7` (17 files) are local, separate-task work, not integrated into this branch or main; their proposed APIs and new simulation matrices are not delivered features. Review inputs are each commit's issue-scoped `specs/` documents, not this roadmap as a second specification.

This adds concurrent preparation, not a new execution engine or automatic scheduler. The default implementation priority remains **090 → 091 → 086 → 092**. Overlapping implementation needs a reviewed file split and contract first; the current plans do not authorize it. Neither knowledge planning nor its later implementation becomes a new gate on the held release.

#### Scope Reconciliation Before Implementation

- **090 — discovery and sharing:** give each item an ID, one-line description, when-to-read guidance, as-of date, state, original link and related issue. Distinguish draft/approved/superseded and public-summary/private-original. Check missing links, stale records and Git-committed accessibility; an uncommitted local file must not rescue a broken shared snapshot. Saving an output must also maintain its catalog/issue references, using existing transaction boundaries where applicable rather than assuming every new artifact is already covered by 103.
- **091 — standards and evidence:** define an external `company → project → issue` profile reference and record the effective version/hash and rule sources. Lower levels cannot relax higher-level privacy/access constraints. Record the decision question, population/comparison, numerator/denominator, time window, maturity, applicable costs, method and checks. Require checks appropriate to exploratory, profitability or causal claims; allow explained non-applicability, never silently treat unknown costs as zero. Record actual skill/adapter versions, query/code hashes and snapshots when available, with explicit missing evidence. The proposed `company-data-analysis` skill is an external integration target, not a verified installed dependency.
- **091 — separate states:** preserve append-oriented runs keyed by project/issue/run, with links to analysis, metrics, validation and decisions. Distinguish run completion, validation, human approval and a decision waiting for mature data. A D+30 follow-up date/condition is stored intent, not proof that any scheduler has been registered. A formal final result needs a real issue association; `unassigned` is only an exploratory holding state.
- **Company documents:** reuse existing business-document and production-record workflows with external approved templates linked by 090. Do not turn 091 into a new document-generation framework. Sharing/promoting organization-wide rules remains bounded by 107; production final-state enforcement remains in 108.
- **086/092 — lightweight projections:** preserve the existing Issue DB default and table/tab design. Consume registry v2/canonical project context. A hidden tab is not a privacy boundary: do not bundle private records from every project into a single portfolio HTML payload. The short machine-readable home and human view must point to the same sources, not duplicate full documents.

#### Pilot and Completion Evidence

- Use the 모두의충전 `data-context.md` / `data-manifest.json` pattern and reference commits `d07c468` / `1668a91` as an application example only; do not copy its data, metrics, or company calculations into the plugin.
- Validate with two distinct projects and synthetic/non-sensitive fixtures: project switching, search and source linkage; empty projects; stale materials; missing required links; absent optional private originals; and a separate worktree reading only committed shared files.
- Separately test a fresh AI task reading the short home and retrieving the relevant source. The reference's 20 shared files / 7 tests demonstrate file-based handoff checks, not automatic cross-chat loading.
- Report implementation, tests, remote merge, plugin publication, installed package and actual-session application as separate evidence. Deliver this project-knowledge slice before expanding automation scope.

#### Cross-Phase Simulation Contract — 2026-09-02 Addition

The user explicitly requested simulations while implementing this roadmap. Each issue's plan must carry scenario inputs, expected outcomes and recorded observations; an expected result is not a passing test. Start with synthetic fixtures/fake runners, then packaged smoke, then separately authorized actual project/host use.

| Owning issues | Simulation | Required boundary |
|---|---|---|
| 111 | Source/package/project roles; stale cache, old/new process, unknown host load, failed install | No guessed runtime identity, no real cache replacement during tests |
| 090/086/092 | Project A→B switching, fresh-task home lookup, missing/stale/private/uncommitted links and separate worktree | No cross-project leakage; selected originals only; shared snapshot must be committed |
| 091 | Company/project/issue profile selection, template applicability, missing validation and immature observation window | No unsupported completion/causal/profit claim; follow-up intent is not a live schedule |
| 112/113/104/108 | Route through one execution backend; mocked specialist failure, review findings and missing approval | No second executor; implementation, review and approval remain distinct |
| Later automation scope | Mocked trigger/retry/pause/result events before any live pilot | No real external sends, paid execution or publication without separate authorization |

Issue 111's approved `specs/111-runtime-provenance-and-validation-mode-separation/plan.md` has been implemented inline. Twelve offline scenarios and packaged CLI/MCP smoke passed; source version 0.3.55 and the strict release check are local evidence only. Final full-suite results are recorded in `status.md`; two real-host observations remain unperformed. No real cache or default checkout was changed.

### Later — Simplify Execution, Then Expand Reuse and Automation

These are queued work, not additional gates on every knowledge task. Pull a safety/compatibility fix forward only when a concrete release or pilot blocker demonstrates the need; preserve that finding and its owning issue.

| Issue | Outcome / reason | Confidence | Dependency / trigger | Next command |
|---|---|---|---|---|
| `112-execution-planner-and-backend-boundary` | Executable tasks only; one inline or Superpowers path, removing duplicate execution responsibility | High | 103 complete; precedes expanded orchestration | `product:spec 112-execution-planner-and-backend-boundary` |
| `105-schema-migration-and-doctor-triage` | Reversible migration and actionable Doctor output; bring forward if a real pilot cannot use its records | High | 102/103 complete | `product:spec 105-schema-migration-and-doctor-triage` |
| `113-review-lifecycle-and-exception-fix-approval` | Separate implementation/review/fixes/approval/merge and approved extra fix rounds | High | 103 complete, 112 | `product:spec 113-review-lifecycle-and-exception-fix-approval` |
| `104-project-aware-natural-language-request-orchestrator` | Route a request through the already proven context and execution contracts | High | 102/103 complete, 112 | `product:spec 104-project-aware-natural-language-request-orchestrator` |
| `108-production-approval-and-verification-gates` | Evidence-backed final production approval rather than equating generated output with approval | High | 104; any analysis-specific extension needs scope review | `product:spec 108-production-approval-and-verification-gates` |
| `106-korean-production-search-and-stable-ids` | Improve Korean retrieval and record IDs based on the pilot's actual search needs | High | No declared blocker | `product:spec 106-korean-production-search-and-stable-ids` |
| `107-shared-approved-playbook-layer` | Promote only approved/redacted reusable company rules, not raw project records | High | 102 complete, 106 | `product:spec 107-shared-approved-playbook-layer` |
| `114-speckit-selective-adapter-1x-compatibility` | Compatibility-tested exact-version refresh of four optional advisory functions | Medium until compatibility review | 112; no automatic upgrade or full Spec Kit lifecycle | `product:spec 114-speckit-selective-adapter-1x-compatibility` |
| `099-vendor-and-host-sync-drift-detection` | Detect source/vendor/host drift; check overlap with 111 before implementation | Medium | Concrete drift findings; not an automatic updater | `product:spec 099-vendor-and-host-sync-drift-detection` |
| `096-read-shaped-commands-that-write` | Remove misleading read/write behavior; re-audit overlap with 103/110 | Medium | Current mutation-surface evidence; safety findings may move it forward | `product:spec 096-read-shaped-commands-that-write` |
| `100-residue-check-after-removal` | Find stale references after removal | High | Removal work or a demonstrated residue defect | `product:spec 100-residue-check-after-removal` |
| `087-korean-github-pr-review-surface` | Improve Korean review readability without blocking core retrieval | High | No declared blocker | `product:spec 087-korean-github-pr-review-surface` |
| `101-production-record-schema-friction` | Better record templates/examples/errors, not weaker schema guarantees | High | Repeated record-entry friction in the pilot | `product:spec 101-production-record-schema-friction` |
| `094-risk-based-security-and-quality-review-gate` | Optional risk-sensitive review adapter, not mandatory review machinery for every task | Medium | 089 complete; explicit policy or observed release risk | `product:spec 094-risk-based-security-and-quality-review-gate` |
| `082-cross-host-model-capability-routing` | Host-aware capability selection when cross-host execution is actually needed | Medium | No declared blocker; later optimization | `product:spec 082-cross-host-model-capability-routing` |
| `083-model-routing-evaluation-harness` | Measure routing quality before widening model-policy use | Medium | 082 | `product:spec 083-model-routing-evaluation-harness` |
| `084-worker-prompt-context-budget` | Bound worker context cost after execution boundaries stabilize | Medium | 082; no prerequisite for the project home | `product:spec 084-worker-prompt-context-budget` |

**Automation direction, not a newly registered issue:** after the manual project/run pilot is stable, reconcile existing issues and define a separate bounded registration/status/approval/playbook interface. An external runner such as the previously proposed Prefect remains replaceable and owns schedules/retries. Start with the three previously proposed automations only after confirming their project owners, inputs and side-effect permissions. Do not add a ModuFlow scheduler, silently schedule follow-ups, or treat a stored schedule as a live automation. No runner installation or automation migration is authorized by this roadmap refresh.

### Immediate Next Action

`product:execute 090-project-knowledge-and-artifact-registry` in its existing task; independent 086 QA preparation in its existing task.

The authorized #45 → #46 integration and 0.3.56 deployment are complete. Record fresh-host R01/R02 separately without treating unknown prompt-skill loading as passed. Do not restart 111 implementation/publication or combine it with dashboard/company-profile/Spec Kit work. Execute approved 090 tasks without repeated per-step approval; 086 product-code implementation remains unapproved. Preserve the 090 → 091 → 086 → 092 implementation priority and independent preparation boundaries.

## Completion and Release Gate — 2026-09-02

- `103-atomic-lifecycle-state-transaction` — implementation and D2 complete; Linux CI passed 1,571 tests plus package/release validation. Dongwon Lee authorized PR #44 merge; the PR and its merge-commit CI are authoritative integration evidence.
- `111-runtime-provenance-and-validation-mode-separation` — active after separate implementation approval; local implementation, 1,610 tests, simulations and source release check passed; human integration review pending. The Issue 103 merge approval does not authorize Issue 111 publication.
- Publication record: `specs/103-atomic-lifecycle-state-transaction/release.md`. Source version `0.3.54` has not been installed through this release workflow.
- The newer Product Direction and Priority Refresh above supersedes the execution ordering below. Older Issue 103 progress snapshots are historical.

## Priority Refresh — 2026-09-01

### Now

- `103-atomic-lifecycle-state-transaction` — P0; transaction core and C1a lifecycle adapter/CLI are complete. Finish C1b/C1c, C2, D1, and D2 before starting another P0 implementation.
- `111-runtime-provenance-and-validation-mode-separation` — P1; may proceed independently but remains required before the next plugin release.

### Next

- `112-execution-planner-and-backend-boundary` — P0; after 103, filter worker plans to concrete implementation tasks and select exactly one inline or Superpowers SDD path.
- `105-schema-migration-and-doctor-triage` — P0; unblocks after 103 and may proceed alongside the later review-state work.
- `113-review-lifecycle-and-exception-fix-approval` — P1; after 103 and 112, separate implementation, review, fixes, approval, and merge evidence.
- `104-project-aware-natural-language-request-orchestrator` — P0; now also depends on 112 so it consumes one execution boundary instead of embedding the old worker model.

### Later

- `114-speckit-selective-adapter-1x-compatibility` — P1; after 112, review and pin one exact Spec Kit 1.x release for the four advisory functions only.
- `106-korean-production-search-and-stable-ids` → `107-shared-approved-playbook-layer`.
- `108-production-approval-and-verification-gates` after 104.
- `084-worker-prompt-context-budget` stays separate as a later cost/context optimization.

### Review Gate

The 2026-09-01 official-source benchmark supports durable agent-neutral artifacts, bounded task execution, host-native subagents, and explicit review gates. It rejects a second ModuFlow execution engine, forced delegation, full Spec Kit lifecycle adoption, and unpinned adapter upgrades. See `knowledge/benchmarks/2026-09-01-agentic-execution-governance-trend.md`.

## Priority Refresh — 2026-08-21

### Now

- `103-atomic-lifecycle-state-transaction` — P0; non-draft plan PR #43 open, readiness passed, execution remains explicitly approval-gated.

### Next

- `111-runtime-provenance-and-validation-mode-separation` — P1; may proceed in parallel and must complete before the next plugin release.
- `104-project-aware-natural-language-request-orchestrator` and `105-schema-migration-and-doctor-triage` — P0; remain blocked by 103.

### Later

- `106-korean-production-search-and-stable-ids` → `107-shared-approved-playbook-layer`.
- `108-production-approval-and-verification-gates` after 104.
- `086-project-aware-production-library-dashboard` remains P2.

### Review Gate

Issues 109 and 110 are complete. Issue 103 now has canonical paths plus centrally enforced write capability and may proceed to transaction planning.

### Recently Completed

- `110-project-operation-capability-enforcement` — PR #42 passed CI and merged as `5f173f4`; 64 mutation surfaces classified with zero gaps and post-merge source release validation passed.
- `109-canonical-project-context-consumer-convergence` — canonical context operation boundary, nested/decoy consumer convergence, canonical Git pathspecs, and repository-wide regression classification guard; package version 0.3.50.

## Priority Refresh — 2026-08-19

### Now

- `103-atomic-lifecycle-state-transaction` — P0; next specification target. It can now consume the completed Issue 102 context contract.

### Next

- `104-project-aware-natural-language-request-orchestrator` — P0; blocked by 102 and 103.
- `105-schema-migration-and-doctor-triage` — P0; blocked by 102 and 103.
- `106-korean-production-search-and-stable-ids` — P1; independent and may proceed after the P0 spec review.

### Later

- `107-shared-approved-playbook-layer` — P1; blocked by 102 and 106.
- `108-production-approval-and-verification-gates` — P1; blocked by 104.
- `086-project-aware-production-library-dashboard` — P2; design/prototype retained, but implementation now consumes 102 instead of creating a second project registry/resolver.

### Review Gate

Issue 102 completed on 2026-08-19 with 1,225 tests, project validation, zero lifecycle drift, and release check passing. Issue 104/105 remain blocked only by Issue 103; Issue 107 still also depends on 106. This refresh is authoritative over the historical snapshots below.

### Recently Completed

- `102-project-registry-and-resolver` — explicit v2 registry, deterministic fail-closed resolver, v1 migration proposal, canonical context API, and all planned read/write consumer convergence shipped on branch `codex/102-project-registry-and-resolver`; package source version is 0.3.49.

## Priority Refresh — 2026-08-13

### Now

- `086-project-aware-production-library-dashboard` — continue the approved project-scoped production/playbook dashboard.

### Next

- Select after the 086 implementation review; no security adapter work blocks routine product execution.

### Recently Shipped

- `097-single-entry-capability-routing-contract` — merged via PR #36 as `46f98c0`; 27/27 routing simulations, 1,077/1,077 local tests, and CI passed.
- `095-commit-issue-resolution-parity` — merged via PR #33 as `f4029f3`; post-merge release check passed, failure history remains preserved, and plugin publication stays held for Issue 096.
- `098-speckit-selective-validation-adapter` — merged via PR #37 as `513e08f`; 24/24 conservative pilot passed, ModuFlow 0.3.48 was installed locally, and wider/default activation remains prohibited.
- `088-canonical-repository-remote-identity-gate` and `089-verified-code-review-intake-and-remediation-routing` — merged, reviewed, approved, and packaged in v0.3.26.
- Legacy `030-project-memory-layer` audit — prototype foundation retained; delivered extensions mapped to 034/040/043/085 and remaining registry/migration scope transferred to 090 on 2026-07-21.

### Then

- `086-project-aware-production-library-dashboard` — approved design/prototype; implement global project selector plus Production Records and Playbooks tabs.

### Later

- `094-risk-based-security-and-quality-review-gate` — reduced to a P2 opt-in external-adapter gate; revisit when a project has repeated risk-sensitive release evidence or explicitly enables the policy.
- `090-project-knowledge-and-artifact-registry` → `091-reproducible-analysis-runs-and-template-pack` → `092-project-home-dashboard`.
- `087-korean-github-pr-review-surface` is independent and does not block 086.

This priority refresh is authoritative over the historical snapshots below.

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
- Next command: `product:status`
- Status: done; PR #13 merged on 2026-07-09 and lifecycle/release evidence reconciled on 2026-07-21.

### `077-implementation-readiness-gate`

- Outcome: `product:execute` checks implementation readiness before worker dispatch, including API contracts, test strategy, frontend fixtures, smoke checks, permissions, and release conditions.
- Reason: Agent execution fails most often when the plan lacks concrete contracts, not when the agent lacks coding ability.
- Confidence: high
- Dependency: 079 plan discipline matrix, 070 spec consistency analyzer.
- Next command: `product:status`
- Status: done; PR #14 merged on 2026-07-09 and lifecycle/release evidence reconciled on 2026-07-21.

### `078-frontend-qa-template-pack`

- Outcome: ModuFlow ships reusable templates for Storybook required states, MSW fixture catalogs, API contract mapping, Playwright smoke matrices, and QA evidence checklists.
- Reason: Frontend work needs state/fixture/test evidence before implementation and review can be trusted.
- Confidence: medium
- Dependency: 077 implementation readiness gate, 046 planning templates.
- Next command: `product:status`
- Status: done; PR #15 merged on 2026-07-09 and lifecycle/release evidence reconciled on 2026-07-21.

### `080-reference-improvement-backlog`

- Outcome: Improvements discovered in reference repositories or templates are captured in a separate backlog and can be promoted later without polluting the active product issue queue.
- Reason: Reference repo insights appear during real work and currently risk disappearing or getting mixed into the wrong issue.
- Confidence: medium
- Dependency: 075 issue-less context capture.
- Next command: `product:status`
- Status: done; PR #16 merged on 2026-07-09 and lifecycle/release evidence reconciled with Dongwon Lee approval on 2026-07-21.

### `085-project-production-records-and-playbooks`

- Outcome: Each project preserves recurring production outputs, decisions, failures, reusable patterns, and approved playbooks without forcing existing asset folders into a central structure.
- Reason: Issue completion records what happened, but recurring banner, PR, proposal, Alimtalk, SMS, and Push work must improve the next production cycle.
- Confidence: high
- Dependency: existing project memory and candidate-promotion foundations (`030`, `040`, `043`).
- Next command: `product:design 086-project-aware-production-library-dashboard`
- Status: done; PR #17 merged and version 0.3.23 released after Korean-first human approval.

### `086-project-aware-production-library-dashboard`

- Outcome: One global project selector controls Issue DB, production records, playbooks, knowledge, decisions, roadmap, and status across the dashboard.
- Reason: Projects have different folders and brand knowledge, so the dashboard must use registered project metadata without mixing project context or crawling arbitrary paths.
- Confidence: high
- Dependency: `085-project-production-records-and-playbooks`, `056-dashboard-database-list-view`, `047-issue-artifact-drilldown`.
- Next command: `product:design 086-project-aware-production-library-dashboard`
- Status: ready; `085` released, so design and implementation are unblocked.

### `087-korean-github-pr-review-surface`

- Outcome: Korean reviewers see Korean-first GitHub PR bodies, review findings, check summaries, and approval requests without losing English canonical artifacts.
- Reason: Issue 057 creates a Korean packet, but the upload step can still publish English `pr.md`, so the human review surface does not enforce the agreed language.
- Confidence: high
- Dependency: `057-korean-human-review-packet`, `052-draft-pr-review-handoff`.
- Next command: `product:spec 087-korean-github-pr-review-surface`
- Status: backlog; PR #17 body corrected manually as dogfood.

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
