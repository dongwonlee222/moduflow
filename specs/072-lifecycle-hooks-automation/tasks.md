# Tasks: 072-lifecycle-hooks-automation

Plan: `specs/072-lifecycle-hooks-automation/plan.md`
Status: ready-for-execute · Order: V1 → (A1 ∥ A2 ∥ B1 ∥ B2) → D1

## Stream V — verification first

- [ ] V1. Hook schema verification: official Claude Code plugin-hooks docs + superpowers shipped hooks → `specs/072-lifecycle-hooks-automation/hook-schema-notes.md` (hooks.json shape, SessionStart matchers, Stop payload, context-injection channel, timeout semantics, plugin-cache CWD behavior; doc URLs cited) — depends: none. **No hook code before this lands.**

## Stream A — hook implementation

- [ ] A1. `hooks/hooks.json` + `hooks/session_start.py` (≤10-line Korean-first banner from state.json/loop-state; corrupt/missing → silent + hooks.log; exit 0 always) + tests — depends: V1
- [ ] A2. `hooks/on_stop.py` (sync-marker change detection → `project_lifecycle.py --sync`; linkage quick-check → one deduped warning line via fingerprint; 5s budget bail; exit 0 always) + tests — depends: V1

## Stream B — doctor + gate coverage

- [ ] B1. Doctor surfaces `.moduflow/logs/hooks.log` tail as warnings (absent/empty → silence) + tests — depends: V1 (log format from Interfaces)
- [ ] B2. Add `hooks/` to `linkage_check.classify_changed_paths` behavior prefixes + test (data-list change only) — depends: none

## Stream D — dogfood + docs

- [ ] D1. Direct-invocation dogfood (Status mutation → on_stop → state propagated; session_start banner matches live state; deliberate unlinked scratch edit → exactly one warning) + `product-doctor.md`/`product-status.md` doc updates — depends: A1, A2, B1

## Verification per task

- V1: doc-cited notes reviewed by coordinator before A dispatch.
- A1/A2/B1/B2: focused unittest; every hook path asserts exit 0; fail-open paths tested with corrupt inputs.
- D1: the dogfood run is the verification; self-application check (this branch stays silent, scratch edit warns once).

## Gates recap

test → self-application (silent-on-linked / warn-once-on-unlinked) → review (converge auto-run) → release (version bump in completion commit; linkage gate now covers `hooks/`). Rollback: revert merge; additive files + one data line.

## Coordination note

Parallel session (028 chip) owns `scripts/validate_project_artifacts.py` — do not touch; targeted `git add` only.
