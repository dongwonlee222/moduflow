# PR Handoff: 088-canonical-repository-remote-identity-gate

## Purpose

Make the pull request the visible review surface instead of waiting until all local review work is finished.
Use a Draft PR or a local PR-ready marker early, then attach review, verification, and dashboard evidence to it as work progresses.

## Draft PR

- Branch: `codex/088-canonical-repository-remote-identity-gate`
- PR: `local:088-canonical-repository-remote-identity-gate:draft-pr-ready`
- Reviewer: `Reviewer`
- Fallback reason: GitHub Draft PR URL is not recorded yet. This local PR-ready marker preserves review state until GitHub sync creates or mirrors the PR.
- Preferred timing: create a Draft PR after the first meaningful commit, or record a local PR-ready marker when GitHub write access is unavailable.
- Do not merge from this handoff. Merge remains gated by Human approval, required reviews, and Required status checks.
- Commit mode: `local-git-write`

## Commands

```bash
python3 scripts/project_pr.py . --issue-id 088-canonical-repository-remote-identity-gate --write
```

```bash
python3 scripts/project_workflow.py . --pr-state --issue-id 088-canonical-repository-remote-identity-gate --pr "local:088-canonical-repository-remote-identity-gate:draft-pr-ready" --reviewer "Reviewer"
```

- Continue review: `product:review 088-canonical-repository-remote-identity-gate`
- Refresh PR handoff: `product:pr 088-canonical-repository-remote-identity-gate`

## PR Body Contract

- Summary: what changed and why.
- Verification: local tests, release checks, CI/status checks, and known gaps.
- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-088-canonical-repository-remote-identity-gate.html`.
- Korean human-review packet: `specs/088-canonical-repository-remote-identity-gate/human-review.ko.md`.
- Review findings: implementation, QA, and PM/spec review results.
- Human approval: who reviewed the dashboard, PR diff, and merge readiness.

## Evidence To Mirror

### Verification

- `python3 -m unittest discover -s tests -p 'test_*.py'` — 528 tests passed.
- Focused identity/link/issue suites — 40 tests passed after the generic-provider capability fix.
- Focused identity/Git handoff suites — 35 tests passed after Git-root and API-fallback fixes.
- `python3 -m unittest tests.test_project_git_handoff -v` — 8 tests passed after the linked-worktree fix.
- `python3 scripts/spec_consistency.py . --issue-id 088-canonical-repository-remote-identity-gate` — 0 errors, 0 warnings.
- `python3 scripts/validate_moduflow.py .` — passed, 137 required files checked.
- `python3 scripts/validate_project_artifacts.py .` — valid, 0 errors.
- `python3 scripts/release_check.py .` — valid; validation, linkage, lint, security, version bump, tests, and doctor checks passed.
- Live `release` identity decision — `allowed: true`, status `match`, project root and provider repository/default branch/archive/fork evidence matched.

### Review Findings

1. **Important — generic providers advertised GitHub write/release capability. Resolved.** `github_write` and `release` now require `provider == github`; a regression test proves a healthy generic remote can execute/commit/push but cannot create GitHub PRs or releases.
2. **Important — accidental parent Git roots could pass. Resolved.** The inspector now emits `git_root_mismatch`, reports mismatch status, and blocks every write capability when the observed Git root differs from the requested project root.
3. **Important — local-only/generic projects could select GitHub API commit fallback. Resolved.** `github_api_commit` now maps to the shared `github_write` capability, and the handoff checks it before calling `gh`.
4. **Important — linked worktrees were misclassified as locally unwritable. Resolved.** The handoff now resolves a `.git` worktree pointer to the actual Git directory before its non-destructive probe; the regression test was observed failing before the fix and passing afterward.

No unresolved critical or important code findings remain.

### Visual Evidence

- Dashboard: `memory/dashboard.html`
- Issue drill-down: `memory/issue-088-canonical-repository-remote-identity-gate.html`

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

- Issue bytes: 6221
- Spec bytes: 17591
- Status bytes: 3775
- Review bytes: 4715
