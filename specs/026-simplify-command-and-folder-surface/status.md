# Status: Simplify Command And Folder Surface

## Issue

`026-simplify-command-and-folder-surface`

## Phase

execute

## Summary

Created the spec and execution plan for simplifying ModuFlow's first user experience. Before implementation, benchmarked GitHub, CLI/developer-tool, and plugin/agent ecosystems to confirm the design rule: ModuFlow tooling should remain central, while target projects keep only PM artifacts, project state, and intentionally selected integration files.

## Completed

- Created `specs/026-simplify-command-and-folder-surface/spec.md`.
- Created `specs/026-simplify-command-and-folder-surface/plan.md`.
- Created `specs/026-simplify-command-and-folder-surface/benchmark.md`.
- Defined the compact command set and 18-folder grouping.
- Defined user-facing copy for `lightweight`, `dogfooding`, and `heavy`.
- Confirmed benchmark evidence from GitHub Actions, GitHub Apps, ESLint, Prettier, Husky, create-next-app, Terraform, VS Code extensions, and agent/plugin ecosystems.

## Verification

- Pending after implementation.

## Blockers

- None.

## Next Command

`/product:execute 026-simplify-command-and-folder-surface`
