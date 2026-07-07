# Release: 073-project-constitution-steering

Issue: `073-project-constitution-steering`
Version: 0.3.17 (from 0.3.16)
Merged: PR https://github.com/dongwonlee222/moduflow/pull/11 → `main`, 2026-07-07
Approval: **Constitution v1.0 ratified** by human merge approval ("비준하고 병합합시다", 2026-07-07); approver recorded in the amendment log as the release reconciliation.

## Shipped

- `workspace/constitution.md` (+ko): 11 origin-referenced principles (C1–C11), human-gated amendments, unlogged-edit-void rule. First ratification completed per its own C6.
- Consumption wiring: plan (reference form), spec (assumption note), review + handoff template (compliance line), converge (transitive-enforcement note). Zero script logic changed.
- Closes the last of the 2026-07-05 competitive benchmark's five gaps (068·070·071·072·073 all shipped).

## Verification at release

- Full suite green; release_check valid; converge self-audit 0 violations; first compliance line used in 073's own review.

## Rollback

Revert the merge; docs + one template string. The ratified constitution reverts with it (a re-ratification would be needed to restore).

## Post-release checks

- **CV-1 forward obligation**: the next executed issue's plan must open its GCs with `Constitution v1.0 applies (workspace/constitution.md). Plan-specific additions:` — record the dogfood evidence in 073's status.md and check off CV-1.
- Reviews from now on must carry the compliance line — its absence is itself a review gap.
