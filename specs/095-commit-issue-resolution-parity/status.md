# Issue 095 Execution Status

**Status: active** — started 2026-07-26. Stream A implemented; streams B, C, D, E open.

## Progress

| Stream | Task | State | Commit |
| --- | --- | --- | --- |
| A | A1 shared resolver module | done | `c9273f1` |
| A | A2 batched branch membership | done | `c9273f1` |
| B | B1 `linkage_check` delegates | open | — |
| B | B2 `project_converge` delegates, reports gaps | open | — |
| C | C1 surface unmatched count for reviewers | open | — |
| D | D1 extend the fixture matrix | open | — |
| E | E1 cross-module parity proof | open | — |
| E | E2 completion gates | open | — |

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
| `unmatched_count` | 147 of 283 examined |
| `errors` | `[]` |

The 57 decomposes as 52 merge-side commits, 4 trailer-bearing commits landed outside the
merge, and the merge commit itself. `project_converge` collected 10 for the same issue before
this work; the gap closes when stream B migrates it to this module.

## Known gaps

- Consumers still run their own resolution. The measured improvement is not yet visible to
  `product:review`, which reads converge output — that lands in B2.
- `tests/git_repo_builder.py` covers the cases stream A needed. The remaining rows of the
  spec's regression table are stream D.
- The plan listed the builder under `tests/fixtures/`; it lives at the tests root because
  `tests/fixtures/` holds data fixtures rather than importable modules. Plan and tasks were
  corrected to match.

## Next gate

`product:execute` continues with stream B. B1 and B2 touch different files and may run in
parallel.
