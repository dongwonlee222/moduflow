# Status: 072-lifecycle-hooks-automation

Issue: `072-lifecycle-hooks-automation`
Phase: execute
Branch: `codex/072-lifecycle-hooks-automation`
Backend: host-subagent
Updated: 2026-07-06

## Done

- Spec (scope expanded with 075-deferred session-time linkage warning + doctor log surfacing, user-approved) + plan/tasks; spec_consistency 0/0/0. Planning committed `3eacb90`.
- **V1 schema verification** (claude-code-guide, official docs cited): `hook-schema-notes.md` — key findings: SessionStart injects via `hookSpecificOutput.additionalContext` JSON; **Stop exit 2 and `decision:"block"` are blocking and forbidden**; fail-open = always exit 0 + log (non-2 nonzero still surfaces stderr to user); hook CWD = project dir; matcher set gains `resume`. Committed.
- **B2 (inline)**: `hooks/` added to linkage_check BEHAVIOR_PREFIXES + test — the new surface is gated from its first commit. 30 linkage tests OK.

## In Progress — main wave (parallel, disjoint files)

- A1 `hooks/hooks.json` + `hooks/session_start.py` (banner) — standard tier
- A2 `hooks/on_stop.py` (sync marker + linkage warning + fingerprint dedup) — standard tier
- B1 doctor hooks.log tail warnings — light tier

## Queued

- D1: direct-invocation dogfood + self-application check (branch silent / scratch edit warns once) + product-doctor/product-status doc updates; review handoff; review (converge auto-run); Draft PR.

## Coordination

- Parallel session's `f56999d` (028 fix) sits on local main unpushed — user owns the main push. This branch stacks on it.
- `validate_project_artifacts.py` untouched per GC9.

## Verification log

- 2026-07-06: V1 notes reviewed by coordinator before A dispatch (gate honored); B2 inline verified (unittest OK).
