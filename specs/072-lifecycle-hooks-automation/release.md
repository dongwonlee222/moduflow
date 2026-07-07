# Release: 072-lifecycle-hooks-automation

Issue: `072-lifecycle-hooks-automation`
Version: 0.3.16 (from 0.3.15)
Merged: PR https://github.com/dongwonlee222/moduflow/pull/10 → `main` (`4f68c57`), 2026-07-07
Approval: explicit human approval in session ("승인 합니다", 2026-07-07) after packet/dashboard/converge review.

## Shipped

- `hooks/` plugin component (first use of the hook surface): SessionStart context banner + Stop hook (batched lifecycle sync via marker + session-time linkage warning with fingerprint dedup — 075's deferred detection, warn-only).
- Fail-open discipline: always exit 0, 5s self-budget, diagnostics only to `.moduflow/logs/hooks.log` (gitignored); Stop blocking channels (exit 2, `decision:"block"`) verified absent.
- `product:doctor` hook-health warnings from hooks.log (7d/20 cap); `hooks/` registered as linkage-gate behavior path from first commit.
- `hook-schema-notes.md` — doc-verified hook contract (V1) for future hook work.

## Verification at release

- 439 tests OK (44 new). release_check valid. Converge self-audit: 5/8 converged, 0 GC violations.
- Self-application live: linked branch silent + sync fired; unlinked fixture warned once, deduped.

## Rollback

Revert merge commit `4f68c57`; hooks are additive files + one linkage prefix line + doctor additions; removing `hooks/` restores pre-072 behavior.

## Post-release checks

- Next session in this project should open with the state banner — first real-world SessionStart firing (verify visually).
- Watch hooks.log for unexpected entries during the first days; doctor now surfaces them.
- Follow-ups: Codex-host hook parity; richer doctor hook-health (065); converge bundle file-ordering (071 review finding 3).
