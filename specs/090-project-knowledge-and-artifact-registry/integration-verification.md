# Issue 090 — Integration Verification Checkpoint

Issue: `090-project-knowledge-and-artifact-registry`.
Owner / decision maker: Dongwon Lee.
Source: approved implementation and 2026-09-03 restart, followed by the existing 090 task's completion handoff.
Phase: complete; explicitly approved PR #47 merged, 0.3.57 published/installed and canonical 090 completed. See release.md for final proof and honest actual-host boundaries.
Next: hand off source; 091 → 086 → 092 later, without starting those tasks here.

## Final Integration and Delivery

The user separately approved main merge/publication/installation with “ㅇㅇ 그러자고” after the explicit consolidated question in implementation-approval.md. PR #47 latest-head CI passed, including 1,680 tests and 13 release checks. It merged as 8869afa3e9e7f0a2f89bd9ea8b77c67ee0480495; exact merged CI and a fresh local complete release check also passed. The source tree matches the tested PR head. [release.md](release.md) records the immutable tag/archive, installed receipt, fresh CLI/MCP and rollback evidence.

The existing lifecycle transaction completed 090 from its documented backlog projection; 111 remains active. No fictional earlier start, gate waiver, host-loading pass or company adoption is asserted. The approval-pending/no-mutation statements below are historical checkpoints superseded by this section, not current blockers.

Remote handoff: the integration branch was pushed and Draft PR #47 created against main. Final pre-push source `957c448` passed the complete release check again (13/13); runtime/tests/manifests were unchanged from full-suite-tested c89fc65. The following PR-link bookkeeping is documentation-only. Remote CI remains separate evidence, not inferred from local results.

## Integration Authority — 2026-09-03

Dongwon Lee approved the proposed history-preserving integration, version increase, full revalidation and PR creation with “그럽시다. 90으로 인하여 뭐가 좋아지는거야? 90”. This authorizes the integration branch only, not main merge or deployment. The existing implementation branch and its commits remain intact. Apply its committed change as a squash into `codex/090-knowledge-registry-integration`, with explicit Issue linkage and the 0.x policy patch increase from 0.3.56 to 0.3.57 in the same feature commit. Neither the author's post-stop synchronization files nor the 25 old Issue 103 plans participate.

Earlier pending-authority and failing-policy statements below describe the incoming implementation snapshot, not the integrated result. Final command results will be appended after execution; no green result is inferred from changing a manifest.

## Verified Integrated Source — c89fc65

- Exact feature commit: `c89fc657fc08e6653dbc59a0fda8182f9f5ecea7`; source 0.3.57 / Codex 0.3.57+codex.20260810222010, Issue trailer included in that commit.
- `git diff 594575b HEAD -- scripts tests commands templates config` returned no differences at this feature commit. The source author's history and post-stop state remain untouched.
- Focused command above, rerun in the integration worktree: **317 passed, 13.531s, exit 0**.
- `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -q`: **1,680 passed, 290.354s, exit 0**. This run used the bundled native Git through `PATH`, `GIT_EXEC_PATH` and `GIT_TEMPLATE_DIR`; Python was the local 3.14 runtime. Invalid CLI-input messages printed by negative cases did not represent test failures.
- Separate `release_check.run_release_check(".")`: **valid=true, errors=[], all 13 checks passed**, including linkage, version, lint, security, focused release suites and Doctor. The two incoming-source policy failures are resolved in the integration history, not ignored.
- Source-package and project artifact validation: valid, zero errors and no lifecycle drift. Operation/path audits: valid, zero errors. Spec consistency: 9 criteria, zero findings. Diff whitespace: passed.
- Direct integration review covered the parser/read boundary, pinned source selection, normalization/source preconditions/recovery entrypoints, opt-in knowledge/CLI behavior, Validator/Doctor and distribution changes, and representative denial/fault/replay/snapshot tests against spec R1–R7 and AC1–AC9. No new blocking finding was identified in that review; it is a direct review, not a subagent review or human approval.
- Main merge, GitHub CI, publication, installed-host reload and actual company-project use are not established by these local results. Canonical 090 backlog / 111 active state remain explicitly unchanged.

## Why Needed / Problem / Expected Benefit

People and new AI tasks need to find selected project evidence without copying originals or inheriting hidden chat memory. Scattered paths and ambiguous source/approval status obstruct that handoff. The expected benefit is a project-scoped, verifiable material catalog; actual deployment or adoption benefit is not established by these tests.

## Source and Verification

- Implementation HEAD: `594575b9799ec5792b9347d63f08f08fdf0d2671`, branch `codex/090-knowledge-registry-plan`, existing isolated 090 worktree. Base: `22c01c9`.
- Committed change: 26 files, 2,352 insertions and 66 deletions. No committed changes since the base under `.moduflow`, `workspace`, `.claude-plugin` or `.codex-plugin`.
- The integration owner independently reran `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_project_knowledge tests.test_project_memory tests.test_project_knowledge_registry tests.test_project_knowledge_registry_transaction tests.test_project_knowledge_registry_simulation tests.test_project_lifecycle_transaction tests.test_project_lifecycle_transaction_storage -q`: **317 passed in 14.331s, exit 0**, including synthetic S01–S14 and temporary packaged CLI smoke. This does not establish real-host/project application.
- Implementation task's recorded full suite: **1,680 run; 1,678 passed / 2 failed, 477.722s, exit 1**. The integration owner did not repeat the full suite at this checkpoint. Both reported failures are release-check aggregate assertions in `tests.test_validation_distribution`.
- Independently reran the actual `release_check.run_linkage_gate` and `version_bump.check_bump_applied`: linkage rejects `3cd88b1` and `2420417`; version gate rejects unchanged `0.3.56`. These remain failures, not waived checks.
- Examined the implementation self-review and selected parser/read/transaction/CLI changes. This checkpoint is not a completed independent line-by-line code review or merge approval.

## Post-Handoff Worktree Observation

The completion message reported a clean worktree. Inspection after the task stopped found two modified tracked files (`.moduflow/state.json`, `workspace/loop-state.json`) and one new transaction evidence file, `workspace/transactions/txn-8a26b0cfef3a0321f0bd0cc1bc5a3c32.json`.

The evidence records `actor=moduflow.lifecycle`, `action=reconcile`, `source_event=sync_lifecycle:...`, applied at `2026-09-03T02:02:00Z`, after the implementation commit at `02:01:10Z`. The differences are updated dates and loop `last_action=reconcile`; the 111 cursor/issue status did not change. The existing `hooks/on_stop.py` calls lifecycle sync against the task CWD when its issue hash marker differs. This is consistent with post-stop automatic synchronization, not part of the 090 implementation commit. Preserve the files and evidence; do not reset, stage with 090, or attribute them to source implementation without further evidence.

## Remaining Boundaries

- Preserve the existing implementation branch/history and any post-handoff changes. Do not rewrite the author's commits to conceal the linkage failure. A separate explicitly linked integration commit is an option to review; no squash/merge has been executed here.
- Source version increase, PR preparation and remote writes are not implied by the previous 0.3.56 publication approval. Resolve their authority and re-run release/full gates before claiming readiness.
- 111 remains active for R01/R02 real-host observations; 090 canonical backlog remains the documented single-active-model limitation. Do not falsely complete 111 or weaken the lifecycle validator to advance the cursor.
- No source merge, version change, push/PR, publication, installed-cache change or real company-data application was performed at this checkpoint. The 25 pre-existing Issue 103 plan files in the integration worktree remain outside staging.
