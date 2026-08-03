# Spec: Commit-to-Issue Resolution Parity

Issue: `095-commit-issue-resolution-parity`
Prev: `093-frontmatter-issue-schema-readiness-gate` · Next: `product:status`

## Problem

Two modules answer "which issue owns this commit?" with different rules, in opposite
directions, and neither reports what it failed to match.

| Module | Direction | Sources recognized | Git calls |
| --- | --- | --- | --- |
| `scripts/linkage_check.py` `resolve_issue_for_commit()` | commit → issue | `trailer`, `branch` (`git branch --contains`) | per commit: `git show` + `git branch --contains` |
| `scripts/project_converge.py` `resolve_commits()` | issue → commits | `trailer`, `merge-subject` | one `git log` for the whole history |

Neither is a superset of the other. `linkage_check` has no merge-subject rule;
`project_converge` has no branch fallback. A commit reachable only through its branch
name is invisible to converge.

### Measured on `main` at `6bca2b4`, 2026-07-26

Re-running the issue's original observation after issue 093 was merged into `main`:

```
project_converge --issue-id 093-... --evidence --json
  commits: 10   (source: trailer 9, merge-subject 1)
  errors:  []

linkage_check.resolve_issue_for_commit over the same 155-commit window
  attributed to 093: 53
```

At least 43 commits are missing from the converge payload, and `errors` is empty. The
original report measured 1 of 44 on the unmerged branch; merging into `main` raised the
count but did not close the gap. The defect is structural, not a branch-lifetime artifact.

`commands/product-review.md` step 5 calls converge "the final evidence step". A reviewer or
judge reading that payload sees ten commits, an empty error list, and no indication that
anything was dropped. Meanwhile `release_check`'s linkage gate passes the same history,
because its branch fallback resolves the commits converge cannot see. Two gates disagree
about one history, and the weaker one feeds review evidence.

This is the failure class issue 093 was built to eliminate — a gate reporting success while
the evidence contradicting it sits in reach — reappearing at the commit layer instead of the
issue layer.

## Goals

- One resolution path, shared by both consumers, recognizing all three sources.
- Under-collection is always visible in the payload. A reviewer never counts commits by hand.
- Converge keeps its single-`git log` cost profile. Correctness must not be bought with a
  per-commit subprocess fan-out.

## Non-Goals

- Changing the `Issue:` trailer format or the `codex/<issue-id>` branch convention.
- Rewriting existing history to add trailers.
- Making converge gate the review verdict. It stays reported, never blocking.
- Unifying the two modules' *other* responsibilities. Only commit resolution moves.

## Product Decisions

### 1. One resolver, both directions

A single module owns commit-to-issue resolution and exposes both query directions over one
shared rule set. `linkage_check.py` and `project_converge.py` delegate; neither keeps a
second implementation. Public helper names in both modules may remain as thin wrappers so
existing callers and tests are unaffected.

### 2. Source precedence is fixed and explicit

`trailer` > `branch` > `merge-subject`. A commit matching more than one source is recorded
once, at the highest-precedence source that matched. Trailer wins because it is intrinsic to
the commit object; branch and merge-subject are positional evidence about where a commit
happened to land.

This preserves `linkage_check` Global Constraint 7 (trailer beats branch) and extends it
rather than replacing it.

### 3. Branch resolution stays a fallback, and says so

Branch-name evidence disappears when a branch is renamed or deleted, and is unavailable in a
detached-HEAD worktree. It is never promoted above the trailer, and any result that depended
on it is marked so a reader can weigh it.

### 4. Unmatched commits are counted, not silently dropped

The converge evidence payload reports how many commits in the examined range matched no
issue, alongside the per-commit resolution source. A run that drops commits cannot present an
empty `errors` list with no other signal.

`unmatched_count` is descriptive, not an error. Most repository commits legitimately belong
to no issue; the number exists so a reader can tell "43 unmatched" from "0 unmatched" at a
glance.

### 5. Degraded resolution is reported, not failed

In a detached-HEAD worktree, trailer resolution still works and branch resolution cannot. The
resolver returns what it can and records that branch resolution was unavailable. It does not
raise, and it does not silently behave as though no branch-linked commits exist.

The limitation is a SHA-scoped structured diagnostic with code
`detached-head-branch-unavailable`. It projects through the existing
`branch-unavailable` degradation and compatibility-error surfaces only for the
current detached HEAD. Attached unrelated commits and other SHAs read from a
reused whole index remain ordinary unmatched results.

For HEAD-state Git boundaries, symbolic-ref rc=1 is the only ordinary
detached result. Command failure, signal termination, and malformed successful
output fail closed, and detached SHA output is trusted only when it names one
known snapshot record.

## Proposed Architecture

A resolver module holding the rules, the precedence order, and the git access strategy.

```
                      ┌─────────────────────────────┐
  linkage_check.py ──▶│  commit → issue  (per sha)  │
                      │                             │──▶ trailer / branch / merge-subject
project_converge.py ──▶│  issue → commits (per id)   │     + unmatched count
                      └─────────────────────────────┘
```

Both entry points read the same trailer regex, the same `codex/<issue-id>` branch grammar,
and the same precedence order.

### Cost constraint

`linkage_check` currently runs two subprocesses per commit. Converge scans full history in
one `git log`. A naive unification that gave converge the per-commit path would multiply its
git calls by the size of history — on the 155-commit sample above that is over 300
subprocesses where one sufficed.

The resolver therefore builds branch membership **once per invocation** — a single
`git for-each-ref` plus reachability computed from the log already being read — rather than
calling `git branch --contains` per commit. Per-commit callers may still ask for one sha; the
batch path is what converge uses.

## Acceptance Criteria

- Both consumers query one attribution index and one precedence policy:
  `trailer > branch > merge-subject`.
- A content commit has exactly one owner under that global precedence. A merge
  boundary may be attributed to multiple issues when it connects their
  histories; precedence still applies within each issue's claim.
- Parity across every declared shape proves consistency rather than literal set
  identity: the owner returned by `linkage_check.py` is among the issues that
  `project_converge.py` claims, and every commit collected by converge resolves
  through the same index and policy.
- Converge evidence for issue 093 includes
  `scripts/project_issue_schema.py` among the changed files.
- The evidence payload carries an unmatched-commit count and a per-commit resolution source.
- Resolution succeeds in a detached-HEAD worktree for trailer-bearing commits and reports that
  branch resolution was unavailable.
- Converge's git subprocess count does not scale with history length.
- `python3 -m unittest tests.test_linkage_check tests.test_project_converge -v` passes.
- `python3 scripts/release_check.py .` passes.

## Regression Coverage

Fixtures build throwaway git repositories; no test depends on this checkout's history.

| Case | Expectation |
| --- | --- |
| Trailer-only history | Both directions resolve; source `trailer` |
| Branch-only history | Both directions resolve; source `branch` |
| Mixed history | Trailer wins on commits carrying both |
| Merge-subject only, branch deleted | Resolves; source `merge-subject` |
| Detached HEAD | Trailer resolves; branch unavailable is reported |
| Commits belonging to no issue | Counted as unmatched; `errors` stays empty |
| Global precedence | Content commits have one owner; merge boundaries may have multiple issue claims |
| Parity | Both query directions are consistent with the same attribution index |

## Dogfood Expectation

Issue 093 is the live verification target. Its converge evidence must include
`scripts/project_issue_schema.py`; no exact historical commit count is part of
the acceptance criterion because the reachable history changes as branches and
merges evolve.
