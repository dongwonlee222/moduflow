# Spec: GitHub Issue Sync

Issue: `054-github-issue-sync`

## Problem

Every ModuFlow issue lives only as a git-file under `issues/`; the repository's GitHub Issues tab is empty. A collaborator with only GitHub access has no way to see what exists, what's active, and what's done without cloning and reading Markdown.

## Users

- External collaborator / reviewer with GitHub access but no local checkout.
- The operator, who wants progress visible without maintaining two trackers.

## Goals

- Opt-in, one-way projection: `issues/<id>.md` → a GitHub Issue with title, status label, and a link back to the canonical file.
- Status stays visible from the GitHub Issues list via namespaced labels (`moduflow:backlog|active|done|superseded`).
- Re-running sync updates the existing GitHub Issue (no duplicates).

## Non-Goals

- No two-way sync: GitHub-side edits never flow back into `issues/*.md`.
- No automatic projection of every issue by default — explicit per-invocation opt-in.
- No migration of historical issues in this change (the command can be pointed at any issue, but nothing bulk-runs).
- No open/close state management on the GitHub side in v1 — status is expressed via label only (close-on-done is a possible follow-up, noted in Alternatives).

## Requirements

Binding design decisions from the issue file (recorded 2026-07-05):

1. **Mapping storage**: after creating a GitHub Issue, write `- GitHub: <issue url>` into the git-file issue's `## Links` section. That line is the create-vs-update discriminator on later runs.
2. **Trigger**: explicit CLI invocation (`python3 scripts/project_github_issues.py . --issue-id <id> --sync`), plus a documented step in the `061` done-flow: when completing an issue that already has a GitHub mapping, refresh its label.
3. **Repo resolution**: parse `owner/repo` from `git remote get-url origin` (supports `git@<any-host-alias>:owner/repo.git`, `git@github.com:owner/repo.git`, `https://github.com/owner/repo[.git]`) and pass `-R owner/repo` explicitly on every `gh` call — `gh` cannot infer the repo from non-`github.com` SSH aliases (live case: `git@github-evmodu:...`).
4. **Label bootstrap**: before applying a label, ensure all four `moduflow:*` status labels exist in the repo, creating missing ones.

Additional:

5. **Enablement gate**: if `.moduflow/config.json`'s `git.github_sync` is `"off"`, the command is a no-op that reports sync disabled. `"optional"` (current value) and `"on"` allow explicit invocations.
6. GitHub Issue body: the git-file issue's `## Outcome` section (fallback: first paragraph) plus a canonical-source note linking to the file's GitHub blob URL. Body ends with a marker line `<!-- moduflow:issue-sync -->`.
7. All `gh` calls go through the injectable-runner pattern (`runner(args, cwd)` defaulting to `project_sync.run_command`) so tests use a `FakeRunner` — no network in tests.

## Acceptance Criteria

- `--sync` on an issue with no `- GitHub:` link creates a GitHub Issue (title = issue title, body per Req 6, label = current status) and writes the URL back into `## Links`.
- `--sync` on an issue that has a `- GitHub:` link updates labels on the existing GitHub Issue (removes stale `moduflow:*` labels, adds the current one) and does not create a new issue.
- With `github_sync: "off"`, `--sync` performs zero `gh` calls and reports disabled.
- Owner/repo parsing handles `git@github-evmodu:dongwonlee222/moduflow.git`, `git@github.com:o/r.git`, and `https://github.com/o/r` forms; every `gh` invocation carries `-R owner/repo`.
- Missing `moduflow:*` labels are created before use.
- `python3 -m unittest tests.test_github_issue_sync -v` passes; `python3 scripts/release_check.py .` passes.

## Risks

- `gh` API failures mid-sync (created issue but write-back failed): mitigated by writing the Links line immediately after create returns the URL, before label application.
- Label collision with repo-native labels: avoided by the `moduflow:` namespace.

## Alternatives Considered

- **GitHub Issues as canonical**: rejected — Git-native files are ModuFlow's foundation (issue Scope Out).
- **Two-way sync**: rejected for v1 — conflict resolution complexity without demonstrated need.
- **Close GitHub issue on done**: deferred — label-only keeps v1 reversible; revisit if collaborators find open-but-done confusing.
- **Bulk `--all` sync**: deferred — opt-in-per-issue matches the "no automatic creation" scope boundary.

## Next Command

`product:plan 054-github-issue-sync`
