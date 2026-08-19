# Review: Project Registry and Resolver

**Verdict: ready** — implementation, focused review, full regression, and release verification passed with no open critical or important findings.

## Scope Reviewed

- Registry v2 parsing, normalization, containment, diagnostics, v1 migration proposal, deterministic resolution, and recent selection.
- Portfolio, intake, lifecycle, loop, Doctor, migration, production, memory/dashboard, MCP, execution, PR, GitHub issue, promotion, repository audit, and issue-generator consumers.
- Distribution manifests and release-test inclusion.

## Findings

1. **Resolved — dashboard CLI ignored configured memory paths.** A RED test showed `--dashboard` wrote to `memory/`; it now writes only to the canonical memory path.
2. **Resolved — production validation raised on an external issues-root symlink.** The existing distribution safety test exposed the exception; validation now returns a contained fail-closed error without reading or disclosing external content.
3. **Resolved — writer surfaces reconstructed default paths.** Execution, PR, GitHub issue sync, promotion, repository audit, and issue generation now accept/infer one project context and use canonical paths for both writes and generated links.
4. **Resolved — source-only test requirement broke the runtime cache package.** Package validation now requires the registry test module only in a source checkout and ships only the three required registry fixtures into the Codex runtime cache.
5. **No open critical or important finding** remains after focused source/test review and fresh release verification.

## Spec Compliance

- All 13 acceptance criteria map to registry, compatibility, isolation, consumer, distribution, or release evidence in `status.md` and focused tests.
- `project_registry.py` owns registry parsing/resolution; `project_issue_schema.py` remains the project-local config/path compatibility owner.
- No sibling-directory discovery, central database, natural-language execution, atomic lifecycle transaction, or dashboard selector was added.
- Ambiguous/unresolved outcomes expose only candidate IDs/names and perform no candidate project-local reads or writes.

## Verification

- Focused convergence: 413/413 passed.
- C2 matrix: 204/204 passed.
- C3 matrix: 80/80 passed.
- Spec consistency: clean.
- Full discovery: 1,225/1,225 passed in 413.431 seconds.
- Project artifact validation: valid with `errors: []`.
- Lifecycle drift: `[]`.
- Release check: valid with every named subcheck passing.
- Diff hygiene: clean.

## Constitution

Constitution: v1.0 checked — no violations.

## Next

Hand off the verified branch for the human integration decision. No push, PR, merge, or local plugin installation was performed.
