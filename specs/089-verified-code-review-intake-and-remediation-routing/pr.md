# PR Handoff: 089-verified-code-review-intake-and-remediation-routing

## Purpose

Make the pull request the visible review surface instead of waiting until all local review work is finished.
Use a Draft PR or a local PR-ready marker early, then attach review, verification, and dashboard evidence to it as work progresses.

## Draft PR

- Branch: `codex/089-verified-code-review-intake-and-remediation-routing`
- PR: `https://github.com/dongwonlee222/moduflow/pull/26`
- Reviewer: `Dongwon Lee`
- Fallback reason: GitHub Draft PR URL is available or expected to be supplied by the workflow.
- Preferred timing: create a Draft PR after the first meaningful commit, or record a local PR-ready marker when GitHub write access is unavailable.
- Do not merge from this handoff. Merge remains gated by Human approval, required reviews, and Required status checks.
- Commit mode: `local-git-write`

## Commands

```bash
python3 scripts/project_pr.py . --issue-id 089-verified-code-review-intake-and-remediation-routing --write
```

```bash
python3 scripts/project_workflow.py . --pr-state --issue-id 089-verified-code-review-intake-and-remediation-routing --pr "https://github.com/dongwonlee222/moduflow/pull/26" --reviewer "Dongwon Lee"
```

- Continue review: `product:review 089-verified-code-review-intake-and-remediation-routing`
- Refresh PR handoff: `product:pr 089-verified-code-review-intake-and-remediation-routing`

## PR Body Contract

- Summary: what changed and why.
- Verification: local tests, release checks, CI/status checks, and known gaps.
- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-089-verified-code-review-intake-and-remediation-routing.html`.
- Korean human-review packet: `specs/089-verified-code-review-intake-and-remediation-routing/human-review.ko.md`.
- Review findings: implementation, QA, and PM/spec review results.
- Human approval: who reviewed the dashboard, PR diff, and merge readiness.

## Evidence To Mirror

### Verification

- TDD implementation commits: `f3804b9`, `962cae3`, `d539f22`, `c794028`, `e7f84c4`, `4bad53d`.
- Synthetic manual intake returned `action: preview`, schema `moduflow.review-intake.v1`, a reference SHA-256, invoked only manual/Superpowers adapters, and skipped GitHub/security/Spec Kit.
- Dry-run left `workspace/reviews` absent; the user's external review source was neither read nor copied during dogfood.
- Source-adapter verification: 5 tests passed.
- Review-intake focused verification after review fixes: 47 tests passed.
- Full `unittest` discovery contains 582 tests; the release test gate passed with zero failures.
- Spec consistency: 0 errors, 0 warnings, 0 info findings.
- `validate_moduflow.py`: passed, 145 required files checked.
- `validate_project_artifacts.py`: passed; only pre-existing non-blocking optional/link-role warnings remain.
- `release_check.py`: passed all package, artifact, linkage, lint, security, version, test, doctor, and documentation gates.
- GitHub CI `test`: passed after the review-fix commit and again after retargeting PR #26 to `main`; final approval-state CI remains required before merge.
- Staged review: four important findings reproduced and fixed; details in `review.md`.
- Dashboard and issue drill-down generated; local `file://` browser rendering was blocked by browser security policy and was not bypassed.
- Converge: 20 AC entries unverifiable because the evidence parser marked them non-parseable and truncated the bundle; non-blocking limitation recorded in `converge.md`.

### Review Findings

1. **Important — source reviewer self-verification across run IDs** (`scripts/review_intake.py`)
   - Before: the same reviewer identity could become Verifier by changing only `run_id`.
   - Resolution: source-reviewer independence now compares actor identity independently of run ID; Router independence still compares the logical run.
   - Evidence: `test_source_reviewer_cannot_self_verify_with_new_run_id` failed before the fix and now passes.

2. **Important — partial acceptance could reuse the rejected remedy** (`scripts/review_intake.py`)
   - Before: a `partial_accept` candidate defaulted to the original recommendation.
   - Resolution: partial acceptance requires `accepted_scope`, records it in disposition history, and uses it as the candidate title.
   - Evidence: `test_partial_accept_requires_accepted_scope` and `test_partial_accept_candidate_uses_accepted_scope_not_original_remedy` failed before the fix and now pass.

3. **Important — review ID path traversal at decision intake** (`scripts/project_review.py`)
   - Before: `--apply-decisions --review-id ../../...` reached filesystem lookup before ID validation.
   - Resolution: decision intake validates the review ID before constructing the packet path.
   - Evidence: `test_decision_update_rejects_review_id_path_traversal` reproduced the escaped lookup and now passes with `review_id_invalid`.

4. **Important — final validation trusted manually edited disposition fields** (`scripts/review_intake.py`)
   - Before: `--validate --final` checked only the disposition state name.
   - Resolution: final validation now requires rationale, confirmed evidence for `accept`, and evidence plus accepted scope for `partial_accept`.
   - Evidence: three final-validation regression tests failed before the fix and now pass.

### Visual Evidence

- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-089-verified-code-review-intake-and-remediation-routing.html`.

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

- Issue bytes: 10217
- Spec bytes: 23607
- Status bytes: 4234
- Review bytes: 4594
