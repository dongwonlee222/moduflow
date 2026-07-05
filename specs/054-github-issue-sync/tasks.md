# Tasks: GitHub Issue Sync

Issue: `054-github-issue-sync`
Plan: `specs/054-github-issue-sync/plan.md`

## Stream A — Sync script

- [ ] `_parse_owner_repo` covering ssh-alias / ssh / https forms
- [ ] Links-line read/write helpers
- [ ] `_ensure_labels` bootstrap
- [ ] `sync_issue` create path (create → write Links → label)
- [ ] `sync_issue` update path (label reconcile, no duplicate create)
- [ ] `github_sync: off` no-op gate
- [ ] CLI entry (`--issue-id`, `--sync`)

## Stream B — Tests

- [ ] disabled no-op (zero gh calls)
- [ ] create path writes Links line
- [ ] update path edits labels, no create
- [ ] owner/repo parsing table test
- [ ] label bootstrap creates only missing

## Stream C — Docs

- [ ] `commands/product-issue.md` opt-in sync section
- [ ] `docs/host-adapter-guidance.md` done-flow label refresh step

## Verification

- [ ] RED → GREEN on `tests.test_github_issue_sync`
- [ ] `python3 -m unittest discover -s tests`
- [ ] `python3 scripts/release_check.py .`

## Next

`product:execute 054-github-issue-sync`
