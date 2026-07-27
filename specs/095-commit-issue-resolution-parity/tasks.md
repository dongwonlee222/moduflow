# Tasks: 095 Commit-to-Issue Attribution Redesign

Issue: `095-commit-issue-resolution-parity`
Design: `docs/superpowers/specs/2026-07-27-095-attribution-architecture-redesign.md`
Plan: `specs/095-commit-issue-resolution-parity/plan.md`
Failure history: `specs/095-commit-issue-resolution-parity/failure-history.md`

The original shared-resolver and corrective streams are preserved in
`status.md` and Git history. The active work below replaces their global-base
architecture; it does not extend that heuristic.

## Stream A

- [ ] A1 Create `scripts/commit_graph.py` with one log/ref snapshot, cached merge-base and ancestry queries, and explicit ordinary-negative versus command-failure behavior (`FH-010`, `FH-014`, `FH-019`).

## Stream B

- [ ] B1 Derive one ancestry-maximal historical fork point per issue ref; prove trunk advancement, equivalent refs, disconnected refs, slash names, and multiple remotes cannot change unrelated attribution (`FH-006`, `FH-011`, `FH-012`, `FH-013`, `FH-017`).
- [ ] B2 Compute topic deltas from the fork point plus ancestry-maximal stacked-issue exclusions; remove the live global-base path (`FH-002`, `FH-003`, `FH-005`).

## Stream C

- [ ] C1 Separate merge-boundary claims from content-side claims, require graph corroboration for octopus/multi-name content, and apply source precedence once (`FH-004`, `FH-007`, `FH-015`, `FH-016`).

## Stream D

- [ ] D1 Add structured `fatal_errors` and scoped diagnostics, preserve compatibility `errors`, and make bare/indexed resolution project the same attribution result (`FH-001`, `FH-008`, `FH-009`, `FH-010`, `FH-018`).

## Stream E

- [ ] E1 Make linkage build one attribution result scoped to behavior SHAs in the requested release range; unrelated historical ambiguity must remain recorded but not fail the release (`FH-018`).
- [ ] E2 Make converge request one issue-scoped result while preserving existing payload keys and cross-consumer parity (`FH-001`, `FH-018`).

## Stream F

- [ ] F1 Trace every open or redesign-superseded `FH-*` entry to an executable invariant test and append implementation evidence without rewriting failure records (`FH-019`, `FH-020`).
- [ ] F2 Pass focused/full/release/project/lifecycle gates, reproduce the original historical-octopus symptom as out of scope, and complete independent whole-branch review before any PR-readiness claim.
