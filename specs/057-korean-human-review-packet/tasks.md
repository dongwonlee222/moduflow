# Tasks: Korean Human Review Packet

Issue: `057-korean-human-review-packet`
Plan: `specs/057-korean-human-review-packet/plan.md`

## Stream A — PR Packet Generator

- [x] Add Korean human-review packet builder to `scripts/project_pr.py`.
- [x] Make `write_pr_handoff()` write `human-review.ko.md` beside `pr.md`.
- [x] Include dashboard, issue detail, branch, PR/local marker, reviewer, summary, artifact checklist, verification, findings, hold criteria, and approval checklist.
- [x] Link `human-review.ko.md` from generated `pr.md`.
- [x] Tighten packet wording for release gates after 057 execution review.

## Stream B — GitHub PR Preflight

- [x] Add `python3 scripts/project_pr.py <project-path> --github-preflight`.
- [x] Check `gh auth status`.
- [x] Check `gh api rate_limit`.
- [x] Return `local-pr-ready` when auth/API fails.
- [x] Update `product:pr` docs to forbid `gh pr create` when preflight fails.

## Stream C — Dashboard Korean Detail

- [x] Add Korean issue descriptions overlay: `workspace/issue-descriptions.ko.json`.
- [x] Show Korean descriptions in the issue DB list.
- [x] Add generated `한글 개요` to issue detail pages.
- [x] Include Korean-only artifacts such as `human-review.ko.md`.
- [x] Keep sidecar rendering for full Korean artifacts.

## Stream D — Command Contracts

- [x] Update `commands/product-pr.md` with Korean packet and GitHub preflight requirements.
- [x] Update `commands/product-review.md` so review starts from the Korean packet.
- [x] Update `commands/product-release.md` to require Korean packet and approval evidence before release.

## Stream E — Tests

- [x] Test Korean packet generation in `tests/test_project_pr.py`.
- [x] Test Korean description overlay in packet generation.
- [x] Test GitHub PR preflight success/failure.
- [x] Test Korean overview in issue detail pages.
- [x] Test Korean-only artifacts in issue detail pages.
- [x] Add release-command contract test or validation coverage if release docs become machine-checked.

## Stream F — Dogfood And Handoff

- [x] Dogfood on Issue 056.
- [x] Generate `specs/056-dashboard-database-list-view/human-review.ko.md`.
- [x] Confirm 056 detail page exposes Korean review material.
- [x] Record 056 approval and release.
- [x] Complete 057 review artifact.
- [x] Complete 057 PR handoff and Korean review packet.

## Verification

- [x] `python3 -m unittest discover -s tests` passed with 175 tests during 056 dogfood.
- [x] `python3 scripts/validate_project_artifacts.py .` passed.
- [x] `python3 scripts/validate_moduflow.py .` passed.
- [x] `python3 scripts/release_check.py .` passed.
- [x] Re-run all gates after 057 PR handoff generation.

## Final Gate Run

- [x] `python3 -m unittest discover -s tests` passed with 176 tests.
- [x] `python3 scripts/validate_project_artifacts.py .` passed.
- [x] `python3 scripts/validate_moduflow.py .` passed.
- [x] `python3 scripts/release_check.py .` passed.

## Next

`product:review 057-korean-human-review-packet`
