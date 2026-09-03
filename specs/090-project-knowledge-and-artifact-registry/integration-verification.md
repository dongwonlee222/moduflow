# Issue 090 — Integration Verification Checkpoint

Issue: `090-project-knowledge-and-artifact-registry`.
Owner / decision maker: Dongwon Lee.
Source: approved implementation and 2026-09-03 restart, followed by the existing 090 task's completion handoff.
Phase: local implementation handed off; focused verification repeated; not release-ready or merged.
Next: review the remaining integration boundaries and obtain authority for history-preserving integration/version/PR preparation. Publication and installation remain separate.

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
