# Issue 095 Execution Status

**Status: active** — started 2026-07-26. Corrective implementation is complete; final review gates are next. Earlier review rounds below are retained as history; the latest state is in “Corrective completion — 2026-07-27”.

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
| E | E2 historical completion gates | superseded by F4 | — |
| F | F1 fail-closed registry and graph handling | done | `21d1290`, `881d81d` |
| F | F2 global precedence and safe base selection | done | `ef149a8`, `4f5d14a` |
| F | F3 artifact and lifecycle reconciliation | done | this documentation commit |
| F | F4 full verification and final review | pending | — |

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

## Review round 2 — conditions addressed

Fixes applied 2026-07-26 after the review above. All four findings are resolved; two
corrections to the review record itself are recorded below, because parts of round 1 were
wrong and leaving them would let the next reader build on a false premise.

### Finding 1 had two causes, not one

Round 1 identified the `--exclude` glob semantics. That was real, but fixing it alone would
have left the defect standing. `build_attribution` also ran a bare `git log`, which walks
HEAD only — commits on an unmerged branch are not reachable from HEAD, so they never entered
`records` and the membership loop skipped them with `if sha not in records: continue`.

| Cause | Fix |
| --- | --- |
| `--exclude` applies only to the next ref glob, so a remote counterpart re-included the branch and it excluded itself | Exclusion is now an explicit ref list; `_same_branch` treats `codex/X` and `origin/codex/X` as one branch |
| `git log` walks HEAD only, so unmerged commits were never in the record set | `GIT_LOG_ARGS` now carries `--branches --remotes`; `project_converge` re-exports the constant so both stay in step |

Measured on this repository: `build_branch_membership` went from 0 attributed commits to 11.

### Correction — the round 1 example was wrong

Round 1 offered issue 092 as evidence: "`resolve_commits_for_issue("092-project-home-dashboard")`
returns 0 commits, though `origin/codex/092-current-dashboard-korean` carries one."

**That example does not demonstrate the defect.** The branch is named
`codex/092-current-dashboard-korean`; the issue is `092-project-home-dashboard`. The names do
not match, so the branch is not attributable to that issue under the `codex/<issue-id>`
convention — and 092 still resolves 0 commits after the fix, correctly. The finding was real
and the fix is measured; the evidence cited for it was not.

What actually recovered:

| Issue | Commits recovered via membership |
| --- | --- |
| `051-autonomous-execute-review-visual-handoff` | 3 |
| `086-project-aware-production-library-dashboard` | 4 |

### Findings 2, 3, 4

- **2** — the per-commit `git branch --contains` probe is removed. Whether branch evidence was
  consultable is a property of the index, which `build_attribution` already reports; probing
  per commit answered a question the index had already answered. A test now asserts no
  `git branch --contains` is issued while resolving a range.
- **3** — `GitRepo.publish()` creates a remote-tracking ref without a server, and three tests
  cover a live branch with a remote counterpart, a remote-only branch, and the guarantee that
  fixing self-exclusion does not reopen the over-collection defect. All three fail without the
  finding 1 fix.
- **4** — `build_branch_membership` now calls `issue_id_from_branch` instead of inlining its
  own match, so branch-name interpretation has one owner again (GC1).

### New observation, not a finding against this change

With membership working, two of the four branches it attributes resolve to issue ids that do
not exist in `issues/`:

| Branch | Resolved id | Exists |
| --- | --- | --- |
| `codex/034-pr-ready-and-dashboard-db-followup` | `034-pr-ready-and-dashboard-db-followup` | no |
| `codex/092-current-dashboard-korean` | `092-current-dashboard-korean` | no |

The resolver behaves as specified — with no known id matching, the branch tail is treated as
the id. The branches simply do not follow `codex/<issue-id>`. Whether the resolver should
reject, warn on, or keep accepting an unknown id is a design decision outside this issue's
scope. Recorded here rather than fixed.

### Verification after fixes

```
python3 -m unittest discover -s tests     778 passed, OK  (774 before, plus 4)
python3 scripts/release_check.py .        errors []
python3 scripts/project_lifecycle.py . --drift   []
```

Test-stub updates: `GIT_LOG_ARGS` changed shape, so `test_linkage_check` and
`test_release_check` now reference the module constant rather than a literal tuple, and three
`rev-list` stubs moved to the explicit-ref form. Assertions on returned values are unchanged.

### Remaining review limitation

Still a single reviewer, still the implementer. Round 1 found two defects by running the code
and one by reading it; round 2 found a third cause of finding 1 — again by running, not by
reading — and an error in round 1's own evidence. The pattern is that reading this diff does
not surface its defects. An independent reviewer executing against a repository with unmerged
branches remains the useful next check.

## Review round 3 — independent

Run 2026-07-26 at head `41e539b` by an independent reviewer (subagent, read-only; repository
verified unmutated afterward). Dispatched after two self-review rounds, on the observation
that reading this diff had not been surfacing its defects.

**Verdict: request changes.** Twelve findings. Two acceptance criteria fail.

| AC | Verdict |
| --- | --- |
| 1. Both modules resolve identical commit sets for the same range | **FAIL** (F1) |
| 2. Converge on 093 collects the full set including `project_issue_schema.py` | PASS — 57 commits, 46 files, present |
| 3. Payload carries unmatched count and per-commit source | PASS structurally; the number is not actionable (F8) |
| 4. Detached HEAD resolves trailers and reports the limitation | **FAIL** (F2, F3) |
| 5. Git calls do not scale with history | PASS — 24 calls / 309 commits / 26 refs |
| 6–7. `unittest`, `release_check` | PASS |

### Findings

| # | Finding | Severity |
| --- | --- | --- |
| F1 | The two consumers still disagree. `resolve_issue_for_commit` short-circuits on `git show` before the index; `build_attribution` only sees `--branches --remotes`. A commit outside that window resolves one way and not the other. | High |
| F5 | `Merge branch 'main' into codex/<id>` names the issue in its subject, so the second-parent side — *main* — is claimed for the issue. Live here: issue 081's PR merge sits inside issue 093's evidence bundle. | High |
| F6 | Branch-exclusive rev-list excludes by name, so any other ref covering the tip (a stacked or follow-up branch) zeroes the branch silently. `codex/089-…` and `codex/089-…-release` are that arrangement. | High |
| F7 | When every other ref is the branch's own counterpart the exclusion list is empty and `rev-list <b> --not` returns all ancestors — the 279-vs-52 over-collection returns. Triggered by `clone --single-branch`. | High |
| F2 | `resolve_commits_for_issue` returns nothing at all in a detached HEAD, including trailer-bearing commits. | High |
| F3 | `branch-unavailable` fires when no issue-shaped ref exists, not when branch resolution is unavailable — false positive on healthy repos, false negative in the detached-HEAD case the spec names. | Medium |
| F4 | Neither consumer surfaces `degraded`. The resolver reports degradation into a channel nothing reads. | Medium |
| F8 | `unmatched_count` is a repository-wide constant — 107 of 309 for every issue, including one that does not exist. It cannot distinguish a run that dropped commits from one that had unrelated ones, which is the job its own comment claims. | Medium |
| F9 | Nested merges attribute the inner branch's commits to the outer issue, silently. | Medium |
| F10 | Octopus merges lose every parent past the second. | Low |
| F11 | `hooks/on_stop.py` reads branch grammar from `linkage_check`'s private copy — a third owner (GC1). Four now-unreferenced helpers remain in `linkage_check` and read as a live second rule set. | Low |
| F12 | `resolve_issue_for_commit` runs `git show` even when the supplied index already holds the answer. | Low |

Probed and clean: real-repo membership matches ground truth on all 20 issue refs; empty
repository; shallow clone; repo with no remotes; non-conforming branch names; merge with an
empty branch side; trailer-over-branch precedence in every arrangement built; GC4 subprocess
scaling across three repositories.

### What this round says about the previous two

Round 1 found 4 findings, round 2 found a fifth cause and an error in round 1's own evidence,
and this round found 12 — including three High-severity over- and under-collection defects in
code that had already passed two reviews and 778 tests. F1 and F6 are the same class as round
1's finding 3 and round 2's fix respectively: each earlier round repaired the instance it was
shown and not the class. F5 is live damage in this repository right now.

The fixtures are the common thread. Every parity fixture leaves HEAD on a branch, so
`rev-list HEAD` is a subset of the index window by construction and F1 cannot appear.
`TestDetachedHead` detaches after committing, so its commit is still on `main` and F2 cannot
appear. `TestDetachedHead.test_branch_only_commit_reports_degraded_not_silent` passes with
`repo.detach()` removed — verified by the reviewer — so it does not pin what its name claims.

### Reviewer limitations, as reported

- `project_converge.py --evidence` was not run because it mutates; `collect_evidence()` was
  imported and called directly instead.
- Ref-count scaling was measured only to 26 refs. `rev-list` argv grows O(refs) per branch
  across O(branches) calls, so cost is O(branches × refs) in argv — unmeasured beyond that.
- Detached HEAD was simulated by clone plus `--detach` rather than `git worktree add`.

## Review round 4 — differential oracle

Round 3's finding was not really twelve defects; it was that three rounds had each fixed the
case they were handed while the tests kept encoding the same understanding of git that
produced the bugs. Fixing twelve items the same way would have produced a thirteenth.

So correctness is no longer decided by the author's model of git:

| File | Role |
| --- | --- |
| `tests/commit_resolution_reference.py` | A slow, obviously-correct resolver. Asks git one plain question at a time — no index, no batching. Too slow to ship, which is the point. |
| `tests/commit_resolution_shapes.py` | Eleven repository shapes, chosen for what the author had least reason to try. Five are arrangements that exist in this repository today. |
| `tests/test_commit_resolution_differential.py` | Runs the shipped resolver against the oracle across every shape. |

It found four divergences on first run, without being told what to look for:

| Shape | Divergence | Matches |
| --- | --- | --- |
| `sync_merge_then_pr_merge` | 2 extra — main's history claimed for the issue | F5 |
| `stacked_live_branches` | 2 missing — descendant branch zeroed its parent | F6 |
| `detached_before_commit` | 2 missing — commits on no branch never entered the record set | F2 |
| `nested_merges` | 1 missing — inner branch's commit claimed by the outer issue | F9 |

### Fixes

- **F5** — `merge_source_issue` reads merge direction from the subject. `Merge branch 'main'
  into codex/X` merges the base *into* the branch, so its second-parent side is main's
  history, not the issue's. Only a merge that brought the branch *in* contributes its side.
- **F6, F7** — a branch's contribution is now what it has that the *base branch* does not,
  rather than what no other ref contains. Excluding every other ref let an unmerged descendant
  zero its parent, and left nothing to exclude at all in a single-branch clone.
- **F2** — `GIT_LOG_ARGS` uses `--all`, which covers every ref plus HEAD. `--branches
  --remotes` missed a detached worktree entirely.
- **F9** — attribution is `{sha: {issue_id: source}}`. A commit can belong to more than one
  issue when a branch is merged into another before reaching main; the single-owner map
  silently dropped the inner one.

### Measured on this repository

| | Before | After |
| --- | --- | --- |
| Issue 081's PR merge attributed to | `093` (`branch`) | `081` (`merge-subject`) |
| Issue 093 commit count | 57 | 53 |
| Issue 093 bundle contains 081's merge | yes | no |

The drop from 57 to 53 is the sync-merge over-collection being removed, not evidence being
lost.

### Verification

```
python3 -m unittest tests.test_commit_resolution_differential    11/11 OK
python3 -m unittest discover -s tests                           789/789 OK
python3 scripts/release_check.py .                              errors []
```

### Still open from round 3

F1, F3, F4, F8, F10, F11, F12 are not addressed in this round. F8 in particular —
`unmatched_count` being a repository-wide constant rather than a property of the run — is a
contract problem, not a bug fix, and needs a decision about what the number should mean.

## Review round 5 — second independent review

Run 2026-07-26 at head `81b943b`, read-only, repository verified unmutated. Eight of round 3's
twelve findings had been addressed; this pass judged the fixes and the new apparatus.

**Verdict: request changes.** The round-4 claim that consumer parity was proven is false.

### Q1 — The AC1 parity test cannot fail. Critical.

`ConsumerParityTests` compares `build_attribution` to itself: both sides of every assertion
are sourced from the same function, and `if sha in converge: assertTrue(claimed)` is true by
construction because converge only emits shas that have attribution. The reviewer
mutation-tested it in process:

| Mutation | Result |
| --- | --- |
| baseline | passes |
| converge returns nothing — **issue 095's founding defect** | passes |
| linkage_check resolves every commit to `None` | passes |
| both consumers return nothing | passes |
| linkage_check reintroduces its pre-095 private rule | passes |
| project_converge reintroduces its pre-095 private rule | passes |

The spec's wording — "fails if either module reintroduces a private rule" — is falsified by
the last two rows. Commit `81b943b` is titled "prove consumer parity across all shapes"; it
proves nothing. There is also no reference implementation for the commit→issue direction, so
half of AC1 has no oracle at all.

### Q3 — The round-4 shape encodes over-collection as correct. High.

`stacked_live_branches`, added to fix F6, asserts that issue `102-beta` collects three commits
when it contributed one — the other two are `101-alpha`'s branch. The F6 fix turned an
under-collection defect into an over-collection defect of the same class as F5, and the
differential suite blesses it because implementation and oracle share the same base-ref rule.
Latent rather than live here (`089-…-release` is not a registered issue id, so both refs map to
one issue); it fires when two registered issues are stacked.

### Q4 — `base_ref` prefers a stale local `main` over `origin/main`. High.

Ground truth 2 commits, oracle 6, implementation 6, differential agrees. Any fork, CI
checkout, or clone whose local `main` has not been fast-forwarded re-opens the 279-versus-52
over-collection this module's docstring claims to have closed. No shape can reach it —
`git_repo_builder` hardcodes `init -b main` and every shape checks out `main`.

### Q5 — The oracle is only half independent. High.

Independent: the graph layer (`git rev-list` subprocesses versus in-memory reachability). That
half earned its four round-4 catches. Verbatim copies: `merge_source_issue`, `BASE_CANDIDATES`,
and the longest-prefix branch rule. Mutation results:

| Mutation | Differential suite |
| --- | --- |
| drop the branch source | catches |
| ignore merge direction (F5) | catches |
| `base_ref` always `None` | catches |
| `base_ref` prefers `origin/main` | **blind** |
| trailer regex tightened | **blind** |

Q3, Q4 and Q6 are all instances of the blind half.

### Q6 — Shapes that break the implementation and that no shape builds. High/Medium.

- Non-`main` default branch (`init -b develop`): ground truth 2, both 0, differential agrees.
- Octopus merge: F10 is worse than described — `102-beta` gets **zero** commits, its work
  attributed to nothing at all, not merely "parents past the second lost".
- `` inside a commit body: `GIT_LOG_FORMAT` uses it as the record terminator with no
  escaping, so one such commit corrupts its neighbours and is dropped from every path
  including its own trailer. The differential suite *would* catch this; no shape builds it.

Clean, verified against subjects git actually generates: merge-subject parsing across
`--no-ff`, remote-tracking, GitHub PR and squash merges, `Merge tag`, reverts, prose
containing " into ", and a non-English locale. Also clean: rebased branches, merge/revert/
re-merge, prefix disambiguation with an unregistered suffix.

### Q7–Q12 — the findings claimed open

F8's rename is an honest improvement but signals over-collection not at all. F3 is confirmed
**and round 3's characterization of its second half was wrong** — the real false negative is
the worktree case, where `degraded` is empty while a detached commit is attributed to nothing.
F4's remaining half, F11 and F12 are confirmed; F12 is a live cost issue rather than a nit
(65 behavior commits → 65 redundant `git show` calls, 1.7s). `rev_range` is a dead parameter no
consumer passes.

### Assessment

Round 4 replaced author-modelled correctness with an oracle, and the oracle's graph layer
works. But its parsing and base-ref layers were copied from the implementation, so the
apparatus reproduces exactly the failure mode it was built to end: agreement between two
expressions of one author's understanding. Two High over-collection defects now sit in the
same class as F5 — the defect round 4 was convened to fix — and one of them is written into a
fixture as expected behaviour.

## Handoff — 2026-07-26

Work stopped here deliberately. Five rounds in, the pattern is that this author's
self-verification produces confidence rather than coverage: rounds 1, 2 and 4 each declared a
problem closed that the next independent pass reopened, and round 4's oracle — built
specifically to remove the author's judgement from the loop — turned out to share half its
logic with the implementation. Continuing in the same session would most likely repeat it.

Nothing is urgent. No PR is open, and the shipped state is better than before this issue:
issue 093 collects 53 commits against 10, `scripts/project_issue_schema.py` is in the bundle,
and issue 081's merge no longer sits inside 093's evidence.

### Done before stopping

`ConsumerParityTests` was deleted rather than left in place. A test that cannot fail reads as
coverage to the next person, which is worse than an absent one — it passed under six
mutations including converge returning nothing. `tests/test_commit_resolution_differential.py`
now carries a comment explaining why the gap exists and what a real replacement requires, so
the same test does not get rebuilt.

Verified after removal: unittest 789/789 OK, release_check errors `[]`, lifecycle drift `[]`.

### Next session, in order

The apparatus comes before any further fixes. Fixing F3 or F10 now would produce claims
nothing can check.

1. Write a commit→issue reference in `commit_resolution_reference.py`. Half of AC1 currently
   has no oracle at all.
2. Re-derive the oracle's base-ref and branch-grammar layers independently — they are verbatim
   copies today, which is why the suite is blind to Q3 and Q4. Assert against ground truth,
   not against implementation-oracle agreement.
3. Remove `-b main` from `git_repo_builder`, and add shapes for a non-`main` default branch, a
   stale local `main`, two registered stacked issues, an octopus merge, and `\x01` in a commit
   body.
4. Then F3, F4's remaining half, F10, F11, F12.

For every new test, mutate the implementation first and confirm the test fails. That check is
what rounds 1 through 4 skipped.

### Open findings

| # | Claim | Severity |
| --- | --- | --- |
| Q3 | `stacked_live_branches` encodes over-collection as expected behaviour | High |
| Q4 | `base_ref` prefers a stale local `main` over `origin/main` | High |
| Q5 | Oracle's parsing and base-ref layers are copies; suite structurally blind | High |
| Q6 | Non-`main` default branch; octopus loses an entire issue; `\x01` corrupts records | High/Medium |
| F3 | `branch-unavailable` keyed on ref layout, not on whether resolution degraded | Medium |
| F4 | `linkage_check` still drops `degraded`; the linkage gate cannot see it | Medium |
| F12 | 65 behavior commits produced 65 redundant `git show` calls, 1.7s | Medium |
| F11 | `hooks/on_stop.py` is a third owner of branch grammar (GC1); four dead helpers | Low |
| Q12 | `rev_range` is a dead parameter; squash merges and `refs/pull/*` under-collect | Low |

## Review round 6 — commit→issue oracle

Apparatus item 1 from round 5's next gate. `reference_issues_for_commit` inverts
`reference_commits_for_issue` over every registered issue, so the commit→issue direction now
has an oracle that reaches its answer differently from the implementation's single index.
`CommitDirectionTests` holds `linkage_check.resolve_issue_for_commit` to it across all 11
shapes.

**It found a gate bypass on first run, without being told what to look for.**

### A branch named for an issue that does not exist satisfied the linkage gate

`issue_id_from_branch` returned the branch tail whenever no registered issue matched. Measured
before the fix:

```
branch   codex/999-not-a-real-issue      (no issues/999-....md)
change   scripts/thing.py                (a behavior path)
gate     ok: True, unlinked: 0           <- passes
issue    999-not-a-real-issue            <- does not exist
```

The gate exists to require that behavior changes link to an issue. Naming a branch is not
having an issue, and the branch name is attacker-controlled in the only sense that matters
here: it is the thing a person types when they want the gate to stop complaining.

Fixed: an unmatched tail resolves to `None` when an issue list is available. When no issues are
tracked at all the tail is still returned — there is nothing to check against, and refusing
everything would be worse than the prior behavior. After the fix the same case reports
`ok: False, unlinked: 1`.

### Impact measured before changing anything

Six commits in this repository were attributed to unregistered ids; five become unattributed,
one is also claimed by a registered issue and is unaffected.

| Branch | Resolved id | Commits |
| --- | --- | --- |
| `codex/034-pr-ready-and-dashboard-db-followup` | unregistered | 3 |
| `codex/086-087-github-issue-projection` | unregistered | 2 |
| `codex/092-current-dashboard-korean` | unregistered | 1 |

All three are branches that do not follow `codex/<issue-id>` — the observation recorded in
round 4 as out of scope, now the thing the gate correctly refuses.

### Mutation-checked

Restoring the old fallback fails three tests. Unlike the test deleted at `e8e4977`, this one
can fail.

### Verification

```
python3 -m unittest discover -s tests     804/804 OK   (789 before)
python3 scripts/release_check.py .        errors []
python3 scripts/project_lifecycle.py . --drift   []
```

### Still open

Apparatus items 2 and 3 from round 5 — the oracle's base-ref and branch-grammar layers are
still verbatim copies, so Q3 and Q4 remain structurally invisible, and `git_repo_builder` still
hardcodes `-b main`. F3, F4's remaining half, F10, F11 and F12 are untouched.

## Review round 7 — remaining findings closed

All twelve findings from the two independent reviews are addressed. Apparatus first, then the
defects it could then see.

### Apparatus (round 5's next gate)

| Item | Done |
| --- | --- |
| commit→issue oracle | `reference_issues_for_commit` inverts the issue→commits reference over every registered issue |
| Oracle's base-ref layer independent | asks `origin/HEAD`, else scores refs by fewest unique commits, tie-broken by containment. No name list |
| Shape generator stops hardcoding `-b main` | `GitRepo(default_branch=...)`, plus four shapes for the arrangements that were unreachable |

Each of the three exposed a defect the moment it landed.

### Findings closed this round

| # | Fix |
| --- | --- |
| N1 | A trunk called anything but `main`/`master` resolved to no base; `base_ref` derives it from the repository |
| N2 | Octopus merges lost every parent past the second — an entire issue's work attributed to nothing. `merge_side_commits` takes a parent index and each named issue is paired with its own parent |
| Q3 | Work stacked on another issue's branch collected that issue's commits. Contribution now excludes the base *and any issue branch this one descends from* — ancestors only, so F6's descendant case stays fixed |
| F12 | A supplied index answers without asking git. Measured: 65 redundant `git show -s` calls to 0, 1.7s to 1.25s |
| F4 | `linkage_check` carries `degraded` through both entry points; the gate can see it |
| F11 | `hooks/on_stop.py` asked `linkage_check`'s private regex — a third owner of branch grammar, carrying the same phantom-issue bypass. Now delegates; four dead helpers deleted |
| F3 | `branch-unavailable` fired whenever no issue-shaped branch existed, true of most healthy repositories. It now means what it says: issue branches exist and no base could be found |

Plus, found by the new commit→issue oracle on its first run rather than by looking for it: a
branch named for an issue that does not exist satisfied both the linkage gate and the stop
hook. `codex/999-not-a-real-issue` with a behavior change reported `ok: True, unlinked: 0`.
Naming a branch is not having an issue.

### Every fix is mutation-checked

Reverting any one of them fails at least one test. The apparatus was checked the same way:
reverting merge-direction detection, the `--all` log range, or the base-ref exclusion each
fails the differential suite.

### State

```
unittest                 820/820 OK   (741 at the start of this issue)
differential              30/30 OK    (15 repository shapes)
release_check            errors []
lifecycle drift          []
```

Resolution on this repository is unchanged across every fix: issue 093 at 53 commits, 086 at
5, 081 at 7, with issue 081's merge commit attributed to 081 rather than sitting inside 093's
evidence.

### Known limitations, asserted rather than hidden

- A commit orphaned by branch deletion is unreachable from every ref, so no source can
  attribute it. It resolves to `None`, indistinguishable from a commit belonging to no issue.
  Pinned by a test that says so.
- `rev_range` remains a parameter no consumer passes.
- Squash merges and work surviving only under `refs/pull/*` under-collect. Both fall outside
  the `codex/<issue-id>` convention the spec declares a non-goal.

## Next gate

A third independent review. Two of the previous three rounds of self-declared completion were
reopened by one, and the one apparatus built to prevent that was itself half a copy of the
implementation.

## Review round 8 — third independent review

Run at head `59432c7`, read-only, repository verified unmutated. **Verdict: request changes.**

### Confirmed

Two claims from round 7 survived checking, and they matter:

- **AC1 is genuinely met.** Replacing `linkage_check.resolve_issue_for_commit` with its
  pre-095 trailer-only rule fails 19 tests. `CommitDirectionTests` is what catches it — the
  test deleted at `e8e4977` has been replaced by something that works.
- **"Every fix is mutation-checked" holds.** All ten mutations the reviewer built were caught,
  across every fix named in round 7. No mutation was blind.

### Not closed, and claimed closed — Q-2

Round 7's apparatus table says the oracle's base-ref layer is independent. It is not:

| Layer | Reality |
| --- | --- |
| `origin/HEAD` lookup | Textually identical in implementation and oracle, and **executes in 0 of 15 shapes** — `GitRepo.publish()` never writes `origin/HEAD` |
| Scoring fallback | Differs only in `_same_branch(other, ref)` versus `other != ref`, and returns the *same wrong answer* as the implementation on every base-ref defect below |

The independence claim is true only of the layer that never runs. This is the third round in
which Q5's substance outlives its closure.

### Q-1 — the base-ref fallback elects an issue branch as the trunk. High.

In 5 of the 15 existing shapes the implementation and the oracle both elect `codex/101-alpha`
as base. They survive it by accident: when the mis-elected base *is* the branch being
measured, `_same_branch` short-circuits and merge topology carries the answer. Add a second
branch and it bites. Five hand-derived arrangements, both sides wrong:

| Arrangement | Hand | Both | Failure |
| --- | --- | --- | --- |
| A merged and kept, B cut from main after | 1 | 3 | over-collection |
| A and B at the identical commit | 1, 1 | 0, 0 | **F6 reopened** |
| Stacked, ancestor merged then deleted | 1 | 0 | work lost entirely |
| Live branch and main each 1 ahead | 1 | 0 | ordinary in-progress branch collects nothing |
| Ancestor branch renamed out of `codex/` | 1 | 3 | claims the renamed branch's commits |

Scope: any repository without `origin/HEAD` — every fixture here, and any local-only project.
This checkout has it set, which is why five rounds of real-repo probing missed it.

It also lands on F3, closed one round ago. The failure is not *no base* but *wrong base*, and
all five report healthy: `degraded: []`, `base_ref_available: True`, with `branch_refs` naming
a branch that produced no sources — a self-contradicting payload.

### Q-3 — the oracle contradicts itself. High.

`_branch_issue` kept the tail fallback that round 6 deliberately removed from
`issue_id_from_branch`. On `branch_name_not_matching_issue`, the oracle's issue→commits half
returns 1 commit for an unregistered id while its commit→issue half returns nothing, and the
shipped rule returns nothing. An oracle that answers two ways cannot arbitrate.

The suite cannot see it because differential coverage is bounded by what each shape *returns*,
not what it *builds*. A sweep over every issue id a shape constructs finds exactly this one
divergence.

### Q-4 — evidence is not reproducible from history. High.

`known_issue_ids` runs `git ls-files issues` — worktree state, not history. On byte-identical
history, resolution differs by which branch is checked out (0 versus 2 commits). For a file
whose purpose is to be the review record, that is worse than a low count.

Same cause, direct blast radius from `0076b67`: archiving or moving an issue file silently
drops its commits, with `degraded: []`. The round-6 phantom-branch fix was right; its cost was
not measured.

### Q-5, Q-6 — Medium

`\x01` in a commit body still drops that commit, now with a surfaced error rather than silent
corruption of neighbours. The Q3 ancestor probe made subprocess count quadratic in branch
count: 208 of 228 calls on this repository, 9.5× round 3. AC5 still passes — it does not scale
with *history* — but GC4 says "bounded by branch count", and it is now branch count squared.

### Assessment

Round 7 closed eleven findings and the mutation discipline is real. The one it reported closed
without closing is the one about the apparatus itself, and that is what let a base-ref cluster
of over- and under-collection — this issue's founding defect class — stay invisible for
another round.

Five of the reviewer's ten new arrangements broke the implementation; four broke the oracle
identically.

## Superseded — round 8 next gate

Item 1 said "derive the oracle's base ref by a genuinely different route". Rounds 4, 5 and 7
each attempted oracle independence and round 8 measured the result: the layer it called
independent executed in 0 of 15 shapes. A fourth attempt was round 9's most likely way to
fail. Round 9 took item 1's *second* clause instead and generalised it, which dissolved all
three items. Recorded rather than deleted because the branch not taken is the finding.

## Round 9 — the oracle is deleted, not repaired

The fixture built the history, so it knows the answer without deriving anything. Every commit
now declares `belongs_to` and the tests compare against that literal, which cannot share a
blind spot with the code it checks. `commit_resolution_reference.py` is gone; a test asserts
it stays gone.

Two rules keep the declarations from re-coupling. They name issue ids only, never a `source` —
truth is what a commit belongs to, not how the resolver finds it, and asserting the strategy
is the same coupling one level down. And a commit built without a declaration is recorded as
`UNDECLARED` and fails `DeclarationCoverageTests`, so a shape added later cannot silently test
nothing.

| Round 8 item | Status |
| --- | --- |
| Next gate 1 — oracle base ref independent | dissolved; no oracle base ref exists |
| Next gate 2 — sweep ids a shape *builds* | dissolved; the sweep is derived from the declarations, so it is structural rather than a list that can be forgotten |
| Next gate 3 — `_branch_issue` tail fallback | dissolved; no `_branch_issue` |
| Q-2 — oracle not independent | dissolved |
| Q-3 — oracle contradicts itself | dissolved |

### Residual risk, stated rather than left to be found

`DeclarationCoverageTests` proves every commit carries a declaration. Nothing proves a
declaration is *right*. That is the cost of the approach, and two declarations were revised
after they failed, which is the shape of the coupling the oracle was deleted to escape:

- the sync merge of `main` into `codex/alpha` — first declared as belonging to nothing, then
  to alpha, by the branch it sits on
- the merge of `codex/alpha` into `codex/beta` — first alpha's, then both

What makes this a loosening of the *merge* convention rather than a fit to the code: merges
carry no content, so a reviewer who sees one in either bundle is not misled, and the strict
part of the declaration — content commits — was left untouched. R9-1 is a content commit
crossing issues, and it still fails. Had the revision been made to satisfy the resolver, R9-1
would have gone green with the others.

An independent reviewer should audit all sixteen shapes' declarations as a named task before
any closure claim. That is the first thing this apparatus makes possible: the declarations are
literals to read, not git semantics to re-derive.

### Found on the declaration's first run

Two shapes that were green under the oracle failed immediately. Both are over-collection
across issues — this issue's founding defect class — and both were green because the oracle
shared the derivation that produced them.

| Id | Shape | Defect |
| --- | --- | --- |
| R9-1 | `nested_merges` | A merged into B, then B to main: B's bundle collects A's *content* commit, not just the boundary merge |
| R9-2 | `stale_local_default_branch` | `base_ref` elects the stale local trunk, so the issue collects trunk commits predating its branch. Recorded as Q4 in round 5, reported closed in round 7 |

Two more came from chasing a surviving mutation rather than from a shape:

| Id | Defect |
| --- | --- |
| R9-3 | Precedence holds in one direction only. A commit whose trailer names beta, sitting on alpha's branch, resolves to beta commit→issue but appears in *both* bundles issue→commits: branch membership is collected without asking whether a higher-precedence source already claimed the commit |
| R9-4 | Precedence is stated twice. `resolve_issue_for_commit` short-circuits on a trailer and returns before `SOURCE_PRECEDENCE` is read; only the index path consults the constant. They agree today solely because the constant happens to list trailer first, so the same commit can resolve differently depending on whether the caller passed an index — GC1's one owner violated inside the resolver |

R9-1, R9-2 and R9-3 are marked `expectedFailure` with their ids, not skipped: unittest reports
an expected failure that starts passing as an unexpected success and fails the run, so a fix
forces the marker's removal. R9-4 has no failing case today; the dual-path assertion added to
`CommitDirectionTests` is what would catch it.

### Mutation results

| Mutation | Result |
| --- | --- |
| `build_attribution` returns an empty index | caught |
| trailer rule disabled | caught |
| branch rule disabled | caught |
| `SOURCE_PRECEDENCE` reversed | **survived**, until the precedence shape and the dual-path assertion were added — then caught |
| `record()` stops storing ground truth | caught |
| a shape omits `belongs_to` | caught |
| a known defect declared to match the code | caught, as unexpected successes |

The surviving mutation is the one worth keeping in view: precedence, the rule the module names
in a constant and documents in GC2, was asserted by no test at all. It survived because no
shape ever made two sources disagree.

### Also corrected

A module-level loop variable left bound to a `TestCase` subclass made `loadTestsFromModule`
collect that class twice. Every count in the differential file was inflated by fifteen, and
the suite total with it: 852 → 837, now 840 with the new shape.

### State

840 tests, OK with 4 expected failures. `release_check` errors `[]`, warnings 0.

## Next gate

Open defects, no apparatus work outstanding: R9-1, R9-2, R9-3, R9-4, and from round 8 Q-1 (the
wider base-ref cluster R9-2 is one instance of), Q-4, Q-5, Q-6.

Take Q-1 and R9-2 together — they are one cause — and expect the R9-2 marker to disappear when
it lands. R9-3 and R9-4 are also one cause: precedence needs a single owner applied in both
directions and both call shapes.

Independent review before any closure claim. Self-declared closure on this issue is 0 for 4.

## Superseded — round 3 next gate

Do not open a PR. F1, F2, F5, F6, and F7 are correctness defects in shipped code; F5 is
actively wrong in this repository's evidence bundles today. The fixture gaps that hid them
need addressing as a class, not case by case — three rounds have now each fixed the instance
they were handed.

## Corrective completion — 2026-07-27

Round 9's four expected failures are removed. The corrective branch is
`codex/095-commit-issue-resolution-parity-fix`.

| Area | Result | Evidence |
| --- | --- | --- |
| Historical issue registry | Fail closed; checkout-independent; unknown issue claims rejected | `21d1290` |
| Git graph queries | Errors and terminated queries surface degradation instead of attribution | `881d81d` |
| Global attribution | Content commits have one owner under `trailer > branch > merge-subject`; merge boundaries may carry multiple issue claims | `ef149a8` |
| Base selection | Issue-shaped refs cannot become the base; unusable candidates fail closed | `4f5d14a` |

### Verification recorded so far

```text
Task 1 focused suite: 92/92 PASS
Five-module focused suite: 195/195 PASS
Expected failures: 0
```

The five-module suite covers `test_commit_resolution`,
`test_commit_resolution_differential`, `test_commit_resolution_parity`,
`test_linkage_check`, and `test_project_converge`.

Task 3 artifact validation reports `valid: true` and `errors: []`; lifecycle
drift is `[]`, and `git diff --check` is clean. Only the current branch's full
unittest suite, release check, and final whole-branch review remain F4 before a
closure claim.

### Independent review

- Task 1 spec review: pass.
- Task 1 quality review: pass after terminated graph-query handling was fixed
  in `881d81d`.
- Task 2 spec review: pass.
- Task 2 quality review: pass after two Important base-selection findings were
  fixed and re-reviewed in `4f5d14a`.

Human approval is still required before merge. No GitHub PR is claimed by this
status record.

### Issue 096 proposed handoff

Issue 095 does not modify Issue 096. Its proposed command-safety handoff is:

- make `--evidence` read-only by default or require an explicit write flag;
- validate issue ids so they cannot traverse paths;
- reject symlinks that resolve outside the repository;
- announce every write path.

Before Issue 096 execution, its canonical issue must be expanded with these
acceptance criteria, an explicit dependency on 095, and the installed-plugin
update gate. The work then proceeds on a separate branch after 095 is approved
and merged. The installed ModuFlow plugin remains on hold until both issues are
safe.

## Next gate

Run F4 full verification and final independent review, then prepare a Draft PR
for human approval.

## Redesign implementation plan — 2026-07-27

The preceding corrective next gate is superseded. Full-suite failures and the
final independent review proved that extending one repository-wide base
heuristic would continue the patch loop.

The active plan is now
`specs/095-commit-issue-resolution-parity/plan.md`. Its six streams replace the
global-base path with:

1. one injected Git graph snapshot and explicit failure semantics;
2. per-issue historical fork points and stacked-issue exclusions;
3. separate merge-boundary and content-side claims;
4. one precedence pass plus caller-scoped diagnostics;
5. release-SHA and converge-issue scope integration;
6. failure-corpus traceability, full gates, and independent review.

No implementation claim accompanies this planning artifact. The branch remains
unfit for a PR until all Stream F gates pass.

Planning validation: spec consistency reported 0 findings across 9 checked
requirements; project validation returned `valid: true` with `errors: []`;
lifecycle drift was `[]`; JSON and diff checks passed.

## Next gate

Execute Stream A1 with RED/GREEN evidence:
`product:execute 095-commit-issue-resolution-parity`.

## Execution start — 2026-07-27

Repository identity allowed `execute`, implementation readiness is `ready`,
and the generated worker plan is sequential because every task touches shared
graph/resolver state or depends on the preceding task. Dongwon Lee selected
the recommended host-subagent workflow.

Each task uses one fresh implementer, then a separate spec-compliance reviewer,
then a separate code-quality reviewer. No later task starts while either
review has an open finding.

## T01 / A1 completion — 2026-07-27

RED exposed stale direct-consumer fixtures, malformed successful merge-base
output, and file-mode module reuse. Those review findings were preserved as
`FH-021` and `FH-022` before the fixes landed.

GREEN is `8068f98` on top of `9356cb0`, `064ca05`, and `1ceb153`. The direct
graph, resolver, parity, and linkage suites passed 105/105. Independent spec
review and independent quality re-review both approved T01 with no open
Critical, Important, or Minor findings.

## Current task

T02 / B1 — derive one ancestry-maximal historical fork point per issue ref
with invariant coverage for `FH-006`, `FH-011`, `FH-012`, `FH-013`, and
`FH-017`.
