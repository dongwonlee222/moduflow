# Plan: GitHub Issue Sync

Issue: `054-github-issue-sync`
Spec: `specs/054-github-issue-sync/spec.md`
Next: `product:execute 054-github-issue-sync`

## Global Constraints

- All `gh` calls carry `-R <owner>/<repo>` explicitly (never rely on `gh` repo inference).
- All subprocess use goes through the injectable-runner pattern; tests never touch the network or the real `gh`.
- `issues/*.md` stays canonical: sync writes only the `- GitHub: <url>` Links line, nothing else in the file.
- One-way only: nothing reads GitHub-side state back except the label list needed for reconciliation.

## Streams

### Stream A — Sync script (`scripts/project_github_issues.py`)

Interfaces (consumed): `scripts/project_sync.run_command`/`CommandResult`; `scripts/project_lifecycle._issue_status`; `.moduflow/config.json` `git.github_sync`; `git remote get-url origin`.
Interfaces (produced): `sync_issue(root, issue_id, runner=None) -> dict` (result with `action: created|updated|disabled`, `url`, `label`), CLI `python3 scripts/project_github_issues.py <root> --issue-id <id> --sync`.

- `_parse_owner_repo(url)` for the three URL forms.
- `_github_link(text)` / `_write_github_link(path, url)` for the Links line.
- `_ensure_labels(runner, cwd, repo)` — list existing labels via `gh -R <repo> label list --json name`, create missing `moduflow:*` ones.
- Create path: `gh -R <repo> issue create --title <t> --body <text> --label moduflow:<status>` → parse URL from stdout → write Links line. (Amended from `--body-file <tmp>` at execute time: FakeRunner tests match exact arg tuples, and tempfile paths are nondeterministic — body passes as a plain argv element, no shell-injection surface.)
- Update path: extract issue number from stored URL → `gh -R <repo> issue edit <n> --add-label <current> --remove-label <stale...>` (stale = other three `moduflow:*`).

### Stream B — Tests (`tests/test_github_issue_sync.py`)

FakeRunner mapping exact arg-tuples → CommandResult (house pattern, see tests/test_project_sync.py). Tempdir fixture with fake `.moduflow/config.json`, `issues/<id>.md`.
Cases: disabled no-op (zero runner calls); create writes Links line; update edits labels & doesn't create; owner/repo parsing (3 forms, table test); label bootstrap creates only missing.

### Stream C — Docs

- `commands/product-issue.md`: document the opt-in sync command.
- `docs/host-adapter-guidance.md`: in the Auto Commit + Push On Issue Done section — after push, if the completed issue's file carries a `- GitHub:` link and `github_sync` isn't `off`, refresh its label with the sync command.

## Task right-sizing

Three tasks, one per stream; A and B land together (TDD), C follows. Single reviewable diff overall (~1 script + 1 test file + 2 doc edits).

## Gates

- RED before implementation, GREEN after (`tests.test_github_issue_sync`)
- `python3 -m unittest discover -s tests`
- `python3 scripts/release_check.py .`

## Rollback

Additive; revert the script, test file, and doc edits. Any GitHub Issues already created remain (harmless projections).
