# Status: 071-spec-code-converge-check

Issue: `071-spec-code-converge-check`
Phase: execute
Branch: `codex/071-spec-code-converge-check`
Backend: host-subagent (recorded in loop-state)
Updated: 2026-07-06

## Done

- Spec (mechanism-benchmark hardened: upstream source reading of spec-kit converge + OpenSpec verify; 3 validated advantages, 6 adjustments, 1 premise correction).
- Plan + tasks; spec_consistency clean (0/0/0). Planning committed `753df8f` with Issue trailer.
- Worker plan generated; backend recorded.

## Done — waves 1-3

- Wave 1 (`8a62d24`): A1 evidence engine (32 tests; real-repo smoke on 075: 8 commits/9 AC/8 GC). B1 judgment template + command doc — coordinator corrected invented CLI flags (--judge/--judge-inline/--judgment-file did not exist; doc now matches the real two-mode CLI). Same flag drift appeared twice across doc workers — pattern noted.
- Wave 2 (`87ea20a`): A2 apply-judgment engine (14 tests: dedup, regression re-append, byte-for-byte no-op, exit contract). B2 review auto-run step. Plugin 0.3.14.
- Wave 3 (D1 dogfood): full pipeline ran on issue 075 — evidence (15-file cap, truncation loud) → independent judge subagent → apply. Result: 1 partial(high), 8 unverifiable, 3 unrequested(low); 4 CV lines appended to 075 tasks.md. **CV-1 was a genuine catch**: two 2026-07-06 decision records lacked `retrieval_trigger` required by 075 GC#8 — fixed and checked off same day. Fixture coverage for missing/unrequested/unverifiable lives in A2 unit tests; unverifiable exercised for real in the dogfood.

## Dogfood lessons (follow-up candidates)

- Bundle file ordering: with tight caps the bundle truncated the implementing scripts/tests first, driving 8/9 ACs to `unverifiable`. Evidence collection should prioritize code/tests over docs when capping. (071 follow-up, not blocking.)
- CV-2..4 (medium unverifiable) remain open on 075 tasks.md as honest bundle-cap artifacts; the behaviors they name are covered by the 393-test suite outside the bundle.

## Review Evidence

- Review: specs/071-spec-code-converge-check/review.md (pass)
- Converge (self): specs/071-spec-code-converge-check/converge.md — 1 high finding caught and resolved via dated plan amendment
- Dashboard: memory/dashboard.html · Drill-down: memory/issue-071-spec-code-converge-check.html

## Verification log

- 2026-07-06: spec_consistency clean after plan authoring; validate clean.
