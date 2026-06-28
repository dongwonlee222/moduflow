# Issue: `045-issue-graph-visualization`

**Status: backlog** — created 2026-06-28. Part of goal `visual-workbench`.

## Goal

Do for issues what `042` did for memory: a read-only graph where nodes = issues, edges = supersedes/related/depends, color = status. See how the 44+ issues actually relate.

## Decision (spine)

Reuse the `042` generator pattern (Python emits node/edge JSON → Cytoscape, single self-contained HTML). The hard part is the relationship source, because issues have no frontmatter.

## Relationship Source — fork (decide in spec)

- **Cheap**: parse the `## Related Issues` section + `**Status:**` line. Brittle text parsing, zero schema change.
- **Proper**: give issues frontmatter (like memory) — `supersedes`/`depends_on`/`related`/`status`. A change to the Git-native artifact model; touches `024-artifact-schema-and-doctor-gates`, doctor/validation, and templates. Bigger, but makes issue relationships first-class and machine-readable.

Do not start adding frontmatter to issue files outside a dedicated decision.

## Scope

- Read-only issue graph rendered the same way as the memory dashboard.
- Status-colored nodes (done / backlog / superseded / active).

## Out of Scope

- Interactive editing/creation (later goal stage).
- The artifact-model schema change itself (separate issue if the "proper" path is chosen).

## Related

- Goal `visual-workbench`
- `042-decision-graph-dashboard` (pattern reused)
- `024-artifact-schema-and-doctor-gates`, `git-native-artifact-model` (if frontmatter path chosen)
