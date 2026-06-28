# Issue: `048-artifact-lifecycle-sync`

**Status: done** — created 2026-06-28, started 2026-06-28, done 2026-06-28. Cross-cutting (supports goal `visual-workbench` but applies to the whole artifact model).

## Outcome

Lifecycle drift is now **detected and propagated** from a single canonical source instead of hand-synced across files:

- **Canonical declared**: the issue file `**Status:**` line. Derived views flow *out* of it; never back.
- **`scripts/project_lifecycle.py`** (new): `lifecycle_state` (canonical map from `issues/*.md`), `lifecycle_drift` (consensus check across issue files ↔ `.moduflow/state.json` ↔ `dashboard.md`), `sync_lifecycle` (single writer: regenerates state.json lifecycle fields + the dashboard's Active Issue section, idempotent, preserves prose). CLI: `--state` / `--drift` / `--sync`.
- **loop-state.json retired from the gate**: `validate_active_state_views` + `validate_schema_gates` now key off `.moduflow/state.json` (live summary), not the dormant `loop-state.json` (frozen at issue 040, a prior goal). The loop-state `next_command`/phase coupling is no longer a lifecycle gate. roadmap.md's active-issue check dropped (it's a narrative roadmap).
- **Drift promoted to a hard gate** (after reconciling): `validate_project_artifacts` fails on genuine disagreement; `project_doctor` reports it. Sequencing followed advisor's mandate (reporter → reconcile → gate) so 048's own commit didn't break.
- **Dogfood**: running `--sync` reconciled this repo's divergence (state.json/dashboard had drifted from the issue files) — the exact failure that recurred all session.

Tests: 155 pass (5 new lifecycle tests: state parsing, drift in-sync/divergent, sync idempotence + prose preservation, phase inference; retired the loop-state next_command test). `release_check` exit 0.

**Out of scope (separate issue):** unifying the `state.v1` / `loop-state.v2` schemas and migrating the 15+ consumers; full dashboard regeneration (prose stays hand-authored).

## Goal

When an issue's lifecycle changes (start / done / pause / supersede), **automatically propagate** that change to the derived views — `workspace/dashboard.md` and the `.moduflow/state.json` summary — so they never silently drift from the canonical issue files. (`roadmap.md` is a narrative roadmap, not a per-issue tracker; it stays hand-authored.)

## Why (concrete evidence)

`workspace/dashboard.md` sat frozen at issue `040` while issues 042/044/045/046/047 were processed — five issues of drift — because lifecycle updates are **manual and AI-remembered**, not enforced. A human asking "does done-processing update the dashboard?" found the honest answer was "no, and it's already stale." Derived views that drift are worse than no views: they mislead.

## Root cause

- The `index` skill *documents* a rule ("on mutating lifecycle actions, update dashboard.md/issues.md/roadmap.md"), but it is guidance an agent must remember, not a guaranteed step.
- Editing issue files directly (instead of via `product:issue`) bypasses even that guidance.
- There is no validation that flags drift between issue statuses and the dashboard.

## Scope (decide in spec)

- A propagation step (script or command hook) that regenerates the derived workspace views from the canonical issue files + state on any lifecycle change.
- A **doctor/validation check** that flags drift (issue says done, dashboard doesn't) — detection even if propagation is skipped.
- Decide: regenerate views from issues (treat dashboard.md as derived, like dashboard.html) vs. enforce-on-write.

## Out of Scope

- The visual graph/panel views themselves (042/045/047).
- Interactive authoring backend (021/028).

## Open question

- Should `workspace/dashboard.md` become a **generated** artifact (canonical = issue files, dashboard.md = derived, possibly `.gitignore`d like dashboard.html), or stay hand-maintained with a drift check? Generated is more robust; decide in spec.

## Related

- Goal `visual-workbench` (motivating context)
- `024-artifact-schema-and-doctor-gates`, `git-native-artifact-model` (where the drift check would live)
- `progress-dashboard` skill, `index` skill (the rule that wasn't enforced)
