# Worker Plan: 072-lifecycle-hooks-automation

Mode: `sequential`
Parallel eligible: `false`

## Tasks

| ID | Worker | Group | Status | Files | Depends | Task |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | `qa-reviewer` | `sequential` | ready | - | - | V1. Hook schema verification: official Claude Code plugin-hooks docs + superpowers shipped hooks → `specs/072-lifecycle-hooks-automation/hook-schema-notes.md` (hooks.json shape, SessionStart matchers, Stop payload, context-injection channel, timeout semantics, plugin-cache CWD behavior; doc URLs cited) — depends: none. **No hook code before this lands.** |
| T02 | `qa-reviewer` | `sequential` | ready | - | - | A1. `hooks/hooks.json` + `hooks/session_start.py` (≤10-line Korean-first banner from state.json/loop-state; corrupt/missing → silent + hooks.log; exit 0 always) + tests — depends: V1 |
| T03 | `qa-reviewer` | `group-1` | ready | - | - | A2. `hooks/on_stop.py` (sync-marker change detection → `project_lifecycle.py --sync`; linkage quick-check → one deduped warning line via fingerprint; 5s budget bail; exit 0 always) + tests — depends: V1 |
| T04 | `qa-reviewer` | `group-1` | ready | - | - | B1. Doctor surfaces `.moduflow/logs/hooks.log` tail as warnings (absent/empty → silence) + tests — depends: V1 (log format from Interfaces) |
| T05 | `qa-reviewer` | `group-1` | ready | - | - | B2. Add `hooks/` to `linkage_check.classify_changed_paths` behavior prefixes + test (data-list change only) — depends: none |
| T06 | `implementation-worker` | `sequential` | ready | - | - | D1. Direct-invocation dogfood (Status mutation → on_stop → state propagated; session_start banner matches live state; deliberate unlinked scratch edit → exactly one warning) + `product-doctor.md`/`product-status.md` doc updates — depends: A1, A2, B1 |

## Isolation

- T01: `codex/072-lifecycle-hooks-automation-t01`
- T02: `codex/072-lifecycle-hooks-automation-t02`
- T03: `codex/072-lifecycle-hooks-automation-t03`
- T04: `codex/072-lifecycle-hooks-automation-t04`
- T05: `codex/072-lifecycle-hooks-automation-t05`
- T06: `codex/072-lifecycle-hooks-automation-t06`

## Merge Order

- T01 → T02 → T03 → T04 → T05 → T06

## Worker Inventory

- All worker files are covered by routing rules.

## Risks

- Task 1 touches shared state: V1. Hook schema verification: official Claude Code plugin-hooks docs + superpowers shipped hooks → `specs/072-lifecycle-hooks-automation/hook-schema-notes.md` (hooks.json shape, SessionStart matchers, Stop payload, context-injection channel, timeout semantics, plugin-cache CWD behavior; doc URLs cited) — depends: none. **No hook code before this lands.**
- Task 2 touches shared state: A1. `hooks/hooks.json` + `hooks/session_start.py` (≤10-line Korean-first banner from state.json/loop-state; corrupt/missing → silent + hooks.log; exit 0 always) + tests — depends: V1
- Task 6 touches shared state: D1. Direct-invocation dogfood (Status mutation → on_stop → state propagated; session_start banner matches live state; deliberate unlinked scratch edit → exactly one warning) + `product-doctor.md`/`product-status.md` doc updates — depends: A1, A2, B1

## Next Command

`product:execute 072-lifecycle-hooks-automation`
