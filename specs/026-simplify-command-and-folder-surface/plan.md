# Plan: Simplify Command And Folder Surface

Goal: Make ModuFlow feel smaller and more predictable by reducing the first visible command/folder model, without removing advanced internals.

Architecture: Documentation and command output copy first, then focused status/doctor helpers if needed. Keep raw machine-readable labels stable.

Tech Stack: Markdown artifacts, Python command helpers, JSON state, existing validation scripts.

## Task 1: RED Checks For User-Facing Copy

- [ ] Add focused tests or fixtures that assert raw mode labels are preserved in JSON output.
- [ ] Add focused tests or fixtures that assert user-facing doctor/status copy includes plain guidance for each project mode.
- [ ] Add a docs check or snapshot fixture for the compact command surface if an existing validator supports it.

## Task 2: Documentation Surface

- [ ] Update README or primary usage docs to lead with `status`, `next`, `issue`, `done`, and `/moduflow`.
- [ ] Add a folder reference that groups the 18 source-repo folders by job.
- [ ] Add target-project guidance that says normal projects keep PM artifacts and state, not central tooling folders.

## Task 3: Status And Doctor Copy

- [ ] Add a small mode-to-guidance mapping near the doctor/status presentation boundary.
- [ ] Keep raw `mode` values in JSON output for automation.
- [ ] Update `/product:status`, `/product:doctor`, or their docs/templates so the user sees guidance before raw labels.

## Task 4: Verification

- [ ] Run focused tests for mode guidance and docs fixtures.
- [ ] Run `python3 scripts/validate_project_artifacts.py .`.
- [ ] Run `python3 scripts/validate_moduflow.py .`.
- [ ] Run the relevant release/check gate before review.

## Next Command

`/product:execute 026-simplify-command-and-folder-surface`
