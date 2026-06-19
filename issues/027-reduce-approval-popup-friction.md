# Issue 027: Reduce Approval Popup Friction

## Summary

Reduce repeated approval prompts by batching safe Git/GitHub operations, documenting expected prompts, and preferring lower-churn workflows that avoid unnecessary `.git`, network, or account writes.

## Source

- Type: user feedback
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

The approval model is important for safety, but repeated popups during merge, fetch, branch cleanup, GitHub API access, and account switching make the workflow feel noisy and fragile. ModuFlow should make approval moments predictable, rare, and clearly tied to real risk.

## Scope

### In

- Identify high-frequency commands that trigger approvals during normal ModuFlow operation.
- Batch related Git operations behind one explicit user-confirmed step where the environment allows it.
- Prefer read-only checks before write operations.
- Add guidance for saved command prefixes and account/credential preflight.
- Improve messaging so users know why a prompt appears and whether it is optional.
- Add a "local-only mode" path that avoids GitHub/network prompts unless sync is requested.

### Out

- Bypassing Codex approval or sandbox safety rules.
- Storing credentials or secrets in the repo.
- Silently deleting branches, rewriting history, or changing accounts without explicit user intent.

## Acceptance Criteria

- Common flows explain up front which approvals may appear.
- Merge-and-cleanup flows batch branch cleanup and remote sync decisions instead of prompting one command at a time where possible.
- `product:doctor` or preflight detects active GitHub account mismatch before a write operation.
- Local-only workflows can complete without GitHub API prompts.
- Documentation explains why `.git` writes, network calls, destructive cleanup, and account switching require approval.

## Workflow Tasks

Every artifact-producing step is a tracked task here - never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [ ] spec -> `specs/027-reduce-approval-popup-friction/spec.md`
- [ ] plan -> `specs/027-reduce-approval-popup-friction/plan.md`
- [ ] execute -> PR / commits
- [ ] review -> review notes
- [ ] map approval-triggering commands
- [ ] add GitHub account preflight guidance
- [ ] add local-only/no-network path documentation

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `021-git-binding-and-execution-backend`, `024-artifact-schema-and-doctor-gates`
- supersedes:
- related: `025-lightweight-project-adoption`, `026-simplify-command-and-folder-surface`

## Sessions

- 2026-06-19: User asked why approval popups appear so often during branch merge, push, cleanup, and GitHub checks.

## Links

- Spec: `specs/027-reduce-approval-popup-friction/spec.md`
- Status: `specs/027-reduce-approval-popup-friction/status.md`
- Sessions: `sessions/027-reduce-approval-popup-friction/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:spec 027-reduce-approval-popup-friction`
