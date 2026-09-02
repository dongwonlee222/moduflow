# Issue 090 — Implementation Approval and Work Ownership

Issue: `090-project-knowledge-and-artifact-registry`.
Owner / decision maker: Dongwon Lee.
Source: the current integration task's proposal to confirm/implement 090 next while independently preparing 086, followed by the user's approval, “ㅇㅇ 그렇게 하자고”, 2026-09-02.
Phase: implementation authorized; not complete, merged or deployed.
Next command: `product:execute 090-project-knowledge-and-artifact-registry` in the existing 090 task.

## Why Needed / Problem / Expected Benefit

Materials saved by one task need a durable, project-scoped index so another task can find the relevant source. Paths or hidden chat history alone do not establish which definition/report/version should be read. The expected benefit is selective, verifiable retrieval and issue-linked output registration without copying original documents or adding an execution engine.

## Approved Scope

The existing `7779b42` spec/plan/tasks/simulation packet is the implementation baseline: Markdown with per-entry JSON metadata, explicit review-after freshness, one read parser, stable project/artifact identity, selected-source reads and committed snapshots, and the bounded issue-linked registration extension of the existing 103 engine. Follow A1 → B1 → C1 → C2 → D1 → D2 inline, with TDD, fault/compatibility tests and S01–S14. No new database, crawler, scheduler, company data or general arbitrary-file transaction API.

The user need not repeat approval for each task within this scope. Stop for a material contract/safety expansion or unresolved substantive blocker; ordinary debugging and planned integration work remain in scope. Source version/push/PR/merge/publication/install decisions remain with the integration task; the 0.3.56 deployment approval does not publish 090 automatically.

## Ownership and Parallel Work

- 090 implementation: existing task `01a060da-62a6-7d40-89b6-fc2e27c9442e`, its existing worktree and named branch only. It owns the exact plan file map, including the transaction/validation integration. No subagents or extra tasks.
- 086: existing task `01a060da-62a6-7d40-89b6-fc1bb10cc471`, QA-document/synthetic-input preparation only. It must not edit scripts, tests, commands, operation inventory, version or common state now.
- Integration: existing task `01a02dc7-0782-7822-b0a6-90b73c5330e7`, common goal/roadmap/lifecycle/approval records and later integration. Neither implementation task writes the other task's checkout.
- Consequently the overlapping memory tests, operation inventory and package/release validators have only one implementation writer (090) in this phase. 086 must not create a registry parser or use its path-derived display ID as 090's persistent project ID.

## Baseline and Readiness

- Main `f99a724` contains the merged 111/060 changes and the completed 0.3.56 publication record. Source publication is no longer held. R01/R02 fresh Codex/Claude observations remain separate; do not claim them passed or restart 111 implementation.
- The integration branch merged the existing 090 plan at `5ff27e6`, without default-checkout changes or deleting the 25 prior Issue 103 plans.
- Existing knowledge/memory baseline: 66 tests passed in 1.334s on the integrated source.
- Initial report-only readiness found API-label and UI-state-label gaps despite the existing R4/R6 contract and explicit non-UI scope. The plan now links those contracts and states the non-applicability of Storybook/MSW/Playwright. No checker code, required test or permission gate was weakened. The generated readiness report records the rerun; a lexical `pass` is not proof of UI tests having run.

## Canonical Lifecycle Observation

The attempted 090 start did not apply. First, an arbitrary supplied idempotency key was rejected by the existing semantic-hash contract. Omitting that optional argument correctly derived `b62687948092c57ebb803c6e771ce722634fb58d770067b62caaa1b42144ff4d`, but transaction `txn-bebf4b66aa717949c6454379047b5085` then returned `PROJECTED_VALIDATION_INVALID` / `PROJECTED_LIFECYCLE_DRIFT` before canonical writes. `consensus_drift` rejects two active issues, while 111 legitimately remains active for R01/R02. The unchanged source validates successfully with no lifecycle drift.

Keep 111 and the common cursor unchanged, and do not mark it done to make 090 start pass. The user-approved 090 implementation proceeds in its isolated task with authority/progress recorded in this packet; its canonical issue projection remains backlog for now. The integration owner will reconcile the single-active projection before final integration. This is not a new lifecycle-engine implementation task, a gate-code waiver, or evidence of successful start/completion. The implementation task must not retry state writes or silently change 111.

Implementation results must distinguish code, focused/full tests, simulated outcomes, remote integration, distribution and real-host observations. On completion or a substantive blocker, send a concise result back to the integration task so the user does not have to relay it manually.
