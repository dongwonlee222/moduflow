# PR Handoff: 097-single-entry-capability-routing-contract

## Purpose

Make the pull request the visible review surface instead of waiting until all local review work is finished.
Use a Draft PR or a local PR-ready marker early, then attach review, verification, and dashboard evidence to it as work progresses.

## Draft PR

- Branch: `codex/097-single-entry-capability-routing-contract`
- PR: `https://github.com/dongwonlee222/moduflow/pull/36`
- Reviewer: `Dongwon Lee`
- Fallback reason: GitHub Draft PR URL is available or expected to be supplied by the workflow.
- Preferred timing: create a Draft PR after the first meaningful commit, or record a local PR-ready marker when GitHub write access is unavailable.
- Do not merge from this handoff. Merge remains gated by Human approval, required reviews, and Required status checks.
- Commit mode: `github-api-commit` — local .git commit probe is unavailable in this worktree; PR artifact commit uses the canonical GitHub API fallback

## Commands

```bash
python3 scripts/project_pr.py . --issue-id 097-single-entry-capability-routing-contract --write
```

```bash
python3 scripts/project_workflow.py . --pr-state --issue-id 097-single-entry-capability-routing-contract --pr "https://github.com/dongwonlee222/moduflow/pull/36" --reviewer "Dongwon Lee"
```

- Continue review: `product:review 097-single-entry-capability-routing-contract`
- Refresh PR handoff: `product:pr 097-single-entry-capability-routing-contract`

## PR Body Contract

- Summary: what changed and why.
- Verification: local tests, release checks, CI/status checks, and known gaps.
- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-097-single-entry-capability-routing-contract.html`.
- Korean human-review packet: `specs/097-single-entry-capability-routing-contract/human-review.ko.md`.
- Review findings: implementation, QA, and PM/spec review results.
- Human approval: who reviewed the dashboard, PR diff, and merge readiness.

## Evidence To Mirror

### Verification

- Implementation readiness: `ready`; all seven checks passed.
- Focused final review suite: 43/43 passed.
- Initial full discovery: 1,065 tests, 3 failures. Root cause was one distribution
  boundary: the Codex personal cache allowlist omitted the newly required routing fixture.
- Packaging correction: added the fixture to `RUNTIME_TEST_FIXTURES`, renamed and expanded
  the cache-copy regression test, and bumped the plugin through version `0.3.43`.
- Final full discovery: 1,077/1,077 passed in 429.782 seconds.
- Before the final run, the version-bump gate correctly caught an unchanged manifest after a
  patch commit; version `0.3.43` corrected it and both release-wrapper regressions passed 2/2.
- `python3 scripts/spec_consistency.py . --issue-id 097-single-entry-capability-routing-contract`:
  0 errors, 0 warnings, 0 info; 13/13 acceptance criteria covered.
- `python3 scripts/validate_moduflow.py .`: passed; 155 required files.
- `python3 scripts/validate_project_artifacts.py .`: valid with no errors; warnings are
  pre-existing optional-memory, dependency-wait, and non-canonical-reference warnings.
- `python3 scripts/project_lifecycle.py . --drift`: `[]`.
- `python3 scripts/release_check.py .`: valid with `errors: []`; all named subchecks passed.
- `git diff --check`: clean.

### Review Findings

| Severity | Open findings |
| --- | ---: |
| Critical | 0 |
| Important | 0 |
| Minor | 0 |

### Visual Evidence

- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-097-single-entry-capability-routing-contract.html`.

## Approval Record

- Dashboard reviewer: `Dongwon Lee` or assigned reviewer before merge.
- PR diff reviewer: `Dongwon Lee` or assigned reviewer before merge.
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

- Issue bytes: 7414
- Spec bytes: 9798
- Status bytes: 2992
- Review bytes: 1518
