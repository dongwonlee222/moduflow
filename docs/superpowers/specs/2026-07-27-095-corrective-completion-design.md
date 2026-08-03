# Issue 095 Corrective Completion Design

## Decision

Issue 095 closes through a corrective branch, not by accepting the four
`expectedFailure` markers as a green test result. The resolver must produce
stable, fail-closed commit attribution before the issue can return to review.

Issue 096 remains a separate delivery unit for converge command safety:
read-only evidence by default, issue-id path containment, and symlink
containment. The Codex plugin is not refreshed from the repository until both
issues pass their own review gates.

## Resolver Model

The attribution index remains the only source used by both consumers.

- A non-merge content commit has one owner.
- Source precedence is global: `trailer > branch > merge-subject`.
- A merge boundary may belong to more than one issue, because it records both
  the branch being integrated and the branch receiving it.
- Nested merge content remains with the inner issue; an outer merge cannot
  re-label that content as its own.
- A trailer or branch only resolves when its issue exists in Git history.

## Repository Model

Issue identity is derived from Git history rather than the checked-out index,
so identical refs and history give identical answers from every checkout.

Base selection follows this order:

1. The remote default branch from `refs/remotes/origin/HEAD`.
2. A remote-tracking counterpart of a non-issue local branch.
3. A non-issue branch that is an ancestor of the issue branches.

Issue-shaped branches are never eligible to become the base. Git failures are
returned through `errors`; they are not treated as ordinary graph answers.

## Test Model

The four known findings become ordinary tests:

- `R9-1`: nested merge content isolation.
- `R9-2`: stale local base selection.
- `R9-3`: global trailer precedence.
- `R9-4`: indexed and non-indexed calls use the same precedence implementation.

Additional regression tests cover an unavailable Git graph command, a missing
issue referenced by trailer or branch, and checkout-independent issue
discovery. The focused suite and the full suite must finish with zero expected
failures.

## Lifecycle

The canonical issue, refined spec, tasks, state, loop state, PR handoff, and
Korean review packet must describe the same phase and acceptance criteria.
Issue 095 remains active until independent spec and quality review pass.

## Out of Scope

The following stay in Issue 096:

- Making `project_converge.py --evidence` read-only by default.
- Rejecting `--issue-id` path traversal.
- Rejecting evidence files that resolve outside the repository through a
  symlink.
- Announcing every evidence write.
