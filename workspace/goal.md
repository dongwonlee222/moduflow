# Goal: Team Visibility & Onboarding

## Objective

Make ModuFlow work visible and approachable beyond the local operator: external collaborators can see issue progress from the GitHub UI without reading repo-local Markdown, and a first-time user lands on a small ranked entry path instead of a 20+ command wall.

## Owner

Dongwon Lee

## Why now

The `visual-workbench` goal (closed 2026-07-05) built the local visual surfaces — L1 issue/knowledge graphs, L2 per-issue drill-down, issue DB list view, Korean review packets. What's left unaddressed is the *other-people* dimension: nothing is visible from GitHub's own UI (`054`), and the command surface still assumes an operator who already knows the tool (`055`).

## Issues

- `055-command-surface-onboarding` — first-run guidance: `product:start`/`product:status` name 2-3 concrete next commands; command reference groups core path vs on-demand. (First: small, doc-only.)
- `054-github-issue-sync` — opt-in, one-way projection of `issues/*.md` to GitHub Issues with status labels. Design decisions recorded in the issue file before implementation.

## Completion Criteria

- A brand-new user can go from install → first issue → status without reading the full command index.
- A collaborator with only GitHub access can see which issues exist, their status, and where progress lives.
- `issues/*.md` stays the single canonical source; GitHub Issues remain a projection.

## Constraints

- Git-tracked Markdown stays canonical — GitHub Issues are one-way projections, never a second source of truth.
- Opt-in only: no automatic GitHub writes without explicit enablement (consistent with `github_sync: "optional"`).
- No command renames/removals for onboarding — grouping and guidance only (muscle memory preserved).

## History

- `visual-workbench` — closed 2026-07-05, all three axes shipped (`042`–`047`, `049`; follow-ons `056`/`057`). Its "Later — Write/Execute (interactive workbench)" stage remains deliberately deferred, gated on validating a chat-backed visual surface before committing to a standalone app; revisit as its own goal when demand shows up. Full axis breakdown preserved in git history of this file (commit `96ede08` and earlier).
