# Spec: Antigravity Artifact Sync Connector

Issue: 029-antigravity-artifact-sync-connector

## Problem

Antigravity maintains native planning artifacts such as `task.md` and `implementation_plan.md` in the brain directory, while ModuFlow stores durable Git-native artifacts under `issues/` and `specs/`. Having to manually duplicate status and checklist progress between both surfaces causes double-entry friction and increases the risk of documentation drift.

## Users

Dongwon Lee and the AI coding agent (Antigravity).

## Goals

- Define a clear field mapping between Antigravity's host-native planning artifacts and ModuFlow's Git-native files.
- Automatically detect and report sync/drift status between both platforms.
- Enable bidirectional sync of progress checklists (e.g. task checkboxes) and status descriptions.
- Ensure host-local or sensitive information (like conversation IDs) is excluded from the public Git repository.

## Non-Goals

- Deprecating or replacing ModuFlow's Git-native PM artifact model.
- Performing automatic bidirectional merges without conflict handling.

## Requirements

- A connector component that maps:
  - `implementation_plan.md` <--> `specs/<issue>/spec.md` and `plan.md`
  - `task.md` <--> `specs/<issue>/tasks.md`
  - `walkthrough.md` <--> `specs/<issue>/status.md` (post-execution status summary)
- Drift detection tool to compare the files and report diffs.
- Explicit `import` and `export` commands/scripts to sync files safely.

## Acceptance Criteria

- A synchronization specification defining the mapping.
- Connector tool detects drift and identifies which side has changed.
- Explicit import/export sync operations that require validation.
- Local host metadata is excluded from Git commits.

## Risks

- Divergent edits on both sides causing merge conflicts.
- Host-local path exposure in Git.

## Open Questions

- Should we implement automatic sync prompts, or run sync explicitly as a command (e.g. `product:sync`)?

## Next Command

`/product:plan 029-antigravity-artifact-sync-connector`
