# Issue: `058-git-write-fallback-via-github-api`

**Status: backlog** — created 2026-07-03, planned 2026-07-03 (deprioritized 2026-07-05 in favor of `053`; spec/plan exist, execute not started — pick up via `product:execute 058-git-write-fallback-via-github-api`).

## Outcome

ModuFlow can finish Git handoff even when the local Codex environment cannot write to `.git`, by detecting the failure early and switching to a GitHub API commit path before asking a human to run terminal commands.

## Why

During Issues 056 and 057, local file edits and validation worked, but `git add` failed because the sandbox could not create `.git/index.lock`. The work still reached GitHub because Codex manually used the GitHub API, but that was an ad hoc fallback. This should become a standard ModuFlow flow so the user is not asked to run terminal commands for routine stage/commit/push work.

## Scope

### In

- Add a Git write preflight that checks whether local Git metadata can be written safely.
- Detect common local Git write failures such as inability to create `.git/index.lock`.
- Define a standard fallback result: `github-api-commit`.
- Add a GitHub API commit handoff contract for branch creation, file upload, commit URL, and recorded evidence.
- Update PR/release/status handoffs so they record whether commit/push happened through local Git or GitHub API.
- Add tests covering local Git write allowed, local Git write blocked, and fallback recommendation.

### Out

- No direct storage of GitHub tokens.
- No automatic merge to `main`.
- No replacement of Git as the canonical artifact store.
- No broad GitHub Issues sync; that remains Issue 054.

## Acceptance Criteria

- A script or helper reports `local-git-write` when local staging/commit is available.
- The same helper reports `github-api-commit` with a clear reason when `.git` writes are blocked.
- Product command docs tell Codex to use GitHub API fallback before asking the user to run terminal commands.
- PR/release handoffs include the commit mode and commit URL or local hash.
- Tests pass and `python3 scripts/release_check.py .` passes.

## Related Issues

- follows_up: `057-korean-human-review-packet`
- related: `052-draft-pr-review-handoff`
- related: `050-repo-sync-preflight`
- related: `054-github-issue-sync`

## Sessions

- 2026-07-03: User said people should not have to run terminal Git commands. Issues 056 and 057 were pushed through GitHub API because local `.git` writes were blocked.
- 2026-07-05: Merged into `main` from `origin/codex/058-git-write-fallback-via-github-api` along with 056/057 (which were done on that branch). 058 itself was still at plan phase on that branch — moved back to backlog here since work shifted to `053` this session; not abandoned.

## Links

- Spec: `specs/058-git-write-fallback-via-github-api/spec.md`
- Spec KO: `specs/058-git-write-fallback-via-github-api/spec.ko.md`
- Plan: `specs/058-git-write-fallback-via-github-api/plan.md`
- Plan KO: `specs/058-git-write-fallback-via-github-api/plan.ko.md`
- Tasks: `specs/058-git-write-fallback-via-github-api/tasks.md`
- Status: `specs/058-git-write-fallback-via-github-api/status.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:execute 058-git-write-fallback-via-github-api`
