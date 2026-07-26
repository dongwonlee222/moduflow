# Commit-to-Issue Resolution Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every consumer that asks "which issue owns this commit?" one shared resolver covering trailer, branch, and merge-subject, and make under-collection impossible to report silently.

**Architecture:** Add a standard-library-only `scripts/commit_resolution.py` that owns the trailer regex, the `codex/<issue-id>` branch grammar, the fixed source precedence, and a batched branch-membership strategy. `linkage_check.py` and `project_converge.py` delegate to it and keep their current public helper names as wrappers. The converge evidence payload gains an unmatched-commit count and a per-commit resolution source.

**Tech Stack:** Python 3 standard library, `unittest`, temporary git repositories as fixtures, JSON contracts, Git-native ModuFlow artifacts.

---

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

1. `scripts/commit_resolution.py` is the only owner of trailer parsing, branch-name issue extraction, merge-subject matching, and source precedence. No consumer may reimplement any of them.
2. Source precedence is exactly `trailer` > `branch` > `merge-subject`. A commit matching several sources is recorded once, at the highest that matched.
3. The `Issue:` trailer format and the `codex/<issue-id>` branch convention do not change. No existing commit history is rewritten.
4. Converge's git subprocess count must not scale with history length. Branch membership is computed once per invocation, never with `git branch --contains` per commit.
5. `unmatched_count` is descriptive, not an error. It never populates `errors` and never blocks.
6. Converge stays reported, never blocking. This plan does not let it gate a review verdict.
7. Public helper names in `linkage_check.py` and `project_converge.py` survive as wrappers. No caller or existing test is edited to accommodate the refactor.
8. Degraded resolution is reported, never raised. Detached HEAD returns trailer results plus an explicit note that branch resolution was unavailable.
9. Every behavior change starts with a failing test, uses the smallest implementation that passes, and gets a focused commit before the next consumer migration.
10. Test fixtures build throwaway git repositories in a temp directory. No test depends on this checkout's history, branches, or remotes.

## Recommended Discipline

- Land Stream A before either consumer migrates. A shared resolver that both modules can already import removes the temptation to patch one side locally.
- Run the parity test (E1) after every consumer task, not only at the end. It is the single check that proves the two modules have not drifted apart again.
- Prefer adding a fixture case over widening an assertion. The regression table in the spec is the coverage contract.

## File Structure

### Create

| Path | Purpose |
| --- | --- |
| `scripts/commit_resolution.py` | Shared resolver: rules, precedence, batched branch membership, both query directions |
| `tests/test_commit_resolution.py` | Unit coverage for the resolver, including detached HEAD and precedence |
| `tests/git_repo_builder.py` | Helper that builds temporary git repositories for the regression table. Lives at the tests root, not under `tests/fixtures/`, which holds data fixtures rather than importable modules. |

### Modify

| Path | Change |
| --- | --- |
| `scripts/linkage_check.py` | `resolve_issue_for_commit()` becomes a wrapper over the shared resolver |
| `scripts/project_converge.py` | `resolve_commits()` delegates; payload gains `unmatched_count` and per-commit `source` |
| `tests/test_linkage_check.py` | Add branch/merge-subject parity cases |
| `tests/test_project_converge.py` | Add unmatched-count, source, and detached-HEAD cases |
| `docs/` release notes or changelog surface | Record the payload field addition |

## Stable Interfaces

The contract both consumers depend on. Task A1 fixes these signatures; downstream tasks may add fields but may not change existing ones.

```python
# commit → issue, one sha
resolve_issue_for_commit(runner, cwd, sha, *, membership=None) -> {
    "sha": str,
    "issue_id": str | None,
    "source": "trailer" | "branch" | "merge-subject" | None,
    "degraded": list[str],     # e.g. ["branch-unavailable"]
    "errors": list[str],
}

# issue → commits, whole range
resolve_commits_for_issue(runner, cwd, issue_id, *, rev_range=None) -> {
    "commits": [{"sha", "subject", "source", "is_merge"}],
    "unmatched_count": int,
    "examined_count": int,
    "degraded": list[str],
    "errors": list[str],
}

# built once per invocation, passed into per-commit calls to avoid fan-out
build_branch_membership(runner, cwd) -> {sha: [branch_name, ...]}
```

`degraded` is the detached-HEAD channel: a non-empty list means some source could not be
consulted, and the caller should present the result as partial.

## Implementation Readiness Contracts

- A1 must land before B1, B2, or C1 — all three import the module A1 creates.
- B1 and B2 touch different files and may run in parallel once A1 is merged.
- C1 depends on B2's payload shape (`unmatched_count`, `source`).
- E1 depends on B1 and B2 both being merged; it asserts across them.

---

### Stream A — Shared Resolver

#### Task A1: Extract the rules and fix the interface

Create `scripts/commit_resolution.py` holding the trailer regex, the `codex/<issue-id>`
branch grammar, merge-subject matching, and the precedence order, behind the three signatures
above. Port the existing behavior of both modules verbatim first — this task adds no new
matching rules, only a single home for the ones that exist.

**Interfaces** — Produces: the module and its three public functions. Consumes: nothing.

**Verify:** `python3 -m unittest tests.test_commit_resolution -v`

#### Task A2: Batched branch membership

Implement `build_branch_membership()` using one `git for-each-ref` plus reachability derived
from the log already being read, replacing per-commit `git branch --contains`. Add a test that
counts subprocess invocations and fails if the count scales with commit count (Global
Constraint 4).

**Interfaces** — Consumes: A1's signatures. Produces: `membership` mapping accepted by
`resolve_issue_for_commit`.

**Verify:** `python3 -m unittest tests.test_commit_resolution -v`

---

### Stream B — Consumer Migration

#### Task B1: `linkage_check.py` delegates

Replace the body of `resolve_issue_for_commit()` with a call to the shared resolver, keeping
the existing public name and return keys so no caller changes. Add the merge-subject source it
previously lacked.

**Interfaces** — Consumes: A1, A2. Produces: unchanged public surface for existing callers.

**Verify:** `python3 -m unittest tests.test_linkage_check -v`

#### Task B2: `project_converge.py` delegates and reports gaps

Replace the body of `resolve_commits()` with a call to the shared resolver, gaining the branch
fallback it previously lacked. Add `unmatched_count` and `examined_count` to the evidence
payload, and `source` per commit. Keep `errors` semantics unchanged (Global Constraint 5).

**Interfaces** — Consumes: A1, A2. Produces: the extended evidence payload that C1 and E1 read.

**Verify:** `python3 -m unittest tests.test_project_converge -v` and
`python3 scripts/project_converge.py . --issue-id 093-frontmatter-issue-schema-readiness-gate --evidence --json`

---

### Stream C — Surface and Documentation

#### Task C1: Surface the gap where reviewers read it

Make the unmatched count visible wherever converge evidence is presented to a human — the
review packet and any rendered evidence surface — so a reader sees "43 unmatched" without
opening the JSON. Do not change the review verdict logic (Global Constraint 6).

**Interfaces** — Consumes: B2's payload fields.

**Verify:** `python3 scripts/release_check.py .`

---

### Stream D — Regression Coverage

#### Task D1: Build the fixture matrix

Extend `tests/git_repo_builder.py` (created in stream A) and cover every remaining row of the
spec's regression table: trailer-only, branch-only, mixed, merge-subject with branch deleted, detached HEAD,
no-issue commits, and parity.

**Interfaces** — Consumes: A1's signatures. Produces: fixtures E1 reuses.

**Verify:** `python3 -m unittest tests.test_commit_resolution tests.test_linkage_check tests.test_project_converge -v`

---

### Stream E — Parity Proof and Completion

#### Task E1: Prove the two modules cannot drift again

Add a parity test asserting both modules return identical commit sets for the same range
across the full fixture matrix. It must fail if either module reintroduces a private matching
rule. Then confirm the motivating case: converge on issue 093's history collects the full
commit set including `scripts/project_issue_schema.py`.

**Interfaces** — Consumes: B1, B2, D1.

**Verify:** all three test modules, plus the converge command from the issue's Verification block.

#### Task E2: Completion gates

Run spec consistency, the full unittest suite, project validation, lifecycle drift, and
release check before handing off to review.

**Verify:**

```
python3 -m unittest discover -s tests
python3 scripts/project_lifecycle.py . --drift
python3 scripts/release_check.py .
```

---

## Gates

| Gate | Command | Pass condition |
| --- | --- | --- |
| Test | `python3 -m unittest discover -s tests` | All tests pass; no reduction from the current 741 |
| Parity | `tests.test_commit_resolution` parity case | Both modules return identical sets |
| Drift | `python3 scripts/project_lifecycle.py . --drift` | `[]` |
| Release | `python3 scripts/release_check.py .` | `errors: []` |
| Review | `product:review 095-commit-issue-resolution-parity` | Converge evidence shows the full commit set and a non-hidden unmatched count |

## Rollback

Each stream is a focused commit. `scripts/commit_resolution.py` is additive, and both consumer
changes are body replacements behind unchanged public names, so reverting Stream B restores
prior behavior without touching callers or tests outside the two modules. No data migration
and no history rewrite means rollback is a `git revert` of the consumer commits.
