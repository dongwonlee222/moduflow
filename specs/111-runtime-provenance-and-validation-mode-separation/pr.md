# PR Handoff: 111-runtime-provenance-and-validation-mode-separation

## Purpose

Prevent false diagnoses of healthy installed plugins and unsupported claims that a source-code update is already active in the current chat.

The confirmed Issue 102 post-release findings F-003 and F-004 identified two defects: installed packages were evaluated against source/project-only requirements, and status/Doctor lacked sufficient evidence to distinguish source, installed package and active process identity. Issue 111 fixes those diagnostic boundaries while keeping source release checks strict.

User benefit: determine which target was checked and which package is executing, separate code defects from installation/runtime mismatches, and avoid unnecessary reinstallations or false deployment-completion reports. Host skill-load information remains unknown when no evidence is available.

This is maintenance of the existing plugin, not a dashboard, wiki, automation engine, automatic chat reload or an actual publication/installation. PR summaries should lead with the purpose, observed problem, expected user benefit and exclusions before implementation details.

## Draft PR

- Branch: `codex/111-runtime-provenance-and-validation-mode-separation`
- PR: https://github.com/dongwonlee222/moduflow/pull/45
- Reviewer: `Dongwon Lee`
- Remote handoff: branch pushed and Draft PR created on 2026-09-02; live CI results are authoritative at the PR. Merge, publication and installation remain unperformed.
- Preferred timing: create a Draft PR after the first meaningful commit, or record a local PR-ready marker when GitHub write access is unavailable.
- Do not merge from this handoff. Merge remains gated by Human approval, required reviews, and Required status checks.
- Commit mode: `local-git-write`

## Commands

```bash
python3 scripts/project_pr.py . --issue-id 111-runtime-provenance-and-validation-mode-separation --write
```

```bash
python3 scripts/project_workflow.py . --pr-state --issue-id 111-runtime-provenance-and-validation-mode-separation --pr "https://github.com/dongwonlee222/moduflow/pull/45" --reviewer "Dongwon Lee"
```

- Continue review: `product:review 111-runtime-provenance-and-validation-mode-separation`
- Refresh PR handoff: `product:pr 111-runtime-provenance-and-validation-mode-separation`

## PR Body Contract

- Summary: what changed and why.
- Verification: local tests, release checks, CI/status checks, and known gaps.
- Dashboard: `memory/dashboard.html`.
- Issue drill-down: `memory/issue-111-runtime-provenance-and-validation-mode-separation.html`.
- Korean human-review packet: `specs/111-runtime-provenance-and-validation-mode-separation/human-review.ko.md`.
- Review findings: implementation, QA, and PM/spec review results.
- Human approval: who reviewed the dashboard, PR diff, and merge readiness.

## Evidence To Mirror

### Verification

- Prior implementation verification: 1,610 tests passed on `b5c3ce3` in 337.291s; source release check passed after the evidence commit `8229170`.
- Current PR handoff: fresh full suite on `8229170` passed on 2026-09-02: 1,610 tests in 359.621s, exit 0, no skipped tests. Implementation code is unchanged.
- Offline coverage: S01–S12 and packaged CLI/MCP smoke passed; these are not actual Codex/Claude host observations.
- GitHub identity/auth/API preflight passed for `dongwonlee222/moduflow`, base `main`; local commit/push capability is `local-git-write`.
- Source release check after PR-document commit `83b338e`: exit 0, all 13 checks passed. No implementation changes since full-suite verification.
- Remote CI was pending at this handoff; consult PR #45 checks for the latest head. Human merge approval, publication and installation are not complete.

### Review Findings

- Inline self-review only; no independent reviewer or human merge approval is claimed.
- Fixed the staged-manifest symlink write path before package validation, and preserved runtime evidence on MCP dispatch errors.
- Corrected the existing downstream security/lint test fixture to identify its source role; source/release gates were not weakened.
- No unresolved must-fix finding from the reviewed Issue 111 implementation. Real-host observations and explicit merge/publication approval remain outstanding.

### Visual Evidence

- No frontend/UI behavior changes in Issue 111; desktop/mobile screenshots are not applicable.
- Existing generated project views: `memory/dashboard.html` and `memory/issue-111-runtime-provenance-and-validation-mode-separation.html`. They are local read models, not installation evidence.
- Start human review with `human-review.ko.md`, then the canonical spec/status/review and GitHub diff.

## Approval Record

- Dashboard reviewer: `Dongwon Lee` or assigned reviewer before merge.
- PR diff reviewer: `Dongwon Lee` or assigned reviewer before merge.
- Merge approver: human approval required; not granted by this handoff.
- Deployment approver: explicit user approval is required for publication or installation, regardless of protected-environment configuration; not granted by this handoff.

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

- Implementation tested: `8229170`; this handoff adds review documents and team review state only.
- Canonical sources: `spec.md`, `status.md`, `review.md`; Korean reader: `human-review.ko.md`.
- Exact PR head and remote checks are recorded at the GitHub review surface after push; source version is not a deployment claim.
