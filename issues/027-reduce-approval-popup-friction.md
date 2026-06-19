# Issue 027: Reduce Approval Popup Friction

## Summary

Reduce repeated approval prompts by batching safe Git/GitHub operations, documenting expected prompts, and preferring in-process validation paths that avoid unnecessary shell, `.git`, network, or account writes.

## Source

- Type: user feedback
- Link: conversation, 2026-06-19
- Date: 2026-06-19

## Lifecycle

- Phase: complete
- Created: 2026-06-19
- Started:
- Target End:
- Completed: 2026-06-19
- Last Updated: 2026-06-19

## Opportunity

The approval model is important for safety, but repeated popups during merge, fetch, branch cleanup, GitHub API access, account switching, and routine validation script execution make the workflow feel noisy and fragile. ModuFlow should make approval moments predictable, rare, and clearly tied to real risk.

Antigravity feedback added a sharper version of this problem: ModuFlow currently relies on many standalone Python validation scripts (`project_doctor.py`, `validate_project_artifacts.py`, `validate_moduflow.py`, `release_check.py`). When an agent environment treats shell execution as an approval boundary, even safe validation can repeatedly interrupt the user.

## Scope

### In

- Identify high-frequency commands that trigger approvals during normal ModuFlow operation.
- Batch related Git operations behind one explicit user-confirmed step where the environment allows it.
- Prefer read-only checks before write operations.
- Add guidance for saved command prefixes and account/credential preflight.
- Improve messaging so users know why a prompt appears and whether it is optional.
- Add a "local-only mode" path that avoids GitHub/network prompts unless sync is requested.
- Refactor validation logic so safe checks can be called in-process as a Python library (`import moduflow`) or tool adapter instead of requiring shell execution.
- Define an MCP/tool-adapter path for doctor/validation checks where the host supports direct tool calls.
- Keep shell scripts as compatibility entrypoints, but make them thin wrappers around importable functions.

### Out

- Bypassing Codex approval or sandbox safety rules.
- Storing credentials or secrets in the repo.
- Silently deleting branches, rewriting history, or changing accounts without explicit user intent.
- Treating in-process validation as permission to perform writes, network calls, or destructive actions.

## Acceptance Criteria

- Common flows explain up front which approvals may appear.
- Merge-and-cleanup flows batch branch cleanup and remote sync decisions instead of prompting one command at a time where possible.
- `product:doctor` or preflight detects active GitHub account mismatch before a write operation.
- Local-only workflows can complete without GitHub API prompts.
- Documentation explains why `.git` writes, network calls, destructive cleanup, and account switching require approval.
- Routine validation can run through importable functions or tool adapters without shelling out for every check.
- Shell validation entrypoints remain available for CLI users and CI.

## Workflow Tasks

Every artifact-producing step is a tracked task here - never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [x] spec -> `specs/027-reduce-approval-popup-friction/spec.md`
- [x] plan -> `specs/027-reduce-approval-popup-friction/plan.md`
- [x] execute -> commits `b1bf566`, `1db6762`, `eade021`
- [x] review -> `specs/027-reduce-approval-popup-friction/review.md`
- [x] map approval-triggering commands -> `specs/027-reduce-approval-popup-friction/approval-surface.md`
- [x] add GitHub account preflight guidance -> `specs/027-reduce-approval-popup-friction/approval-surface.md`
- [x] add local-only/no-network path documentation -> `docs/host-adapter-guidance.md`
- [x] refactor validation scripts into importable validation engine APIs
- [x] add host/tool adapter guidance for environments such as Antigravity that can call tools directly -> `docs/host-adapter-guidance.md`

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `021-git-binding-and-execution-backend`, `024-artifact-schema-and-doctor-gates`
- supersedes:
- related: `025-lightweight-project-adoption`, `026-simplify-command-and-folder-surface`

## Sessions

- 2026-06-19: User asked why approval popups appear so often during branch merge, push, cleanup, and GitHub checks.
- 2026-06-19: Antigravity feedback noted that routine shell-based validation scripts also create approval fatigue; suggested importable validation or MCP/tool calls.

## Links

- Spec: `specs/027-reduce-approval-popup-friction/spec.md`
- Status: `specs/027-reduce-approval-popup-friction/status.md`
- Tasks: `specs/027-reduce-approval-popup-friction/tasks.md`
- Sessions: `sessions/027-reduce-approval-popup-friction/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:spec 028-real-subagent-execution-backend`
