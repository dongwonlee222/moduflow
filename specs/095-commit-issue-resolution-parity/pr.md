# PR Handoff: 095-commit-issue-resolution-parity

## Purpose

Replace repository-global commit attribution guesses with one evidence-backed,
per-issue graph model shared by release linkage and project convergence.

## Draft PR

- Branch: `codex/095-commit-issue-resolution-parity-fix`
- PR: pending GitHub Draft PR creation
- Reviewer: `Reviewer`
- GitHub preflight: passed for `dongwonlee222/moduflow`; mode `github-draft-pr`.
- Do not merge from this handoff. Merge remains gated by Human approval, required reviews, and Required status checks.
- Commit mode: `local-git-write`

## Commands

```bash
python3 scripts/project_pr.py . --issue-id 095-commit-issue-resolution-parity --write
```

```bash
python3 scripts/project_workflow.py . --pr-state --issue-id 095-commit-issue-resolution-parity --pr "<github-pr-url>" --reviewer "Reviewer"
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

- Controller full discovery: `1035/1035 PASS` in 417.627 seconds.
- Issue 095 six-suite gate: `371/371 PASS` after final evidence hardening.
- Spec consistency: findings `0/0/0`; 9 requirements checked, 0 flagged.
- Release check: `valid: true`, `errors: []`; every named subgate passed.
- Project validation: `valid: true`, `errors: []`.
- Lifecycle drift: `[]`; `git diff --check` and worktree clean.
- Issue 093 live evidence: 56 commits, 46 files, schema file included,
  diagnostics/fatal/errors all empty.

### Review Findings

- Independent final whole-branch spec review: Critical/Important/Minor `0/0/0`.
- Independent final whole-branch quality review: Critical/Important/Minor `0/0/0`.
- Forty append-only failure families (`FH-001`–`FH-040`) map to independent
  executable invariants and mutation-sensitive required components.
- Historical octopus ambiguity remains recorded globally, is excluded from an
  unrelated release scope, and fails closed when explicitly in scope.

### Visual Evidence

- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-095-commit-issue-resolution-parity.html`.

## Summary and Risk

- One attribution snapshot and policy now serve both query directions and both
  consumers.
- Historical fork selection is per issue; stacked topics, deleted refs,
  detached HEAD, complex merges, and unrelated side refs have explicit tests.
- Fatal Git failures are separate from caller-scoped diagnostics; ambiguous
  evidence fails closed instead of silently under-collecting.
- Main risk is the breadth of Git-topology behavior. Mitigation is the 1,035
  test full gate, actual-Git metamorphic fixtures, and independent whole-branch
  review.

## Rollout Notes

- Canonical source manifest is `0.3.41`.
- This PR does not update the installed plugin/cache and does not release.
- Issue 096 evidence-write and path-safety work remains separate.

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

- Issue bytes: 15036
- Spec bytes: 8842
- Status bytes: 66633
- Review bytes: 0
