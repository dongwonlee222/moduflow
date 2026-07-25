# Frontmatter Issue Schema and Readiness/Dependency Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every ModuFlow consumer one normalized issue model and prevent contradictory schema, dependency, definition-readiness, gate, artifact, or next-command data from being shown or routed as executable.

**Architecture:** Add a standard-library-only `scripts/project_issue_schema.py` domain boundary that parses Markdown and the supported `0.1.0` frontmatter subset, emits `moduflow.issue.v2`, evaluates structural readiness in a fixed precedence order, and builds a read-only migration report. Keep existing public lifecycle helpers as compatibility wrappers, then migrate loop, validation, doctor, MCP, dashboard, and generators to consume the shared boundary. Issue 077 implementation-content readiness remains a later gate after Issue 093 structural readiness passes.

**Tech Stack:** Python 3 standard library, `unittest`, JSON contracts, Markdown/YAML-subset fixtures, Git-native ModuFlow artifacts.

---

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

- `scripts/project_issue_schema.py` is the only owner of issue frontmatter, Markdown status, priority, dependency, definition-readiness, gate, phase, and declared-next-command interpretation.
- Markdown-only issues preserve the current public values and sort order. Existing functions in `project_lifecycle.py` may remain only as wrappers over the normalized model.
- Supported frontmatter is exactly schema `0.1.0`, top-level scalars, and top-level scalar lists. Duplicate keys, anchors, aliases, tags, multi-document input, and nested structures produce stable diagnostics; no PyYAML dependency is added.
- Unversioned frontmatter cannot advance lifecycle or readiness. It may warn and may conservatively block execution when a known unfinished dependency is present.
- Unsupported or malformed versioned frontmatter is a hard structural block. It cannot fall back to a guessed executable state.
- `ready` is always derived. The `status` values `ready` and `blocked` are invalid lifecycle projections in schema `0.1.0`.
- Structural gate precedence is schema → lifecycle projection → dependency integrity → definition readiness → artifact phase → gate state → Issue 077 content readiness → declared next command.
- Migration is report-only. Issue 093 does not expose a `--write` mode and never rewrites issue files.
- Dashboard markup and visual layout stay unchanged; only its issue-row data source and diagnostic flags change.
- All fixtures derived from ModuPay Biz are sanitized and stored locally. Tests never depend on another checkout.
- Every behavior change starts with a failing test, uses the smallest implementation needed to pass, and gets a focused commit before the next consumer migration.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — parser and normalized model | Superpowers TDD | The compatibility boundary needs RED/GREEN proof before consumers move. |
| B — readiness and migration | Superpowers TDD + ModuFlow PM routing | Precedence and commands must be deterministic and product-aware. |
| C — consumer migration | Superpowers TDD | Each consumer needs a parity test before its local parser is removed. |
| D — authoring and distribution | Superpowers TDD | New files must ship and generated Markdown must remain canonical. |
| E — convergence | verification-before-completion | Completion requires fresh focused, full, static, and release evidence. |

## File Structure

### Create

- `scripts/project_issue_schema.py`: YAML-subset reader, Markdown adapter, schema `0.1.0` adapter, normalized record, dependency/readiness evaluator, diagnostics, migration report, and report CLI.
- `tests/test_project_issue_schema.py`: parser, adapter, evaluator, migration, and CLI contract tests.
- `tests/fixtures/issue-schema/BIZ-033.md`: sanitized active release-QA dependency fixture.
- `tests/fixtures/issue-schema/BIZ-038.md`: sanitized invalid `ready` projection plus unmet dependency fixture.
- `tests/fixtures/issue-schema/BIZ-039.md`: sanitized execute-routing dependency fixture.
- `tests/fixtures/issue-schema/BIZ-040.md`: sanitized draft-definition fixture.
- `tests/fixtures/issue-schema/legacy-markdown.md`: canonical Markdown parity fixture.

### Modify

- `scripts/project_lifecycle.py`: delegate lifecycle/list/ready/dependency drift to the shared normalizer while preserving CLI payloads.
- `scripts/project_loop.py`: use normalized artifact phase and structural gate result before Issue 077 readiness and delegation checks.
- `scripts/validate_project_artifacts.py`: surface normalized error diagnostics and actionable warnings.
- `scripts/project_doctor.py`: summarize structural issue diagnostics and recommend the report command.
- `scripts/mcp_server.py`: return additive normalized fields without breaking existing payload keys.
- `scripts/project_memory.py`: build graph and Issue DB rows from normalized status, dependencies, recommended command, and diagnostics.
- `scripts/issue_generator.py`: keep generated Markdown canonical and parser-compatible.
- `templates/issues/issue.md`: keep the default Markdown schema explicit and parser-compatible.
- `tests/test_issue_dependencies.py`: preserve priority/dependency behavior and add frontmatter graph regressions.
- `tests/test_project_lifecycle.py`: preserve lifecycle state and drift behavior through wrappers.
- `tests/test_project_loop.py`: cover structural routing before Issue 077 and delegation.
- `tests/test_validation_distribution.py`: cover validator diagnostics and ensure the new module/fixtures ship.
- `tests/test_project_doctor.py`: cover doctor summary/recommendation for schema failures.
- `tests/test_mcp_server.py`: cover additive v2 data and legacy payload compatibility.
- `tests/test_project_memory.py`: cover normalized graph/table status and attention flags.
- `tests/test_issue_generator.py`: verify generated issues parse as canonical Markdown.
- `issues/093-frontmatter-issue-schema-readiness-gate.md`, `specs/093-frontmatter-issue-schema-readiness-gate/tasks.md`, `status.md`, `workspace/dashboard.md`, `workspace/roadmap.md`: track implementation and verification.

## Stable Interfaces

`scripts/project_issue_schema.py` exposes these public functions:

```python
def parse_issue(path, project_root):
    """Return one moduflow.issue.v2 normalized dict with parse diagnostics."""

def list_normalized_issues(project_root):
    """Return normalized issue dicts sorted by issue_id."""

def build_artifact_index(project_root, issue_ids):
    """Return actual spec/plan/tasks/review/release coverage by issue id."""

def evaluate_issue(issue, issue_index, artifact_index):
    """Return the issue plus structural readiness, command, and diagnostics."""

def evaluate_project(project_root):
    """Return evaluated issues and project-level dependency diagnostics."""

def build_migration_report(project_root):
    """Return moduflow.issue-migration-report.v1 without writing files."""
```

The minimum normalized record is:

```python
{
    "schema": "moduflow.issue.v2",
    "issue_id": "BIZ-038",
    "source_path": "issues/BIZ-038.md",
    "source_format": "frontmatter-0.1.0",
    "schema_version": "0.1.0",
    "title": "Charging history boundary refactor",
    "lifecycle_state": "backlog",
    "projection_status": "ready",
    "priority": "p2",
    "blocked_by": ["BIZ-033"],
    "definition_readiness": "ready",
    "gate_state": "pending",
    "declared_phase": "post_release_qa_refactor",
    "artifact_phase": "issue",
    "declared_next_command": "product:execute BIZ-038",
    "recommended_next_command": "product:status",
    "readiness": "blocked",
    "diagnostics": [],
}
```

Each diagnostic uses this exact data shape:

```python
{
    "code": "ISSUE_DEPENDENCY_UNMET",
    "severity": "error",
    "issue_id": "BIZ-038",
    "source_path": "issues/BIZ-038.md",
    "field": "depends_on",
    "current": "BIZ-033: active",
    "expected": "done or superseded",
    "message": "BIZ-038 cannot execute while BIZ-033 is active.",
    "recommendation": "Keep BIZ-038 blocked and continue BIZ-033.",
}
```

## Implementation Readiness Contracts

- **API contract mapping:** No HTTP endpoint, remote request/response, or network error-state contract changes. MCP remains the existing local stdio JSON-RPC surface: the `moduflow.mcp.v1` envelope and current keys stay compatible, while `normalized_schema`, `readiness`, `recommended_next_command`, and `diagnostic_codes` are additive issue payload fields. Invalid issue IDs and internal errors retain the existing tested responses.
- **Storybook required states:** Not applicable. Issue 093 does not add or redesign a UI component; the current dashboard HTML/CSS and control layout remain unchanged.
- **MSW fixture baseline:** Not applicable. No browser network request is added; the BIZ fixtures are local Markdown files read through temporary filesystem projects.
- **Playwright smoke matrix:** Not applicable. No browser route, action, viewport, or interactive state changes; dashboard regression proof is the existing HTML marker and issue-row `unittest` suite.
- **Permission/role model:** Not applicable. The new normalizer and report CLI are local read-only operations and add no authentication or authorization boundary.
- **Release/rollback:** Full `release_check.py` is required before review. Rollback is commit-level: revert the isolated Issue 093 commits; no source-file migration or external state write needs reversal.

### Stream A — Shared Parser and Normalized Model

#### Task A1: Lock legacy parity and the supported frontmatter grammar

**Files:**
- Create: `tests/test_project_issue_schema.py`
- Create: `tests/fixtures/issue-schema/legacy-markdown.md`
- Create: `tests/fixtures/issue-schema/BIZ-033.md`
- Create: `tests/fixtures/issue-schema/BIZ-038.md`
- Create: `tests/fixtures/issue-schema/BIZ-039.md`
- Create: `tests/fixtures/issue-schema/BIZ-040.md`
- Create: `scripts/project_issue_schema.py`

- [ ] **Step 1: Add sanitized contract fixtures**

Use the same top-level contract in all four BIZ fixtures:

```yaml
---
schema_version: 0.1.0
issue_id: BIZ-038
canonical_state: backlog
status: ready
priority: p2
definition_readiness: ready
gate_state: pending
depends_on: [BIZ-033]
next_command: product:execute BIZ-038
---
```

Set BIZ-033 to `canonical_state: active` / `status: in_progress`; set BIZ-039 to the same dependency and execute claim as BIZ-038; set BIZ-040 to `definition_readiness: draft` with no dependency. Every versioned fixture also contains a matching Markdown `**Status: ...**` projection except tests that deliberately exercise drift.

- [ ] **Step 2: Write failing grammar and safety tests**

Add `ProjectIssueSchemaParsingTests` with exact assertions for:

```python
self.assertEqual(issue["schema"], "moduflow.issue.v2")
self.assertEqual(issue["source_format"], "markdown")
self.assertEqual(issue["lifecycle_state"], "backlog")
self.assertEqual(issue["priority"], "p1")
self.assertEqual(issue["blocked_by"], ["001-dependency"])
```

Add table-driven cases that assert `ISSUE_SCHEMA_MALFORMED` for duplicate keys, nested mappings, anchors, aliases, `!tag`, and a second `---` document. Assert unknown scalar fields are preserved in `extensions` but do not change routing fields.

- [ ] **Step 3: Run the focused test and confirm RED**

Run:

```bash
python3 -m unittest tests.test_project_issue_schema.ProjectIssueSchemaParsingTests -v
```

Expected: import or attribute failures because `project_issue_schema.py` and its parser do not exist.

- [ ] **Step 4: Implement the narrow reader and Markdown primitives**

Add constants and pure helpers:

```python
NORMALIZED_SCHEMA = "moduflow.issue.v2"
SUPPORTED_SCHEMA_VERSIONS = {"0.1.0"}
LIFECYCLE_STATES = {"backlog", "active", "done"}
PROJECTION_TO_LIFECYCLE = {
    "backlog": "backlog",
    "in_progress": "active",
    "done": "done",
}

def split_frontmatter(text): ...
def parse_frontmatter_subset(frontmatter_text, issue_id, source_path): ...
def metadata_region(text): ...
def markdown_status(text): ...
def markdown_priority(text): ...
def markdown_blocked_by(text): ...
def markdown_title(text): ...
```

Parse quoted/unquoted strings, booleans, null, integers, inline scalar lists, and indented scalar lists. Reject richer YAML syntax before interpreting values. Return diagnostics as data; do not raise on a bad user issue file.

- [ ] **Step 5: Run the parser tests and commit**

Run:

```bash
python3 -m unittest tests.test_project_issue_schema.ProjectIssueSchemaParsingTests -v
```

Expected: all parsing tests pass.

Commit:

```bash
git add scripts/project_issue_schema.py tests/test_project_issue_schema.py tests/fixtures/issue-schema
git commit -m "feat(093): parse issue schema inputs safely"
```

#### Task A2: Normalize Markdown, versioned, unversioned, and unsupported inputs

**Files:**
- Modify: `scripts/project_issue_schema.py`
- Modify: `tests/test_project_issue_schema.py`

- [ ] **Step 1: Write failing adapter tests**

Cover all compatibility rows:

```python
self.assertEqual(markdown["source_format"], "markdown")
self.assertEqual(versioned["source_format"], "frontmatter-0.1.0")
self.assertEqual(versioned["lifecycle_state"], "active")
self.assertEqual(unversioned["source_format"], "frontmatter-unversioned")
self.assertEqual(unversioned["lifecycle_state"], "backlog")
self.assertIn("ISSUE_FRONTMATTER_UNVERSIONED", codes(unversioned))
self.assertEqual(unsupported["readiness"], "blocked")
self.assertIn("ISSUE_SCHEMA_UNSUPPORTED", codes(unsupported))
```

Add hard-drift tests for a versioned `canonical_state: active` paired with Markdown `**Status: backlog**`, invalid auxiliary `status: ready`, and mismatched `depends_on` / `**Blocked-by:**` projections.

- [ ] **Step 2: Run the adapter tests and confirm RED**

Run:

```bash
python3 -m unittest tests.test_project_issue_schema.ProjectIssueSchemaAdapterTests -v
```

Expected: failures because `parse_issue()` does not yet dispatch adapters or emit projection diagnostics.

- [ ] **Step 3: Implement explicit adapter dispatch**

Implement:

```python
def parse_issue(path, project_root):
    text = Path(path).read_text(encoding="utf-8")
    frontmatter, body, parse_diagnostics = split_frontmatter(text)
    if frontmatter is None:
        return normalize_markdown_issue(path, project_root, body)
    version = frontmatter.get("schema_version")
    if version == "0.1.0":
        return normalize_frontmatter_0_1_0(path, project_root, frontmatter, body)
    if version is None:
        return normalize_unversioned_frontmatter(path, project_root, frontmatter, body)
    return normalize_unsupported_frontmatter(path, project_root, frontmatter, body)
```

Normalize superseded Markdown values using the existing `superseded-by-*` convention. For versioned inputs require `canonical_state` and a matching Markdown projection. For unversioned inputs retain Markdown lifecycle/priority/dependency truth, attach migration warnings, and copy known frontmatter dependency IDs only into `advisory_blocked_by`.

- [ ] **Step 4: Run all shared-schema tests and commit**

Run:

```bash
python3 -m unittest tests.test_project_issue_schema -v
```

Expected: parser and adapter suites pass.

Commit:

```bash
git add scripts/project_issue_schema.py tests/test_project_issue_schema.py
git commit -m "feat(093): normalize versioned and legacy issues"
```

### Stream B — Structural Readiness and Migration Report

#### Task B1: Evaluate dependencies, definition readiness, artifacts, gates, and commands

**Files:**
- Modify: `scripts/project_issue_schema.py`
- Modify: `tests/test_project_issue_schema.py`

- [ ] **Step 1: Write failing project evaluator tests**

Add tests for dangling, self, cycle, unmet, and satisfied dependencies. Add the sanitized dogfood expectations:

```python
self.assertEqual(by_id["BIZ-033"]["lifecycle_state"], "active")
self.assertEqual(by_id["BIZ-038"]["readiness"], "blocked")
self.assertIn("ISSUE_AUX_STATUS_INVALID", codes(by_id["BIZ-038"]))
self.assertIn("ISSUE_DEPENDENCY_UNMET", codes(by_id["BIZ-038"]))
self.assertEqual(by_id["BIZ-039"]["recommended_next_command"], "product:status")
self.assertEqual(by_id["BIZ-040"]["recommended_next_command"], "product:spec BIZ-040")
```

Also assert:

- `definition_readiness: draft` wins over a declared execute command.
- missing `spec.md` recommends `product:spec`; present spec but missing plan recommends `product:plan`; plan/tasks coverage allows `product:execute` only after earlier gates pass.
- `gate_state: blocked` and unresolved `pending` prevent execute.
- `ISSUE_NEXT_COMMAND_INVALID` records both the declared and recommended commands.
- an active issue with an unfinished dependency is structurally blocked and emits an error.

- [ ] **Step 2: Run evaluator tests and confirm RED**

Run:

```bash
python3 -m unittest tests.test_project_issue_schema.ProjectIssueSchemaEvaluationTests -v
```

Expected: failures because project indexing, cycle detection, artifact indexing, and precedence evaluation are absent.

- [ ] **Step 3: Implement project indexing and iterative dependency analysis**

Add:

```python
def list_normalized_issues(project_root): ...
def build_artifact_index(project_root, issue_ids): ...
def dependency_diagnostics(issue_index): ...
def evaluate_issue(issue, issue_index, artifact_index): ...
def evaluate_project(project_root): ...
```

Use iterative DFS, not recursion, so the existing ~2,000-node regression remains safe. Treat `done` and `superseded` dependencies as satisfied. Merge `advisory_blocked_by` only as a conservative blocking input; never promote lifecycle or readiness from unversioned frontmatter.

- [ ] **Step 4: Implement command precedence as one pure function**

Use one internal result accumulator and stop later rules from replacing an earlier blocking recommendation:

```python
def derive_structural_route(issue, issue_index, artifact_index):
    if has_schema_error(issue):
        return "blocked", "product:doctor"
    if has_projection_error(issue):
        return "blocked", "product:doctor"
    if has_dependency_error(issue):
        return "blocked", "product:status"
    if issue["definition_readiness"] == "draft":
        return "blocked", f"product:spec {issue['issue_id']}"
    if missing_spec(issue, artifact_index):
        return "not_ready", f"product:spec {issue['issue_id']}"
    if missing_plan(issue, artifact_index):
        return "not_ready", f"product:plan {issue['issue_id']}"
    if unresolved_gate(issue):
        return "blocked", gate_recovery_command(issue)
    return "ready", f"product:execute {issue['issue_id']}"
```

Keep the issue-type exception allowlist empty in v1. Any later exception requires code, rationale, and a test as specified.

- [ ] **Step 5: Run focused and deep-chain tests, then commit**

Run:

```bash
python3 -m unittest tests.test_project_issue_schema.ProjectIssueSchemaEvaluationTests -v
python3 -m unittest tests.test_issue_dependencies -v
```

Expected: all tests pass, including dangling/cycle/deep-chain behavior.

Commit:

```bash
git add scripts/project_issue_schema.py tests/test_project_issue_schema.py
git commit -m "feat(093): enforce structural issue readiness"
```

#### Task B2: Add a deterministic read-only migration report CLI

**Files:**
- Modify: `scripts/project_issue_schema.py`
- Modify: `tests/test_project_issue_schema.py`

- [ ] **Step 1: Write failing migration report and CLI tests**

Assert the report has no write path and contains routing impact:

```python
self.assertEqual(report["schema"], "moduflow.issue-migration-report.v1")
self.assertEqual(report["project_root"], str(root.resolve()))
self.assertEqual(report["summary"]["issues_scanned"], 4)
self.assertIn("safe_mappings", report["issues"][0])
self.assertIn("human_decisions", report["issues"][0])
self.assertIn("routing_before", report["issues"][0])
self.assertIn("routing_after", report["issues"][0])
self.assertEqual(before_hashes, after_hashes)
```

Invoke `main([str(root), "--report"])` under captured stdout and assert valid JSON. Assert `--write` is rejected by `argparse`.

- [ ] **Step 2: Run migration tests and confirm RED**

Run:

```bash
python3 -m unittest tests.test_project_issue_schema.ProjectIssueMigrationReportTests -v
```

Expected: failures because the report and CLI do not exist.

- [ ] **Step 3: Implement report-only output**

Add `build_migration_report(project_root)` and a CLI accepting only:

```bash
python3 scripts/project_issue_schema.py <project-path> --report
```

Exit `0` when scanning completes, even if issues need migration; encode error/warning counts in the JSON. Exit nonzero only for an unreadable project root or internal contract failure. Proposals are data fields such as `set_schema_version`, `align_markdown_status`, and `align_dependency_projection`; never write source files.

- [ ] **Step 4: Run migration and full schema tests, then commit**

Run:

```bash
python3 -m unittest tests.test_project_issue_schema -v
python3 scripts/project_issue_schema.py . --report
```

Expected: tests pass; repository report is valid `moduflow.issue-migration-report.v1` JSON and no issue file changes.

Commit:

```bash
git add scripts/project_issue_schema.py tests/test_project_issue_schema.py
git commit -m "feat(093): report issue schema migrations"
```

### Stream C — Consumer Convergence

#### Task C1: Move lifecycle, ready queue, and dependency drift to the shared model

**Files:**
- Modify: `scripts/project_lifecycle.py`
- Modify: `tests/test_project_lifecycle.py`
- Modify: `tests/test_issue_dependencies.py`

- [ ] **Step 1: Add failing parity and frontmatter graph tests**

Snapshot the existing `lifecycle_state()`, `list_issues()`, and `ready_issues()` keys for legacy Markdown. Add frontmatter assertions that BIZ-038/039 are absent from `ready_issues()`, a versioned dangling dependency reaches `lifecycle_drift()`, and an active issue with an unmet frontmatter dependency is drift.

- [ ] **Step 2: Run lifecycle/dependency tests and confirm RED**

Run:

```bash
python3 -m unittest tests.test_project_lifecycle tests.test_issue_dependencies -v
```

Expected: new frontmatter cases fail because lifecycle still parses only Markdown.

- [ ] **Step 3: Replace local parsing with compatibility projections**

Import `evaluate_project` and project normalized records into existing payloads:

```python
def list_issues(root):
    evaluated = evaluate_project(root)["issues"]
    return [
        {
            "id": item["issue_id"],
            "status": item["lifecycle_state"],
            "title": item["title"],
            "priority": item["priority"],
            "blocked_by": item["blocked_by"],
        }
        for item in evaluated
    ]
```

Make `_issue_status`, `_issue_priority`, and `_issue_blocked_by` thin compatibility wrappers over shared text helpers or remove their consumer use. Translate normalized error diagnostics into the existing lifecycle drift strings without inventing a second dependency traversal.

- [ ] **Step 4: Run lifecycle/dependency regressions and commit**

Run:

```bash
python3 -m unittest tests.test_project_lifecycle tests.test_issue_dependencies -v
python3 scripts/project_lifecycle.py . --ready
python3 scripts/project_lifecycle.py . --drift
```

Expected: tests pass; CLI JSON shapes remain compatible; current repository drift is `[]`.

Commit:

```bash
git add scripts/project_lifecycle.py tests/test_project_lifecycle.py tests/test_issue_dependencies.py
git commit -m "refactor(093): share lifecycle issue interpretation"
```

#### Task C2: Put structural readiness before loop, validation, doctor, and Issue 077

**Files:**
- Modify: `scripts/project_loop.py`
- Modify: `scripts/validate_project_artifacts.py`
- Modify: `scripts/project_doctor.py`
- Modify: `tests/test_project_loop.py`
- Modify: `tests/test_validation_distribution.py`
- Modify: `tests/test_project_doctor.py`

- [ ] **Step 1: Write failing routing and validation tests**

Create temporary BIZ fixtures with plan/tasks coverage and assert:

```python
self.assertEqual(loop_result["phase"], "plan")
self.assertNotIn("product:execute", loop_result["next_command"])
self.assertIn("ISSUE_DEPENDENCY_UNMET", loop_result["blocker"])
self.assertTrue(any("ISSUE_STATE_PROJECTION_MISMATCH" in e for e in validation["errors"]))
self.assertTrue(any("project_issue_schema.py . --report" in r for r in doctor["recommendation"]))
```

Add an ordering test where both structural dependency failure and Issue 077 `not_ready` exist; the returned blocker must be the structural diagnostic, proving 093 runs first. Add a clean legacy project test proving existing delegation/readiness routing remains unchanged.

- [ ] **Step 2: Run focused consumers and confirm RED**

Run:

```bash
python3 -m unittest tests.test_project_loop tests.test_validation_distribution tests.test_project_doctor -v
```

Expected: new structural-gate assertions fail.

- [ ] **Step 3: Integrate the shared evaluator once per consumer**

In `project_loop.recommend_loop()`, evaluate the active issue before loading `implementation-readiness.json`:

```python
structural = evaluated_issue(root, active_issue_id)
if structural["readiness"] != "ready":
    state["phase"] = command_phase(structural["recommended_next_command"])
    state["status"] = "needs_decision"
    state["blocker"] = format_primary_diagnostic(structural)
    state["next_command"] = structural["recommended_next_command"]
    return state
```

In validation, append normalized `error` diagnostics to `errors` and `warning` diagnostics to `warnings` with code, path, message, and recommendation. In doctor, expose counts/codes under `issue_schema` and recommend the exact report command when any schema diagnostic exists.

- [ ] **Step 4: Run focused tests and commit**

Run:

```bash
python3 -m unittest tests.test_project_loop tests.test_validation_distribution tests.test_project_doctor -v
```

Expected: all focused tests pass and structural failures precede Issue 077/content/delegation routing.

Commit:

```bash
git add scripts/project_loop.py scripts/validate_project_artifacts.py scripts/project_doctor.py tests/test_project_loop.py tests/test_validation_distribution.py tests/test_project_doctor.py
git commit -m "feat(093): gate loop and validation on issue schema"
```

#### Task C3: Move MCP and the current dashboard data model to normalized issues

**Files:**
- Modify: `scripts/mcp_server.py`
- Modify: `scripts/project_memory.py`
- Modify: `tests/test_mcp_server.py`
- Modify: `tests/test_project_memory.py`

- [ ] **Step 1: Write failing additive-contract tests**

For MCP, preserve `id`, `status`, `title`, `priority`, and `blocked_by`, then assert additive fields:

```python
self.assertEqual(item["normalized_schema"], "moduflow.issue.v2")
self.assertEqual(item["readiness"], "blocked")
self.assertEqual(item["recommended_next_command"], "product:status")
self.assertIn("ISSUE_DEPENDENCY_UNMET", item["diagnostic_codes"])
```

For the current dashboard table/graph, assert BIZ-038 has normalized `status: backlog`, `readiness: blocked`, a `blocked` attention flag, and no execute next command. Assert the existing issue DB controls, row links, Korean descriptions, and visual layout markers are unchanged.

- [ ] **Step 2: Run MCP/dashboard tests and confirm RED**

Run:

```bash
python3 -m unittest tests.test_mcp_server tests.test_project_memory -v
```

Expected: additive normalized fields and frontmatter routing assertions fail.

- [ ] **Step 3: Replace raw status/command parsing at the data-source boundary**

Make `mcp_server` consume evaluated records for list, get, status counts, and ready. Keep the `moduflow.mcp.v1` envelope and current keys; add normalized fields only.

Make `_collect_issue_graph()` and `_collect_issue_table()` build from one evaluated issue index. Preserve prose-only helpers for summaries, dates, related links, and Korean overlays. Remove raw lifecycle/dependency/next-command regex use from graph/table status routing; do not alter the HTML/CSS structure.

- [ ] **Step 4: Run MCP/dashboard regressions and commit**

Run:

```bash
python3 -m unittest tests.test_mcp_server tests.test_project_memory -v
```

Expected: all tests pass, including path traversal, persistent-server survival, current Issue DB controls, Korean overlays, and normalized blocking flags.

Commit:

```bash
git add scripts/mcp_server.py scripts/project_memory.py tests/test_mcp_server.py tests/test_project_memory.py
git commit -m "refactor(093): converge MCP and dashboard issue data"
```

### Stream D — Authoring Compatibility and Distribution

#### Task D1: Keep generators canonical and prevent parser duplication from returning

**Files:**
- Modify: `scripts/issue_generator.py`
- Modify: `templates/issues/issue.md`
- Modify: `tests/test_issue_generator.py`
- Modify: `tests/test_validation_distribution.py`

- [ ] **Step 1: Write failing generator and distribution tests**

Generate an issue, parse it with `parse_issue()`, and assert:

```python
self.assertEqual(parsed["source_format"], "markdown")
self.assertEqual(parsed["lifecycle_state"], "backlog")
self.assertEqual(parsed["priority"], "p2")
self.assertEqual(parsed["diagnostics"], [])
```

Add distribution assertions that `scripts/project_issue_schema.py` and all five `tests/fixtures/issue-schema/*.md` files are present. Add a narrow static check that lifecycle, MCP, and project-memory issue consumers import the shared module and do not define new functions named `parse_issue_frontmatter`, `issue_status`, or `issue_blocked_by`.

- [ ] **Step 2: Run authoring/distribution tests and confirm RED**

Run:

```bash
python3 -m unittest tests.test_issue_generator tests.test_validation_distribution -v
```

Expected: distribution and parser-compatibility assertions fail before updates.

- [ ] **Step 3: Align generated Markdown without changing the default format**

Keep this canonical header shape in the generator and template:

```markdown
**Status: backlog** — created YYYY-MM-DD.
**Priority: p2**
**Blocked-by:**
```

Use concrete backticked workflow links only when the corresponding files exist; otherwise retain validator-safe placeholder paths. Do not add frontmatter to generated issues.

- [ ] **Step 4: Run authoring/distribution tests and commit**

Run:

```bash
python3 -m unittest tests.test_issue_generator tests.test_validation_distribution -v
```

Expected: generated Markdown normalizes without diagnostics and distribution/static checks pass.

Commit:

```bash
git add scripts/issue_generator.py templates/issues/issue.md tests/test_issue_generator.py tests/test_validation_distribution.py
git commit -m "test(093): lock canonical issue authoring"
```

### Stream E — Convergence, Dogfood, and Completion Evidence

#### Task E1: Run cross-consumer parity and repository dogfood

**Files:**
- Modify: `tests/test_project_issue_schema.py`
- Modify: `specs/093-frontmatter-issue-schema-readiness-gate/tasks.md`
- Create: `specs/093-frontmatter-issue-schema-readiness-gate/status.md`

- [ ] **Step 1: Add one cross-consumer parity test**

For one legacy issue and BIZ-038, compare normalized lifecycle/readiness/dependencies across `project_issue_schema`, `project_lifecycle`, `project_loop`, MCP payloads, and dashboard rows. The same issue may have different presentation fields, but no consumer may disagree on lifecycle, blockers, readiness, or recommended command.

- [ ] **Step 2: Run the focused Issue 093 matrix**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*issue*schema*.py' -v
python3 -m unittest tests.test_issue_dependencies tests.test_project_lifecycle tests.test_project_loop tests.test_validation_distribution tests.test_project_doctor tests.test_mcp_server tests.test_project_memory tests.test_issue_generator -v
```

Expected: all focused tests pass.

- [ ] **Step 3: Run static and migration dogfood checks**

Run:

```bash
python3 scripts/project_issue_schema.py . --report
rg -n "re\.search\(.*Status|Blocked-by|canonical_state|depends_on" scripts/project_lifecycle.py scripts/project_loop.py scripts/mcp_server.py scripts/project_memory.py scripts/validate_project_artifacts.py
git diff --check
```

Expected: the report is valid and read-only; the static search shows no independent issue-state/dependency routing parser in consumers; whitespace check is clean.

- [ ] **Step 4: Record evidence and commit**

Write `status.md` with exact commands, pass counts, migration-report summary, known warnings, and the latest commit hashes. Check completed items in `tasks.md` only after their evidence exists.

Commit:

```bash
git add specs/093-frontmatter-issue-schema-readiness-gate/tasks.md specs/093-frontmatter-issue-schema-readiness-gate/status.md tests/test_project_issue_schema.py
git commit -m "test(093): prove cross-consumer issue parity"
```

#### Task E2: Run full release gates and update lifecycle artifacts

**Files:**
- Modify: `issues/093-frontmatter-issue-schema-readiness-gate.md`
- Modify: `specs/093-frontmatter-issue-schema-readiness-gate/tasks.md`
- Modify: `specs/093-frontmatter-issue-schema-readiness-gate/status.md`
- Modify: `workspace/dashboard.md`
- Modify: `workspace/roadmap.md`
- Modify: `.moduflow/state.json`
- Modify: `workspace/loop-state.json`

- [ ] **Step 1: Run plan/spec convergence before the full suite**

Run:

```bash
python3 scripts/spec_consistency.py . --issue-id 093-frontmatter-issue-schema-readiness-gate
```

Expected: `error: 0`, `coverage_flagged: 0`, and no missing plan/tasks artifact info.

- [ ] **Step 2: Run full verification**

Run:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_project_artifacts.py .
python3 scripts/project_lifecycle.py . --drift
python3 scripts/release_check.py .
```

Expected: all tests pass; project validation is valid; lifecycle drift is `[]`; release check exits `0`.

- [ ] **Step 3: Update workflow only from fresh evidence**

After the full suite passes:

- check `execute` in Issue 093 and link the implementation commits;
- set the next command to `product:review 093-frontmatter-issue-schema-readiness-gate`;
- update dashboard/roadmap/status with exact verification results;
- keep the issue `active` until review and release are separately completed;
- preserve the full branch binding `codex/093-frontmatter-issue-schema-readiness-gate`.

- [ ] **Step 4: Commit the verified implementation state**

Run:

```bash
git add issues/093-frontmatter-issue-schema-readiness-gate.md specs/093-frontmatter-issue-schema-readiness-gate workspace/dashboard.md workspace/roadmap.md workspace/loop-state.json .moduflow/state.json
git commit -m "docs(093): record issue schema gate verification"
git status --short --branch
```

Expected: branch is clean and ahead of `origin/main`; no push, PR, merge, release, or external issue mutation occurs without the user's next instruction.

## Acceptance-Criteria Trace

| Spec acceptance criterion | Planned proof |
| --- | --- |
| Markdown-only behavior remains backward compatible | A1, A2, C1, C3, D1, E1 |
| Versioned frontmatter produces `moduflow.issue.v2` | A1, A2 |
| Unversioned frontmatter stays Markdown-canonical and cannot advance ready/execute | A2, B1 |
| Frontmatter `depends_on` participates in ready, dangling, and cycle checks | B1, C1 |
| Versioned canonical state and Markdown projection disagreement is hard drift | A2, C1, C2 |
| Unfinished dependency cannot be ready, active, or execute-routed | B1, C1, C2, C3 |
| Draft definition readiness routes to `product:spec` | B1, C2 |
| Lifecycle, projection, gate, artifact, and command contradictions have stable diagnostics | A2, B1, C2 |
| BIZ-038/039 blocked and BIZ-040 routed to spec | B1, E1 |
| Lifecycle, loop, validation, doctor, MCP, and dashboard share one normalizer | C1, C2, C3, D1, E1 |
| Migration report proposes changes without writes | B2, E1 |
| Focused tests, validation, and release check pass | E1, E2 |

## Execution Notes

- Run tasks in order A1 → A2 → B1 → B2 → C1 → C2 → C3 → D1 → E1 → E2. Later streams depend on the normalized contract and evaluator being stable.
- Do not combine consumer migrations into one commit. A regression must be attributable to one boundary.
- If a legacy parity test fails, preserve the existing public payload first and expose new information additively.
- If the supported subset encounters a real field it cannot represent, emit `ISSUE_SCHEMA_MALFORMED` plus migration guidance; do not broaden YAML support inside a consumer.
- Stop before any push, PR, merge, release, GitHub issue update, or automated source rewrite and request explicit authorization.
