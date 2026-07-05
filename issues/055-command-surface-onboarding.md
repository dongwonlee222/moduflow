# Issue: `055-command-surface-onboarding`

**Status: done** — created 2026-07-03, started 2026-07-05, done 2026-07-05.

## Outcome

A first-time user lands on a small, clear entry point (`product:start` -> `product:status` -> dashboard) instead of facing 20+ `product-*` commands with no ranking of which ones matter early versus later.

## Why

`product-*` commands now number more than 20 (inbox, opportunity, issue, spec, plan, workers, execute, review, pr, release, roadmap, dashboard, sync, doctor, ...). Issue 026 already simplified the command/folder surface once, and 044/045 added dashboard-based visualization that helps. But nothing currently ranks or stages the commands for a brand-new install — a new user still has to guess what to run first beyond `product:start`.

## Scope

### In

- Audit the current command list and classify each as "core path" (start, status, loop) vs. "on-demand" (analysis, design, business-plan, etc.).
- Strengthen the first-run guidance in `product:start`/`product:status` output so it names 2-3 concrete next commands instead of listing the full surface.
- Cross-check whether `044-product-dashboard-command`'s dashboard already covers this and only documentation/ordering needs to change, versus needing new command grouping.

### Out

- No deleting or renaming existing commands (breaks muscle memory and any existing automation).
- No forced interactive tutorial/wizard.

## Acceptance Criteria

- `product:start` and `product:status` output a short, ranked "what to run next" list (not the full command index).
- Command reference docs (README or equivalent) group commands by core-path vs. on-demand.
- `python3 scripts/release_check.py .` passes.

## Related Issues

- related: `026-simplify-command-and-folder-surface`
- related: `044-product-dashboard-command`

## Workflow Tasks

- [x] execute → `commands/product-start.md`, `commands/product-status.md`, `README.md`

## Sessions

- 2026-07-03: User asked what to improve next; noted the command surface is still wide for new users despite 026/044. Registered as backlog issue only, per user's choice — implementation deferred.
- 2026-07-05: Executed as first issue of goal `team-visibility-onboarding`. Scope cross-check confirmed doc-only suffices (044's dashboard covers visualization; no new command grouping code needed). `product:start` gained a First-Run Guidance section (3-command core path: goal → issue → status, full index banned at start); `product:status` gained a Next-Command Guidance section (ranked ≤3 next commands from loop state, `product:loop` as the escape hatch); README's flat 37-command list regrouped into Core path (6) / Build cycle (6) / On-demand (categorized). No command renamed or removed. release_check passes.

## Links

- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:status`
