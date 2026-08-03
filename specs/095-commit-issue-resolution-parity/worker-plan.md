# Worker Plan: 095-commit-issue-resolution-parity

Mode: `sequential`
Parallel eligible: `false`

## Tasks

| ID | Worker | Group | Status | Files | Depends | Task |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | `implementation-worker` | `sequential` | ready | scripts/commit_graph.py, scripts/commit_resolution.py, tests/test_commit_graph.py | - | A1 Create `scripts/commit_graph.py` with one log/ref snapshot, cached merge-base and ancestry queries, and explicit ordinary-negative versus command-failure behavior (`FH-010`, `FH-014`, `FH-019`). |
| T02 | `implementation-worker` | `sequential` | ready | scripts/commit_graph.py, tests/test_commit_graph.py, tests/git_repo_builder.py, tests/commit_resolution_shapes.py | T01 | B1 Derive one ancestry-maximal historical fork point per issue ref; prove trunk advancement, equivalent refs, disconnected refs, slash names, and multiple remotes cannot change unrelated attribution (`FH-006`, `FH-011`, `FH-012`, `FH-013`, `FH-017`). |
| T03 | `implementation-worker` | `sequential` | ready | scripts/commit_graph.py, scripts/commit_resolution.py, tests/test_commit_graph.py, tests/commit_resolution_shapes.py, tests/test_commit_resolution_differential.py | T02 | B2 Compute topic deltas from the fork point plus ancestry-maximal stacked-issue exclusions; remove the live global-base path (`FH-002`, `FH-003`, `FH-005`). |
| T04 | `implementation-worker` | `sequential` | ready | scripts/commit_resolution.py, tests/commit_resolution_shapes.py, tests/test_commit_resolution.py, tests/test_commit_resolution_differential.py | T03 | C1 Separate merge-boundary claims from content-side claims, require graph corroboration for octopus/multi-name content, and apply source precedence once (`FH-004`, `FH-007`, `FH-015`, `FH-016`). |
| T05 | `pm-strategist` | `sequential` | ready | scripts/commit_resolution.py, tests/test_commit_resolution.py, tests/test_commit_resolution_differential.py, tests/test_commit_resolution_parity.py | T04 | D1 Add structured `fatal_errors` and scoped diagnostics, preserve compatibility `errors`, and make bare/indexed resolution project the same attribution result (`FH-001`, `FH-008`, `FH-009`, `FH-010`, `FH-018`). |
| T06 | `pm-strategist` | `sequential` | ready | scripts/linkage_check.py, tests/test_linkage_check.py, tests/test_commit_resolution_parity.py | T05 | E1 Make linkage build one attribution result scoped to behavior SHAs in the requested release range; unrelated historical ambiguity must remain recorded but not fail the release (`FH-018`). |
| T07 | `pm-strategist` | `sequential` | ready | scripts/project_converge.py, tests/test_project_converge.py, tests/test_commit_resolution_parity.py | T06 | E2 Make converge request one issue-scoped result while preserving existing payload keys and cross-consumer parity (`FH-001`, `FH-018`). |
| T08 | `qa-reviewer` | `sequential` | ready | tests/test_commit_graph.py, tests/test_commit_resolution.py, tests/test_commit_resolution_differential.py, tests/test_commit_resolution_parity.py, tests/test_linkage_check.py, tests/test_project_converge.py, specs/095-commit-issue-resolution-parity/failure-history.md | T07 | F1 Trace every open or redesign-superseded `FH-*` entry to an executable invariant test and append implementation evidence without rewriting failure records (`FH-019`, `FH-020`). |
| T09 | `pm-strategist` | `sequential` | ready | specs/095-commit-issue-resolution-parity/status.md, issues/095-commit-issue-resolution-parity.md, .moduflow/state.json, workspace/loop-state.json, workspace/dashboard.md | T08 | F2 Pass focused/full/release/project/lifecycle gates, reproduce the original historical-octopus symptom as out of scope, and complete independent whole-branch review before any PR-readiness claim. |

## Isolation

- T01: `codex/095-commit-issue-resolution-parity-t01`
- T02: `codex/095-commit-issue-resolution-parity-t02`
- T03: `codex/095-commit-issue-resolution-parity-t03`
- T04: `codex/095-commit-issue-resolution-parity-t04`
- T05: `codex/095-commit-issue-resolution-parity-t05`
- T06: `codex/095-commit-issue-resolution-parity-t06`
- T07: `codex/095-commit-issue-resolution-parity-t07`
- T08: `codex/095-commit-issue-resolution-parity-t08`
- T09: `codex/095-commit-issue-resolution-parity-t09`

## Merge Order

- T01 → T02 → T03 → T04 → T05 → T06 → T07 → T08 → T09

## Worker Inventory

- All worker files are covered by routing rules.

## Risks

- Task 1 touches shared state: A1 Create `scripts/commit_graph.py` with one log/ref snapshot, cached merge-base and ancestry queries, and explicit ordinary-negative versus command-failure behavior (`FH-010`, `FH-014`, `FH-019`).
- Task 2 touches shared state: B1 Derive one ancestry-maximal historical fork point per issue ref; prove trunk advancement, equivalent refs, disconnected refs, slash names, and multiple remotes cannot change unrelated attribution (`FH-006`, `FH-011`, `FH-012`, `FH-013`, `FH-017`).
- Task 3 touches shared state: B2 Compute topic deltas from the fork point plus ancestry-maximal stacked-issue exclusions; remove the live global-base path (`FH-002`, `FH-003`, `FH-005`).
- Task 4 touches shared state: C1 Separate merge-boundary claims from content-side claims, require graph corroboration for octopus/multi-name content, and apply source precedence once (`FH-004`, `FH-007`, `FH-015`, `FH-016`).
- Task 5 touches shared state: D1 Add structured `fatal_errors` and scoped diagnostics, preserve compatibility `errors`, and make bare/indexed resolution project the same attribution result (`FH-001`, `FH-008`, `FH-009`, `FH-010`, `FH-018`).
- Task 6 touches shared state: E1 Make linkage build one attribution result scoped to behavior SHAs in the requested release range; unrelated historical ambiguity must remain recorded but not fail the release (`FH-018`).
- Task 7 touches shared state: E2 Make converge request one issue-scoped result while preserving existing payload keys and cross-consumer parity (`FH-001`, `FH-018`).
- Task 8 touches shared state: F1 Trace every open or redesign-superseded `FH-*` entry to an executable invariant test and append implementation evidence without rewriting failure records (`FH-019`, `FH-020`).
- Task 9 touches shared state: F2 Pass focused/full/release/project/lifecycle gates, reproduce the original historical-octopus symptom as out of scope, and complete independent whole-branch review before any PR-readiness claim.
- scripts/commit_graph.py is expected by T01 and T02
- tests/test_commit_graph.py is expected by T01 and T02
- scripts/commit_graph.py is expected by T01 and T03
- scripts/commit_resolution.py is expected by T01 and T03
- tests/test_commit_graph.py is expected by T01 and T03
- tests/commit_resolution_shapes.py is expected by T02 and T03
- scripts/commit_resolution.py is expected by T01 and T04
- tests/commit_resolution_shapes.py is expected by T02 and T04
- tests/test_commit_resolution_differential.py is expected by T03 and T04
- scripts/commit_resolution.py is expected by T01 and T05
- tests/test_commit_resolution.py is expected by T04 and T05
- tests/test_commit_resolution_differential.py is expected by T03 and T05
- tests/test_commit_resolution_parity.py is expected by T05 and T06
- tests/test_commit_resolution_parity.py is expected by T05 and T07
- tests/test_commit_graph.py is expected by T01 and T08
- tests/test_commit_resolution.py is expected by T04 and T08
- tests/test_commit_resolution_differential.py is expected by T03 and T08
- tests/test_commit_resolution_parity.py is expected by T05 and T08
- tests/test_linkage_check.py is expected by T06 and T08
- tests/test_project_converge.py is expected by T07 and T08

## Next Command

`product:execute 095-commit-issue-resolution-parity`
