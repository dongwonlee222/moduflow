# Issue 095 Attribution Architecture Redesign

## Decision

Replace repository-wide base selection with per-issue fork-point attribution,
and replace the resolver's flat global error list with diagnostics projected to
the caller's requested scope.

Branch-only attribution remains supported. The redesign does not require
rewriting history, adding mandatory trailers, or changing the
`codex/<issue-id>` convention.

## Why the Corrective Loop Kept Failing

The repeated failures were not independent edge cases. They came from three
architectural assumptions that do not hold in Git.

### 1. One repository does not have one usable attribution base

`base_ref()` selects one ref and applies it to every live issue branch. In
practice, branches can be cut from different points, from different remotes, or
from another issue branch. A base that is correct for one issue can over- or
under-attribute another.

This caused the stale-local, disconnected-ref, local-slash, multiple-remote,
and trunk-advanced-after-fork failures. Each corrective patch changed the
heuristic for choosing a ref tip, but the real question is different for every
topic branch: "where did this branch fork?"

### 2. Current ref tips are not historical fork evidence

A default branch normally advances after a topic branch is created. The current
`main` tip is therefore often not an ancestor of the topic branch even when it
is unquestionably the correct base lineage. Branches can also be renamed or
deleted after merge.

Using current tips to infer historical ownership made the answer depend on
repository cleanup and fetch state. Subject text then became a substitute for
missing graph evidence, which caused reordered octopus and multi-name merge
subjects to relabel content.

### 3. Attribution ambiguity is flattened into a global failure

`find_unlinked_behavior_commits()` knows the exact release range, but calls
`build_attribution()` without that range. The resolver scans all history and
returns one flat `errors` list. `release_check` then fails because of an
ambiguous historical merge even when that merge is unrelated to every commit
being released.

The full suite reproduced this at historical octopus merge
`777b04e6fe531d46a123aadbb236fcf3cb33e5c7`: focused attribution tests passed,
but the current release gate failed on an out-of-scope ambiguity.

### 4. The tests repeated the implementation's assumptions

The deleted reference oracle derived answers with the same base-selection
logic as the resolver. Later ground-truth shapes removed that shared oracle,
but coverage still grew one reported topology at a time. Passing cases proved
the enumerated shapes, not the invariants that equivalent refs, advancing
trunks, unrelated history, and subject reordering must preserve.

## Considered Approaches

### A. Continue strengthening the global-base heuristic

This is the smallest code change, but it has already produced multiple
corrective rounds. Every additional rule couples all topic branches and all
remotes more tightly. Rejected.

### B. Require explicit branch metadata or `Issue:` trailers

Persisting the issue and fork point when a branch is created would be the most
reliable future source. Mandatory trailers would be simpler still. Both
approaches fail Issue 095's compatibility requirement for existing branch-only
history and branches created by other tools. Deferred as a possible future
hardening layer, not used to close 095.

### C. Per-issue fork points with scoped diagnostics

For each issue branch, derive its own fork point from merge bases, calculate
only that branch's delta, and attach ambiguity to the affected branch, issue,
or commit. Consumers then project only diagnostics relevant to their query.
Selected.

## Architecture

Keep `scripts/commit_resolution.py` as the public API and policy owner. Move
Git snapshot and fork-point mechanics into a focused internal module,
`scripts/commit_graph.py`.

### `scripts/commit_graph.py`

Responsibilities:

- Load one repository snapshot: commit records, full ref names, ref object ids,
  and registered issue ids.
- Cache ancestry and merge-base queries.
- Collapse refs that point to the same object before comparing lineages.
- Derive a fork point for one topic ref.
- Derive stacked-issue exclusions for one topic ref.
- Return structured graph diagnostics instead of assigning issue ownership.

It does not parse trailers, choose source precedence, or know consumer policy.

### `scripts/commit_resolution.py`

Responsibilities:

- Parse trailer, branch-name, and merge-subject evidence.
- Build candidate claims from the graph snapshot.
- Apply `trailer > branch > merge-subject` once.
- Keep content commits single-owner and allow merge boundaries to carry
  multiple issue claims.
- Project claims and diagnostics to a requested scope.
- Preserve the existing public wrappers used by `linkage_check.py` and
  `project_converge.py`.

## Per-Issue Fork-Point Algorithm

For each live issue ref `topic`:

1. Gather non-issue base candidates from local and remote refs.
2. Collapse candidates with identical object ids.
3. Compute `merge-base(topic, candidate)` for each candidate.
4. Compare the merge-base commits, not the current candidate tips.
5. Select the unique ancestry-maximal merge base.
6. Treat multiple candidates producing the same merge base as equivalent.
7. If maximal merge bases are incomparable, mark only this topic branch
   unresolved.

This remains stable when `main` advances: the tip changes, but the merge base
between `topic` and the advanced `main` lineage stays at the historical fork.

For stacked issue branches, compute `merge-base(topic, other_issue_ref)` for
each other registered issue ref. Any pairwise merge base strictly below the
selected non-issue fork point is ignored. Maximal pairwise merge bases above
the fork point become exclusions. The topic delta is:

```text
git rev-list <topic> --not <fork-point> <stacked-issue-exclusions...>
```

The result is a candidate claim set. Global precedence and inner-first claim
ordering still decide final content ownership.

## Merge Attribution

- A two-parent merge with exactly one registered source issue may attribute
  its second-parent side to that issue.
- A merge boundary may retain all registered issue names found in its source
  description.
- Multi-name two-parent merges and octopus merges require graph
  corroboration for each content side.
- If branch refs no longer provide that corroboration, retain boundary claims
  but leave side content unresolved.
- Reordering subject tokens must never change content ownership.

An unresolved historical merge is not automatically a repository-wide error.
It becomes relevant only when the caller asks about that merge, its unresolved
content, or the affected issue.

## Scoped Diagnostic Model

The resolver returns:

- `fatal_errors`: Git command or snapshot failures that invalidate the whole
  requested operation.
- `diagnostics`: structured entries with `code`, `message`, and optional
  `sha`, `issue_id`, and `ref`.
- `degraded`: derived codes for the projected scope.
- `claims`: the attribution index.

Projection rules:

- Commit lookup: include diagnostics for that commit.
- Issue evidence: include diagnostics for that issue and commits collected for
  it.
- Release linkage: include diagnostics only for commits in
  `merge_base..HEAD` that touch behavior paths.
- Actual Git command failures needed to build the requested snapshot remain
  fatal.

`find_unlinked_behavior_commits()` must pass its known target SHA set into the
resolver instead of building an unscoped all-history result.

## Performance

The redesign preserves the no-per-commit-fan-out constraint.

- One Git log snapshot per resolver invocation.
- One full ref scan per invocation.
- Merge-base and ancestry queries cached by ref/commit pair.
- Work scales with issue refs and base candidates, not total commit count.
- Both query directions continue to reuse one attribution result.

## Test Strategy

Keep declared ground-truth shapes and add invariant-oriented metamorphic tests:

- Advancing a base ref after topic creation does not change the topic delta.
- Duplicating a ref as an equivalent local or remote ref does not change
  attribution.
- Adding an unrelated or disconnected ref does not change attribution.
- Reordering merge-subject issue tokens does not change content ownership.
- Adding an ambiguous historical merge outside a release range does not change
  that release result.
- Ambiguity inside the requested range is visible and fail-closed.
- Bare and indexed commit lookup return the same owner.
- Every Git boundary has ordinary-negative, command-failure, and terminated
  return-code coverage.

Full-suite and release-check verification must run before any new completion
claim. Focused suites are not sufficient closure evidence.

## Failure Memory and Traceability

`specs/095-commit-issue-resolution-parity/failure-history.md` is the durable,
append-only input to this design and every later attribution plan or review.
Each entry preserves the reproducing topology, observed failure, invalid
assumption, derived invariant, evidence, and current status.

Architecture requirements and invariant tests must link to one or more
`FH-*` ids. A new Critical or Important finding is recorded in the corpus
before another fix begins. Passing a focused suite may record a regression,
but cannot close the entry; closure requires the relevant invariant, full
suite, release check, and independent review.

## Migration and Compatibility

- Existing consumers keep their public function signatures.
- Existing `Issue:` trailers and branch names remain valid.
- No repository history is rewritten.
- Current heuristic code is replaced rather than extended with another
  special-case branch.
- Issue 096 remains a separate proposed command-safety handoff.
- The installed plugin remains unchanged until 095 and 096 both pass their
  independent gates.

## Completion Gates

Issue 095 returns to review only when all of the following are true:

- Fork-point invariant tests pass.
- Focused resolver/parity/linkage/converge tests pass with zero expected
  failures.
- Full unittest discovery passes.
- `release_check.py` returns `valid: true` with `errors: []`.
- Project validation is valid and lifecycle drift is empty.
- Independent spec and quality reviews report no Critical or Important
  findings.
- Every Critical or Important finding has a failure-history entry and a
  mapped regression or invariant test.
- Issue 093 evidence still includes `scripts/project_issue_schema.py`.
