# Issue 095 Attribution Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace repository-wide base guessing with per-issue historical fork
points and prevent unrelated attribution ambiguity from failing the caller's
current commit or issue scope.

**Architecture:** A new `scripts/commit_graph.py` owns one Git snapshot,
ref-object identity, cached merge-base/ancestry queries, per-topic fork points,
and stacked-issue exclusions. `scripts/commit_resolution.py` remains the public
policy owner, applies `trailer > branch > merge-subject` once, and projects
structured diagnostics to the requested SHA or issue scope before compatibility
wrappers expose `errors`.

**Tech Stack:** Python 3 standard library, injected command runners, Git graph
commands, `unittest`, disposable Git repositories, Git-native ModuFlow
artifacts.

---

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific
additions:

1. `scripts/commit_graph.py` is the only owner of Git log/ref snapshots,
   ref-object equivalence, merge-base queries, ancestry queries, fork-point
   selection, and stacked-issue exclusions.
2. There is no repository-wide attribution base. Every live issue ref is
   measured from its own fork point. The current tip of `main`, `origin/main`,
   or another preferred ref name is never used as the historical fork itself.
3. `scripts/commit_resolution.py` remains the only owner of issue registry,
   trailer parsing, branch grammar, merge-subject parsing, source precedence,
   content ownership, and caller-scope projection.
4. Content commits have one owner under
   `trailer > branch > merge-subject`. Merge boundaries may retain multiple
   registered issue claims, but subject text alone never assigns side content.
5. Git command failures that invalidate the requested snapshot populate
   `fatal_errors`. Attribution ambiguity uses structured `diagnostics` carrying
   any known `sha`, `issue_id`, and `ref`; only diagnostics intersecting the
   caller's scope become compatibility `errors`.
6. Existing public wrapper names and existing result keys survive. New keys
   may be added. `errors` remains available as
   `fatal_errors + projected diagnostic messages`.
7. Git subprocess count does not scale with commit count. Merge-base and
   ancestry calls are cached by commit/ref pair. A resolver invocation reads
   the Git log once and refs once.
8. `specs/095-commit-issue-resolution-parity/failure-history.md` is
   append-only. Every RED test and every Critical/Important review finding
   names at least one `FH-*` id.
9. No focused-suite result closes Issue 095. Closure requires full unittest
   discovery, release check, project validation, lifecycle drift, and
   independent whole-branch review.
10. Tests use `tests/git_repo_builder.py` and declared literal ownership.
    `commit_resolution_reference.py` remains deleted; no derived reference
    oracle may return.
11. The `Issue:` trailer syntax, `codex/<issue-id>` convention, history, Issue
    096, and installed plugin are unchanged.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — graph snapshot | Superpowers TDD | Git boundaries must distinguish ordinary negative results from command failure. |
| B — fork points | Superpowers TDD + `moduflow:git-native-artifact-model` | Historical contribution is a Git topology contract, not a ref-name heuristic. |
| C — claims | Superpowers TDD | Merge boundaries, side content, and precedence require explicit RED/GREEN proofs. |
| D — diagnostics | Superpowers TDD + `moduflow:source-adapter-policy` | Internal structured diagnostics must remain compatible with both consumers. |
| E — consumers | Superpowers TDD | Release and converge must project the same attribution result to different scopes. |
| F — completion | `verification-before-completion` + `moduflow:source-command-product-review` | Full gates and independent review are required before any closure claim. |

The matrix guides execution; it does not replace the readiness or review
gates.

## File Structure

### Create

| Path | Responsibility |
| --- | --- |
| `scripts/commit_graph.py` | Git snapshot, ref identity, cached merge-base/ancestry, per-topic fork point, stacked exclusions, topic deltas |
| `tests/test_commit_graph.py` | Unit and real-repository tests for graph errors, fork invariants, and cached query behavior |

### Modify

| Path | Responsibility |
| --- | --- |
| `scripts/commit_resolution.py` | Candidate claims, one precedence pass, merge policy, structured diagnostics, scope projection, compatibility results |
| `scripts/linkage_check.py` | Build one resolver result scoped to behavior SHAs in `merge_base..HEAD` |
| `scripts/project_converge.py` | Ask for one issue-scoped result and surface projected diagnostics |
| `tests/git_repo_builder.py` | Small helpers for advancing trunks and creating explicit local/remote refs |
| `tests/commit_resolution_shapes.py` | Preserve literal truth and add metamorphic source topologies |
| `tests/test_commit_resolution.py` | Public resolver contracts, precedence, fatal versus scoped diagnostic behavior |
| `tests/test_commit_resolution_differential.py` | Declared-truth and bare/indexed parity across all shapes |
| `tests/test_commit_resolution_parity.py` | Cross-consumer parity and shared-policy ownership |
| `tests/test_linkage_check.py` | Release-range diagnostic projection and behavior-SHA scoping |
| `tests/test_project_converge.py` | Issue-scoped diagnostics and compatibility payload |
| `specs/095-commit-issue-resolution-parity/failure-history.md` | Append implementation evidence and status changes without rewriting entries |
| `specs/095-commit-issue-resolution-parity/status.md` | Record RED/GREEN commits, full verification, and review verdict |
| `issues/095-commit-issue-resolution-parity.md` | Track execution and review artifacts |
| `.moduflow/state.json` | Advance plan → execute → review only when gates permit |
| `workspace/loop-state.json` | Preserve next command and fresh verification evidence |
| `workspace/dashboard.md` | Show the active redesign phase and gate status |

## Stable Interfaces

### Graph snapshot

`commit_graph.load_snapshot()` returns one immutable-by-convention mapping:

```python
{
    "records": {
        sha: {
            "sha": sha,
            "subject": str,
            "parents": list[str],
            "body": str,
        }
    },
    "order": list[str],
    "refs": {full_ref_name: object_sha},
    "merge_base_cache": {},
    "ancestor_cache": {},
    "fatal_errors": list[str],
}
```

### Topic graph result

```python
{
    "issue_id": str,
    "topic_ref": str,
    "fork_point": str | None,
    "equivalent_base_refs": list[str],
    "stacked_exclusions": list[str],
    "commits": set[str],
    "diagnostics": [
        {
            "code": str,
            "message": str,
            "issue_id": str,
            "ref": str,
            # sha appears only when the diagnostic belongs to one commit
            "sha": str,
        }
    ],
}
```

### Public attribution result

`commit_resolution.build_attribution()` keeps current keys and adds scoped
diagnostic fields:

```python
build_attribution(
    runner,
    cwd,
    *,
    rev_range=None,
    target_shas=None,
    target_issue_ids=None,
) -> {
    "attribution": {sha: {issue_id: source}},
    "records": dict,
    "order": list[str],
    "unmatched": list[str],
    "branches": list[str],
    "issue_ids": list[str],
    "fatal_errors": list[str],
    "diagnostics": list[dict],
    "degraded": list[str],
    "errors": list[str],
}
```

`target_shas=None` and `target_issue_ids=None` mean an explicitly unscoped
administrative query. A consumer that knows its scope must pass it.

The issue-direction wrapper adds only an optional keyword:

```python
resolve_commits_for_issue(
    runner,
    cwd,
    issue_id,
    *,
    rev_range=None,
    index=None,
    target_issue_ids=None,
)
```

`resolve_issue_for_commit(..., attribution=...)` accepts either the legacy
`{sha: {issue_id: source}}` mapping or the whole new attribution result. New
internal callers pass the whole result so projected diagnostics are preserved.

### Diagnostic projection

```python
def project_diagnostics(
    diagnostics,
    *,
    target_shas=None,
    target_issue_ids=None,
):
    ...
```

A diagnostic is relevant when:

- its `sha` is in `target_shas`;
- its `issue_id` is in `target_issue_ids`;
- it has both fields and either requested dimension matches;
- neither scope is supplied.

Snapshot `fatal_errors` are never filtered.

## Implementation Readiness Inputs

- **API contract mapping:** the three interfaces above map graph mechanics to
  policy and both existing consumers. Public consumer helper signatures remain
  unchanged.
- **Test strategy:** unit tests prove command outcomes and projection;
  disposable repositories prove fork/stack/merge topology; declared truth
  proves ownership; metamorphic tests prove equivalent refs, trunk advancement,
  unrelated refs, and subject reordering do not change results.
- **Storybook required states:** not applicable; no frontend UI.
- **MSW fixture baseline:** not applicable; no HTTP API.
- **Playwright smoke matrix:** not applicable; no browser-visible flow.
- **Permission/role model:** not applicable; this is read-only Git analysis.
- **Release condition:** full unittest discovery passes with zero expected
  failures, `release_check.py` returns `valid: true` with `errors: []`, project
  validation is valid, lifecycle drift is `[]`, and independent review reports
  no Critical or Important findings.
- **Rollback condition:** each stream is one focused commit. Revert consumer
  integration before graph internals. No data migration or history rewrite is
  involved.

---

### Stream A — Graph Snapshot and Failure Semantics

#### Task A1: Create the graph snapshot boundary

**Files:**

- Create: `scripts/commit_graph.py`
- Create: `tests/test_commit_graph.py`
- Modify: `scripts/commit_resolution.py`

**Interfaces:** Produces `load_snapshot()`, `diagnostic()`, cached
`merge_base()` and `is_ancestor()`. Stream B consumes them.

- [ ] **Step 1: Write RED tests for one snapshot and three Git outcomes**

Add tests that call `load_snapshot()` and assert:

```python
class SnapshotTests(unittest.TestCase):
    def test_loads_log_and_refs_once(self):
        with GitRepo() as repo:
            repo.commit("chore: base", belongs_to=None)
            repo.add_issue_file(ALPHA)
            snapshot = commit_graph.load_snapshot(repo.runner, repo.path)
            self.assertEqual(snapshot["fatal_errors"], [])
            self.assertEqual(len(snapshot["records"]), len(snapshot["order"]))
            self.assertTrue(
                all(ref.startswith("refs/") for ref in snapshot["refs"])
            )
            self.assertEqual(
                sum(call[:2] == ["git", "log"] for call in repo.call_log),
                1,
                "the graph snapshot reads the commit log once",
            )
            self.assertEqual(
                sum(call[:2] == ["git", "for-each-ref"] for call in repo.call_log),
                1,
            )

    def test_merge_base_distinguishes_no_base_from_failure(self):
        no_base = commit_graph.merge_base(
            disconnected_runner(returncode=1), Path("."), empty_snapshot(), "a", "b"
        )
        failed = commit_graph.merge_base(
            disconnected_runner(returncode=128), Path("."), empty_snapshot(), "a", "b"
        )
        self.assertIsNone(no_base["sha"])
        self.assertEqual(no_base["fatal_errors"], [])
        self.assertTrue(failed["fatal_errors"])

    def test_terminated_ancestry_query_is_a_failure(self):
        result = commit_graph.is_ancestor(
            disconnected_runner(returncode=-15), Path("."), empty_snapshot(), "a", "b"
        )
        self.assertIsNone(result["value"])
        self.assertIn("terminated", result["fatal_errors"][0])
```

Tag the tests `FH-010`, `FH-014`, and `FH-019` in their docstrings.

Define the test-only runner and snapshot used above:

```python
def disconnected_runner(returncode):
    def run(args, cwd):
        stderr = (
            "no merge base" if returncode == 1
            else "graph query terminated"
        )
        return subprocess.CompletedProcess(
            args, returncode, stdout="", stderr=stderr
        )
    return run


def empty_snapshot():
    return {
        "records": {},
        "order": [],
        "refs": {},
        "merge_base_cache": {},
        "ancestor_cache": {},
        "fatal_errors": [],
    }
```

- [ ] **Step 2: Run the RED tests**

Run:

```bash
python3 -m unittest tests.test_commit_graph.SnapshotTests -v
```

Expected: FAIL because `scripts.commit_graph` and its functions do not exist.

- [ ] **Step 3: Implement the snapshot and cache primitives**

Create these concrete primitives:

```python
def diagnostic(code, message, *, sha=None, issue_id=None, ref=None):
    item = {"code": code, "message": message}
    for key, value in (("sha", sha), ("issue_id", issue_id), ("ref", ref)):
        if value is not None:
            item[key] = value
    return item


def merge_base(runner, cwd, snapshot, left, right):
    key = tuple(sorted((left, right)))
    if key in snapshot["merge_base_cache"]:
        return snapshot["merge_base_cache"][key]
    args = ["git", "merge-base", left, right]
    result = runner(args, cwd)
    if result.returncode == 0:
        value = {"sha": result.stdout.strip(), "fatal_errors": []}
    elif result.returncode == 1:
        value = {"sha": None, "fatal_errors": []}
    else:
        value = {
            "sha": None,
            "fatal_errors": [_command_error(args, result)],
        }
    snapshot["merge_base_cache"][key] = value
    return value


def is_ancestor(runner, cwd, snapshot, older, newer):
    key = (older, newer)
    if key in snapshot["ancestor_cache"]:
        return snapshot["ancestor_cache"][key]
    args = ["git", "merge-base", "--is-ancestor", older, newer]
    result = runner(args, cwd)
    if result.returncode == 0:
        value = {"value": True, "fatal_errors": []}
    elif result.returncode == 1:
        value = {"value": False, "fatal_errors": []}
    else:
        detail = _command_error(args, result)
        if result.returncode < 0:
            detail = f"{detail} (terminated by signal {-result.returncode})"
        value = {"value": None, "fatal_errors": [detail]}
    snapshot["ancestor_cache"][key] = value
    return value
```

Move commit-log/ref constants and record parsing behind `load_snapshot()`.
`known_issue_ids()`, branch classification, and `ISSUE_HISTORY_ARGS` remain in
`commit_resolution.py`. The policy layer passes already-classified topic and
base refs to graph functions. `commit_resolution.py` re-exports
`GIT_LOG_ARGS` and `BRANCH_REF_ARGS` during compatibility migration so
existing fixtures do not break for an unrelated reason.

- [ ] **Step 4: Run the focused tests**

Run:

```bash
python3 -m unittest tests.test_commit_graph.SnapshotTests tests.test_commit_resolution -v
```

Expected: PASS; no existing resolver test regresses.

- [ ] **Step 5: Commit**

```bash
git add scripts/commit_graph.py scripts/commit_resolution.py tests/test_commit_graph.py
git commit -m "refactor(095): isolate commit graph snapshot"
```

---

### Stream B — Per-Issue Fork Points and Stacked Deltas

#### Task B1: Select a fork point from merge-base commits

**Files:**

- Modify: `scripts/commit_graph.py`
- Modify: `tests/test_commit_graph.py`
- Modify: `tests/git_repo_builder.py`
- Modify: `tests/commit_resolution_shapes.py`

**Interfaces:** Consumes Stream A snapshot/cache. Produces
`derive_fork_point()` for B2 and Stream C.

- [ ] **Step 1: Write RED metamorphic tests**

Add these tests, with `FH-006`, `FH-011`, `FH-012`, `FH-013`, `FH-014`, and
`FH-017` in docstrings:

```python
class ForkPointInvariantTests(unittest.TestCase):
    def test_advancing_trunk_does_not_change_fork_point(self):
        with GitRepo() as repo:
            repo.commit("chore: base", belongs_to=None)
            repo.add_issue_file(ALPHA)
            repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: alpha", belongs_to=ALPHA)
            before = derive_for_repo(repo, ALPHA)
            repo.checkout("main")
            repo.commit("chore: main advances", belongs_to=None)
            after = derive_for_repo(repo, ALPHA)
            self.assertEqual(after["fork_point"], before["fork_point"])
            self.assertEqual(after["diagnostics"], [])

    def test_equivalent_remote_ref_does_not_change_fork_point(self):
        with GitRepo() as repo:
            repo.commit("chore: base", belongs_to=None)
            repo.add_issue_file(ALPHA)
            repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: alpha", belongs_to=ALPHA)
            before = derive_for_repo(repo, ALPHA)
            repo.publish("main", remote="upstream")
            after = derive_for_repo(repo, ALPHA)
            self.assertEqual(after["fork_point"], before["fork_point"])

    def test_disconnected_ref_does_not_change_connected_topic(self):
        with GitRepo() as repo:
            repo.commit("chore: base", belongs_to=None)
            repo.add_issue_file(ALPHA)
            repo.branch(f"codex/{ALPHA}")
            repo.commit("feat: alpha", belongs_to=ALPHA)
            before = derive_for_repo(repo, ALPHA)
            repo.create_orphan_ref("refs/heads/unrelated")
            after = derive_for_repo(repo, ALPHA)
            self.assertEqual(after["fork_point"], before["fork_point"])

    def test_incomparable_maximal_forks_are_scoped_to_topic(self):
        with GitRepo() as repo:
            shapes.ambiguous_same_tail_remotes(repo)
            result = derive_for_repo(repo, ALPHA)
            self.assertIsNone(result["fork_point"])
            self.assertEqual(
                {item["issue_id"] for item in result["diagnostics"]},
                {ALPHA},
            )
```

Add the explicit test helper:

```python
def derive_for_repo(repo, issue_id):
    errors = []
    ids = cr.known_issue_ids(repo.runner, repo.path, errors)
    assert errors == []
    snapshot = commit_graph.load_snapshot(repo.runner, repo.path)
    topic_refs = {
        ref: cr.issue_id_from_branch(ref, ids)
        for ref in snapshot["refs"]
        if cr.issue_id_from_branch(ref, ids) is not None
    }
    base_refs = [
        ref for ref in snapshot["refs"] if ref not in topic_refs
    ]
    topic_ref = next(
        ref
        for ref, found_issue in topic_refs.items()
        if found_issue == issue_id
    )
    return commit_graph.derive_fork_point(
        repo.runner,
        repo.path,
        snapshot,
        topic_ref,
        issue_id,
        base_refs=base_refs,
    )
```

Add `GitRepo.create_orphan_ref()` as a fixture-only helper. `git commit-tree`
creates a disconnected root without changing HEAD or the worktree:

```python
def create_orphan_ref(self, full_ref):
    tree = self._git("rev-parse", "HEAD^{tree}").strip()
    sha = self._git(
        "commit-tree",
        tree,
        "-m",
        "chore: disconnected root",
    ).strip()
    self._git("update-ref", full_ref, sha)
    return self.record(sha, None)
```

- [ ] **Step 2: Run the RED tests**

Run:

```bash
python3 -m unittest tests.test_commit_graph.ForkPointInvariantTests -v
```

Expected: FAIL because `derive_fork_point()` is absent or the current global
base changes after trunk advancement.

- [ ] **Step 3: Implement ref identity and fork-point selection**

Implement:

```python
def derive_fork_point(
    runner, cwd, snapshot, topic_ref, issue_id, *, base_refs
):
    candidates = []
    diagnostics = []
    if topic_ref not in snapshot["refs"]:
        return {
            "issue_id": issue_id,
            "topic_ref": topic_ref,
            "fork_point": None,
            "equivalent_base_refs": [],
            "diagnostics": [
                diagnostic(
                    "topic-ref-missing",
                    f"{topic_ref} is not present in the graph snapshot",
                    issue_id=issue_id,
                    ref=topic_ref,
                )
            ],
        }

    for ref in base_refs:
        if ref not in snapshot["refs"]:
            continue
        result = merge_base(runner, cwd, snapshot, topic_ref, ref)
        snapshot["fatal_errors"].extend(result["fatal_errors"])
        if result["sha"] is not None:
            candidates.append((result["sha"], ref))

    by_fork = {}
    for fork_sha, ref in candidates:
        by_fork.setdefault(fork_sha, []).append(ref)

    maximal = []
    for fork_sha in sorted(by_fork):
        dominated = False
        for other_sha in sorted(by_fork):
            if fork_sha == other_sha:
                continue
            relation = is_ancestor(
                runner, cwd, snapshot, fork_sha, other_sha
            )
            snapshot["fatal_errors"].extend(relation["fatal_errors"])
            if relation["value"] is True:
                reverse = is_ancestor(
                    runner, cwd, snapshot, other_sha, fork_sha
                )
                snapshot["fatal_errors"].extend(reverse["fatal_errors"])
                if reverse["value"] is False:
                    dominated = True
                    break
        if not dominated:
            maximal.append(fork_sha)

    if len(maximal) != 1:
        diagnostics.append(
            diagnostic(
                "ambiguous-topic-fork",
                f"{topic_ref} has {len(maximal)} incomparable fork points",
                issue_id=issue_id,
                ref=topic_ref,
            )
        )
        fork_point = None
        equivalent = []
    else:
        fork_point = maximal[0]
        equivalent = sorted(by_fork[fork_point])

    return {
        "issue_id": issue_id,
        "topic_ref": topic_ref,
        "fork_point": fork_point,
        "equivalent_base_refs": equivalent,
        "diagnostics": diagnostics,
    }
```

Use full ref names throughout. Refs are equivalent for candidate reporting
when they produce the same selected merge-base commit; same tail text alone
never collapses them.

- [ ] **Step 4: Run the invariant and declared-truth suites**

Run:

```bash
python3 -m unittest tests.test_commit_graph.ForkPointInvariantTests -v
```

Expected: PASS. Integration with declared-truth attribution begins in B2.

- [ ] **Step 5: Commit**

```bash
git add scripts/commit_graph.py tests/test_commit_graph.py tests/git_repo_builder.py tests/commit_resolution_shapes.py
git commit -m "feat(095): derive per-topic fork points"
```

#### Task B2: Compute stacked-issue exclusions and topic deltas

**Files:**

- Modify: `scripts/commit_graph.py`
- Modify: `tests/test_commit_graph.py`
- Modify: `tests/commit_resolution_shapes.py`
- Modify: `tests/test_commit_resolution_differential.py`

**Interfaces:** Consumes B1 fork point. Produces `topic_delta()` consumed by
Stream C claim building.

- [ ] **Step 1: Write RED tests for branch contribution and stacking**

```python
class TopicDeltaTests(unittest.TestCase):
    def test_base_history_is_not_topic_work(self):
        with GitRepo() as repo:
            shapes.stale_local_default_branch(repo)
            result = delta_for_repo(repo, ALPHA)
            self.assertEqual(result["commits"], repo.truth_for(ALPHA))

    def test_stacked_issue_excludes_inner_content(self):
        with GitRepo() as repo:
            shapes.two_registered_stacked_issues(repo)
            alpha = delta_for_repo(repo, ALPHA)
            beta = delta_for_repo(repo, BETA)
            self.assertEqual(alpha["commits"], repo.truth_for(ALPHA))
            self.assertEqual(beta["commits"], repo.truth_for(BETA))
            self.assertTrue(beta["stacked_exclusions"])

    def test_nested_merge_does_not_relabel_inner_content(self):
        with GitRepo() as repo:
            shapes.nested_merges(repo)
            beta = delta_for_repo(repo, BETA)
            self.assertTrue(
                repo.truth_for(ALPHA).isdisjoint(beta["commits"])
            )
```

`delta_for_repo()` loads registered ids and one snapshot exactly as
`derive_for_repo()` does, builds the same policy-owned
`{topic_ref: issue_id}` mapping and base-ref list, selects the full topic ref,
and calls `commit_graph.topic_delta()`.

Tag the tests `FH-002`, `FH-003`, and `FH-005`.

- [ ] **Step 2: Run the RED tests**

Run:

```bash
python3 -m unittest tests.test_commit_graph.TopicDeltaTests -v
```

Expected: FAIL because topic deltas still depend on `base_ref()` and
repository-wide exclusion.

- [ ] **Step 3: Implement stacked exclusions and the delta query**

```python
def topic_delta(
    runner,
    cwd,
    snapshot,
    topic_ref,
    issue_id,
    *,
    topic_refs,
    base_refs,
):
    fork = derive_fork_point(
        runner,
        cwd,
        snapshot,
        topic_ref,
        issue_id,
        base_refs=base_refs,
    )
    diagnostics = list(fork["diagnostics"])
    if fork["fork_point"] is None:
        return {
            **fork,
            "stacked_exclusions": [],
            "commits": set(),
            "diagnostics": diagnostics,
        }

    exclusions = []
    for other_ref in sorted(topic_refs):
        if (
            other_ref == topic_ref
            or topic_refs[other_ref] == issue_id
        ):
            continue
        pair = merge_base(runner, cwd, snapshot, topic_ref, other_ref)
        snapshot["fatal_errors"].extend(pair["fatal_errors"])
        pair_sha = pair["sha"]
        if pair_sha is None or pair_sha == fork["fork_point"]:
            continue
        above_fork = is_ancestor(
            runner, cwd, snapshot, fork["fork_point"], pair_sha
        )
        snapshot["fatal_errors"].extend(above_fork["fatal_errors"])
        if above_fork["value"] is True:
            exclusions.append(pair_sha)

    exclusions = _ancestry_maximal(
        runner, cwd, snapshot, sorted(set(exclusions))
    )
    args = [
        "git", "rev-list", topic_ref,
        "--not", fork["fork_point"], *exclusions,
    ]
    result = runner(args, cwd)
    if result.returncode != 0:
        snapshot["fatal_errors"].append(_command_error(args, result))
        commits = set()
    else:
        commits = set(result.stdout.split())

    return {
        **fork,
        "stacked_exclusions": exclusions,
        "commits": commits,
        "diagnostics": diagnostics,
    }
```

Deduplicate topic refs that point to the same object and issue before querying
their deltas. Keep different refs for the same issue only when their object ids
differ; ambiguity remains scoped to that issue.

- [ ] **Step 4: Remove the old global-base path from live attribution**

Stop calling `base_ref()` and the old exclusion loop from
`build_branch_membership()`. Keep a temporary compatibility wrapper only if a
test outside Issue 095 imports it; the wrapper must delegate per topic and
must not elect one repository-wide ref.

- [ ] **Step 5: Run focused suites**

Run:

```bash
python3 -m unittest tests.test_commit_graph tests.test_commit_resolution_differential -v
```

Expected: PASS with zero expected failures.

- [ ] **Step 6: Commit**

```bash
git add scripts/commit_graph.py scripts/commit_resolution.py tests/test_commit_graph.py tests/commit_resolution_shapes.py tests/test_commit_resolution_differential.py
git commit -m "feat(095): compute stacked topic deltas"
```

---

### Stream C — Merge Claims and Single Ownership

#### Task C1: Separate merge-boundary claims from content-side claims

**Files:**

- Modify: `scripts/commit_resolution.py`
- Modify: `tests/commit_resolution_shapes.py`
- Modify: `tests/test_commit_resolution.py`
- Modify: `tests/test_commit_resolution_differential.py`

**Interfaces:** Consumes Stream B topic deltas and snapshot refs. Produces
candidate claims for Stream D.

- [ ] **Step 1: Write RED merge-invariant tests**

```python
class MergeClaimInvariantTests(unittest.TestCase):
    def test_subject_token_order_does_not_change_content(self):
        normal = resolve_shape("octopus_merge")
        reversed_order = resolve_shape("octopus_subject_order_reversed")
        self.assertEqual(
            normal["content_owners"],
            reversed_order["content_owners"],
        )

    def test_deleted_refs_keep_boundary_but_not_unproven_content(self):
        result = resolve_shape("octopus_mapping_ambiguous")
        self.assertEqual(result["boundary_issues"], {ALPHA, BETA})
        self.assertTrue(
            any(
                d["code"] == "merge-side-unresolved"
                for d in result["diagnostics"]
            )
        )

    def test_two_parent_multi_name_subject_does_not_relabel_side(self):
        result = resolve_shape("two_parent_multi_name_ambiguous")
        self.assertEqual(
            result["content_owners"],
            result["declared_content_owners"],
        )
```

Define the helper in the test module so comparison is by stable subjects, not
the different SHA values created by two repositories:

```python
def resolve_shape(name):
    with GitRepo(**shapes.REPO_KWARGS.get(name, {})) as repo:
        shapes.ALL_SHAPES[name](repo)
        built = cr.build_attribution(repo.runner, repo.path)
        content_owners = {}
        declared_content_owners = {}
        boundary_issues = set()
        for sha, record in built["records"].items():
            actual = frozenset((built["attribution"].get(sha) or {}).keys())
            if len(record["parents"]) < 2:
                content_owners[record["subject"]] = actual
                declared_content_owners[record["subject"]] = repo.truth[sha]
            else:
                boundary_issues.update(actual)
        return {
            "content_owners": content_owners,
            "declared_content_owners": declared_content_owners,
            "boundary_issues": boundary_issues,
            "diagnostics": built["diagnostics"],
        }
```

Tag the tests `FH-004`, `FH-015`, and `FH-016`.

- [ ] **Step 2: Run the RED tests**

Run:

```bash
python3 -m unittest tests.test_commit_resolution.MergeClaimInvariantTests -v
```

Expected: at least subject-order or deleted-ref content ownership FAILS under
the current parent/subject mapping.

- [ ] **Step 3: Implement separate candidate channels**

Represent candidates before precedence:

```python
candidate_claims = {
    sha: [
        {
            "issue_id": issue_id,
            "source": "trailer" | "branch" | "merge-subject",
            "kind": "content" | "boundary",
        }
    ]
}
```

Use:

```python
def add_candidate(candidates, sha, issue_id, source, kind):
    if issue_id not in registered_issue_ids:
        return
    item = {
        "issue_id": issue_id,
        "source": source,
        "kind": kind,
    }
    if item not in candidates.setdefault(sha, []):
        candidates[sha].append(item)
```

For every merge:

1. Add every registered source-subject name as a `boundary` claim on the merge
   SHA.
2. For a two-parent merge with exactly one registered source issue, its
   second-parent side may be claimed for that issue. For an octopus or a
   multi-name two-parent merge, assign side content only when a retained full
   ref points to that parent and identifies exactly one registered issue.
3. Otherwise add `merge-side-unresolved` diagnostics carrying the merge
   boundary `sha`, and conservatively attach the same code to every commit on
   each unresolved side with each affected issue id. This lets a caller
   selecting an affected content SHA fail closed without guessing its owner.
   Do not guess ownership from subject position.
4. Apply live topic deltas from Stream B as `branch/content` candidates.

- [ ] **Step 4: Apply precedence once**

```python
def finalize_claims(records, candidates):
    attribution = {}
    for sha, items in candidates.items():
        if len(records[sha]["parents"]) >= 2:
            per_issue = {}
            for item in items:
                current = per_issue.get(item["issue_id"])
                if current is None or precedence(item) < precedence(current):
                    per_issue[item["issue_id"]] = item
            attribution[sha] = {
                issue_id: item["source"]
                for issue_id, item in per_issue.items()
            }
            continue

        winner = min(
            (item for item in items if item["kind"] == "content"),
            key=lambda item: (
                SOURCE_PRECEDENCE.index(item["source"]),
                item["issue_id"],
            ),
            default=None,
        )
        if winner is not None:
            attribution[sha] = {
                winner["issue_id"]: winner["source"]
            }
    return attribution
```

Delete inline precedence decisions from trailer, merge, and live-branch loops.

- [ ] **Step 5: Run merge, precedence, and differential suites**

Run:

```bash
python3 -m unittest tests.test_commit_resolution tests.test_commit_resolution_differential -v
```

Expected: PASS; reversing subject tokens changes no content owner, and declared
truth still matches every shape.

- [ ] **Step 6: Commit**

```bash
git add scripts/commit_resolution.py tests/commit_resolution_shapes.py tests/test_commit_resolution.py tests/test_commit_resolution_differential.py
git commit -m "fix(095): separate merge boundaries from content"
```

---

### Stream D — Scoped Diagnostics and Public Resolver

#### Task D1: Project diagnostics and unify bare/indexed resolution

**Files:**

- Modify: `scripts/commit_resolution.py`
- Modify: `tests/test_commit_resolution.py`
- Modify: `tests/test_commit_resolution_differential.py`
- Modify: `tests/test_commit_resolution_parity.py`

**Interfaces:** Consumes Stream C candidates. Produces the stable public result
used by both consumers.

- [ ] **Step 1: Write RED scope and call-shape tests**

```python
class DiagnosticProjectionTests(unittest.TestCase):
    def test_unrelated_issue_diagnostic_is_not_an_error(self):
        diagnostics = [
            {"code": "ambiguous-topic-fork", "message": "alpha", "issue_id": ALPHA},
            {"code": "ambiguous-topic-fork", "message": "beta", "issue_id": BETA},
        ]
        projected = cr.project_diagnostics(
            diagnostics, target_issue_ids={BETA}
        )
        self.assertEqual([d["issue_id"] for d in projected], [BETA])

    def test_snapshot_failure_is_never_filtered(self):
        result = cr.compatibility_errors(
            ["git log failed"], []
        )
        self.assertEqual(result, ["git log failed"])

    def test_bare_and_indexed_resolution_use_same_policy(self):
        with GitRepo() as repo:
            shapes.trailer_disagrees_with_branch(repo)
            sha = next(
                sha
                for sha, owners in repo.truth.items()
                if owners == frozenset({BETA})
            )
            built = cr.build_attribution(
                repo.runner, repo.path, target_shas={sha}
            )
            bare = cr.resolve_issue_for_commit(repo.runner, repo.path, sha)
            indexed = cr.resolve_issue_for_commit(
                repo.runner, repo.path, sha, attribution=built
            )
            self.assertEqual(bare, indexed)
```

Tag the tests `FH-001`, `FH-007`, `FH-008`, `FH-009`, `FH-010`, and `FH-018`.

- [ ] **Step 2: Run the RED tests**

Run:

```bash
python3 -m unittest tests.test_commit_resolution.DiagnosticProjectionTests tests.test_commit_resolution_differential.CommitDirectionTests -v
```

Expected: FAIL because errors are global and the bare path still performs its
own trailer short-circuit.

- [ ] **Step 3: Implement projection and compatibility errors**

```python
def project_diagnostics(
    diagnostics, *, target_shas=None, target_issue_ids=None
):
    if target_shas is None and target_issue_ids is None:
        return list(diagnostics)
    target_shas = set(target_shas or ())
    target_issue_ids = set(target_issue_ids or ())
    projected = []
    for item in diagnostics:
        sha_match = item.get("sha") in target_shas
        issue_match = item.get("issue_id") in target_issue_ids
        if sha_match or issue_match:
            projected.append(item)
    return projected


def compatibility_errors(fatal_errors, projected_diagnostics):
    return [
        *fatal_errors,
        *(item["message"] for item in projected_diagnostics),
    ]
```

`build_attribution()` collects all structured diagnostics, projects them once,
and returns:

```python
projected = project_diagnostics(
    diagnostics,
    target_shas=target_shas,
    target_issue_ids=target_issue_ids,
)
errors = compatibility_errors(snapshot["fatal_errors"], projected)
```

Derive `degraded` from unique projected diagnostic codes plus existing
compatibility degradation names. Do not put unrelated diagnostic codes in it.

- [ ] **Step 4: Remove the bare trailer resolver**

When no attribution result is supplied:

```python
built = build_attribution(
    runner,
    cwd,
    target_shas={sha},
)
return _from_index_result(sha, built)
```

When an attribution result mapping is supplied, support the existing mapping
shape for compatibility. New internal callers pass the whole build result so
`errors` and `degraded` remain available. There is no `git show` shortcut and
no second precedence path.

- [ ] **Step 5: Run resolver and parity suites**

Run:

```bash
python3 -m unittest tests.test_commit_resolution tests.test_commit_resolution_differential tests.test_commit_resolution_parity -v
```

Expected: PASS with bare and indexed results identical across all declared
shapes.

- [ ] **Step 6: Commit**

```bash
git add scripts/commit_resolution.py tests/test_commit_resolution.py tests/test_commit_resolution_differential.py tests/test_commit_resolution_parity.py
git commit -m "feat(095): scope attribution diagnostics"
```

---

### Stream E — Consumer Scope Integration

#### Task E1: Scope the release linkage query to behavior commits

**Files:**

- Modify: `scripts/linkage_check.py`
- Modify: `tests/test_linkage_check.py`
- Modify: `tests/test_commit_resolution_parity.py`

**Interfaces:** Consumes Stream D `target_shas`. Produces a release result
unaffected by unrelated historical diagnostics.

- [ ] **Step 1: Write the RED historical-ambiguity release test**

```python
def test_out_of_range_ambiguity_does_not_fail_release_linkage(self):
    with ambiguous_release_repo(ambiguity_in_range=False) as repo:
        result = linkage_check.find_unlinked_behavior_commits(
            repo.runner,
            repo.path,
            repo.release_base,
            repo.head(),
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["errors"], [])


def test_in_range_ambiguity_fails_closed(self):
    with ambiguous_release_repo(ambiguity_in_range=True) as repo:
        result = linkage_check.find_unlinked_behavior_commits(
            repo.runner,
            repo.path,
            repo.release_base,
            repo.head(),
        )
        self.assertFalse(result["ok"])
        self.assertTrue(result["errors"])
```

Tag both tests `FH-018`.

Define both fixtures in `tests/test_linkage_check.py` with
`contextlib.contextmanager`. They create the same deleted-ref octopus history;
the only difference is whether `release_base` is recorded before or after that
history:

```python
@contextlib.contextmanager
def ambiguous_release_repo(*, ambiguity_in_range):
    with GitRepo() as repo:
        repo.commit("chore: base", belongs_to=None)
        repo.add_issue_file(ALPHA)
        repo.add_issue_file(BETA)
        base = repo.head()

        first = repo.branch(f"codex/{ALPHA}")
        (repo.path / "scripts").mkdir()
        repo.commit(
            "feat: alpha",
            filename="scripts/alpha.py",
            belongs_to=ALPHA,
        )
        repo.checkout("main")
        second = repo.branch(f"codex/{BETA}")
        (repo.path / "scripts").mkdir(exist_ok=True)
        repo.commit(
            "feat: beta",
            filename="scripts/beta.py",
            belongs_to=BETA,
        )
        repo.checkout("main")
        repo._git(
            "merge", "-q", "--no-ff", "-m",
            f"Merge branches 'codex/{BETA}' and 'codex/{ALPHA}'",
            first, second,
        )
        repo.record(repo.head(), [ALPHA, BETA])
        repo.delete_branch(first)
        repo.delete_branch(second)

        if ambiguity_in_range:
            repo.release_base = base
        else:
            repo.release_base = repo.head()
            repo.commit(
                "fix: current linked change",
                issue=ALPHA,
                filename="scripts/current.py",
                belongs_to=ALPHA,
            )
        yield repo
```

- [ ] **Step 2: Run the RED test**

Run:

```bash
python3 -m unittest tests.test_linkage_check.FindUnlinkedBehaviorCommitsTests.test_out_of_range_ambiguity_does_not_fail_release_linkage -v
```

Expected: FAIL with the old historical ambiguity in `errors`.

- [ ] **Step 3: Collect the behavior scope before resolving**

Refactor `find_unlinked_behavior_commits()` into two passes:

```python
behavior = []
for sha in shas:
    paths = _changed_paths_for_commit(runner, cwd, sha, errors)
    if paths is None:
        continue
    classified = classify_changed_paths(paths)
    if classified["behavior"]:
        behavior.append((sha, classified["behavior"]))

if not behavior:
    return {
        "ok": not errors,
        "commits": [],
        "unlinked": [],
        "degraded": [],
        "errors": errors,
    }

target_shas = {sha for sha, _paths in behavior}
built = commit_resolution.build_attribution(
    runner,
    cwd,
    target_shas=target_shas,
)
```

Resolve each behavior commit from `built` without rebuilding the index. Copy
only `built["errors"]` and `built["degraded"]` into the release result.

- [ ] **Step 4: Run linkage and cross-consumer parity**

Run:

```bash
python3 -m unittest tests.test_linkage_check tests.test_commit_resolution_parity -v
```

Expected: PASS. Neutral-only ranges still perform no attribution build.

- [ ] **Step 5: Commit**

```bash
git add scripts/linkage_check.py tests/test_linkage_check.py tests/test_commit_resolution_parity.py
git commit -m "fix(095): scope release attribution to behavior commits"
```

#### Task E2: Scope converge to the requested issue

**Files:**

- Modify: `scripts/project_converge.py`
- Modify: `tests/test_project_converge.py`
- Modify: `tests/test_commit_resolution_parity.py`

**Interfaces:** Consumes Stream D `target_issue_ids`. Produces the existing
converge payload plus scoped diagnostic fields.

- [ ] **Step 1: Write RED issue-scope tests**

```python
def test_other_issue_ambiguity_does_not_pollute_bundle(self):
    runner = object()
    resolver_result = {
        "commits": [],
        "repo_unmatched_count": 0,
        "repo_examined_count": 0,
        "coverage": {
            "sources": {},
            "branch_refs": [],
            "base_ref_available": True,
        },
        "diagnostics": [],
        "fatal_errors": [],
        "degraded": [],
        "errors": [],
    }
    with mock.patch.object(
        project_converge.commit_resolution,
        "resolve_commits_for_issue",
        return_value=resolver_result,
    ) as resolver:
        result = project_converge.resolve_commits(
            runner, Path("."), BETA
        )
        self.assertEqual(result["errors"], [])
        resolver.assert_called_once_with(
            runner,
            Path("."),
            BETA,
            target_issue_ids={BETA},
        )


def test_requested_issue_ambiguity_is_visible(self):
    runner = object()
    resolver_result = {
        "commits": [],
        "repo_unmatched_count": 0,
        "repo_examined_count": 0,
        "coverage": {
            "sources": {},
            "branch_refs": [],
            "base_ref_available": False,
        },
        "diagnostics": [
            {
                "code": "ambiguous-topic-fork",
                "message": "alpha is ambiguous",
                "issue_id": ALPHA,
            }
        ],
        "fatal_errors": [],
        "degraded": ["ambiguous-topic-fork"],
        "errors": ["alpha is ambiguous"],
    }
    with mock.patch.object(
        project_converge.commit_resolution,
        "resolve_commits_for_issue",
        return_value=resolver_result,
    ):
        result = project_converge.resolve_commits(
            runner, Path("."), ALPHA
        )
        self.assertTrue(result["errors"])
        self.assertIn("ambiguous-topic-fork", result["degraded"])
```

Import `mock` from `unittest`. Tag both tests `FH-018`.

- [ ] **Step 2: Run the RED tests**

Run:

```bash
python3 -m unittest tests.test_project_converge.ResolveCommitsTests -v
```

Expected: the unrelated ambiguity test FAILS under the flat global error list.

- [ ] **Step 3: Pass issue scope through the resolver**

Implement:

```python
resolved = commit_resolution.resolve_commits_for_issue(
    runner,
    cwd,
    issue_id,
    target_issue_ids={issue_id},
)
```

Add the optional keyword to `resolve_commits_for_issue()` and pass it to
`build_attribution()`. Preserve existing payload keys and add
`diagnostics`/`fatal_errors` for machine consumers.

- [ ] **Step 4: Run converge and parity suites**

Run:

```bash
python3 -m unittest tests.test_project_converge tests.test_commit_resolution_parity -v
python3 scripts/project_converge.py . --issue-id 093-frontmatter-issue-schema-readiness-gate --evidence --json
```

Expected: tests PASS; issue 093 evidence includes
`scripts/project_issue_schema.py`; the JSON reports only diagnostics relevant
to issue 093.

- [ ] **Step 5: Commit**

```bash
git add scripts/project_converge.py tests/test_project_converge.py tests/test_commit_resolution_parity.py
git commit -m "fix(095): scope converge attribution by issue"
```

---

### Stream F — Invariant Audit and Completion Gates

#### Task F1: Trace every failure family to executable evidence

**Files:**

- Modify: `tests/test_commit_graph.py`
- Modify: `tests/test_commit_resolution.py`
- Modify: `tests/test_commit_resolution_differential.py`
- Modify: `tests/test_commit_resolution_parity.py`
- Modify: `tests/test_linkage_check.py`
- Modify: `tests/test_project_converge.py`
- Modify: `specs/095-commit-issue-resolution-parity/failure-history.md`

**Interfaces:** Consumes all implementation streams. Produces the reviewable
failure-to-test matrix.

- [ ] **Step 1: Add a failure-history traceability test**

```python
class FailureHistoryTraceabilityTests(unittest.TestCase):
    def test_every_open_or_redesign_failure_has_a_test_reference(self):
        corpus = Path(
            "specs/095-commit-issue-resolution-parity/failure-history.md"
        ).read_text(encoding="utf-8")
        tests = "\n".join(
            path.read_text(encoding="utf-8")
            for path in Path("tests").glob("test_commit*.py")
        ) + Path("tests/test_linkage_check.py").read_text(
            encoding="utf-8"
        ) + Path("tests/test_project_converge.py").read_text(
            encoding="utf-8"
        )
        required = re.findall(
            r"\|\s*(FH-\d{3})\s*\|.*\|\s*(?:open|superseded by redesign)\s*\|",
            corpus,
        )
        missing = [failure_id for failure_id in required if failure_id not in tests]
        self.assertEqual(missing, [])
```

This enforces traceability, not correctness by string alone; the linked test
must also assert the derived invariant named in the corpus.

- [ ] **Step 2: Run the traceability test**

Run:

```bash
python3 -m unittest tests.test_commit_resolution.FailureHistoryTraceabilityTests -v
```

Expected: FAIL listing every `FH-*` not yet named in executable tests.

- [ ] **Step 3: Add missing IDs to the invariant tests and audit assertions**

Do not add IDs to unrelated docstrings. For every missing ID, either link it to
an existing test that asserts its derived invariant or add a focused test that
does. Update each failure record with the test class/method and implementing
commit, preserving all prior text.

- [ ] **Step 4: Run all Issue 095 focused suites**

Run:

```bash
python3 -m unittest \
  tests.test_commit_graph \
  tests.test_commit_resolution \
  tests.test_commit_resolution_differential \
  tests.test_commit_resolution_parity \
  tests.test_linkage_check \
  tests.test_project_converge -v
```

Expected: PASS, zero expected failures, no skipped Issue 095 invariant.

- [ ] **Step 5: Commit**

```bash
git add tests specs/095-commit-issue-resolution-parity/failure-history.md
git commit -m "test(095): trace attribution failure invariants"
```

#### Task F2: Run full verification and prepare independent review

**Files:**

- Modify: `specs/095-commit-issue-resolution-parity/status.md`
- Modify: `issues/095-commit-issue-resolution-parity.md`
- Modify: `.moduflow/state.json`
- Modify: `workspace/loop-state.json`
- Modify: `workspace/dashboard.md`

**Interfaces:** Consumes all prior commits. Produces fresh gate evidence and the
review handoff. It does not merge, push, release, or update the plugin.

- [ ] **Step 1: Run plan/spec consistency**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/spec_consistency.py . --issue-id 095-commit-issue-resolution-parity
```

Expected: zero error-severity findings; every stream in this plan exists in
`tasks.md`.

- [ ] **Step 2: Run full unittest discovery**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
```

Expected: exit 0, zero failures, zero unexpected successes, zero expected
failures.

- [ ] **Step 3: Run release and project gates**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/release_check.py .
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_artifacts.py .
PYTHONDONTWRITEBYTECODE=1 python3 scripts/project_lifecycle.py . --drift
git diff --check
```

Expected:

- release check `valid: true`, `errors: []`;
- project validation `valid: true`, `errors: []`;
- lifecycle drift `[]`;
- `git diff --check` exit 0.

- [ ] **Step 4: Re-run the original release symptom**

Run the current release check against the repository containing historical
merge `777b04e6fe531d46a123aadbb236fcf3cb33e5c7`.

Expected: the unrelated historical ambiguity is retained in the full
diagnostic corpus but does not appear in the current release's `errors`.

- [ ] **Step 5: Request independent spec and quality review**

The review must explicitly audit:

- per-topic fork selection against `FH-006`, `FH-011`, `FH-013`, `FH-017`;
- subject-independent merge content against `FH-015`, `FH-016`;
- range/issue diagnostic projection against `FH-018`;
- failure corpus traceability and absence of a derived reference oracle.

Any Critical or Important finding is appended to
`failure-history.md` before implementation resumes.

- [ ] **Step 6: Reconcile lifecycle only after review**

If and only if the review has no Critical or Important findings, set phase to
`review`, next command to
`product:pr 095-commit-issue-resolution-parity`, and record fresh command
outputs in status/loop/dashboard. Otherwise remain in `execute` with the exact
finding as the next action.

- [ ] **Step 7: Commit the verified handoff**

```bash
git add specs/095-commit-issue-resolution-parity/status.md issues/095-commit-issue-resolution-parity.md .moduflow/state.json workspace/loop-state.json workspace/dashboard.md
git commit -m "docs(095): record redesign verification"
```

## Gates

| Gate | Command or evidence | Pass condition |
| --- | --- | --- |
| Failure traceability | `FailureHistoryTraceabilityTests` | Every open/redesign `FH-*` maps to an invariant test |
| Fork invariants | `tests.test_commit_graph` | Trunk advance, equivalent refs, and unrelated refs preserve the topic fork |
| Ownership | differential + parity suites | Declared truth matches; bare/indexed and both consumers agree |
| Scope | linkage + converge tests | Out-of-scope ambiguity is retained but not projected as an error |
| Focused | six Issue 095 test modules | Zero failures and zero expected failures |
| Full | `python3 -m unittest discover -s tests` | Exit 0 with no failure masking |
| Release | `python3 scripts/release_check.py .` | `valid: true`, `errors: []` |
| Project | validation + lifecycle | `valid: true`, `errors: []`, drift `[]` |
| Review | independent spec and quality review | No Critical or Important findings |
| Human | Draft PR approval | Human decides merge; no automatic main transition |

## Rollback

Rollback uses `git revert`, never history rewrite:

1. Revert E1/E2 first to restore existing consumer integration.
2. Revert D1 to restore the compatibility error surface.
3. Revert C1, B2, B1, then A1 only if the entire graph redesign is abandoned.
4. Keep `failure-history.md` even when implementation commits are reverted;
   append the rollback reason and resulting status.

The installed plugin and Issue 096 remain untouched throughout, so neither
requires rollback.
