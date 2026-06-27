# Issue 029: Antigravity Artifact Sync Connector

## Summary

Reduce duplicate planning/documentation work by syncing Antigravity-native artifacts with ModuFlow's Git-native issue/spec/status files.

## Source

- Type: user feedback / Antigravity feedback
- Link: conversation, 2026-06-19
- Date: 2026-06-19

## Lifecycle

- Phase: backlog
- Created: 2026-06-19
- Started:
- Target End:
- Completed:
- Last Updated: 2026-06-19

## Opportunity

Antigravity may maintain native planning artifacts such as `task.md` and `implementation_plan.md`, while ModuFlow stores durable Git artifacts such as `issues/*.md`, specs/<issue>/spec.md, `plan.md`, `tasks.md`, and `status.md`. If both systems are updated separately, agents duplicate effort and the record fragments.

## Scope

### In

- Map Antigravity artifacts to ModuFlow issue/spec/plan/task/status files.
- Define one source-of-truth policy per artifact type.
- Add conflict detection when both sides changed.
- Preserve ModuFlow's Git-native files as the durable audit trail unless a verified host API requires another source.
- Support one-way import/export first, then two-way sync only after conflict rules are clear.

### Out

- Blind bidirectional sync without conflict handling.
- Replacing ModuFlow's Git artifact model.
- Storing private host workspace metadata in public repo files.
- Assuming Antigravity artifact filenames or APIs before verification.

## Acceptance Criteria

- A sync spec defines field mapping between Antigravity artifacts and ModuFlow artifacts.
- The connector can detect drift and report which side changed.
- Users can update one surface without manually duplicating the same content into the other.
- Sync operations are explicit and auditable.
- Sensitive or host-local metadata is excluded from Git by default.

## Workflow Tasks

Every artifact-producing step is a tracked task here - never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [x] spec -> `specs/029-antigravity-artifact-sync-connector/spec.md`
- [x] plan -> `specs/029-antigravity-artifact-sync-connector/plan.md`
- [x] execute -> PR / commits
- [x] review -> review notes
- [x] verify Antigravity artifact model and filenames before implementation
- [x] define artifact mapping and conflict policy
- [x] prototype one-way import/export
- [x] add drift detection

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `011-workflow-task-tracking`, `019-loop-kernel-and-state-model`, `024-artifact-schema-and-doctor-gates`
- supersedes:
- related: `027-reduce-approval-popup-friction`, `028-real-subagent-execution-backend`

## Sessions

- 2026-06-19: Antigravity feedback noted duplicate document management between host-native artifacts and ModuFlow Git artifacts.

## Links

- Spec: `specs/029-antigravity-artifact-sync-connector/spec.md`
- Status: `specs/029-antigravity-artifact-sync-connector/status.md`
- Sessions: `sessions/029-antigravity-artifact-sync-connector/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:status`
