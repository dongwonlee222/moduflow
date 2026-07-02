# Issue: `055-command-surface-onboarding`

**Status: backlog** — created 2026-07-03.

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

## Sessions

- 2026-07-03: User asked what to improve next; noted the command surface is still wide for new users despite 026/044. Registered as backlog issue only, per user's choice — implementation deferred.

## Links

- Roadmap: `workspace/roadmap.md`

## Next Command

`/product:status`
