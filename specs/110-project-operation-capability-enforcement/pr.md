# PR Handoff: 110-project-operation-capability-enforcement

## Purpose

Make the pull request the visible review surface instead of waiting until all local review work is finished.
Use a Draft PR or a local PR-ready marker early, then attach review, verification, and dashboard evidence to it as work progresses.

## Draft PR

- Branch: `codex/110-project-operation-capability-enforcement`
- PR: `local:110-project-operation-capability-enforcement:draft-pr-ready`
- Reviewer: `Reviewer`
- Fallback reason: GitHub Draft PR URL is not recorded yet. This local PR-ready marker preserves review state until GitHub sync creates or mirrors the PR.
- Preferred timing: create a Draft PR after the first meaningful commit, or record a local PR-ready marker when GitHub write access is unavailable.
- Do not merge from this handoff. Merge remains gated by Human approval, required reviews, and Required status checks.
- Commit mode: `local-git-write`

## Commands

```bash
python3 scripts/project_pr.py . --issue-id 110-project-operation-capability-enforcement --write
```

```bash
python3 scripts/project_workflow.py . --pr-state --issue-id 110-project-operation-capability-enforcement --pr "local:110-project-operation-capability-enforcement:draft-pr-ready" --reviewer "Reviewer"
```

- Continue review: `product:review 110-project-operation-capability-enforcement`
- Refresh PR handoff: `product:pr 110-project-operation-capability-enforcement`

## PR Body Contract

- Summary: what changed and why.
- Verification: local tests, release checks, CI/status checks, and known gaps.
- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-110-project-operation-capability-enforcement.html`.
- Korean human-review packet: `specs/110-project-operation-capability-enforcement/human-review.ko.md`.
- Review findings: implementation, QA, and PM/spec review results.
- Human approval: who reviewed the dashboard, PR diff, and merge readiness.

## Evidence To Mirror

### Verification

- Issue 110 focused suites: 572/572 passed.
- Full discovery: 1,339/1,339 passed.
- Project artifact validation: `valid: true`, `errors: []`.
- Spec consistency: 0 errors, 0 warnings, 0 info.
- Lifecycle drift: `[]` before review artifact synchronization.
- Mutation audit: `valid: true`; 64/64 classified with every gap count at zero.
- Diff hygiene: `git diff --check` clean.
- Independent code review: merge-ready for implementation; no Critical or Important finding remains.
- Source release check: `valid: true`, `errors: []`; operation audit, version bump, focused tests, validation, linkage, lint, and security checks passed.

### Review Findings

1. **Resolved — mutable capability projection could fail open.** Authorization now recomputes the expected policy from observed inputs and validates the complete normalized projection before allowing an operation.
2. **Resolved — public team-state writer bypassed its parent guard.** `write_team_state()` now resolves context and enforces `execute` before directory or file creation.
3. **Resolved — static audit proved only guard presence.** It now verifies operation literals, guard dominance, direct/nested helper ownership, and broader filesystem/network surfaces.
4. **Resolved — external-control was initially too broad.** It is publish-only and network-only; mixed file/Git mutation fails the audit.
5. **Resolved — open flags/modes could hide behind assignments.** Reaching assignments are evaluated at call position; multiple, augmented, unresolved, and nested-scope cases fail closed as dynamic mutation.
6. **Resolved — explicit-root compatibility used raw trust alone.** It now requires `explicit_root` provenance and exact `active/project-local` synthetic inputs.
7. **Resolved — Antigravity canonical control path and nested rewrite helper were not fully classified.** Both are explicitly reviewed, and helper calls are dominated by the outer execute guard.
8. **No open Critical or Important finding** remains after independent re-review of `60f7651`.

### Visual Evidence

- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-110-project-operation-capability-enforcement.html`.

## Approval Record

- Dashboard reviewer: `Reviewer` or assigned reviewer before merge.
- PR diff reviewer: `Reviewer` or assigned reviewer before merge.
- Merge approver: human approval required; not granted by this handoff.
- Deployment approver: required only when a protected deployment environment is configured.

## Human Checkpoints

- Spec/plan approval before implementation starts.
- Dashboard and issue drill-down inspection after review.
- GitHub PR diff, conversation, and status checks before approval.
- Merge and deployment approval through protected branch or environment gates.

## GitHub Gate Alignment

- PR review can approve, comment, or request changes.
- Required status checks must pass before merge when branch protection is configured.
- Required reviewers or CODEOWNERS remain the merge authority.
- Deployment environments may add a separate approval gate after merge or before release.

## Source Snapshot

- Issue bytes: 5130
- Spec bytes: 17086
- Status bytes: 3243
- Review bytes: 4038
