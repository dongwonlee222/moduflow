# Canonical Project Context Consumer Convergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every production target-project path consumer use one validated resolved project context, including nested layouts, generated links, and Git history pathspecs.

**Architecture:** Extend `project_registry.py` with context/root validation and contained child/relative helpers, then inject the same context through each public consumer boundary. Preserve low-level parsers and stronger Spec Kit containment rules, and add a behavior-backed repository path-literal classifier so legitimate fixed layouts remain explicit without masking runtime consumers.

**Tech Stack:** Python 3 standard library, `pathlib`, `unittest`, JSON/Markdown Git artifacts, existing ModuFlow resolver and issue-schema APIs.

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

- A supplied `project_context` is authoritative. Only literal `None` may call `project_context_for_root()`; truthiness fallback is forbidden.
- Every supplied context must be resolved and bound to the same canonical root as the positional root before target-project filesystem I/O.
- `canonical_path()` remains the role-root authority. Child and project-relative paths must use `canonical_child_path()` and `canonical_relative_path()`.
- `project_issue_schema.py` remains the only normalized issue/configured-path layer and must not import `project_registry.py`.
- Spec Kit must retain its no-follow, regular-file, and atomic-write protections after canonical roots are injected.
- Issue 109 does not add operation capabilities, lifecycle transactions, folder migration, or source-package validation modes.
- Default-layout positional callers and existing output schemas remain compatible; new `project_context` parameters are keyword-only.
- Every behavior change follows RED/GREEN TDD with focused `unittest` evidence before production edits.
- Decoy default folders must remain byte-identical in nested-layout mutating tests.
- The user requested GitHub publication only after Issue 109 implementation, review, and full verification; no early remote branch or Draft PR is created.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — canonical context boundary | Superpowers TDD | Context validation, containment, and relative path behavior require RED/GREEN contract proof. |
| B — filesystem consumers | Superpowers TDD + ModuFlow Git-native artifact model | Reads, writes, and generated artifact paths must agree across nested/default layouts. |
| C — adapters and Git history | Superpowers TDD | Spec Kit and historical pathspecs have stricter failure and containment cases. |
| D — regression classification | Superpowers TDD | Static findings must be classified without replacing behavior tests. |
| E — completion | verification-before-completion + ModuFlow review | Completion requires focused suites, release gates, review artifacts, and clean Git evidence. |

## File Structure

### Create

- `scripts/canonical_path_guard.py`: scan production Python path construction and compare findings with reviewed classifications.
- `config/canonical-path-literals.json`: machine-readable approved literal classifications with module, pattern, class, and rationale.
- `tests/test_canonical_path_guard.py`: guard behavior, unclassified-hit, stale-entry, and prohibited-runtime-exception tests.
- `tests/project_context_fixture.py`: reusable default Project A / nested Project B / poisoned-default fixture and context builders.
- `specs/109-canonical-project-context-consumer-convergence/status.md`: execution and verification evidence.
- `specs/109-canonical-project-context-consumer-convergence/review.md`: post-implementation spec-compliance review.
- `specs/109-canonical-project-context-consumer-convergence/review-handoff.md`: generated execution-to-review handoff.

### Modify

- `scripts/project_registry.py`, `tests/test_project_registry.py`: root/context binding, contained child paths, and canonical relative POSIX paths.
- `scripts/project_knowledge.py`, `tests/test_project_knowledge.py`: knowledge initialization and artifact creation.
- `scripts/project_workflow.py`, `tests/test_project_workflow.py`: workflow state, records, review checks, and generated issue/spec/memory links.
- `scripts/validate_project_artifacts.py`, `tests/test_validation_distribution.py`: validation of workspace, workflow, memory, issues, specs, and knowledge through one context.
- `scripts/project_review.py`, `tests/test_project_review.py`: review packets, candidate queue, overlap reads, and decision application.
- `scripts/project_converge.py`, `tests/test_project_converge.py`: spec/plan/tasks/evidence/judgment/result paths.
- `scripts/worker_orchestrator.py`, `tests/test_worker_orchestration.py`: task files, worker plans, and related memory lookup.
- `scripts/spec_consistency.py`, `tests/test_spec_consistency.py`: spec/plan/tasks analysis under canonical specs.
- `scripts/project_reference_backlog.py`, `tests/test_project_reference_backlog.py`: canonical workspace backlog and actual canonical origin-spec links.
- `scripts/project_memory.py`, `tests/test_project_memory.py`: dashboard/drill-down issue, spec, workspace, and memory path propagation.
- `scripts/spec_kit_adapter.py`, `tests/test_spec_kit_adapter.py`: canonical issue/spec/workspace inputs and outputs while preserving no-follow protections.
- `scripts/project_sync.py`, `tests/test_project_sync.py`: configured issue prefixes for local/remote Git tree queries and status reads.
- `scripts/commit_resolution.py`, `tests/test_commit_resolution.py`, `tests/test_commit_resolution_parity.py`: configured issue prefixes for historical registration and attribution.
- `scripts/validate_moduflow.py`, `scripts/release_check.py`: require and exercise the guard and new focused tests.
- `issues/109-canonical-project-context-consumer-convergence.md`, `workspace/dashboard.md`, `workspace/roadmap.md`, `.moduflow/state.json`, `workspace/loop-state.json`: lifecycle and evidence tracking.

## Stable Interfaces

```python
def context_for_operation(project_root, *, project_context=None):
    """Return a resolved context bound to project_root; reject supplied invalid/mismatched contexts."""

def canonical_child_path(project_context, role, *parts):
    """Return a contained child below role root; reject empty, absolute, '.', '..', and escape components."""

def canonical_relative_path(project_context, role, *parts):
    """Return the canonical child as a project-root-relative POSIX path string."""
```

Public consumer functions keep positional parameters and add `*, project_context=None`. Internal functions receive the validated context or already-derived canonical paths; they never re-resolve it.

## Implementation Readiness Contracts

- **API contract mapping:** No HTTP API. Existing Python positional calls and CLI JSON keys remain; keyword-only `project_context` is additive. Git helpers add an optional canonical issue-prefix input with the default produced at the public root boundary.
- **Test strategy:** Registry tests prove validation/containment. Consumer tests prove default/nested parity, poisoned-default isolation, returned/generated paths, and zero I/O for invalid contexts. Git FakeRunner tests prove exact pathspecs. Guard tests prove classifications are complete and not stale.
- **Storybook required states:** Not applicable; no frontend UI changes.
- **MSW fixture baseline:** Not applicable; no browser/API-backed UI.
- **Playwright smoke matrix:** Not applicable; generated dashboard interaction is unchanged.
- **Permission/role model:** Not applicable to Issue 109; Issue 110 owns read/write/execute/publish enforcement.
- **Release/rollback:** Release requires focused suites, `unittest` discovery, valid project artifacts, lifecycle drift `[]`, guard success, `git diff --check`, and full release check. Rollback is commit-by-commit in reverse task order, with consumer commits reverted before the shared helper commit.

---

### Stream A — Shared Boundary and Regression Guard

### Task A1: Canonical context operation boundary

**Files:**
- Modify: `scripts/project_registry.py`
- Modify: `tests/test_project_registry.py`

**Interfaces:**
- Produces: `context_for_operation()`, `canonical_child_path()`, `canonical_relative_path()` for all later tasks.
- Preserves: `canonical_path()` and `project_context_for_root()` output schemas.

- [ ] Write focused tests where malformed, unresolved, empty, and Project-A-context/Project-B-root inputs raise before a patched filesystem probe is called.
- [ ] Run `python3 -m unittest tests.test_project_registry -v` and confirm the new tests fail because the three interfaces do not exist.
- [ ] Implement strict `is None` compatibility, canonical root equality, component validation, role/project containment, and POSIX relative output.
- [ ] Re-run the focused suite and confirm all registry tests pass.
- [ ] Commit only the registry implementation and tests with `feat(109): add canonical context operation boundary`.

### Task A2: Repository path-literal classification guard

**Files:**
- Create: `scripts/canonical_path_guard.py`
- Create: `config/canonical-path-literals.json`
- Create: `tests/test_canonical_path_guard.py`
- Modify: `scripts/validate_moduflow.py`
- Modify: `scripts/release_check.py`

**Interfaces:**
- Consumes: production `scripts/*.py` and the reviewed classification JSON.
- Produces: `moduflow.canonical-path-guard.v1` with `valid`, `findings`, `stale_entries`, and classification counts.

- [ ] Write tests using temporary scripts that prove an unclassified `root / "issues"` hit fails, an unused classification is stale, and a reviewed default declaration passes.
- [ ] Run `python3 -m unittest tests.test_canonical_path_guard -v` and confirm RED because the guard is absent.
- [ ] Implement an AST scanner for `Path` joins and string path fragments, exact module/pattern/class matching, approved class validation, and JSON CLI output.
- [ ] Seed classifications only for canonical defaults, canonical-role suffixes, `.moduflow`, package/distribution layout, and test fixtures; runtime target-project I/O cannot use an exception class.
- [ ] Add distribution and release requirements, then run the focused guard and validation distribution suites to GREEN.
- [ ] Commit with `test(109): guard canonical project path consumers`.

### Stream B — Filesystem Consumer Convergence

### Task B1: Knowledge, workflow, and project validation consumers

**Files:**
- Modify: `scripts/project_knowledge.py`, `tests/test_project_knowledge.py`
- Modify: `scripts/project_workflow.py`, `tests/test_project_workflow.py`
- Modify: `scripts/validate_project_artifacts.py`, `tests/test_validation_distribution.py`
- Create/Modify: `tests/project_context_fixture.py`

**Interfaces:**
- Consumes: Task A1 helpers and one context per public call.
- Produces: canonical knowledge/workflow writes and one-context project validation.

- [ ] Add reusable Project A/B fixtures with all eight nested roles and conflicting default knowledge/workflow/issues/specs/workspace/memory files.
- [ ] Add failing nested-path tests for knowledge plan/apply/artifact creation, team state/records/review inputs/release memory links, and validation loop/memory/workflow/issue checks.
- [ ] Run the three focused suites and confirm failures point to default-folder reads or writes.
- [ ] Add keyword-only context boundaries, derive role roots/children once, and pass canonical relative links to generated records and memory candidates.
- [ ] Re-run focused suites and assert every poisoned default file remains byte-identical.
- [ ] Commit with `feat(109): converge knowledge workflow and validation paths`.

### Task B2: Review, converge, worker, consistency, and reference backlog consumers

**Files:**
- Modify: `scripts/project_review.py`, `tests/test_project_review.py`
- Modify: `scripts/project_converge.py`, `tests/test_project_converge.py`
- Modify: `scripts/worker_orchestrator.py`, `tests/test_worker_orchestration.py`
- Modify: `scripts/spec_consistency.py`, `tests/test_spec_consistency.py`
- Modify: `scripts/project_reference_backlog.py`, `tests/test_project_reference_backlog.py`

**Interfaces:**
- Consumes: Task A1 helpers and canonical specs/workspace/memory roots.
- Produces: context-safe review packets, convergence evidence, worker plans, consistency findings, and backlog links.

- [ ] Add failing Project B tests for each public read/write path and exact returned project-relative paths.
- [ ] Add invalid/mismatched context tests that patch file open/stat/write and assert zero target-project calls.
- [ ] Run the five focused suites and confirm RED on default `specs/` or `workspace/` assumptions.
- [ ] Propagate the same context through internal helpers, related-memory lookup, Git evidence outputs, and generated `origin_spec` metadata.
- [ ] Re-run focused suites and confirm nested paths are used exclusively.
- [ ] Commit with `feat(109): converge planning and review artifact paths`.

### Stream C — Adapter and Git History Convergence

### Task C1: Memory dashboard and Spec Kit adapter

**Files:**
- Modify: `scripts/project_memory.py`, `tests/test_project_memory.py`
- Modify: `scripts/spec_kit_adapter.py`, `tests/test_spec_kit_adapter.py`

**Interfaces:**
- Consumes: Task A1 helpers; Spec Kit retains its existing `_project_path` no-follow checks below canonical role roots.
- Produces: context-propagated dashboard/drill-down artifacts and canonical Spec Kit handoff/persistence paths.

- [ ] Add failing Project B dashboard, issue-panel, memory-link, Spec Kit input, validation-output, and decoy-default tests.
- [ ] Add failure tests for symlinked canonical inputs/outputs and verify existing error codes remain unchanged.
- [ ] Run both focused suites and confirm RED for nested paths while current no-follow tests remain green.
- [ ] Thread one context through dashboard/drill-down helpers; change Spec Kit logical inputs to role-plus-relative parts before applying the stronger safe-path layer.
- [ ] Re-run focused suites and confirm nested behavior plus no-follow protections pass.
- [ ] Commit with `feat(109): converge memory and spec kit paths`.

### Task C2: Git history and synchronization consumers

**Files:**
- Modify: `scripts/project_sync.py`, `tests/test_project_sync.py`
- Modify: `scripts/commit_resolution.py`, `tests/test_commit_resolution.py`, `tests/test_commit_resolution_parity.py`

**Interfaces:**
- Consumes: `canonical_relative_path(context, "issues")` at the public root boundary.
- Produces: Git `ls-tree`, `ls-files`, `show`, and historical registration queries scoped to the configured issue prefix.

- [ ] Add FakeRunner tests with `product/issues` and conflicting `issues` entries; assert exact command pathspecs and issue IDs.
- [ ] Add a revision-without-configured-prefix test that returns no registered issues and never falls back to `issues/`.
- [ ] Run focused sync/resolution suites and confirm RED on literal pathspecs.
- [ ] Pass the canonical issue prefix through branch discovery, status lookup, attribution, and parity paths without inferring historical registry changes.
- [ ] Re-run focused and differential/parity suites to GREEN.
- [ ] Commit with `feat(109): scope git history to canonical issue paths`.

### Stream D — Verification and Publication

### Task D1: Full convergence, lifecycle evidence, and review

**Files:**
- Modify: all Issue 109 lifecycle artifacts listed above.
- Create: `specs/109-canonical-project-context-consumer-convergence/status.md`
- Create: `specs/109-canonical-project-context-consumer-convergence/review.md`
- Generate: `specs/109-canonical-project-context-consumer-convergence/review-handoff.md`

**Interfaces:**
- Consumes: all prior task commits and the twelve acceptance criteria in `spec.md`.
- Produces: auditable completion evidence and a PR-ready branch; no release or merge.

- [ ] Run the canonical guard and classify every production hit; migrate any runtime consumer rather than allowlisting it.
- [ ] Run all focused suites, `python3 -m unittest discover -s tests`, project validation, spec consistency, lifecycle drift, and `git diff --check`.
- [ ] Run `python3 scripts/project_execution.py . --issue-id 109-canonical-project-context-consumer-convergence --review-handoff --write`.
- [ ] Review each acceptance criterion against tests and diff, record findings in `review.md`, and fix any P0/P1/P2 defect through a new RED/GREEN cycle.
- [ ] Run `python3 scripts/release_check.py .` fresh, update issue/tasks/status/dashboard/roadmap/state, and commit with `docs(109): complete canonical context convergence review`.
- [ ] Push the completed branch and open one non-draft GitHub PR against `main`, because the user explicitly requested publication after Issue 109 completion.
