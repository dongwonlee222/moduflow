# Spec: Git Write Fallback Via GitHub API

Issue: `058-git-write-fallback-via-github-api`

## Problem

Codex can sometimes edit project files but cannot write local Git metadata. In this environment, `git add` failed because `.git/index.lock` could not be created. ModuFlow should not hand that failure to the user as a terminal chore when a connected GitHub API path is available.

## Goals

- Detect local Git write availability before stage/commit/push handoff.
- Route blocked local Git writes to a GitHub API commit path.
- Record the chosen commit mode in status, PR, and release artifacts.
- Keep human approval semantics unchanged.
- Avoid asking the user to run terminal commands unless both local Git and GitHub API paths are unavailable.

## Non-Goals

- No automatic merge.
- No GitHub token storage in repo files.
- No GitHub Issues mirror; see Issue 054.
- No automatic force-push or destructive local Git repair.

## Behavior

The workflow should classify commit capability:

- `local-git-write`: local `.git` metadata can be written; stage/commit/push can proceed normally.
- `github-api-commit`: local `.git` metadata is not writable, but GitHub API can create/update a branch and push files.
- `blocked`: neither local Git write nor GitHub API commit is available.

When `github-api-commit` is selected, ModuFlow should record:

- repository owner/name
- branch
- base branch or base commit
- commit message
- commit URL
- file list
- reason local Git was skipped

## Acceptance Criteria

- Git write preflight returns structured JSON with `mode`, `ok`, `reason`, and `recommendations`.
- `.git/index.lock` permission failures are classified as `github-api-commit` when GitHub API is available.
- Command docs instruct Codex to try GitHub API fallback before asking the user for terminal commands.
- PR/release artifacts can cite API-created commits.
- Unit tests cover the mode decision.
- `python3 scripts/release_check.py .` passes.

## Next Command

`product:plan 058-git-write-fallback-via-github-api`
