# Goal: Lightweight ModuFlow UX

## Objective

Make ModuFlow feel lightweight and predictable in real projects while preserving Git-native PM artifacts and the central plugin/tooling model.

## Owner

Dongwon Lee

## Linked Issues

- `025-lightweight-project-adoption`
- `026-simplify-command-and-folder-surface`
- `027-reduce-approval-popup-friction`

## Completion Criteria

- Normal project adoption uses light mode by default and does not copy central tooling folders into target projects.
- The current 18 top-level folder surface has a documented grouping or reduction plan.
- User-facing status and docs clearly separate project artifacts from internal ModuFlow tooling.
- Approval prompts are predictable, explained before risky flows, and reduced through batching/local-only paths where possible.
- Doctor/preflight can detect project mode and GitHub account mismatch before write operations.

## Constraints

- Keep Git artifacts as the source of truth.
- Do not bypass Codex approval or sandbox safety rules.
- Do not delete or move existing user artifacts automatically.
- Keep dogfooding support for the ModuFlow repo itself.

## Budget

- Steps: 3 linked issues, starting with 025
- Time:
- Tokens:

## Status

active

## Blocker

None.

## Notes

- Created from user feedback on 2026-06-19 that ModuFlow feels too heavy, has too many visible folders, and triggers too many approval prompts.
- Treat this as a UX cleanup goal after the 0.2.11 goal-loop merge.

## Next Command

`product:execute 026-simplify-command-and-folder-surface`
