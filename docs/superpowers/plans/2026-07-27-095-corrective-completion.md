# Issue 095 Corrective Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close Issue 095 with stable, fail-closed commit attribution and zero expected failures.

**Architecture:** `scripts/commit_resolution.py` remains the single attribution engine. It discovers registered issues from Git history, selects only a non-issue base, applies precedence globally to content commits, permits multi-attribution only for merge boundaries, and propagates Git graph failures. Both existing consumers continue to delegate to this index.

**Tech Stack:** Python 3 standard library, `unittest`, temporary Git repositories, Git-native ModuFlow artifacts.

---

## File Map

- Modify `scripts/commit_resolution.py`: issue registry, base selection, graph
  error propagation, global source precedence, nested merge attribution.
- Modify `tests/commit_resolution_shapes.py`: explicit corrective fixtures.
- Modify `tests/test_commit_resolution.py`: focused fail-closed and registry
  tests.
- Modify `tests/test_commit_resolution_differential.py`: turn R9 findings into
  ordinary tests and require zero expected failures.
- Modify `tests/test_linkage_check.py`: reject unregistered trailer and branch
  linkage.
- Modify `issues/095-commit-issue-resolution-parity.md`: canonical refined AC
  and corrective history.
- Modify `specs/095-commit-issue-resolution-parity/{spec,tasks,status,pr,human-review.ko}.md`:
  align requirements, evidence, and review state.
- Modify `.moduflow/state.json`, `workspace/loop-state.json`, and
  `workspace/dashboard.md`: project the active corrective phase.

### Task 1: Fail-closed repository and issue discovery

**Files:**
- Modify: `scripts/commit_resolution.py`
- Modify: `tests/test_commit_resolution.py`
- Modify: `tests/test_linkage_check.py`

- [ ] **Step 1: Write failing registry tests**

Add tests proving that issue discovery reads historical `issues/*.md` paths
independently of checkout, and that a trailer or branch naming
`999-not-a-real-issue` does not satisfy the linkage gate.

```python
def test_checkout_does_not_change_known_issue_ids(self):
    on_issue_branch = cr.known_issue_ids(repo.runner, repo.path, [])
    repo.checkout("main")
    on_main = cr.known_issue_ids(repo.runner, repo.path, [])
    self.assertEqual(on_main, on_issue_branch)

def test_unknown_trailer_does_not_satisfy_linkage(self):
    result = linkage_check.find_unlinked_behavior_commits(
        repo.runner, repo.path, base, head
    )
    self.assertFalse(result["ok"])
    self.assertIsNone(result["commits"][0]["issue_id"])
```

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_commit_resolution tests.test_linkage_check -v
```

Expected: checkout-independence and unknown-issue assertions fail.

- [ ] **Step 3: Implement historical issue discovery**

Replace index-only discovery with one injected Git query over issue paths in
all history. Accept only names matching `ISSUE_ID_PATTERN`. Empty repositories
return an empty registry without an error; every other Git failure is appended
to `errors`. Apply the registry check to trailer, branch, and merge-subject
claims.

- [ ] **Step 4: Add failing graph-error tests**

Inject return code `128` for `git merge-base --is-ancestor` and `git rev-list`.
Assert that `errors` is non-empty, `degraded` contains
`branch-unavailable`, and the affected branch contributes no commits.

- [ ] **Step 5: Implement graph error propagation**

Change base and membership helpers to receive the shared `errors` list.
Distinguish return code `1` (“not an ancestor”) from all other nonzero results.
Do not score or attribute a branch after a failed graph query.

- [ ] **Step 6: Verify GREEN**

Run the command from Step 2. Expected: all tests pass with no expected
failures in these modules.

- [ ] **Step 7: Commit**

```bash
git add scripts/commit_resolution.py tests/test_commit_resolution.py \
  tests/test_linkage_check.py
git commit -m "fix(095): fail closed on commit attribution inputs"
```

### Task 2: Global precedence and nested merge isolation

**Files:**
- Modify: `scripts/commit_resolution.py`
- Modify: `tests/commit_resolution_shapes.py`
- Modify: `tests/test_commit_resolution_differential.py`

- [ ] **Step 1: Remove expected-failure masking**

Delete `OPEN_FINDINGS` and `_mark_open_findings()`. Keep all generated shape
tests as ordinary tests.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_commit_resolution_differential -v
```

Expected: R9-1, R9-2, and R9-3 fail as ordinary failures.

- [ ] **Step 3: Make base selection exclude issue branches**

Pass the registered issue set into base selection. Prefer
`origin/HEAD`; otherwise deduplicate local/remote counterparts and select only
from non-issue branches. Prefer the remote counterpart when it is ahead of the
local branch. A repository with issue branches but no usable non-issue base is
degraded.

- [ ] **Step 4: Apply precedence once**

Use one `claim()` policy for both directions:

```python
def claim(sha, issue_id, source):
    current = attribution.get(sha, {})
    if records[sha]["parents"] and len(records[sha]["parents"]) >= 2:
        claim_merge_boundary(current, issue_id, source)
    else:
        claim_single_owner(current, issue_id, source, SOURCE_PRECEDENCE)
```

For content commits, a stronger source replaces weaker claims and an equal
source keeps the earlier inner-branch owner. For merge commits, retain
per-issue claims but still apply precedence within each issue.

- [ ] **Step 5: Process nested merges inner-first**

Walk merge records oldest-first before live-branch claims. This lets the inner
issue claim its content before an outer merge examines the same ancestry.

- [ ] **Step 6: Verify GREEN**

Run the differential suite from Step 2. Expected: 50 tests pass, zero
failures, zero expected failures.

- [ ] **Step 7: Run consumer parity tests**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_commit_resolution tests.test_commit_resolution_differential \
  tests.test_commit_resolution_parity tests.test_linkage_check \
  tests.test_project_converge -v
```

Expected: all tests pass, zero expected failures.

- [ ] **Step 8: Commit**

```bash
git add scripts/commit_resolution.py tests/commit_resolution_shapes.py \
  tests/test_commit_resolution_differential.py
git commit -m "fix(095): make commit attribution globally consistent"
```

### Task 3: Reconcile Issue 095 artifacts

**Files:**
- Modify: `issues/095-commit-issue-resolution-parity.md`
- Modify: `specs/095-commit-issue-resolution-parity/spec.md`
- Modify: `specs/095-commit-issue-resolution-parity/tasks.md`
- Modify: `specs/095-commit-issue-resolution-parity/status.md`
- Modify: `specs/095-commit-issue-resolution-parity/pr.md`
- Modify: `specs/095-commit-issue-resolution-parity/human-review.ko.md`
- Modify: `.moduflow/state.json`
- Modify: `workspace/loop-state.json`
- Modify: `workspace/dashboard.md`

- [ ] **Step 1: Align the canonical acceptance criteria**

Replace “identical set / 44 commits” with the refined multi-attribution
consistency contract and the current dogfood assertion that Issue 093 includes
`project_issue_schema.py`.

- [ ] **Step 2: Record corrective verification**

Add the corrective branch, exact test counts, zero-expected-failure
requirement, independent review state, and Issue 096 separation to
`status.md`, `pr.md`, and `human-review.ko.md`.

- [ ] **Step 3: Reconcile lifecycle projections**

Set active issue `095`, phase `review`, and next command
`product:review 095-commit-issue-resolution-parity` in both state files and
the dashboard. Do not mark the issue done before review.

- [ ] **Step 4: Verify artifacts**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_artifacts.py .
PYTHONDONTWRITEBYTECODE=1 python3 scripts/project_lifecycle.py . --drift
```

Expected: validation `valid: true`; lifecycle drift `[]`.

- [ ] **Step 5: Commit**

```bash
git add issues/095-commit-issue-resolution-parity.md \
  specs/095-commit-issue-resolution-parity .moduflow/state.json \
  workspace/loop-state.json workspace/dashboard.md
git commit -m "docs(095): reconcile corrective review state"
```

### Task 4: Completion and independent review

**Files:**
- Review all files changed from `origin/main`

- [ ] **Step 1: Run focused verification**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_commit_resolution tests.test_commit_resolution_differential \
  tests.test_commit_resolution_parity tests.test_linkage_check \
  tests.test_project_converge
```

Expected: zero failures and zero expected failures.

- [ ] **Step 2: Run full verification**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_artifacts.py .
PYTHONDONTWRITEBYTECODE=1 python3 scripts/project_lifecycle.py . --drift
PYTHONDONTWRITEBYTECODE=1 python3 scripts/release_check.py .
git diff --check
```

Expected: full suite passes with zero expected failures; validation and release
check are valid; drift is `[]`; diff check is clean.

- [ ] **Step 3: Independent reviews**

Dispatch one read-only reviewer for spec compliance and another for code
quality/security. Every Important or Critical finding is fixed and re-reviewed.

- [ ] **Step 4: Prepare PR**

Push `codex/095-commit-issue-resolution-parity-fix` and create a Draft PR.
Do not merge or mark Issue 095 done without explicit human approval.

## Issue 096 Handoff

After the 095 corrective PR is approved and merged, create
`codex/096-read-shaped-commands-that-write` from updated `main`. Its separate
plan must cover explicit evidence writes, canonical issue-id validation,
resolved-path containment, symlink rejection, and write-path reporting.

