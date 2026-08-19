# Project Registry and Resolver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve exactly one explicitly registered ModuFlow project before project-local reads or writes, then give every migrated consumer the same contained canonical path map.

**Architecture:** Add a standard-library-only `scripts/project_registry.py` boundary that owns `projects.v1`/`projects.v2` parsing, deterministic project resolution, v1 migration proposals, recent explicit selection state, and resolved project contexts. Keep `scripts/project_issue_schema.py` as the owner of project-local issue/spec/workspace config compatibility; the registry boundary calls it only after one project has been selected. Existing single-project functions remain compatible through an explicit-root context adapter while portfolio and future natural-language callers use the registry resolver.

**Tech Stack:** Python 3 standard library, `unittest`, JSON/Markdown Git artifacts, existing ModuFlow project schema/lifecycle APIs.

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

- `scripts/project_registry.py` is the only owner of multi-project registry parsing, project alias normalization, resolution precedence, v1→v2 migration proposals, and recent-selection metadata.
- `scripts/project_issue_schema.py` remains the only owner of project-local issue-schema parsing and `.moduflow/config.json` path compatibility; no second issue parser or local-config parser is introduced.
- Multi-project candidates come only from the explicit registry. No task may scan sibling, parent, workspace, or home directories to discover projects.
- Resolution precedence is exactly: explicit registered project ID → exactly one containing registered CWD root → exactly one normalized project name/alias match → valid registered active-issue project → valid most-recent explicit selection → `ambiguous` or `unresolved`.
- `ambiguous` and `unresolved` results read no candidate project issue, memory, production-record, playbook, config, or state file and perform no write.
- A v2 registry declares exactly one relative path per canonical key: `issues`, `specs`, `workspace`, `knowledge`, `memory`, `production_records`, `playbooks`, and `workflow`.
- Every v2 path resolves under the project's canonical real root. Absolute child paths, `..` escapes, and symlink escapes are blocking diagnostics; there is no external-path grant in Issue 102.
- `projects.v1` remains read-compatible and produces a deterministic v2 migration proposal. Issue 102 never rewrites a v1 registry automatically.
- Recent selection stores only `project_id` and ISO-8601 `selected_at` in `project-selection.json` adjacent to the registry. It contains no project content and has no time-based expiry in v1; invalid timestamps, missing IDs, and no-longer-registered IDs are ignored with warnings.
- Existing root-argument APIs remain compatible. A bare root is treated as an explicit single-project boundary, never as permission to inspect sibling projects.
- Git Markdown/JSON stays canonical. No database, network lookup, vector index, external service, or browser-side write is added.
- Existing public CLI and MCP payload keys remain compatible; new resolution/context fields are additive.
- Every behavior change starts with a focused failing `unittest`, proves RED/GREEN, and lands as a reviewable Issue 102 commit before the next task.
- Execution begins only from a `codex/102-project-registry-and-resolver` branch or worktree after preserving the approved planning artifacts. Existing unrelated `.playwright-mcp/` and PNG files are never staged.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — registry and resolver contract | Superpowers TDD | Schema, precedence, ambiguity, and fail-closed behavior need direct RED/GREEN evidence. |
| B — compatibility and portfolio integration | Superpowers TDD + ModuFlow Git-native artifact model | v1 compatibility and explicit selection must preserve current Git artifacts. |
| C — consumer convergence | Superpowers TDD | Each consumer needs a nested-path parity test before direct path construction is removed. |
| D — distribution and convergence | verification-before-completion | Completion requires focused suites, full release gates, drift checks, and package-distribution proof. |

## File Structure

### Create

- `scripts/project_registry.py`: v1/v2 registry reader, diagnostics, normalization, pure resolver, selected-project context materialization, v1 migration proposal, and recent-selection helpers/CLI.
- `tests/test_project_registry.py`: registry schema, resolution precedence, ambiguity, isolation, path containment, v1 compatibility, recent-selection, and CLI contract tests.
- `tests/fixtures/project-registry/projects-v1.json`: current registry compatibility fixture.
- `tests/fixtures/project-registry/projects-v2.json`: two-project Korean-alias and nested-path fixture.
- `tests/fixtures/project-registry/projects-v2-alias-collision.json`: deterministic ambiguity fixture.
- `portfolio/project-selection.json`: not created during implementation; this is the runtime location produced only by an explicit `--select` action.

### Modify

- `scripts/project_issue_schema.py`: expand the shared project-local path key map and expose it to explicit-root/resolved-context adapters without changing issue parsing.
- `scripts/project_portfolio.py`: initialize v2 registries, read statuses through the registry boundary, render resolver diagnostics, and support explicit recent selection.
- `scripts/project_intake.py`: use resolved issue/workspace paths for duplicate search and inbox/loop reads.
- `scripts/project_loop.py`: use the resolved workspace path for `loop-state.json` while retaining current issue/spec path behavior.
- `scripts/project_lifecycle.py`: use resolved workspace paths for dashboard reads/writes and pass the common relative path map into issue evaluation.
- `scripts/project_doctor.py`: stop reconstructing workspace paths and report registry/context diagnostics.
- `scripts/project_migrate.py`: derive all mapped directories from one explicit-root context without changing migration semantics.
- `scripts/project_production.py`: use canonical issues, production-record, and playbook paths for list/create/search/validate/approval.
- `scripts/project_memory.py`: use canonical memory/knowledge/workspace/issue/spec paths for memory commands and dashboard/panel projections.
- `scripts/mcp_server.py`: accept/propagate one resolved context while preserving `moduflow.mcp.v1` keys.
- `scripts/project_execution.py`: use canonical issue/spec paths for readiness and review handoff artifacts.
- `scripts/project_pr.py`: use canonical issue/spec/workspace paths for Korean packets and PR handoffs.
- `scripts/project_github_issues.py`: locate the canonical issue file before GitHub projection/write-back.
- `scripts/project_promote.py`: create promoted issues in the canonical issue path.
- `scripts/project_repository_identity.py`: audit canonical issue/spec trees rather than root defaults.
- `scripts/issue_generator.py`: allocate and write generated issues in the canonical issue path.
- `scripts/validate_moduflow.py`: require the new script, tests, fixtures, and v2 template in package validation.
- `scripts/release_check.py`: add `tests.test_project_registry` to the required release test modules.
- `templates/portfolio/projects.json`: change the newly initialized template to `moduflow.projects.v2` while keeping v1 readable.
- `portfolio/projects.json`: migrate this repository's one project to the reviewed v2 shape only as Issue 102 dogfood, after v1 parsing tests pass.
- `commands/product-projects.md`, `commands/product-portfolio.md`: document registry v2, resolution evidence, ambiguity, and explicit `--select` behavior.
- `tests/test_project_portfolio.py`, `tests/test_project_intake.py`, `tests/test_project_loop.py`, `tests/test_project_lifecycle.py`, `tests/test_project_doctor.py`, `tests/test_project_migration.py`, `tests/test_project_production.py`, `tests/test_project_memory.py`, `tests/test_mcp_server.py`, `tests/test_project_execution.py`, `tests/test_project_pr.py`, `tests/test_project_github_issues.py`, `tests/test_project_promote.py`, `tests/test_project_repository_identity.py`, `tests/test_issue_generator.py`, `tests/test_validation_distribution.py`: focused compatibility and nested-path regressions.
- `issues/102-project-registry-and-resolver.md`, `specs/102-project-registry-and-resolver/tasks.md`, `status.md`, `review.md`, `workspace/dashboard.md`, `workspace/roadmap.md`, `.moduflow/state.json`, `workspace/loop-state.json`: lifecycle, task, and evidence tracking.

## Stable Interfaces

### Registry v2 source schema

```json
{
  "schema": "moduflow.projects.v2",
  "projects": [
    {
      "id": "modu-charge",
      "name": "모두의충전",
      "root": "/configured/project/root",
      "aliases": ["모두의충전", "모두충전", "modu-charge"],
      "paths": {
        "issues": "projects/modu-charge/issues",
        "specs": "specs",
        "workspace": "workspace",
        "knowledge": "knowledge",
        "memory": "memory",
        "production_records": "memory/production-records",
        "playbooks": "playbooks",
        "workflow": "workflow"
      },
      "trust_scope": "internal",
      "status": "active",
      "owner": "Dongwon Lee"
    }
  ]
}
```

`root` may be absolute or relative to the registry directory. It is normalized to a canonical real path. `id`, normalized aliases, and path keys are deterministic; registry order never resolves a tie. `trust_scope` is a required non-empty lowercase slug, not a hard-coded organization policy enum.

### Normalized registry result

```python
{
    "schema": "moduflow.project-registry-read.v1",
    "valid": True,
    "source_schema": "moduflow.projects.v2",
    "registry_path": "/portfolio/projects.json",
    "projects": [
        {
            "id": "modu-charge",
            "name": "모두의충전",
            "root": "/configured/project/root",
            "aliases": ["modu-charge", "모두의충전", "모두충전"],
            "relative_paths": {"issues": "projects/modu-charge/issues"},
            "paths": {"issues": "/configured/project/root/projects/modu-charge/issues"},
            "trust_scope": "internal",
            "status": "active",
            "owner": "Dongwon Lee",
            "source_schema": "moduflow.projects.v2"
        }
    ],
    "diagnostics": [],
    "migration_proposal": None
}
```

Every diagnostic uses:

```python
{
    "code": "PROJECT_PATH_OUTSIDE_ROOT",
    "severity": "error",
    "project_id": "modu-charge",
    "field": "paths.issues",
    "current": "../other/issues",
    "message": "Configured project path escapes the canonical root.",
    "recommendation": "Use a project-relative path contained by the registered root."
}
```

### Public Python API

```python
def load_project_registry(registry_path):
    """Return moduflow.project-registry-read.v1; malformed input is diagnostics, not an exception."""

def resolve_loaded_registry(
    registry,
    *,
    explicit_project_id="",
    cwd=None,
    request_text="",
    active_project_id="",
    recent_selection=None,
):
    """Purely return moduflow.project-resolution.v1 from an already loaded registry."""

def resolve_project(
    registry_path,
    *,
    explicit_project_id="",
    cwd=None,
    request_text="",
    active_project_id="",
    recent_selection=None,
):
    """Load the registry, resolve one project, and materialize only the selected context."""

def project_context_for_root(project_root):
    """Return a resolved compatibility context for one explicitly supplied root."""

def canonical_path(project_context, key):
    """Return a contained pathlib.Path for one named canonical location."""

def load_recent_selection(registry_path):
    """Return {project_id, selected_at} or a warning-bearing empty selection."""

def record_recent_selection(registry_path, project_id, selected_at):
    """Atomically write project-selection.json after registry membership validation."""
```

### Resolution result

```python
{
    "schema": "moduflow.project-resolution.v1",
    "status": "resolved",
    "project_id": "modu-charge",
    "reason_code": "explicit_id",
    "candidates": [{"id": "modu-charge", "name": "모두의충전"}],
    "canonical_root": "/configured/project/root",
    "relative_paths": {"issues": "projects/modu-charge/issues"},
    "paths": {"issues": "/configured/project/root/projects/modu-charge/issues"},
    "trust_scope": "internal",
    "warnings": [],
    "question": ""
}
```

`ambiguous` and `unresolved` results keep `canonical_root`, `relative_paths`, `paths`, and `trust_scope` empty. Candidate entries expose only `id` and `name`.

### Compatibility rule for consumers

Each migrated public function keeps its current positional root and adds a keyword-only context where needed:

```python
def route_intake(root, request, write=False, *, project_context=None): ...
def sync_lifecycle(root, *, project_context=None): ...
def validate_production_project(project_root, *, project_context=None): ...
```

The first line inside each function is equivalent to:

```python
context = project_context or project_registry.project_context_for_root(root)
issues_dir = project_registry.canonical_path(context, "issues")
```

This keeps current direct callers working and lets future Issue 104 callers inject one already-resolved context without re-resolving or inspecting another project.

## Implementation Readiness Contracts

- **API contract mapping:** No HTTP API changes. Python functions and CLI JSON are local contracts. Existing `moduflow.mcp.v1`, portfolio status keys, and direct root arguments remain compatible; registry/resolution fields are additive.
- **Test strategy:** Unit tests prove registry parsing, precedence, containment, ambiguity, negative I/O, v1 migration guidance, and recent selection. Consumer contract tests prove identical nested-path behavior across read and write surfaces. Full release tests prove distribution and regression safety.
- **Storybook required states:** Not applicable. Issue 102 adds no frontend component.
- **MSW fixture baseline:** Not applicable. No browser/API-backed UI is added.
- **Playwright smoke matrix:** Not applicable. Dashboard markup and interaction are unchanged; project path input is covered by local HTML-generation `unittest` assertions.
- **Permission/role model:** `trust_scope` is metadata only in Issue 102. Resolution never grants external-write permission. `ambiguous`/`unresolved` fail closed for project-local reads and all writes.
- **Release/rollback:** Release requires focused suites, full `release_check.py`, project validation, lifecycle drift `[]`, and `git diff --check`. Rollback is commit-by-commit in reverse task order; registry dogfood is reverted before the v1 parser if rollback reaches Task B2.

---

### Stream A — Registry and Resolver Contract

#### Task A1: Lock the projects.v2 parser and path-containment boundary

**Files:**
- Create: `scripts/project_registry.py`
- Create: `tests/test_project_registry.py`
- Create: `tests/fixtures/project-registry/projects-v1.json`
- Create: `tests/fixtures/project-registry/projects-v2.json`
- Create: `tests/fixtures/project-registry/projects-v2-alias-collision.json`

**Interfaces:**
- Consumes: `project_issue_schema.configured_project_paths(project_root)` only in later context materialization, not during v2 candidate parsing.
- Produces: `load_project_registry()`, normalized registry/project/diagnostic shapes, `normalize_project_label()`, and canonical v2 path validation for Tasks A2–D1.

- [ ] **Step 1: Add fixed v1/v2/collision fixtures**

Use the exact v2 schema in “Stable Interfaces”. The main v2 fixture contains Project A with `issues/` and Project B with `projects/modu-charge/issues/`; add aliases `모두의충전` and `모두충전` only to Project B. The collision fixture gives both projects the alias `이벤트`.

- [ ] **Step 2: Write failing parser and containment tests**

Add `ProjectRegistryParsingTests` covering valid v2 normalization, relative roots, Unicode NFKC/casefold alias normalization, missing/unknown schema, duplicate IDs, non-list projects, empty IDs/names/trust scopes, unknown/missing path keys, absolute child paths, `..` escapes, and a symlink escaping the canonical root.

```python
registry = self.registry.load_project_registry(self.v2_path)
self.assertTrue(registry["valid"])
self.assertEqual(registry["projects"][1]["id"], "modu-charge")
self.assertEqual(
    registry["projects"][1]["relative_paths"]["issues"],
    "projects/modu-charge/issues",
)
self.assertTrue(
    registry["projects"][1]["paths"]["issues"].endswith(
        "/projects/modu-charge/issues"
    )
)
```

- [ ] **Step 3: Run the parser class and confirm RED**

Run:

```bash
python3 -m unittest tests.test_project_registry.ProjectRegistryParsingTests -v
```

Expected: import failure because `scripts/project_registry.py` does not exist.

- [ ] **Step 4: Implement the minimal registry reader**

Implement the constants and helpers:

```python
REGISTRY_READ_SCHEMA = "moduflow.project-registry-read.v1"
REGISTRY_V1 = "moduflow.projects.v1"
REGISTRY_V2 = "moduflow.projects.v2"
RESOLUTION_SCHEMA = "moduflow.project-resolution.v1"
CANONICAL_PATH_DEFAULTS = {
    "issues": "issues",
    "specs": "specs",
    "workspace": "workspace",
    "knowledge": "knowledge",
    "memory": "memory",
    "production_records": "memory/production-records",
    "playbooks": "playbooks",
    "workflow": "workflow",
}

def normalize_project_label(value):
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return " ".join(re.findall(r"[0-9a-z가-힣._-]+", normalized))
```

Validate v2 roots and child paths with `Path.resolve()` plus `relative_to(canonical_root)`. Return stable diagnostics instead of raising for malformed user data.

- [ ] **Step 5: Run the parser class and commit**

Run the Step 3 command. Expected: all parser tests pass.

```bash
git add scripts/project_registry.py tests/test_project_registry.py tests/fixtures/project-registry
git commit -m "feat(102): add project registry v2 parser"
```

#### Task A2: Implement deterministic resolution and fail-closed ambiguity

**Files:**
- Modify: `scripts/project_registry.py`
- Modify: `tests/test_project_registry.py`

**Interfaces:**
- Consumes: normalized `moduflow.project-registry-read.v1` from Task A1.
- Produces: `resolve_loaded_registry()` and `moduflow.project-resolution.v1`, consumed by Tasks B1–D1.

- [ ] **Step 1: Write failing precedence and ambiguity tests**

Add `ProjectResolutionTests` for explicit ID over conflicting CWD/alias, one containing CWD, Korean alias in request text, active project, recent selection, duplicate alias, no signal with multiple projects, invalid registry, missing root, and unregistered sibling directories.

```python
result = self.registry.resolve_loaded_registry(
    catalog,
    explicit_project_id="project-a",
    cwd=project_b_root,
    request_text="모두의충전 배너 수정",
)
self.assertEqual(result["status"], "resolved")
self.assertEqual(result["project_id"], "project-a")
self.assertEqual(result["reason_code"], "explicit_id")
self.assertIn("PROJECT_SIGNAL_CONFLICT", result["warnings"])
```

Assert ambiguous candidates contain exactly `id` and `name`; path/root/trust fields must be empty.

- [ ] **Step 2: Add the negative-I/O test and confirm RED**

Load the registry first, then patch project-local readers while resolving a collision:

```python
with mock.patch.object(Path, "read_text", side_effect=AssertionError("project read")):
    result = self.registry.resolve_loaded_registry(
        catalog,
        request_text="이벤트 배너",
    )
self.assertEqual(result["status"], "ambiguous")
self.assertEqual(result["paths"], {})
```

Run:

```bash
python3 -m unittest tests.test_project_registry.ProjectResolutionTests -v
```

Expected: attribute failures because resolver functions do not exist.

- [ ] **Step 3: Implement candidate extraction and fixed precedence**

Implement pure helpers that operate only on the normalized registry:

```python
def _project_label_matches(project, request_text): ...
def _cwd_matches(projects, cwd): ...
def _candidate_view(project): ...
def _resolved(project, reason_code, warnings=None): ...
def _ambiguous(projects, reason_code, question): ...
def _unresolved(reason_code, question, warnings=None): ...
```

Exact name/alias matching means a normalized registered phrase appears as a complete normalized phrase in the request. Equal matches remain ambiguous; registry order and recent selection never break that tie.

- [ ] **Step 4: Run resolver/parser tests and commit**

Run:

```bash
python3 -m unittest tests.test_project_registry.ProjectRegistryParsingTests tests.test_project_registry.ProjectResolutionTests -v
```

Expected: all tests pass.

```bash
git add scripts/project_registry.py tests/test_project_registry.py
git commit -m "feat(102): resolve registered projects deterministically"
```

### Stream B — Compatibility and Portfolio

#### Task B1: Add v1 compatibility, selected-context materialization, and recent selection

**Files:**
- Modify: `scripts/project_registry.py`
- Modify: `scripts/project_issue_schema.py`
- Modify: `tests/test_project_registry.py`
- Modify: `tests/test_project_issue_schema.py`

**Interfaces:**
- Consumes: Task A2 resolution and existing `configured_project_paths()`.
- Produces: `resolve_project()`, `project_context_for_root()`, `canonical_path()`, v1 migration proposals, and `load/record_recent_selection()` for portfolio and all consumers.

- [ ] **Step 1: Write failing v1/context/selection tests**

Add `ProjectContextCompatibilityTests` proving:

- v1 remains valid and returns `moduflow.projects-migration-proposal.v1` without rewriting the fixture;
- only the uniquely selected v1 project has `.moduflow/config.json` read;
- configured nested issues/specs/workspace paths merge with defaults for new path keys;
- explicit-root context returns the same canonical paths as current `configured_project_paths()`;
- `canonical_path()` rejects unresolved contexts and unknown keys;
- `project-selection.json` contains only `schema`, `project_id`, and `selected_at`;
- second identical selection write is byte-for-byte `noop`;
- malformed, unregistered, or invalid-time selection is ignored with a warning.

- [ ] **Step 2: Run the compatibility class and confirm RED**

```bash
python3 -m unittest tests.test_project_registry.ProjectContextCompatibilityTests -v
```

Expected: missing migration/context/selection helpers.

- [ ] **Step 3: Expand the existing project-local path map**

Add the five new keys to `project_issue_schema.DEFAULT_PROJECT_PATHS` without changing the existing three values:

```python
DEFAULT_PROJECT_PATHS = {
    "issues": "issues",
    "specs": "specs",
    "workspace": "workspace",
    "knowledge": "knowledge",
    "memory": "memory",
    "production_records": "memory/production-records",
    "playbooks": "playbooks",
    "workflow": "workflow",
}
```

Extend containment/path-violation tests so unsafe new-key config values report diagnostics rather than becoming canonical paths.

- [ ] **Step 4: Implement v1 materialization and selection state**

Use this high-level flow:

```python
def resolve_project(registry_path, **signals):
    registry = load_project_registry(registry_path)
    result = resolve_loaded_registry(registry, **signals)
    if result["status"] != "resolved":
        return result
    return _materialize_selected_context(result, registry)
```

For v1 only, `_materialize_selected_context` reads the selected root's project-local configured paths after unique resolution. Write selection through `<registry-parent>/project-selection.json.tmp` followed by `replace()`.

- [ ] **Step 5: Run registry/schema tests and commit**

```bash
python3 -m unittest tests.test_project_registry tests.test_project_issue_schema -v
```

Expected: all tests pass and existing Issue 093 path behavior remains green.

```bash
git add scripts/project_registry.py scripts/project_issue_schema.py tests/test_project_registry.py tests/test_project_issue_schema.py
git commit -m "feat(102): materialize compatible project contexts"
```

#### Task B2: Move the portfolio surface to registry v2 and explicit selection

**Files:**
- Modify: `scripts/project_portfolio.py`
- Modify: `tests/test_project_portfolio.py`
- Modify: `templates/portfolio/projects.json`
- Modify: `portfolio/projects.json`
- Modify: `commands/product-projects.md`
- Modify: `commands/product-portfolio.md`

**Interfaces:**
- Consumes: `load_project_registry()`, `resolve_project()`, `record_recent_selection()`, and `canonical_path()` from Task B1.
- Produces: v2-initialized portfolio files, resolver-aware status rows, and `--resolve/--select` CLI results used by future Issue 104 and Issue 086.

- [ ] **Step 1: Write failing portfolio compatibility tests**

Cover:

- new portfolio initialization emits `moduflow.projects.v2`;
- existing v1 registry is preserved and rendered through its normalized read model;
- v2 status collection reads only each registered root's state/workflow path;
- invalid/ambiguous registry entries become warnings without first-entry selection;
- `--resolve "모두의충전 배너"` prints one resolution object and writes nothing;
- `--select modu-charge` writes only `project-selection.json`;
- unknown `--select` returns a non-zero code and leaves files unchanged.

- [ ] **Step 2: Run portfolio tests and confirm RED**

```bash
python3 -m unittest tests.test_project_portfolio -v
```

Expected: v2/template/CLI assertions fail against the v1-only portfolio implementation.

- [ ] **Step 3: Implement registry-backed portfolio operations**

Add CLI options:

```python
operations.add_argument("--render", action="store_true")
operations.add_argument("--resolve")
operations.add_argument("--select")
```

`collect_project_statuses()` consumes normalized projects and derives workflow from `canonical_path(context, "workflow")`. Preserve current status/team/dashboard keys and add `registry_schema`, `resolution_status`, and `warnings` only.

- [ ] **Step 4: Dogfood this repository's registry**

Convert `portfolio/projects.json` to the exact v2 schema with the current ModuFlow root, aliases `["ModuFlow", "모두플로", "모두플로우"]`, default canonical paths, and `trust_scope: internal`. Do not create `project-selection.json` during dogfood.

- [ ] **Step 5: Run portfolio/registry tests and commit**

```bash
python3 -m unittest tests.test_project_registry tests.test_project_portfolio -v
```

Expected: all tests pass; v1 fixture bytes remain unchanged.

```bash
git add scripts/project_portfolio.py tests/test_project_portfolio.py templates/portfolio/projects.json portfolio/projects.json commands/product-projects.md commands/product-portfolio.md
git commit -m "feat(102): adopt registry v2 in portfolio workflows"
```

### Stream C — Consumer Convergence

#### Task C1: Converge intake, loop, lifecycle, Doctor, and migration on one context

**Files:**
- Modify: `scripts/project_intake.py`
- Modify: `scripts/project_loop.py`
- Modify: `scripts/project_lifecycle.py`
- Modify: `scripts/project_doctor.py`
- Modify: `scripts/project_migrate.py`
- Modify: `tests/test_project_intake.py`
- Modify: `tests/test_project_loop.py`
- Modify: `tests/test_project_lifecycle.py`
- Modify: `tests/test_project_doctor.py`
- Modify: `tests/test_project_migration.py`

**Interfaces:**
- Consumes: `project_context_for_root()`, `canonical_path()`, and `context["relative_paths"]` from Task B1.
- Produces: nested-path-compatible request routing, loop/lifecycle/dashboard state, Doctor diagnostics, and migration planning for Tasks C2–D1.

- [ ] **Step 1: Add the shared Project A/B nested-path fixture helper**

In each test module, use temporary projects with:

```python
paths = {
    "issues": "product/issues",
    "specs": "product/specs",
    "workspace": "product/workspace",
}
```

Project A contains issue `A-001`; Project B contains `B-001`; place a tempting `root/issues/WRONG.md` outside each configured issue path.

- [ ] **Step 2: Write failing consumer tests and reproduce the audit defect**

Assert:

```python
routed = intake.route_intake(root, "A-001 배너 수정")
self.assertEqual([item["issue_id"] for item in routed["related_issues"]], ["A-001"])
self.assertNotIn("WRONG", json.dumps(routed))
```

Add equivalent checks for configured `loop-state.json`, lifecycle dashboard sync, Doctor loop initialization, and migration planned workspace writes.

- [ ] **Step 3: Run the five focused modules and confirm RED**

```bash
python3 -m unittest tests.test_project_intake tests.test_project_loop tests.test_project_lifecycle tests.test_project_doctor tests.test_project_migration -v
```

Expected: intake, loop-state, lifecycle dashboard, and Doctor assertions fail on hard-coded paths.

- [ ] **Step 4: Add optional context plumbing and remove direct path reconstruction**

Use one compatibility pattern per public entry point:

```python
context = project_context or project_registry.project_context_for_root(root)
workspace_dir = project_registry.canonical_path(context, "workspace")
evaluation = evaluate_project(root, project_paths=context["relative_paths"])
```

Do not change lifecycle status precedence, Doctor severity, intake similarity thresholds, or migration write semantics in this issue.

- [ ] **Step 5: Run focused and schema parity tests and commit**

```bash
python3 -m unittest tests.test_project_intake tests.test_project_loop tests.test_project_lifecycle tests.test_project_doctor tests.test_project_migration tests.test_project_issue_schema -v
```

Expected: all tests pass; the R1 configured-path reproduction now returns `A-001`.

```bash
git add scripts/project_intake.py scripts/project_loop.py scripts/project_lifecycle.py scripts/project_doctor.py scripts/project_migrate.py tests/test_project_intake.py tests/test_project_loop.py tests/test_project_lifecycle.py tests/test_project_doctor.py tests/test_project_migration.py
git commit -m "fix(102): converge core workflows on canonical paths"
```

#### Task C2: Converge production, memory/dashboard, and MCP reads

**Files:**
- Modify: `scripts/project_production.py`
- Modify: `scripts/project_memory.py`
- Modify: `scripts/mcp_server.py`
- Modify: `tests/test_project_production.py`
- Modify: `tests/test_project_memory.py`
- Modify: `tests/test_mcp_server.py`

**Interfaces:**
- Consumes: resolved context/path helpers from Task B1 and normalized issue evaluation from Task C1.
- Produces: isolated production/memory/dashboard/MCP read models used by Issue 104, Issue 086, Issue 107, and Issue 108.

- [ ] **Step 1: Write failing production/memory/MCP isolation tests**

Configure non-default `issues`, `memory`, `production_records`, `playbooks`, and `workspace` paths. Put identically named decoy records in root defaults and assert only configured records appear.

```python
result = production.search_production(root, "banner")
self.assertEqual([item["id"] for item in result["items"]], ["configured-banner"])
self.assertNotIn("decoy-banner", json.dumps(result))
```

Assert Production Record issue references validate against configured issues, dashboard HTML contains only configured project records/issues, and MCP status/issues payloads retain existing keys.

- [ ] **Step 2: Run the three modules and confirm RED**

```bash
python3 -m unittest tests.test_project_production tests.test_project_memory tests.test_mcp_server -v
```

Expected: production and memory-path tests fail on default directories.

- [ ] **Step 3: Route all relevant entry points through canonical directories**

Make `list_production_records`, `list_playbooks`, `validate_production_project`, `build/apply_production_plan`, and `create_production_record` accept one optional context. Make memory initialization, candidate iteration, search, graph/dashboard generation, and issue/memory panels use canonical `memory`, `knowledge`, `workspace`, `issues`, and `specs` paths.

MCP loads one explicit-root context per request and passes it down; it does not add multi-project selection to the stdio protocol in Issue 102.

- [ ] **Step 4: Run read-model tests and commit**

```bash
python3 -m unittest tests.test_project_production tests.test_project_memory tests.test_mcp_server tests.test_project_issue_schema -v
```

Expected: all tests pass with no Project B/decoy content in Project A results.

```bash
git add scripts/project_production.py scripts/project_memory.py scripts/mcp_server.py tests/test_project_production.py tests/test_project_memory.py tests/test_mcp_server.py
git commit -m "fix(102): isolate production and dashboard read paths"
```

#### Task C3: Converge issue/spec writers and handoff surfaces

**Files:**
- Modify: `scripts/project_execution.py`
- Modify: `scripts/project_pr.py`
- Modify: `scripts/project_github_issues.py`
- Modify: `scripts/project_promote.py`
- Modify: `scripts/project_repository_identity.py`
- Modify: `scripts/issue_generator.py`
- Modify: `tests/test_project_execution.py`
- Modify: `tests/test_project_pr.py`
- Modify: `tests/test_project_github_issues.py`
- Modify: `tests/test_project_promote.py`
- Modify: `tests/test_project_repository_identity.py`
- Modify: `tests/test_issue_generator.py`

**Interfaces:**
- Consumes: explicit-root/resolved context helpers from Task B1.
- Produces: canonical issue/spec/workspace write locations for later transaction and orchestrator issues; existing output content and permission behavior stay unchanged.

- [ ] **Step 1: Write failing write-containment tests**

For each writer, configure `product/issues`, `product/specs`, and `product/workspace`; create decoy default directories and assert:

- readiness/review/PR artifacts write below configured specs;
- Korean issue descriptions read from configured workspace;
- GitHub issue link write-back touches only the configured issue;
- promotion/generator creates only under configured issues;
- repository identity audits configured issues/specs and ignores decoys.

- [ ] **Step 2: Run writer modules and confirm RED**

```bash
python3 -m unittest tests.test_project_execution tests.test_project_pr tests.test_project_github_issues tests.test_project_promote tests.test_project_repository_identity tests.test_issue_generator -v
```

Expected: nested-path assertions fail on direct `root/issues`, `root/specs`, or `root/workspace` construction.

- [ ] **Step 3: Inject the common context without broadening permissions**

Add keyword-only `project_context=None` parameters at top-level build/write functions and derive paths with `canonical_path()`. Preserve injected command runners in Git/GitHub functions, current repository identity gates, and every dry-run/write flag.

- [ ] **Step 4: Run writer and containment tests and commit**

```bash
python3 -m unittest tests.test_project_execution tests.test_project_pr tests.test_project_github_issues tests.test_project_promote tests.test_project_repository_identity tests.test_issue_generator tests.test_project_registry -v
```

Expected: all tests pass and no default/decoy file changes.

```bash
git add scripts/project_execution.py scripts/project_pr.py scripts/project_github_issues.py scripts/project_promote.py scripts/project_repository_identity.py scripts/issue_generator.py tests/test_project_execution.py tests/test_project_pr.py tests/test_project_github_issues.py tests/test_project_promote.py tests/test_project_repository_identity.py tests/test_issue_generator.py
git commit -m "fix(102): route issue writers through project context"
```

### Stream D — Distribution and Verification

#### Task D1: Package, document, dogfood, and prove convergence

**Files:**
- Modify: `scripts/validate_moduflow.py`
- Modify: `scripts/release_check.py`
- Modify: `tests/test_validation_distribution.py`
- Modify: `issues/102-project-registry-and-resolver.md`
- Modify: `specs/102-project-registry-and-resolver/tasks.md`
- Create: `specs/102-project-registry-and-resolver/status.md`
- Create after implementation review: `specs/102-project-registry-and-resolver/review.md`
- Modify: `workspace/dashboard.md`
- Modify: `workspace/roadmap.md`
- Modify: `.moduflow/state.json`
- Modify: `workspace/loop-state.json`

**Interfaces:**
- Consumes: every prior task's public contract and tests.
- Produces: distributable ModuFlow package evidence and the review handoff; no new runtime behavior.

- [ ] **Step 1: Write failing distribution checks**

Require the new registry module, test module, fixture directory, v2 portfolio template, and command documentation. Assert release_check includes `tests.test_project_registry`.

- [ ] **Step 2: Run distribution tests and confirm RED**

```bash
python3 -m unittest tests.test_validation_distribution -v
```

Expected: required-file/release-module assertions fail until manifests are updated.

- [ ] **Step 3: Update distribution manifests and status evidence**

Add the required paths/modules, then create `status.md` with task commits, focused test counts, v1/v2 fixtures, Project A/B isolation evidence, known warnings, and rollback order. Mark completed task boxes only after their evidence commands pass.

- [ ] **Step 4: Run spec/plan/task consistency**

```bash
python3 scripts/spec_consistency.py . --issue-id 102-project-registry-and-resolver
```

Expected: zero blocking errors; any heuristic warning is either fixed or recorded with concrete rationale in `status.md`.

- [ ] **Step 5: Run focused convergence suites**

```bash
python3 -m unittest \
  tests.test_project_registry \
  tests.test_project_issue_schema \
  tests.test_project_portfolio \
  tests.test_project_intake \
  tests.test_project_loop \
  tests.test_project_lifecycle \
  tests.test_project_doctor \
  tests.test_project_migration \
  tests.test_project_production \
  tests.test_project_memory \
  tests.test_mcp_server \
  tests.test_project_execution \
  tests.test_project_pr \
  tests.test_project_github_issues \
  tests.test_project_promote \
  tests.test_project_repository_identity \
  tests.test_issue_generator \
  tests.test_validation_distribution -v
```

Expected: all focused tests pass.

- [ ] **Step 6: Run full project gates**

```bash
python3 -m unittest discover -s tests
python3 scripts/validate_project_artifacts.py .
python3 scripts/project_lifecycle.py . --drift
python3 scripts/release_check.py .
git diff --check
```

Expected: full discovery passes; project validation and release check return `valid: true` with `errors: []`; lifecycle drift prints `[]`; diff check is clean.

- [ ] **Step 7: Perform the required self-review and handoff**

Verify all 13 Issue 102 acceptance criteria map to passing tests/status evidence, scan plan/runtime changes for duplicate registry/config parsers, confirm ambiguous/unresolved negative-I/O evidence, and confirm no file under unrelated `.playwright-mcp/` or PNG paths is staged.

- [ ] **Step 8: Commit convergence evidence**

```bash
git add scripts/validate_moduflow.py scripts/release_check.py tests/test_validation_distribution.py issues/102-project-registry-and-resolver.md specs/102-project-registry-and-resolver workspace/dashboard.md workspace/roadmap.md .moduflow/state.json workspace/loop-state.json
git commit -m "test(102): verify project resolver convergence"
```

## Plan Self-Review

- **Spec coverage:** Tasks A1/A2 cover AC 1–6 and 10–11; B1/B2 cover AC 2, 9, and 10; C1–C3 cover AC 7–8 and 13; D1 covers AC 11–12 and package/release evidence.
- **Scope fence:** No task implements natural-language orchestration, multi-file transactions, dashboard selector UI, shared-playbook search, schema migration apply, or artifact verification owned by Issues 103–108/086.
- **Parser ownership:** `project_registry.py` owns portfolio registry/resolution. `project_issue_schema.py` remains the project-local issue/config path owner. Consumers receive normalized outputs and do not parse either artifact independently.
- **Type consistency:** All consumers receive the same `moduflow.project-resolution.v1` context with `relative_paths` strings and absolute `paths` strings; `canonical_path()` is the only Path conversion at consumer boundaries.
- **Placeholder scan:** The plan contains exact files, signatures, schemas, test classes, commands, and expected results; no deferred implementation marker is used.

## Execution Handoff

Plan artifacts are complete when `spec_consistency.py` and the current release gate pass. Implementation must still be explicitly started with `product:execute 102-project-registry-and-resolver`; creating this plan does not authorize code changes.
