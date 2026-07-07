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

## Done — main wave + D1

- Main wave (`1300881`): A1 banner hook (7 tests, live: 5-line banner in 0.32s), A2 stop hook (20 tests incl. first real-git-fixture e2e in the repo), B1 doctor hooks.log surfacing (17 tests), B2 hooks/ behavior-path gating. Plugin 0.3.16. 439 tests OK, release_check valid.
- Coordination incident: B2's uncommitted edits were reverted mid-wave by an unidentified parallel actor (workers deny touching scripts/); coordinator re-applied post-wave and verified. Lesson: pre-commit inline edits before dispatching workers, or commit them immediately.
- D1 dogfood: **self-application gate fully passed** — live on_stop on this branch: silent + sync fired + marker written + exit 0; temp-fixture unlinked edit: exactly one warning, second run deduped silent, exit 0. session_start live banner correct. `.moduflow/state/` + `logs/` gitignored (machine-local). product-doctor/product-status docs updated.

## Coordination

- Parallel session's `f56999d` (028 fix) sits on local main unpushed — user owns the main push. This branch stacks on it.
- `validate_project_artifacts.py` untouched per GC9.

## Verification log

- 2026-07-06: V1 notes reviewed by coordinator before A dispatch (gate honored); B2 inline verified (unittest OK).
