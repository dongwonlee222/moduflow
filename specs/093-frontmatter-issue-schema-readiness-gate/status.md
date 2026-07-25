# Issue 093 Execution Status

**Status: execute and E2 verification complete; independent review remains pending.**

## E2 full verification

Fresh verification was run on 2026-07-25 at implementation HEAD
`ab682e349e260dedfd6539b10fa114c1705a32a1` before lifecycle files changed.

```bash
python3 scripts/spec_consistency.py . --issue-id 093-frontmatter-issue-schema-readiness-gate
```

Result: exit `0`; `error: 0`, `warn: 0`, `info: 0`, `coverage_checked: 12`,
and `coverage_flagged: 0`.

```bash
python3 -m unittest discover -s tests -v
```

Result: exit `0`; `732/732` tests passed in `46.152s` with `OK`.

```bash
python3 scripts/validate_project_artifacts.py .
```

Result: exit `0`; `valid: true`, no errors, issue-schema errors `0`,
issue-schema warnings `4`, and lifecycle drift `[]`. The four schema warnings
are normal backlog dependency waits: one on issue `091` and three on issue
`092`. The remaining non-blocking warnings are one optional memory capability
notice and nine existing repository-link role advisories.

```bash
python3 scripts/project_lifecycle.py . --drift
```

Result: exit `0`; `[]`.

```bash
python3 scripts/release_check.py .
```

Result: exit `0`; `valid: true`, no errors, and every check is `ok`:
`validate_moduflow`, project-artifact validation, linkage, lint, security,
version-bump gate, unittest, doctor, and both release documents.

```bash
git diff --check
```

Result: exit `0`; no whitespace errors. The package version was not changed
because the fresh version-bump gate was already valid and Issue 093 is moving
to review, not release.

## Cross-consumer parity

The fresh parity test places one legacy Markdown issue and sanitized
`BIZ-033`/`BIZ-038`/`BIZ-039`/`BIZ-040` fixtures in one temporary project.
`project_issue_schema`, lifecycle list/ready, loop routing, MCP issue payloads,
and dashboard graph/table projections agree on every semantic field they expose.

| Issue | Lifecycle | Dependencies | Readiness | Recommended command |
| --- | --- | --- | --- | --- |
| `legacy-markdown` | `backlog` | `001-dependency` (done) | `ready` | `product:execute legacy-markdown` |
| `BIZ-033` | `active` | none | `not_ready` | `product:spec BIZ-033` |
| `BIZ-038` | `backlog` | `BIZ-033` (active) | `blocked` | `product:status` |
| `BIZ-039` | `backlog` | `BIZ-033` (active) | `blocked` | `product:status` |
| `BIZ-040` | `backlog` | none | `blocked` | `product:spec BIZ-040` |

Exact command:

```bash
python3 -m unittest tests.test_project_issue_schema.ProjectIssueSchemaCrossConsumerParityTests -v
```

Result: `1/1` passed. No consumer semantic difference was found.

## Focused verification

```bash
python3 -m unittest discover -s tests -p 'test_*issue*schema*.py' -v
```

Result: `92/92` passed.

```bash
python3 -m unittest tests.test_issue_dependencies tests.test_project_lifecycle tests.test_project_loop tests.test_validation_distribution tests.test_project_doctor tests.test_mcp_server tests.test_project_memory tests.test_issue_generator -v
```

Result: a fresh rerun at commit `34be14b` completed `213/213` tests with
`OK` and exit `0`.

```bash
python3 scripts/release_check.py .
```

Result: `valid: true`, no errors, and every reported check is `ok`, including
`validate_moduflow`, project-artifact validation, linkage, lint, security,
version-bump gate, unittest, doctor, and release documentation.

## Read-only migration dogfood

Issue-file digest command, run before and after the report:

```bash
find issues -type f -name '*.md' -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256
```

Digest before and after:
`13333ccd3cfac622bd6401db75ae0778485eeeb164b720e34be7a4005f8d7069`.

```bash
python3 scripts/project_issue_schema.py . --report
```

Result: exit `0`, schema `moduflow.issue-migration-report.v1`,
`91` issues scanned, `0` errors, `4` warnings, and `2` migration proposals.
The four warnings are normal unfinished-dependency waits: one on issue `091`
and three on issue `092`. No issue file changed.

## Static convergence and diff hygiene

```bash
rg -n "re\.search\(.*Status|Blocked-by|canonical_state|depends_on" scripts/project_lifecycle.py scripts/project_loop.py scripts/mcp_server.py scripts/project_memory.py scripts/validate_project_artifacts.py
git diff --check
```

Result: `git diff --check` is clean. Search matches are limited to lifecycle
documentation, validator presence checking, and `project_memory.py`'s separate
memory-artifact `depends_on` model/UI; no consumer contains an independent
issue lifecycle/dependency routing parser.

## Reviewed implementation commits

| Stream | Latest reviewed commit |
| --- | --- |
| A1 parser | `7207a0f` |
| A2 adapters | `2b786d5` |
| B1 evaluator | `e220e4a` |
| B2 migration report | `96485a2` |
| C1 lifecycle | `28ac7ff` |
| C2 loop/validation/doctor | `26659dd` |
| C3 MCP/dashboard | `4c9b46a` |
| D1 authoring/distribution | `7d76100` |

## Review

Run 2026-07-25 at head `098c0f3` by Claude Opus 5, inline (coordinator-judged).
Subagent dispatch was withheld this session, so findings are single-reviewer
judgments rather than independent multi-reviewer consensus.

Verification reproduced at review time: `unittest discover` 737 passed `OK`;
`release_check.py` `valid: true` with every sub-check `ok`.

Verdict: **approve with conditions**. Full notes:
`specs/093-frontmatter-issue-schema-readiness-gate/review.md`.

| # | Finding | Verdict | Severity |
| --- | --- | --- | --- |
| 1 | Converge collects 1 of 44 commits, silently; no implementation file reaches the judge | Confirmed | Important (pre-existing, not 093) |
| 2 | `infer_issue_phase` checkbox-less default flipped `status` to `execute`, reachable with no gate passed | Plausible | Medium |
| 3 | 43 of 44 commits carry no `Issue:` trailer; linkage passes only via branch fallback | Confirmed | Low (process) |

Conditions before merge:

1. Finding 2 — record a reachability argument here, or add a regression test.
2. Finding 1 — register as a new issue. Pre-existing, so it does not block 093.

## Evidence

- Review notes: `specs/093-frontmatter-issue-schema-readiness-gate/review.md`
- Review handoff: `specs/093-frontmatter-issue-schema-readiness-gate/review-handoff.md`
- Dashboard: `memory/dashboard.html`
- Issue drill-down: `memory/issue-093-frontmatter-issue-schema-readiness-gate.html`
- Converge: **not usable this run.** `project_converge.py --evidence` returned
  1 commit and 7 files, none of them implementation, with `errors: []`. See
  finding 1. Per `product-review.md` step 5 converge is reported, never
  gating; the verdict rests on the test suite, release gates, and inline
  reading instead.
- Reference improvements: none found.

## Next gate

Issue 093 remains `active`. No push, PR, merge, or release has been performed.
Clear the two review conditions, then proceed to PR.

`product:pr 093-frontmatter-issue-schema-readiness-gate`
