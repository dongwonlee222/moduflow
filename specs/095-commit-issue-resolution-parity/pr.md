# PR Handoff: 095-commit-issue-resolution-parity

## Purpose

Make the pull request the visible review surface instead of waiting until all local review work is finished.
Use a Draft PR or a local PR-ready marker early, then attach review, verification, and dashboard evidence to it as work progresses.

## Draft PR

- Branch: `codex/095-commit-issue-resolution-parity`
- PR: `local:095-commit-issue-resolution-parity:draft-pr-ready`
- Reviewer: `Reviewer`
- Fallback reason: GitHub Draft PR URL is not recorded yet. This local PR-ready marker preserves review state until GitHub sync creates or mirrors the PR.
- Preferred timing: create a Draft PR after the first meaningful commit, or record a local PR-ready marker when GitHub write access is unavailable.
- Do not merge from this handoff. Merge remains gated by Human approval, required reviews, and Required status checks.
- Commit mode: `local-git-write`

## Commands

```bash
python3 scripts/project_pr.py . --issue-id 095-commit-issue-resolution-parity --write
```

```bash
python3 scripts/project_workflow.py . --pr-state --issue-id 095-commit-issue-resolution-parity --pr "local:095-commit-issue-resolution-parity:draft-pr-ready" --reviewer "Reviewer"
```

- Continue review: `product:review 095-commit-issue-resolution-parity`
- Refresh PR handoff: `product:pr 095-commit-issue-resolution-parity`

## PR Body Contract

- Summary: what changed and why.
- Verification: local tests, release checks, CI/status checks, and known gaps.
- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-095-commit-issue-resolution-parity.html`.
- Korean human-review packet: `specs/095-commit-issue-resolution-parity/human-review.ko.md`.
- Review findings: implementation, QA, and PM/spec review results.
- Human approval: who reviewed the dashboard, PR diff, and merge readiness.

## Evidence To Mirror

### Verification

- Verification evidence has not been recorded yet.

### Review Findings

- Review findings have not been recorded yet.

### Visual Evidence

- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-095-commit-issue-resolution-parity.html`.

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

- Issue bytes: 5907
- Spec bytes: 7818
- Status bytes: 10909
- Review bytes: 0
