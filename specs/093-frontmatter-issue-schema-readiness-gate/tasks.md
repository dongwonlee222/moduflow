# Tasks: 093-frontmatter-issue-schema-readiness-gate

Issue: `093-frontmatter-issue-schema-readiness-gate`
Plan: `specs/093-frontmatter-issue-schema-readiness-gate/plan.md`

## Stream A — Shared Parser and Normalized Model

- [x] A1 Lock legacy Markdown parity, sanitized BIZ fixtures, and the safe top-level YAML subset.
- [x] A2 Normalize versioned `0.1.0`, unversioned, unsupported, and projection-conflict inputs to `moduflow.issue.v2`.

## Stream B — Structural Readiness and Migration Report

- [x] B1 Enforce schema, state projection, dependency, definition-readiness, artifact, gate, and next-command precedence.
- [x] B2 Add `moduflow.issue-migration-report.v1` report-only CLI with before/after routing impact and zero writes.

## Stream C — Consumer Convergence

- [x] C1 Move lifecycle state, priority, `depends_on`/`Blocked-by`, ready queue, dangling, cycle, and active-unmet drift to the shared normalizer.
- [x] C2 Put the structural gate before Issue 077 in loop routing, validation, and doctor recommendations.
- [x] C3 Move MCP and the current dashboard graph/Issue DB data model to normalized state, readiness, diagnostics, and recommended command.

## Stream D — Authoring Compatibility and Distribution

- [x] D1 Keep generated/template issues canonical Markdown, ship the new module/fixtures, and prevent independent consumer parsers from returning.

## Stream E — Convergence, Dogfood, and Completion Evidence

- [x] E1 Prove cross-consumer parity for legacy Markdown and BIZ-033/038/039/040, then record focused-test and migration-report evidence.
- [ ] E2 Pass spec consistency, full unittest, project validation, lifecycle drift, and release check before moving to review.

## Acceptance Coverage

- AC1 Markdown-only issue behavior remains backward compatible → A1, A2, C1, C3, D1, E1.
- AC2 recognized versioned frontmatter produces `moduflow.issue.v2` → A1, A2.
- AC3 unversioned frontmatter keeps Markdown canonical, emits migration guidance, and cannot advance ready/execute → A2, B1, B2.
- AC4 frontmatter `depends_on` participates in ready/blocked queries and dangling/cycle validation → B1, C1.
- AC5 canonical state and Markdown projection disagreement is a hard drift error → A2, C1, C2.
- AC6 unfinished dependency cannot be ready, active, or routed to execute → B1, C1, C2, C3.
- AC7 `definition_readiness: draft` routes to `product:spec` → B1, C2.
- AC8 lifecycle, projection status, gate state, artifact phase, and next command produce stable actionable diagnostics → A2, B1, C2.
- AC9 BIZ-038/BIZ-039 are blocked by BIZ-033 and BIZ-040 routes to spec → B1, E1.
- AC10 lifecycle, loop, validation, doctor, MCP, and dashboard consume one shared normalizer → C1, C2, C3, D1, E1.
- AC11 migration report proposes changes without writing issue files → B2, E1.
- AC12 focused tests, dependency/loop regressions, validation, and `release_check.py` pass → E1, E2.

## Next

`product:execute 093-frontmatter-issue-schema-readiness-gate`
