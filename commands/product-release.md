---
description: Prepare release, deploy, rollback, and post-release checks.
argument-hint: "<issue id>"
---

# /product:release

Prepare release.

## Do

1. Confirm merged PR, version, deploy target, rollback path, and post-release checks.
2. Run the canonical repository release decision before tag, release, deploy, or publish:

```bash
python3 scripts/project_repository_identity.py <project-path> --operation release
```

Continue only when `allowed` is `true`. This requires matching fetch/push identity, configured base ref, active lifecycle, explicit GitHub `nameWithOwner`, matching default branch, and non-archived/non-fork provider evidence. A stale PR/release URL never selects the target repository; all GitHub commands use explicit canonical `-R OWNER/REPOSITORY`. There is no force bypass.

3. Before any local `git commit`/`push` this step needs, run `python3 scripts/project_git_handoff.py <project-path> --operation commit` and rerun with `--operation push` immediately before push. If `mode` is `github-api-commit`, use the GitHub API only after canonical identity allowed the operation; only ask the user to run terminal Git commands when `mode` is `blocked` (see `/product:pr`'s Commit Capability step for the full contract).
4. Confirm `specs/<issue>/human-review.ko.md` exists and was used as the first human approval surface.
5. Confirm human approval evidence is recorded before release. The evidence must identify who reviewed the dashboard, issue detail, PR diff or local change scope, verification result, and release readiness.
6. Hold release if the Korean packet is missing, stale, or does not include verification, hold criteria, and approval checklist.
7. Run `scripts/release_check.py .` before publishing a plugin/package update. Since issue 075 this includes the **linkage gate**: every behavior-affecting commit since the canonical base ref (paths under `scripts/`, `commands/`, `skills/`, `templates/`, workflow config — `commands/*.md` count as behavior) must resolve to an issue via branch name (`codex/<issue-id>-*`) or commit trailer (`Issue: <id>`), or be covered by a no-issue declaration in `releases/no-issue-declarations.md` whose `git blame` author is a human identity from `.moduflow/humans.json`. Git plumbing failures make the gate error loudly — a failing or erroring gate holds the release; never work around it by weakening paths or config.
8. Save to `specs/<issue>/release.md`.
9. Update roadmap and status.

## Korean Human Review Gate

Release can proceed only after a Korean-speaking reviewer can start from `human-review.ko.md` and make an approve/hold decision without searching through English-only artifacts.

The release note should link:

- `specs/<issue>/human-review.ko.md`
- `specs/<issue>/pr.md`
- `memory/dashboard.html#issue-db`
- `memory/issue-<issue>.html`

If GitHub PR creation is unavailable, record the local PR-ready marker and keep the Korean packet current. Do not treat the local marker as merge or release approval.

## Next

- `/product:update` for stakeholder communication
- `/product:analyze` for post-release metric readout
