# Status: Automatic Memory Candidate Capture

## Issue

`040-automatic-memory-candidate-capture`

## Current Phase

✅ Done

## Done

- Spec defined in `specs/040-automatic-memory-candidate-capture/spec.md`.
- Implemented CLI options `--candidates`, `--approve`, `--reject`, `--capture`, `--source` in `scripts/project_memory.py`.
- Added automatic 14-day candidate stale pruning.
- Integrated auto-capture trigger on `released` status transition in `scripts/project_workflow.py`.
- Created comprehensive unit tests in `tests/test_project_memory.py`.
- Ran 137/137 tests successfully.

## Verification

- Automated tests successfully pass (`python3 -m unittest discover -s tests -v`).
- Checked artifact relations using `python3 scripts/validate_project_artifacts.py .` (Valid).

## Next Command

`product:status`

## Automated Review Checklist

- [x] `product:release` triggers the creation of a memory candidate under `memory/.candidates/` summarizing the issue goals and changes.
  - *Verification*: `create_workflow_record` triggers `create_memory_candidate` when state is `released`. Tested and verified.
- [x] Running `python3 scripts/project_memory.py . --candidates` lists all pending candidate IDs.
  - *Verification*: Evaluated candidate files and verified in tests.
- [x] Running `python3 scripts/project_memory.py . --approve <id>` moves the candidate to the appropriate subdirectory (`decisions/`, `evidence/`, etc.) based on its `kind` frontmatter, validating the structure.
  - *Verification*: Moves file and updates status to approved. Verified in tests.
- [x] Unit tests verify candidate generation, parsing, list outputs, and approval movement.
  - *Verification*: Added 4 comprehensive unit tests in `test_project_memory.py`. All pass.

