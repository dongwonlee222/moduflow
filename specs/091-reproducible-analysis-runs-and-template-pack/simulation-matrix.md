# Simulation Matrix: Reproducible Analysis Runs and Template Pack

Issue: `091-reproducible-analysis-runs-and-template-pack` · Owner: Dongwon Lee
Phase: proposed scenarios, revision 2 of 2026-09-03. **Nothing below has been executed.** Every `Observed` cell stays `Not run` until an approved implementation runs it.
Source: `workspace/roadmap.md` cross-phase simulation contract of 2026-09-02, row `091`: profile selection, template applicability, missing validation and immature observation window; no unsupported completion/causal/profit claim; follow-up intent is not a live schedule. Profile-chain rows are replaced by playbook-resolution rows because the profile chain is deferred out of this issue.
Prev: [spec](spec.md) / [plan](plan.md) · Next: record observations in `status.md` after Stream F2.

## Fixture Boundary

Use only generated synthetic files under a `TemporaryDirectory`. Projects A and B have distinct registry-v2 IDs, owners, issue IDs and canary strings, and both receive a run with the same UUID to prove `(project_id, run_id)` scoping. Project B uses non-default workspace paths with poisoned default folders, and holds a playbook with the same name as A's but different content.

Synthetic playbooks carry invented deliverable types, check IDs and copy blocks only — no company rule text, metric definition, cost amount or currency value. Fixed evaluation date: `2026-09-07`; a follow-up `due_on` of `2026-09-06` is due and `2026-10-07` is not.

Git-backed cases use a disposable local repository with commits and a separate detached worktree; never the active source repository, the default checkout, or another task's worktree. All subprocess calls flow through the injected runner. No remotes, no network, no real external connectors, and no installed external analysis skill. Cleanup is restricted to exact fixture paths.

## Offline Scenario Matrix

Proposed module: `tests/test_project_analysis_run_simulation.py`.

| ID / proposed test | Input / action | Expected result and proof | Observed |
| --- | --- | --- | --- |
| S01 `test_run_file_initialization_is_non_destructive` | Empty project; preview init; apply twice | Preview creates nothing; missing-only init creates the run file with `moduflow.analysis-runs.v1`; second apply changes zero bytes; existing files untouched | Not run |
| S02 `test_append_only_history_explains_change` | Append run 1, then run 2 superseding it with a `change_reason`; attempt an in-place edit of run 1's analysis fields | Run 1's analysis fields unchanged; run 2 names its predecessor and reason; the edit returns `RUN_AMENDMENT_FORBIDDEN`; a no-op append is byte-identical | Not run |
| S02b `test_state_amendment_appends_history` | Amend a run through completed → validated → approved → decided; then edit, drop and desynchronize a history entry | Each amendment appends exactly one `state_history` entry with a reason and existing evidence for validation and approval; edited, missing and mismatched history all return `RUN_AMENDMENT_FORBIDDEN`; no analysis field changes | Not run |
| S03 `test_playbook_resolution_prefers_project` | Same playbook name in the default pack and in projects A and B; a project-only name; a default-only name; a name in neither | Project wins over default with the resolution reason reported; project-only and default-only both resolve; neither present returns `PLAYBOOK_UNRESOLVED` with no silent fallback; defaults are never edited in place | Not run |
| S04 `test_second_run_needs_only_the_window` | Run a deliverable once with every field, then again supplying only `time_window` | Claim class, measure unit, checks skeleton, default caveats and structure reference come from the resolved playbook; no restated field; the pinned `{playbook_id, version}` is stored on both runs | Not run |
| S05 `test_code_checks_cannot_be_skipped` | One run per claim class with a required code check absent, present-and-passing, and `not_applicable` with and without a reason; a causal `pass` with no evidence | Absent returns `CHECK_MISSING`; unexplained returns `CHECK_UNEXPLAINED`; a `pass` without existing evidence on a causal run is rejected; any `fail` blocks `validation_state=passed` | Not run |
| S06 `test_unknown_cost_is_never_zero` | Profitability run with two `unknown_items` and a settled conclusion; the same run resolved; a run with `costs.applicable=false` and a reason | First returns `COST_UNKNOWN_NOT_ZERO`; second passes; third passes on its reason; no output renders, sums or defaults an unknown cost as `0` | Not run |
| S07 `test_one_claim_per_run` | A run recording both a trend and a margin conclusion; then the same work split into two linked runs | The combined run is rejected; the split runs validate and link through `decision_refs`; the author's prose is never rewritten | Not run |
| S08 `test_four_states_stay_independent` | Runs at each combination of completion, validation, approval and decision maturity, including approved with a missing `approval_ref` | No state implies another; approval without existing evidence is rejected and no writer invents `approval_ref`; `waiting_on_maturity` requires immature maturity or a follow-up condition; no read collapses two states | Not run |
| S09 `test_unassigned_run_is_a_holding_state` | `issue_id=unassigned` run: complete, validate, then approve and request as final; then promote to a real issue and attempt a second promotion | Completion and validation succeed; approval and final-result requests return `RUN_UNASSIGNED_NOT_FINAL`; promotion appends one history entry and one backlink; the second promotion is rejected; an unbound-identity context emits no cross-project reference | Not run |
| S10 `test_immature_window_and_follow_up_are_not_a_schedule` | Policy-impact run days after the change with `observation_until`; follow-ups due and not due at the fixed date; a record attempting `scheduled: true` | Maturity is `immature` with a reason; `FOLLOW_UP_DUE` and `FOLLOW_UP_INTENT_ONLY` are read-time only; `scheduled: true` returns `FOLLOW_UP_NOT_SCHEDULABLE`; no timer, job, queue or re-run is created and no state changes | Not run |
| S11 `test_pinned_sources_reopen_without_substitution` | Pinned artifacts across commits: renamed-but-same-ID, superseded, unknown ID, A's artifact under B's context, optional absent private source, injected Git failure | Rename reopens at the stored OID; superseded, unknown and mismatch return explicit diagnostics with no similarly-titled substitution and no snapshot switch; optional absence does not block an unrelated run; Git failure never falls back to local bytes | Not run |
| S12 `test_document_form_stays_consistent_across_cadences` | A weekly run and an off-cycle run in project A using the same playbook family; then an output whose production record names a different playbook; then 25 runs against limit 20; an archived project; a failed output registration | Both cadences pin the same playbook family and share its approved copy and structure; the divergent record returns `PLAYBOOK_MISMATCH`; `total=25`, `returned=20`, `omitted=5`, `truncated=true`; the archived project is denied before any staging write; a failed registration reports `unregistered` | Not run |

## Roadmap Boundary Coverage

| Roadmap-required boundary | Scenarios |
| --- | --- |
| Profile selection, reinterpreted as playbook selection | S03, S04 |
| Template applicability | S03, S04, S12 |
| Missing validation | S05, S07, S08, S02b |
| Immature observation window | S10 |
| No unsupported completion / causal / profit claim | S05, S06, S07, S08, S09 |
| Follow-up intent is not a live schedule | S10 |

## Acceptance Demonstration

Separate from the matrix above, the spec's five-step Acceptance Demonstration must be performed and recorded. Its decisive step is the second run supplying only the time window: if the re-explanation is not removed, the issue has not met its purpose regardless of these scenarios passing.

## Observable Evidence Format

For each executed scenario append: ID, source commit, test name, fixture identity (synthetic ID only), input OID where applicable, expected assertions, observed diagnostics and read-trace summary, before/after byte-hash comparison, pass/fail, and remediation if failed. Do not store private temporary absolute paths, source bodies or playbook copy text in durable evidence. An `Observed` cell is filled from a run, never from an expectation.
