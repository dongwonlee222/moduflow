# Review: Project Operation Capability Enforcement

**Verdict: ready** — all fourteen acceptance criteria have implementation, independent review, full regression, and fresh source release evidence; no Critical or Important finding remains.

## Scope Reviewed

- Resolver policy projection and authorization invariants.
- Every registered target-project, portfolio-control, package-maintenance, and standalone external-control mutation surface.
- Guard-before-side-effect ordering, declared operation matching, helper ownership, and nested call surfaces.
- Git/GitHub publication ordering and downstream repository, review, release, CI/status, and human gates.
- Default positional-root compatibility and diagnostic reads for denied mutation policies.

## Findings

1. **Resolved — mutable capability projection could fail open.** Authorization now recomputes the expected policy from observed inputs and validates the complete normalized projection before allowing an operation.
2. **Resolved — public team-state writer bypassed its parent guard.** `write_team_state()` now resolves context and enforces `execute` before directory or file creation.
3. **Resolved — static audit proved only guard presence.** It now verifies operation literals, guard dominance, direct/nested helper ownership, and broader filesystem/network surfaces.
4. **Resolved — external-control was initially too broad.** It is publish-only and network-only; mixed file/Git mutation fails the audit.
5. **Resolved — open flags/modes could hide behind assignments.** Reaching assignments are evaluated at call position; multiple, augmented, unresolved, and nested-scope cases fail closed as dynamic mutation.
6. **Resolved — explicit-root compatibility used raw trust alone.** It now requires `explicit_root` provenance and exact `active/project-local` synthetic inputs.
7. **Resolved — Antigravity canonical control path and nested rewrite helper were not fully classified.** Both are explicitly reviewed, and helper calls are dominated by the outer execute guard.
8. **No open Critical or Important finding** remains after independent re-review of `60f7651`.

## Acceptance-Criteria Review

1. **Pass:** every resolved route exposes normalized project status, policy trust, observed inputs, all four capabilities, and deterministic reasons.
2. **Pass:** unresolved and ambiguous contexts expose the complete all-denied shape without candidate project-local reads.
3. **Pass:** active/internal contexts allow read/write/execute and only mark publish policy-eligible.
4. **Pass:** archived contexts allow diagnostic read and deny write/execute/publish.
5. **Pass:** read-only contexts allow diagnostic read and deny write/execute/publish.
6. **Pass:** missing or unsupported status/trust preserves observed values, allows diagnostics, and denies mutation.
7. **Pass:** unknown operations deny with `PROJECT_OPERATION_UNKNOWN`.
8. **Pass:** every discovered target mutation has a declared operation and a dominating central guard before its side effect.
9. **Pass:** denial tests prove zero file/temp/Git/subprocess/network/external calls at guarded boundaries.
10. **Pass:** the repository audit reports 64 classified findings and zero unclassified, unguarded, stale, duplicate, or configuration errors.
11. **Pass:** portfolio-control authorization is root-bound and cannot authorize a selected target mutation.
12. **Pass:** publish policy eligibility cannot bypass repository identity, review, release, status-check, or human approval gates.
13. **Pass:** positional explicit-root callers remain compatible, while registry `project-local` is not mistaken for legacy provenance.
14. **Pass:** project validation is valid, spec consistency is clean, lifecycle drift is `[]`, full discovery passed 1,339/1,339, diff hygiene is clean, and the post-evidence source release check is valid with empty errors.

## Constitution

Constitution: v1.0 checked — no violations.

## Next

Open a non-draft PR. Merge remains subject to explicit human approval.
