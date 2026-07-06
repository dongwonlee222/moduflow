# Release: 075-issue-less-context-capture

Issue: `075-issue-less-context-capture`
Version: 0.3.13 (from 0.3.11; 0.3.12 was an intermediate wave bump within this issue)
Merged: PR https://github.com/dongwonlee222/moduflow/pull/8 → `main` (`a4ae79f`), 2026-07-06
Approval: human merge approval in session, 2026-07-06 (dashboard + drill-down + Korean packet reviewed; PR evidence comment mirrored)

## Shipped

- `scripts/linkage_check.py` — commit↔issue linkage (branch `codex/<issue-id>-*` + trailer `Issue: <id>`), path classification (`commands/*.md` = behavior), declaration blame validation. Importable for 072 hooks.
- `scripts/release_check.py` — linkage gate on merge-base diff; silent `except: pass` holes removed; git failures error loudly; CI fetch-depth 0.
- `scripts/project_promote.py` + `commands/product-promote.md` — record→issue promotion with automatic bidirectional links.
- `.moduflow/humans.json` + `releases/no-issue-declarations.md` — human-identity-gated no-issue declarations, listed in `human-review.ko.md` packets.
- `templates/issues/issue.md` — Verification / Entry Points / Scope Fence sections.
- Record Contract + ADD/UPDATE/SUPERSEDE/NOOP discipline in the four capture commands.
- `scripts/project_retention.py` — release-count retention (archive after 2 unpromoted releases), status surfacing.

## Verification at release

- Full suite 346 tests OK; release_check `valid: true`; self-application gate passed on the issue branch.
- No no-issue declarations in this release (declarations file empty of entries).

## Rollback

Revert merge commit `a4ae79f` — restores prior gate behavior; all new files are additive; template sections are backward-compatible.

## Post-release checks

- Next release on any branch must pass the linkage gate (first external application).
- Retention surfaced 8 archive candidates (pre-075 records) — ops decision pending, not auto-archived.
- Follow-up scoped: in-session threshold detection → issue 072; shared-git-identity blame limitation documented.
