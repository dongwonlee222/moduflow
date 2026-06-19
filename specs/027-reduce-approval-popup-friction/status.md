# Status: Reduce Approval Popup Friction

## Issue

`027-reduce-approval-popup-friction`

## Phase

plan

## Summary

Created the spec and plan for reducing approval popup fatigue. The work focuses on distinguishing safe local validation from risky shell/Git/network/account/destructive operations, while preserving existing CLI scripts for compatibility.

## Completed

- Created `specs/027-reduce-approval-popup-friction/spec.md`.
- Created `specs/027-reduce-approval-popup-friction/plan.md`.
- Captured Antigravity feedback around shell-based validation prompts.
- Defined initial approval classes and importable validation engine direction.

## Verification

- Pending implementation.

## Blockers

- Antigravity host API details need verification before host-specific adapter implementation.

## Next Command

`/product:execute 027-reduce-approval-popup-friction`
