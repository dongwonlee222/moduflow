# Issue: `061-auto-commit-push-on-issue-done`

**Status: done** — created 2026-07-05, started 2026-07-05, done 2026-07-05.

## Outcome

When an agent (Antigravity, Claude Code, or Codex) marks a ModuFlow issue `Status: done` and `release_check.py` passes, it commits and pushes immediately without asking for separate commit/push confirmation each time — instead of leaving work local until the user separately requests a push.

## Why

The user works across multiple machines/sessions. In a prior session, work was completed on one machine but left uncommitted/unpushed; a later session on a different machine had no way to see it, and the user had to notice and ask for a push after the fact. Asking "커밋할까요?" then "푸시할까요?" separately after every completed issue (as this session did for 059/060) is exactly the friction that causes this — each confirmation is a chance for a session to end before the push happens.

The repo's pre-push hook already runs `release_check.py` (tests + validation + drift) and blocks a broken push, so auto-push has a real safety net — this isn't push-without-verification.

## Scope

### In

- Update `docs/host-adapter-guidance.md`'s "When Full Preflight Is Expected" section: completing an issue (`Status: done`, `release_check.py` passing) is itself a trigger for commit + push, not something that waits for a separate user request.
- Applies to all three tools reading this repo's guidance (Antigravity, Claude Code, Codex) — same standing authorization for all.

### Out

- Does not change anything about mid-work commits (partial progress, spec/plan-only states) — those remain ask-first, since they're not yet verified by `release_check.py`.
- Does not remove the pre-push `release_check` hook or weaken it — auto-push relies on that gate staying in place.
- Does not apply to force-push, branch deletion, or any other destructive Git operation — those remain explicit-confirmation-only per the host's general safety protocol.

## Acceptance Criteria

- `docs/host-adapter-guidance.md` states the auto-commit-push-on-done policy explicitly, including the `release_check.py` dependency.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- related: `050-repo-sync-preflight`
- related: `059-auto-fetch-in-repo-sync`
- caused-by: user feedback, 2026-07-05 — work completed in one session wasn't visible from another machine until manually pushed later.

## Workflow Tasks

- [x] execute → `docs/host-adapter-guidance.md`

## Sessions

- 2026-07-05: User asked why completed work isn't automatically pushed, citing a prior cross-machine incident. Confirmed via AskUserQuestion: auto commit+push on `done` without per-instance confirmation, relying on the existing pre-push `release_check` hook as the safety net.

## Links

- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:status`
