# Issue: `054-github-issue-sync`

**Status: backlog** — created 2026-07-03.

## Outcome

Git-file issues in `issues/*.md` gain a lightweight, opt-in sync to actual GitHub Issues, so external collaborators can see status and progress from the GitHub UI without reading local Markdown — without making GitHub Issues the canonical source.

## Why

ModuFlow's own repository has zero GitHub Issues in use; every issue lives only as a git-file under `issues/`. Recent work (050, 052) strengthened the GitHub PR-facing side of the flow (Draft PR handoff, repo-sync preflight), but the issue-tracking side has no GitHub-visible counterpart. As soon as a non-local collaborator needs to see "what's in progress," they have no GitHub-native place to look.

## Scope

### In

- Extend `product:issue` (or `product:sync`) with an opt-in action to create/update a matching GitHub Issue for a git-file issue, gated by explicit user approval (consistent with `github_sync: "optional"` in `.moduflow/config.json`).
- Map the canonical `**Status:** backlog|active|done|superseded` line to a GitHub label, so status stays visible from the GitHub Issues list view.
- Keep `issues/*.md` as the single canonical source; GitHub Issue is a synced projection, not a second source of truth.

### Out

- No automatic creation of a GitHub Issue for every git-file issue by default — opt-in only.
- No automatic closing/reopening from GitHub-side edits (one-way sync: local file -> GitHub, same direction as the existing PR handoff).
- No migration of historical issues (001-052) into GitHub Issues.

## Acceptance Criteria

- A documented command/flag creates or updates a GitHub Issue from a given `issues/<id>.md`, with title, status label, and a link back to the file.
- Status label updates on `issue <id> start|complete` lifecycle actions when GitHub sync is enabled for that issue.
- Tests cover: sync disabled (no-op), sync enabled + create, sync enabled + status update.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- related: `035-team-issue-branch-pr-workflow`
- related: `052-draft-pr-review-handoff` (equivalent GitHub-facing pattern on the PR side)

## Sessions

- 2026-07-03: User asked what to improve next; GitHub check showed 0 GitHub Issues in use despite an active PR/CI flow. Registered as backlog issue only, per user's choice — implementation deferred.

## Links

- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:status`
