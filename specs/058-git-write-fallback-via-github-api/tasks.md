# Tasks: Git Write Fallback Via GitHub API

Issue: `058-git-write-fallback-via-github-api`
Plan: `specs/058-git-write-fallback-via-github-api/plan.md`

## Stream A — Commit Capability Preflight

- [ ] Add `scripts/project_git_handoff.py`.
- [ ] Detect repo root and origin.
- [ ] Add non-destructive `.git` write probe.
- [ ] Classify `local-git-write`, `github-api-commit`, and `blocked`.
- [ ] Return structured JSON for command use.

## Stream B — GitHub API Fallback Contract

- [ ] Update `commands/product-pr.md`.
- [ ] Update `commands/product-release.md`.
- [ ] Update `commands/product-sync.md`.
- [ ] State that Codex should try GitHub API fallback before asking the user for terminal commands.

## Stream C — Artifact Recording

- [ ] Add commit mode wording to PR handoff.
- [ ] Add commit mode wording to release notes.
- [ ] Record local Git skip reason for API-created commits.

## Stream D — Tests

- [ ] Test local Git write success.
- [ ] Test local Git write blocked.
- [ ] Test GitHub API fallback recommendation.
- [ ] Test fully blocked mode.

## Verification

- [ ] `python3 -m unittest discover -s tests`
- [ ] `python3 scripts/validate_project_artifacts.py .`
- [ ] `python3 scripts/validate_moduflow.py .`
- [ ] `python3 scripts/release_check.py .`

## Next

`product:execute 058-git-write-fallback-via-github-api`
