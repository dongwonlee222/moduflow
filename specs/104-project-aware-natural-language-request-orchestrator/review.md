# Review: Project-Aware Natural-Language Request Orchestrator

Issue: 104-project-aware-natural-language-request-orchestrator

Eleven tasks, all closed 2026-09-07. 47 tests. Versions 0.3.80 → 0.3.87.

## What shipped

`scripts/request_routing.py` — five stages behind one public entry, called in a
fixed order. Each stage calls a module that already worked and carries its
result verbatim; nothing is re-implemented.

```
route_request(request, registry_path, *, chosen_issue=None, commit=False)
  ├─ stage_resolve      project_registry.resolve_project
  ├─ stage_overlap      the resolved project's open issues
  ├─ stage_capability   capability_routing.route_request
  ├─ stage_execution    execution_routing.build_routing
  └─ stage_commit       project_lifecycle.transition_lifecycle
```

`commands/moduflow.md` routes a bare sentence here. **No new command file** —
41 before, 41 after, frozen by test.

## Did it work

Yes, and the proof is that it was run against the live registry rather than only
against fixtures. `/moduflow Bot Ops 현재 상태 확인해줘` returns `ok` / `commit` /
33 candidates / `written: []`. `/moduflow 현재 상태 확인해줘` stops at `resolve`
and asks one question. Both through the installed 0.3.87 package, not the
working tree.

Five source scenarios, all with `written: []`:

| Scenario | Outcome |
|---|---|
| Existing work, revision | `ok` · `attach` · the existing issue id |
| New deliverable | `ok` · no issue file created, asserted by directory listing |
| Ambiguous project | `ambiguous` · one question · zero candidates, zero capability calls |
| Unavailable capability | `ok` · `outcome: none` — not a refusal |
| State-write failure | `blocked` · every contract field still present |

## The two decisions that changed the design

**Stage 2 does not judge overlap, because nothing can.** The plan's open question
asked for a threshold and said to measure first. Measured over 147 issues and
10,731 pairs against 220 human-declared same-work pairs, all four candidate rules
fail — best precision (67%) finds 2 of 220. Re-checked against seven pairs a
person read and merged, **five score 0.00** on title similarity and three share
no file. So the stage returns candidates and the reader names the overlap.
`test_no_score_rank_or_verdict` is there to fail if a threshold returns.

**`commit` defaults to False.** R6 says stage 5 commits and does not say when it
is asked to. Taken literally, asking "what would this do?" changes state in order
to answer. Recorded in the spec as a deviation, with the one line to change named.

## What running it for real found that 45 green tests did not

Two defects, both fixed, and this is the part worth keeping.

1. **`unresolved` was reported as `ambiguous`.** The live registry's three
   projects all had unreachable roots; the resolver said so correctly and this
   module asked the person to pick among three broken projects. No answer helped.
2. **`stage` said `resolve` on a request that cleared all five stages**, because
   only the stages that stopped or wrote were setting it.

And one defect underneath, filed and fixed as **issue 149**: every root in the
live registry was written with a `~` that nothing expanded, so all three
registered projects resolved to paths that had never existed — while the registry
still loaded as `valid: true`. That is why `/moduflow` did nothing when the owner
first tried it.

**None of the 45 tests could have caught any of these**, because every fixture
builds its own registry with absolute paths that exist. That is the limit of a
fixture, and it is why the last task was "run it for real".

## Seven sabotage checks

Each break deliberately introduced, each reverted:

| Break | Tests that caught it |
|---|---|
| Drop the open-state filter → `done` issues become candidates | 2 |
| Skip the candidate check → any id attaches | 1 |
| Read a sibling project's `issues/` | **6** |
| Swallow a broken capability registry as `none` | 1 |
| Let `needs_plan` through to the writing stage | 1 |
| Ignore the `commit` flag and always write | 1 |
| Report a failed transaction as success | 1 |

The third matters most: the two isolation tests **passed at step 1 while
asserting nothing**, since stages 2-5 read no files. The class docstring said so
at the time rather than letting them read as proof, and step 2 made them real.

## What this did not do

- **103's rollback is not re-tested.** 103 owns proving a refused transaction
  leaves no half-written state. This module asserts only that it stops and
  reports `written: []` rather than success.
- **No capability is invoked.** Stage 3 routes; running a specialist is not this.
- **Overlap candidates carry no `## 안 고치면` line outside this repository.**
  The rule shipped here and has not spread, so a candidate list from another
  project is titles only. Recorded in that project's inbox, not filed as an
  issue here.

## Cost

About 1,100 lines of `scripts/` and ~700 of tests. Measured the same day: the
repository is 44,843 script lines across 117 closed issues — roughly 383 lines
per issue, and no small set of commits explains it (the seven largest total 19%).
This issue is at that average, not below it. Worth stating in a review of an
issue whose own goal file says the product should be getting lighter.

## Next Command

`product:status`
