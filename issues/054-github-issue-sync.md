# Issue: `054-github-issue-sync`

**Status: done** — created 2026-07-03, started 2026-07-05, done 2026-07-05.

## Outcome

Git-file issues in `issues/*.md` gain a lightweight, opt-in sync to actual GitHub Issues, so external collaborators can see status and progress from the GitHub UI without reading local Markdown — without making GitHub Issues the canonical source.

## Why

ModuFlow's own repository has zero GitHub Issues in use; every issue lives only as a git-file under `issues/`. Recent work (050, 052) strengthened the GitHub PR-facing side of the flow (Draft PR handoff, repo-sync preflight), but the issue-tracking side has no GitHub-visible counterpart. As soon as a non-local collaborator needs to see "what's in progress," they have no GitHub-native place to look.

## Scope

### In

- Extend `product:issue` (or `product:sync`) with an opt-in action to create/update a matching GitHub Issue for a git-file issue, gated by explicit user approval (consistent with `github_sync: "optional"` in `.moduflow/config.json`).
- Map the canonical `**Status:** backlog|active|done|superseded` line to a GitHub label, so status stays visible from the GitHub Issues list view.
- Keep `issues/*.md` as the single canonical source; GitHub Issue is a synced projection, not a second source of truth.

### Design decisions (recorded 2026-07-05 pre-implementation review; binding for spec/plan)

1. **Mapping storage**: the GitHub issue number is written back into the git-file issue's `## Links` section as `- GitHub: <issue url>` — canonical file carries the mapping, so re-sync updates instead of duplicating. No separate mapping file.
2. **Update trigger**: no hook mechanism exists for "lifecycle actions". Label updates ride the existing surfaces: (a) the `061` done-flow (when an issue completes, sync its label if a GitHub mapping exists) and (b) an explicit `product:sync` pass for bulk reconciliation. Nothing fires on raw file edits.
3. **Repo resolution**: `gh` cannot infer owner/repo from a non-`github.com` remote host (this machine's origin is the `github-evmodu` SSH alias). The sync command parses `owner/repo` from the origin URL path and passes it explicitly via `-R owner/repo` on every `gh` call. Tests cover the SSH-alias URL form.
4. **Label bootstrap**: on first sync, ensure the four status labels exist (`moduflow:backlog|active|done|superseded`, namespaced to avoid colliding with repo-native labels), creating any that are missing before applying.

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

## Workflow Tasks

- [x] spec → `specs/054-github-issue-sync/spec.md`
- [x] plan → `specs/054-github-issue-sync/plan.md`
- [x] execute → `scripts/project_github_issues.py`, `tests/test_github_issue_sync.py`, `commands/product-issue.md`, `docs/host-adapter-guidance.md`, `scripts/release_check.py`

## Sessions

- 2026-07-03: User asked what to improve next; GitHub check showed 0 GitHub Issues in use despite an active PR/CI flow. Registered as backlog issue only, per user's choice — implementation deferred.
- 2026-07-05: Pre-implementation design review recorded the 4 binding decisions above (mapping storage, trigger, explicit `-R`, label bootstrap). Spec/plan authored with the `067`-absorbed structure (Global Constraints + stream Interfaces).
- 2026-07-05: Executed per the model-tier convention. One process incident: the first implementation dispatch mis-delegated to a duplicate child agent (produced nothing; corrected via re-instruction, and future dispatch prompts now forbid sub-delegation). Implementation landed via TDD (5 tests RED→GREEN); independent read-only verification returned SPEC pass / QUALITY fail with 11 findings, of which 8 were fixed in the main loop (code-fence-aware Outcome extraction, Links-section-scoped discriminator, replace-instead-of-duplicate link write-back, `blob/HEAD` canonical link, nested-path rejection in owner/repo parsing, "already exists" tolerance in label bootstrap, unused import, update-path file-unchanged assertion) and 3 accepted with rationale (`--body` plan amendment documented; `ssh://` URL form out of documented scope; state.json bookkeeping handled at closure). Final: 9 module tests, 232 full suite, release_check valid.
- 2026-07-05: Live projection run with user approval — created https://github.com/dongwonlee222/moduflow/issues/6 (`moduflow:done` label, all four labels bootstrapped) and the URL wrote back into Links below. Operational note: the active `gh` account (`webn77`) got HTTP 404 on the labels endpoint (no write access to `dongwonlee222/moduflow`); required `gh auth switch --user dongwonlee222` for the call, switched back after — same identity split as the `github-evmodu` push alias.

## Links

- Roadmap: `workspace/roadmap.md`
- GitHub: https://github.com/dongwonlee222/moduflow/issues/6

## Next Command

`/product:status`
