# Issue 088: Canonical Repository/Remote Identity Gate

**Status: active** — created 2026-07-16, prioritized first 2026-07-16, implementation completed and reviewed after fixes 2026-07-16; Draft PR #25 opened for human review.
**Priority: p0**

## Summary

Store the canonical repository, remote identity, and base branch in the project profile, then stop execute, PR, release, or push workflows before any write when the current repository does not match that identity.

## Source

- Type: user product direction
- Link: local Codex session, 2026-07-16
- Owner / decision maker: Dongwon Lee
- Original requested ID: `081`; mapped to `088` because local issues `081`–`087` already exist.
- Current phase: pr

## Problem

ModuFlow currently has repository sync and doctor checks, but a remote named `origin` and a branch named `main` can still point to the wrong repository. A valid Git state is not enough: destructive or externally visible workflows must prove that the actual normalized repository URL and base branch match the project’s canonical identity.

## Product Decision

- Canonical repository identity is explicit project metadata, not inferred from the remote name.
- HTTPS, SSH, and optional `.git` suffix variants normalize to the same repository identity.
- `product:doctor` and `product:status` report identity health; `product:execute`, `product:pr`, `product:release`, and push handoffs hard-stop on mismatch before writes.
- Legacy repositories have an explicit `active`, `archive`, or `read_only` lifecycle state.
- GitHub API calls use an explicit canonical `owner/repo`, never an implicit current-directory fallback after a mismatch.

## Scope

### In

- Extend project profile/config metadata with canonical repository URL or slug, expected remote role, base branch, and lifecycle state.
- Normalize common Git URL forms before comparison.
- Compare the current Git root, actual remote URL, canonical repository, base branch, GitHub default branch, and archive state.
- Audit repository-bearing links in issue, spec, plan, status, PR, release, and review artifacts; non-canonical repositories must be explicitly classified as `mirror` or `reference`.
- Surface machine-readable identity results from doctor/status.
- Add pre-write gates to execute, PR, release, commit/push handoff, and optional GitHub issue sync.
- Provide migration guidance for existing projects and explicit archive/read-only behavior.

### Out

- Automatically rewriting remotes without approval.
- Deleting legacy repositories or branches.
- Treating the remote name `origin` as canonical identity.
- Requiring GitHub for local-only projects; local-only mode must be explicit.

## Acceptance Criteria

- A project profile can persist canonical repo identity, base branch, and repository lifecycle state.
- Equivalent HTTPS/SSH URLs normalize to the same identity.
- A wrong repository, fork, missing remote, wrong base branch, archived repository, and read-only repository each produce a deterministic result.
- `product:doctor` and `product:status` show expected identity, observed identity, and mismatch reason.
- `product:execute`, `product:pr`, `product:release`, and push handoff stop before external or Git writes on a hard mismatch.
- Tests prove that a remote merely named `origin` cannot bypass the URL check.
- Doctor/status report GitHub artifact links that point to a non-canonical repository without an explicit mirror/reference role.
- GitHub issue, PR, and release writes cannot reuse a stale artifact link from another repository.
- Current ModuFlow repository configuration passes the new gate after its canonical profile is recorded.
- `python3 scripts/release_check.py .` passes.

## Verification

- `python3 -m unittest discover -s tests -p 'test_*repo*identity*.py' -v`
- `python3 scripts/project_doctor.py .`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

- `scripts/project_profile.py`
- `scripts/project_doctor.py`
- `scripts/project_sync.py`
- `scripts/project_execution.py`
- `scripts/project_pr.py`
- `scripts/project_git_handoff.py`
- `scripts/validate_project_artifacts.py`
- `templates/`
- `.moduflow/config.json`
- `tests/`

## Scope Fence

Do not mutate remotes automatically. The first release must prove identity and block unsafe writes; remediation remains an explicit user action.

## Workflow Tasks

- [x] spec → `specs/088-canonical-repository-remote-identity-gate/spec.md` (+ `spec.ko.md`)
- [x] plan → `specs/088-canonical-repository-remote-identity-gate/plan.md`
- [x] execute → profile schema, normalizer, gates, migration path, and tests
- [x] review → `specs/088-canonical-repository-remote-identity-gate/review.md`

## Related Issues

- follows_up: `002-project-profile`, `013-project-doctor-gate`, `050-repo-sync-preflight`, `058-git-write-fallback-via-github-api`, `062-detect-unmerged-branch-work`, `074-sync-fetch-sandbox-handling`
- related: `021-git-binding-and-execution-backend`, `054-github-issue-sync`
- blocks:
- blocked_by:

## Reference Implementations

- GitHub CLI explicit default repository: `https://cli.github.com/manual/gh_repo_set-default`
- semantic-release `repositoryUrl` and dry-run push-permission verification: `https://semantic-release.gitbook.io/semantic-release/usage/configuration`
- Backstage canonical GitHub project slug: `https://backstage.io/docs/features/software-catalog/well-known-annotations/`

## Sessions

- 2026-07-16: User approved the identity gate as the first priority after reviewing the proposed change map.

## Links

- Spec: `specs/088-canonical-repository-remote-identity-gate/spec.md`
- Korean sidecar: `specs/088-canonical-repository-remote-identity-gate/spec.ko.md`
- Plan: `specs/088-canonical-repository-remote-identity-gate/plan.md`
- Tasks: `specs/088-canonical-repository-remote-identity-gate/tasks.md`
- Status: `specs/088-canonical-repository-remote-identity-gate/status.md`
- Review: `specs/088-canonical-repository-remote-identity-gate/review.md`
- Roadmap: `workspace/roadmap.md`
- Goal: `workspace/goal.md`
- GitHub: https://github.com/dongwonlee222/moduflow/issues/18
- PR: https://github.com/dongwonlee222/moduflow/pull/25

## Next Command

Human review and merge of [PR #25](https://github.com/dongwonlee222/moduflow/pull/25). Use `product:review 088-canonical-repository-remote-identity-gate` if feedback or checks fail; after merge use `product:release 088-canonical-repository-remote-identity-gate`.
