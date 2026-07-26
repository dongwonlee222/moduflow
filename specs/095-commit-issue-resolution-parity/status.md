# Issue 095 Execution Status

**Status: active** — started 2026-07-26. Streams A through E implemented; review is the next gate.

## Progress

| Stream | Task | State | Commit |
| --- | --- | --- | --- |
| A | A1 shared resolver module | done | `5f24e86` |
| A | A2 batched branch membership | done | `5f24e86` |
| A | parity made structural via one attribution index | done | `7a70138` |
| B | B1 `linkage_check` delegates | done | `dee42dc` |
| B | B2 `project_converge` delegates, reports gaps | done | `5f8fd42` |
| C | C1 surface unmatched count for reviewers | done | pending commit |
| D | D1 extend the regression matrix | done | pending commit |
| E | E1 cross-module parity proof | done | pending commit |
| E | E2 completion gates | done | pending commit |

## Stream A outcome

`scripts/commit_resolution.py` owns trailer, branch, and merge-subject matching and the
`trailer > branch > merge-subject` precedence. Consumers are untouched in this stream; they
migrate in stream B.

### Correction found during implementation

The spec assumed adding a branch fallback was sufficient. Running it proved otherwise:
branch *containment* is not branch *authorship*.

| Strategy | Commits attributed to issue 093 | Verdict |
| --- | --- | --- |
| `git rev-list <branch>` | 279 | Over-collects — a branch cut from main carries all of main as ancestors |
| `git rev-list <branch> --not main` | 0 | Under-collects — empty once the branch is merged |
| `git rev-list <merge>^2 --not <merge>^1` | 52 | Correct |

Merged work is now delimited by walking the merge commit's second-parent side and
subtracting its first-parent side. That walk runs on the log records already parsed for
trailer matching, so it adds no subprocess — a stronger position on Global Constraint 4 than
the plan required. Unmerged branches, which have no merge commit to delimit them, use
branch-exclusive `rev-list` bounded by branch count.

Both failure modes are pinned by tests in `TestOverCollection`.

## Verification at `c9273f1`

```bash
python3 -m unittest tests.test_commit_resolution -v
```

Result: `15/15` passed.

```bash
python3 -m unittest discover -s tests
```

Result: `756/756` passed, `OK` (741 before, plus 15 resolver tests).

```bash
python3 scripts/release_check.py .
```

Result: `errors: []`.

```bash
python3 scripts/project_lifecycle.py . --drift
```

Result: `[]`.

### Measured against the real defect

Resolver output for issue 093 on `main`:

| Field | Value |
| --- | --- |
| `commits` | 57 — trailer 9, branch 47, merge-subject 1 |
| merge-side coverage | 52 of 52 |
| `scripts/project_issue_schema.py` present | yes |
| `unmatched_count` | 102 of 287 examined (final; 147 of 283 at the A-stream measurement) |
| `errors` | `[]` |

The 57 decomposes as 52 merge-side commits, 4 trailer-bearing commits landed outside the
merge, and the merge commit itself. `project_converge` collected 10 for the same issue before
this work; the gap closed when stream B migrated it to this module.

## Streams B through E outcome

Both consumers now delegate. Measured on issue 093 through `project_converge` itself:

| Field | Before | After |
| --- | --- | --- |
| `commits` | 10 | 57 — trailer 9, branch 47, merge-subject 1 |
| `scripts/project_issue_schema.py` in bundle | absent | present |
| `unmatched_count` | not reported | 102 of 287 examined |
| `errors` | `[]` | `[]` |

`linkage_check` resolved identically to its previous implementation on 30 real commits
(0 differ) while gaining the merge-subject source it never had.

### Corrections found by running rather than reasoning

| Where | What | How it surfaced |
| --- | --- | --- |
| A | `git rev-list <branch>` attributed 279 commits to issue 093 against 52 contributed | Ran the resolver on real history instead of trusting the spec's assumption |
| A | Only one of the two directions walked merge topology; they disagreed on 13 of 30 commits | Compared against the existing `linkage_check` before migrating anything |
| B1 | Eager index build broke `test_neutral_only_commit_ignored` | An existing test asserted neutral-only ranges do no resolution work; it was right |
| B2 | `codex/<id>-<suffix>` resolved the suffix into the issue id | Existing converge test for suffixed work branches |

### Constraint amended

Global Constraint 7 as first written also froze existing tests. `test_linkage_check`,
`test_release_check`, and `test_project_converge` stub git commands by exact tuple, and the
shared resolver issues different ones. Honoring the freeze would have required a second,
containment-based resolution path — the split this issue exists to remove. Amended with the
reasoning in `plan.md`; every assertion on returned values is unchanged and no scenario was
dropped. The one exception is `test_full_evidence_shape`, whose key list gains the two fields
B2 exists to add.

### Regression protection

The parity suite was checked by breaking the thing it guards: removing branch-sourced commits
from `project_converge` fails 3 of its 11 tests. It is not a test that passes by construction.

## Known gaps

- Review has not run. `product:review` is the next gate.
- `project_converge --evidence` overwrites `specs/<issue>/converge-evidence.json` with no
  confirmation. Running it twice during this work silently rewrote issue 093's completed
  review record, restored both times. Out of scope here; worth its own issue.

## Review

Run 2026-07-26 at head `5dc5fdd` by Claude Opus 5, inline.

**Limitation — single reviewer.** Subagent dispatch was withheld this session by operator
instruction, so every finding below is a single-reviewer judgment rather than independent
multi-reviewer consensus. The reviewer is also the implementer, which is the weakest possible
review configuration; findings 1 and 2 were found by running the code against this repository
rather than by reading the diff, and a reader should assume defects of the same kind remain
where no such run was performed.

Verification reproduced at review time: `unittest discover` 774 passed `OK`;
`release_check.py` errors `[]`; lifecycle drift `[]`; spec consistency 0 error 0 warn.

Verdict: **request changes**. Finding 1 is a dead code path in shipped code.

| # | Finding | Verdict | Severity |
| --- | --- | --- | --- |
| 1 | `build_branch_membership` returns an empty map on this repository — 20 issue branches detected, 0 commits attributed. The live-branch source is dead. | Confirmed | High |
| 2 | The degraded probe issues `git branch --contains` once per unresolved commit, reintroducing the per-commit fan-out task A2 removed | Confirmed | Medium |
| 3 | No fixture creates a remote-tracking ref, which is why finding 1 passed 33 new tests | Confirmed | Medium |
| 4 | Branch-name filtering in `build_branch_membership` duplicates parsing that `issue_id_from_branch` already owns | Confirmed | Low |

### Finding 1 — live-branch membership resolves nothing

`build_branch_membership` builds its rev-list as:

```
git rev-list <branch> --not --exclude=<branch> --branches --remotes
```

`--exclude` applies only to the **next** ref glob. With `--branches` first, the exclusion is
consumed there — where a remote branch does not appear — and `--remotes` then re-includes the
branch itself. The branch excludes itself, and the result is empty. Measured:

| Command | Result |
| --- | --- |
| `rev-list <b> --not --exclude=<b> --branches --remotes` | 0 commits |
| `rev-list <b> --not --exclude=<b> --remotes --branches` | 1 commit |
| `rev-list <b> --not main` | 1 commit |

Impact: `resolve_commits_for_issue("092-project-home-dashboard")` returns 0 commits, though
`origin/codex/092-current-dashboard-korean` carries one. Issue 081 still resolves 6 because
those come through merge topology, which masks the failure on merged work — most of this
repository. **Unmerged branch work is exactly the case this issue exists to make visible, and
it is the case that does not work.**

The measured 10 → 57 improvement on issue 093 stands: it comes from merge topology and
trailers, neither of which is affected.

### Finding 2 — per-commit fan-out returns through the degraded probe

`resolve_issue_for_commit` runs `git branch --contains <sha>` when nothing matched, to decide
whether to report `branch-unavailable`. Measured: resolving 5 unmatched commits issued 5
`git show` plus 5 `git branch` calls. In `find_unlinked_behavior_commits`, whose range can be
large and whose commits are frequently unmatched, this scales with the number of unlinked
commits — the shape Global Constraint 4 exists to prevent, arriving through the diagnostic
path rather than the resolution path.

### Finding 3 — the fixture gap that let finding 1 through

`tests/git_repo_builder.py` never runs `git remote add` or `git push`; no test constructs a
remote-tracking ref. Local-only branches take the `--branches` glob, where `--exclude` does
apply, so every fixture exercises the one arrangement in which the bug is invisible. 33 new
tests passed over a broken path. The regression matrix needs a remote-ref row.

### Finding 4 — duplicated branch parsing

`build_branch_membership` inlines its own name-splitting and `BRANCH_ISSUE_RE` match to decide
whether a ref is issue-shaped, duplicating logic `issue_id_from_branch` already owns. Global
Constraint 1 puts branch-name interpretation in one place; this is a second copy inside the
same module. It is also a single dense expression that resisted review by reading.

### Spec compliance versus quality

Separated per the review integrity rules:

- **Spec compliance:** partial. The acceptance criterion "converge evidence on issue 093
  collects all commits and includes `project_issue_schema.py`" is met and measured. The
  criterion "`project_converge` and `linkage_check` resolve identical commit sets, proven by a
  parity test" is met in the sense that both read one index — but both are equally wrong for
  live branches, so parity is satisfied while correctness is not. A parity test cannot detect
  a defect shared by construction; that is a real limit of the chosen proof, not a gap in its
  execution.
- **Quality:** finding 1 is a shipped dead path. Findings 2 and 4 are constraint drift.

### Not verifiable from this review

- Behavior in a repository whose issue branches are local-only was not exercised against real
  history; only fixtures cover it, and per finding 3 the fixtures cover only that shape.
- Detached-HEAD behavior is fixture-covered but was never run against this repository.

## Conditions before PR

1. Fix finding 1 and add a fixture with a remote-tracking ref that fails without the fix.
2. Resolve finding 2 — either drop the probe or fold the branch-unavailable signal into the
   index that is already built.
3. Finding 4 is optional cleanup; record the decision either way.

## Next gate

Address the conditions above, then re-review before `product:pr`.
