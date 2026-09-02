# Issue 103 D1c Distribution, Release, and Guarantees Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and superpowers:test-driven-development inline. Do not use subagents.

**Goal:** Prevent lifecycle transaction code/tests from disappearing from a ModuFlow distribution or release run, and document the exact local atomicity and remote-after-local boundary.

**Architecture:** Extend the existing package manifest and non-recursive release test list; do not introduce a new validator or execution layer. Add one distribution contract that checks packaged runtime files, source-only test assets, release-suite registration, and the required architecture/workflow guarantees. Keep version bump, full discovery, live source release validation, review evidence, and PR publication in D2.

**Tech Stack:** Python lists and `unittest`, existing package/release validators, Markdown architecture/workflow docs.

## Global Constraints

- Work only in the existing Issue 103 worktree and preserve every existing untracked plan file.
- Runtime transaction modules and public adapters are packaged; test modules and fixtures are source-checkout-only.
- `tests.test_validation_distribution` remains excluded from `release_check.py` to prevent recursive release-check execution.
- Release registration must cover Doctor, lifecycle adapter, transaction engine, storage, loop adapter, and Production Record adapter suites.
- Document local project-filesystem atomicity only. Git commits, pushes, GitHub changes, messages, deployments, and other remote effects are outside the transaction.
- Remote publication or deployment starts only after a local `applied` or semantically identical `noop` result plus its existing review/release/human gates.
- A remote failure never causes the local transaction engine to guess or roll back an already completed local mutation; it is recorded/retried by the owning remote workflow.
- Do not bump the package version, run full discovery/source release validation, create review evidence, publish a PR, merge, push, or clean the worktree in D1c.

---

### Task 1: RED distribution and release-suite contract

**Files:**
- Modify: `tests/test_validation_distribution.py`
- Test: `scripts/validate_moduflow.py`
- Test: `scripts/release_check.py`

**Interfaces:**
- Consumes: `validate_moduflow.REQUIRED_FILES`, `SOURCE_ONLY_REQUIRED_FILES`, and the static release test command.
- Produces: one failing current-repository contract for all Issue 103 runtime/source/release registrations.

- [ ] **Step 1: Add `test_distribution_ships_lifecycle_transaction_and_release_suites`**

Assert these packaged runtime files are in `REQUIRED_FILES` and exist:

```python
packaged = {
    "scripts/project_doctor.py",
    "scripts/project_lifecycle.py",
    "scripts/project_lifecycle_transaction.py",
    "scripts/project_lifecycle_transaction_storage.py",
    "scripts/project_loop.py",
    "scripts/project_production.py",
}
```

Assert these source-only assets are in both `REQUIRED_FILES` and `SOURCE_ONLY_REQUIRED_FILES` and exist:

```python
source_only = {
    "tests/lifecycle_transaction_fixture.py",
    "tests/test_project_doctor.py",
    "tests/test_project_lifecycle.py",
    "tests/test_project_lifecycle_transaction.py",
    "tests/test_project_lifecycle_transaction_storage.py",
    "tests/test_project_loop.py",
    "tests/test_project_production.py",
}
```

Read `scripts/release_check.py` and assert it contains each corresponding `tests.test_*` module while still containing the comment and exclusion for `test_validation_distribution`.

- [ ] **Step 2: Run the new test and verify RED**

```bash
python3 -m unittest -v \
  tests.test_validation_distribution.ValidationDistributionTests.test_distribution_ships_lifecycle_transaction_and_release_suites
```

Expected: failure because the transaction runtime/source assets and focused suites are not yet completely registered.

---

### Task 2: Register packaged files and non-recursive focused suites

**Files:**
- Modify: `scripts/validate_moduflow.py`
- Modify: `scripts/release_check.py`
- Test: `tests/test_validation_distribution.py`

**Interfaces:**
- Consumes: Task 1 exact file/module sets.
- Produces: package-presence enforcement and one non-recursive release test command.

- [ ] **Step 1: Add runtime and source-only files to the package validator**

Add the six runtime files to `REQUIRED_FILES`. Add the seven source assets to `REQUIRED_FILES`, and also add the same seven to `SOURCE_ONLY_REQUIRED_FILES` so installed plugin validation does not require source tests.

- [ ] **Step 2: Add focused suites to the release command**

Register these modules before `tests.test_release_check`:

```python
"tests.test_project_doctor",
"tests.test_project_lifecycle",
"tests.test_project_lifecycle_transaction",
"tests.test_project_lifecycle_transaction_storage",
"tests.test_project_loop",
"tests.test_project_production",
```

Do not add `tests.test_validation_distribution`.

- [ ] **Step 3: Run the registration contract GREEN**

```bash
python3 -m unittest -v \
  tests.test_validation_distribution.ValidationDistributionTests.test_distribution_ships_lifecycle_transaction_and_release_suites \
  tests.test_validation_distribution.ValidationDistributionTests.test_validate_moduflow_exposes_importable_api
python3 -m py_compile scripts/validate_moduflow.py scripts/release_check.py
```

Expected: both tests and compilation pass.

- [ ] **Step 4: Commit the executable gate**

```bash
git add \
  scripts/validate_moduflow.py \
  scripts/release_check.py \
  tests/test_validation_distribution.py
git commit -m "test(103): register transaction release gates"
```

---

### Task 3: RED documentation guarantee contract and minimal docs

**Files:**
- Modify: `tests/test_validation_distribution.py`
- Modify: `docs/architecture.md`
- Modify: `docs/workflow.md`

**Interfaces:**
- Consumes: Issue 103 terminal statuses, Doctor recovery command, and existing publication gates.
- Produces: user-facing local/remote boundary text protected by a distribution test.

- [ ] **Step 1: Add `test_lifecycle_transaction_docs_define_local_and_remote_boundaries`**

Read both Markdown files, lowercase them, and assert the combined contract contains:

- `local project filesystem` and `same filesystem`;
- `applied`, `noop`, `denied`, `conflict`, `rolled_back`, and `recovery_required`;
- a statement that Git commit/push, GitHub, deployment, and external messages are outside the transaction;
- `remote-after-local` and a statement that remote work begins only after local `applied` or `noop` plus existing gates;
- the exact recovery command shape `python3 scripts/project_lifecycle.py <root> --recover <transaction-id>`;
- a statement that ambiguous recovery evidence is preserved rather than guessed or manually deleted.

- [ ] **Step 2: Run the documentation contract and verify RED**

```bash
python3 -m unittest -v \
  tests.test_validation_distribution.ValidationDistributionTests.test_lifecycle_transaction_docs_define_local_and_remote_boundaries
```

Expected: failure because architecture/workflow do not yet describe the lifecycle transaction boundary.

- [ ] **Step 3: Add the architecture guarantee section**

Document:

- pure planning and projected validation before private apply;
- write authorization before any transaction lock/journal/staging/temp/evidence mutation;
- same-project-filesystem private staging, fsynced journal state, optimistic hash recheck, deterministic replacement, post-apply validation, and reverse rollback;
- redacted evidence and the six exact public statuses;
- local project-filesystem scope and remote exclusions;
- read-only Doctor diagnosis and preserved `recovery_required` evidence.

- [ ] **Step 4: Add the workflow sequence and remote-after-local rule**

Document the operational sequence:

```text
plan -> authorize -> recover barrier -> re-plan/projected validate
-> lock + hash/semantic recheck -> journaled local apply
-> post-apply validation -> applied/noop or rollback/recovery_required
-> existing review/release/human gates -> remote publication/deployment
```

State that remote failure is handled by that remote workflow and does not cause speculative local rollback.

- [ ] **Step 5: Run documentation GREEN**

```bash
python3 -m unittest -v \
  tests.test_validation_distribution.ValidationDistributionTests.test_lifecycle_transaction_docs_define_local_and_remote_boundaries
```

Expected: pass.

---

### Task 4: Focused verification, tracking, and commits

**Files:**
- Modify: `specs/103-atomic-lifecycle-state-transaction/plan.md`
- Modify: `specs/103-atomic-lifecycle-state-transaction/tasks.md`
- Modify: `docs/superpowers/plans/2026-09-02-issue-103-d1c-distribution-release-guarantees.md`

**Interfaces:**
- Consumes: Tasks 1-3.
- Produces: completed D1/D1c evidence with D2 active.

- [ ] **Step 1: Run focused D1c verification**

```bash
python3 -m unittest -v \
  tests.test_validation_distribution.ValidationDistributionTests.test_distribution_ships_lifecycle_transaction_and_release_suites \
  tests.test_validation_distribution.ValidationDistributionTests.test_lifecycle_transaction_docs_define_local_and_remote_boundaries \
  tests.test_validation_distribution.ValidationDistributionTests.test_validate_moduflow_exposes_importable_api \
  tests.test_project_doctor \
  tests.test_project_lifecycle \
  tests.test_project_lifecycle_transaction \
  tests.test_project_lifecycle_transaction_storage \
  tests.test_project_loop \
  tests.test_project_production
python3 -m py_compile \
  scripts/validate_moduflow.py \
  scripts/release_check.py \
  scripts/project_lifecycle_transaction.py \
  scripts/project_lifecycle_transaction_storage.py
python3 scripts/project_operation_audit.py .
python3 scripts/canonical_path_guard.py .
git diff --check
```

Expected: all focused tests/static checks pass and both audits remain zero-gap. Do not run or claim the D2 full discovery, version gate, or source release result.

- [ ] **Step 2: Commit docs and tracking**

Mark D1c and aggregate D1 complete, make D2 active, record fresh test counts, and commit:

```bash
git add \
  docs/architecture.md \
  docs/workflow.md \
  specs/103-atomic-lifecycle-state-transaction/plan.md \
  specs/103-atomic-lifecycle-state-transaction/tasks.md \
  docs/superpowers/plans/2026-09-02-issue-103-d1c-distribution-release-guarantees.md
git commit -m "docs(103): define transaction release guarantees"
```

## Completion Gate

- [ ] Installed/source package validation cannot omit required transaction runtime or source-test assets.
- [ ] The non-recursive release suite runs Doctor, transaction, storage, lifecycle, loop, and production coverage.
- [ ] Architecture/workflow docs state local-only atomicity, exact terminal/recovery behavior, and remote-after-local sequencing.
- [ ] D1 is complete; D2 full verification, version/release gate, review evidence, PR publication, merge, and cleanup remain open.
