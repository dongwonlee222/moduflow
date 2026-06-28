# Issue: `048-artifact-lifecycle-sync`

**Status: backlog** — created 2026-06-28. Cross-cutting (supports goal `visual-workbench` but applies to the whole artifact model).

## Goal

When an issue's lifecycle changes (start / done / pause / supersede), **automatically propagate** that change to the derived views — `workspace/dashboard.md`, `workspace/issues.md`, `workspace/roadmap.md`, and the `.moduflow/state.json` summary — so they never silently drift from the canonical issue files.

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
