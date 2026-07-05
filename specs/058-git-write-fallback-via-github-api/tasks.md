# Tasks: Git Write Fallback Via GitHub API

Issue: `058-git-write-fallback-via-github-api`
Plan: `specs/058-git-write-fallback-via-github-api/plan.md`

## Stream A — Commit Capability Preflight

- [x] Add `scripts/project_git_handoff.py`.
- [x] Detect repo root and origin.
- [x] Add non-destructive `.git` write probe.
- [x] Classify `local-git-write`, `github-api-commit`, and `blocked`.
- [x] Return structured JSON for command use.

## Stream B — GitHub API Fallback Contract

- [x] Update `commands/product-pr.md`.
- [x] Update `commands/product-release.md`.
- [x] Update `commands/product-sync.md`.
- [x] State that Codex should try GitHub API fallback before asking the user for terminal commands.

## Stream C — Artifact Recording

- [x] Add commit mode wording to PR handoff.
- [x] Add commit mode wording to release notes.
- [x] Record local Git skip reason for API-created commits.

## Stream D — Tests

- [x] Test local Git write success.
- [x] Test local Git write blocked.
- [x] Test GitHub API fallback recommendation.
- [x] Test fully blocked mode.

## Verification

- [x] `python3 -m unittest discover -s tests`
- [x] `python3 scripts/validate_project_artifacts.py .`
- [x] `python3 scripts/validate_moduflow.py .`
- [x] `python3 scripts/release_check.py .`

## Next

`product:execute 058-git-write-fallback-via-github-api`
