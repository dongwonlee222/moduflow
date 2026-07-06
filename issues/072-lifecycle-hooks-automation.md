# Issue: `072-lifecycle-hooks-automation`

**Status: active** — created 2026-07-05, spec 2026-07-06, plan 2026-07-06, started 2026-07-06.
**Priority: p2**

## Outcome

ModuFlow ships a `hooks/` component: a SessionStart hook that injects current project state (`.moduflow/state.json` summary + active issue) into new sessions, and a Stop/PostToolUse hook that runs `project_lifecycle.py --sync` when issue files changed — turning lifecycle propagation from a remember-to-run discipline into an architectural guarantee.

## Why

Benchmark (knowledge/benchmarks/2026-07-05-competitive-gap-benchmark.md): ModuFlow uses zero of the plugin hook surface while superpowers demonstrates the pattern (SessionStart context injection). The cost of not having it is already documented in-house: `048`'s dashboard sat silently stale across five issues because propagation depended on someone remembering to run it. This session repeated the same class twice (065 activation drift; state.json bookkeeping finding in the 054 review).

## Scope

### In

- `hooks/hooks.json` + scripts: SessionStart (startup|clear|compact) emits a compact state banner/context; a post-change hook triggers lifecycle sync when `issues/*.md` mutate.
- Keep hooks fast and fail-open (a hook failure must never block the session).

### Out

- No file-watcher daemon; hooks fire on Claude Code events only.
- No hook-driven auto-commit (061's flow stays agent-driven and gate-checked).

## Acceptance Criteria

- New session in a ModuFlow project surfaces goal/active-issue/next-command without running product:status manually.
- Editing an issue's Status line then stopping propagates state.json/dashboard without a manual sync call.
- Hook failure degrades silently (session unaffected), logged for doctor.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- related: `048-artifact-lifecycle-sync` (the propagation logic hooks will trigger)
- related: `065-installed-plugin-staleness-detection` (doctor could surface hook health)

## Sessions

- 2026-07-05: Registered from the competitive-gap benchmark (priority 4 of 5).

## Workflow Tasks

- [x] spec → `specs/072-lifecycle-hooks-automation/spec.md` (+ `spec.ko.md`; scope expanded 2026-07-06 with 075-deferred session-time linkage warning + doctor log surfacing, both user-approved)
- [x] plan → `specs/072-lifecycle-hooks-automation/plan.md` (+ tasks.md)
- [x] execute → commits `3eacb90` (planning), V1 notes, `1300881` (main wave), D1 dogfood
- [ ] review

## Links

- Benchmark: `knowledge/benchmarks/2026-07-05-competitive-gap-benchmark.md`
- Spec: `specs/072-lifecycle-hooks-automation/spec.md`

## Next Command

`/product:execute 072-lifecycle-hooks-automation`
