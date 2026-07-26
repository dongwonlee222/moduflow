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

## Next gate

`product:review 095-commit-issue-resolution-parity`.
