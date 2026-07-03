# Plan: Git Write Fallback Via GitHub API

Issue: `058-git-write-fallback-via-github-api`
Spec: `specs/058-git-write-fallback-via-github-api/spec.md`
Next: `product:execute 058-git-write-fallback-via-github-api`

## Implementation Shape

Add a small commit-capability preflight and wire the result into command guidance. The first implementation should be local and testable; actual GitHub API commit creation may remain host/tool-provided, but ModuFlow should decide and record the right path.

## Streams

### Stream A — Commit Capability Preflight

- Add a helper, likely `scripts/project_git_handoff.py`.
- Check repo root and origin.
- Attempt a non-destructive local Git write probe:
  - verify `.git` exists
  - attempt to create and remove a temporary lock/probe file under `.git`
  - never touch `index.lock` if it already exists
- Return structured JSON:
  - `mode`
  - `ok`
  - `local_git_write`
  - `github_api_available`
  - `reason`
  - `recommendations`

### Stream B — GitHub API Fallback Contract

- Document the fallback in `commands/product-pr.md`, `commands/product-release.md`, and `commands/product-sync.md`.
- Define required evidence fields:
  - branch
  - base ref
  - commit URL/SHA
  - uploaded file count
  - local Git skip reason
- Make the user-facing rule explicit: do not ask the user to run terminal Git commands until both local Git and GitHub API paths fail.

### Stream C — Artifact Recording

- Extend PR/release handoff wording to include commit mode.
- For API commits, record `github-api-commit`.
- For local commits, record `local-git-write`.
- For blocked cases, record the blocker and next recovery action.

### Stream D — Tests

- Unit test local Git write success.
- Unit test permission/index-lock style failure.
- Unit test fallback mode when GitHub API is available.
- Unit test blocked mode when both paths fail.

## Manual QA

1. Run the preflight in the current Codex environment.
2. Confirm it reports local Git write blocked.
3. Confirm it recommends GitHub API commit fallback.
4. Confirm release/check handoff can record that mode.

## Gates

- `python3 -m unittest discover -s tests`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/release_check.py .`

## Rollback

This is additive. Roll back by reverting the helper script, command-doc updates, and tests.

## Out Of Scope

- Automatic merge.
- Token storage.
- GitHub Issues sync.
- Destructive local Git cleanup.
