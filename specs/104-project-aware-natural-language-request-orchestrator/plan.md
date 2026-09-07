# Plan: Project-Aware Natural-Language Request Orchestrator

Issue: 104-project-aware-natural-language-request-orchestrator

## Approach

One module, `scripts/request_routing.py`, holding five stage functions and one
`route_request` that calls them in order. Each stage takes the result-so-far and
returns it, either advanced or stopped.

Nothing is re-implemented. Every stage is a call into a module that already
works, and the module's result is carried verbatim.

```
route_request(request, root, *, host=None)
  ├─ stage_resolve      project_registry.resolve_project
  ├─ stage_overlap      the resolved project's issues, then its records
  ├─ stage_capability   capability_routing.route
  ├─ stage_execution    execution_routing.build_routing
  └─ stage_commit       project_lifecycle_transaction
```

**Order is enforced by structure, not discipline.** `route_request` is the only
public entry; the stage functions take the accumulated result and refuse to run
without the fields the previous stage sets. A stage called out of order fails on
a missing field rather than running against an unresolved project.

The spec names silent reordering as this issue's characteristic failure. Tests
assert call order with mocks, not just outcomes — an outcome test passes when the
stages run backwards and happen to agree.

## Sequence

Stages land one at a time, each with its refusal path, because a half-built
pipeline that runs stages 1–3 and then falls through is worse than one that
stops at stage 2 and says so.

1. **The contract and stage 1.** `moduflow.request-routing.v1`, every field
   present in every result. Ambiguity asks one question and writes nothing.
2. **Stage 2, overlap.** Unblocked 2026-09-07 — see Open Questions. It gathers
   the resolved project's open issues (id, title, `## 안 고치면`) and returns
   them as `overlap_candidates`. It does **not** score, rank or decide, and the
   measurement that ruled that out is the acceptance evidence for this step.
3. **Stage 3, capability.** `outcome: none` is a normal result — resolved during
   this plan and recorded in the spec's Risks. Reading it as failure would refuse
   every request ModuFlow handles itself, which is most of them.
4. **Stage 4, execution.** 112's result, unchanged. `needs_plan` stops with
   `written: []`.
5. **Stage 5, commit.** Through 103's transaction. Last, because it is the only
   stage that writes.
6. **Hub wiring.** `commands/moduflow.md` routes a bare sentence here. No new
   command file — a test freezes the filename set.

## Work Streams

- PM: the overlap question is closed by measurement, not by a decision — no
  threshold exists to choose. Nothing blocks step 2.
- Data: no schema changes to existing artifacts. One new result schema.
- Implementation: `scripts/request_routing.py` (new), `commands/moduflow.md`.
  `capability_routing.py`, `execution_routing.py`, `project_registry.py` and
  `project_lifecycle_transaction.py` are **read-only** here.
- QA: below, RED first per stage.
- Release: version bump, `release_check.py`, `Issue:` trailer.

## Verification

Per stage, and the ordering tests are the ones that matter:

- `test_stages_run_in_order` — mock all five, assert call sequence. Not outcomes.
- `test_a_stage_refuses_without_its_predecessor` — call stage 3 with no resolved
  project; assert it raises rather than proceeding.
- `test_ambiguous_writes_nothing_and_calls_no_capability` — by mock, not by
  inspecting the tree afterwards.
- `test_none_outcome_is_not_a_refusal` — the case resolved during this plan.
- `test_overlap_returns_candidates_without_a_verdict` — assert the stage 2
  result carries `overlap_candidates` and **no** score, rank or chosen issue.
  This is the test that would fail if someone re-adds a threshold; the
  measurement in Open Questions is why it exists.
- `test_overlap_candidates_are_open_issues_of_the_resolved_project_only` —
  a `done` issue and another project's issue both absent.
- `test_needs_plan_stops_with_written_empty`.
- `test_project_a_never_reads_project_b` — Korean and English fixtures, both
  directions.
- `test_no_new_command_file` — the filename set, frozen.
- Full suite and `release_check`.

## Rollback

The module is new and nothing calls it until step 6. Reverting before that is a
file deletion; reverting after also restores one section of `commands/moduflow.md`.

No artifact changes shape, so nothing needs migrating either way.

## Open Questions

**None open.** The one that blocked step 2 is answered below.

### Resolved 2026-09-07 — what counts as high-confidence overlap

The answer is **nothing does**, and step 2 changes shape because of it.

This question said title similarity was "the cheap answer and probably wrong"
and asked for a measurement first. Measured over 147 issues and 10,731 pairs
against 220 human-declared same-work pairs, all four candidate rules fail:

| Rule | Precision | Recall |
|---|---|---|
| Title Jaccard ≥ 0.3 / 0.4 / 0.5 | 23% / 25% / 67% | 3.2% / 0.9% / 0.9% |
| Entry Points share ≥ 1 file | 16.8% | 23.6% |
| Entry Points share ≥ 2 files | 39.7% | 11.4% |
| Title ≥ 0.3 **and** a shared file | 33.3% | 0.5% |

Re-checked against the seven pairs a person read and merged on 2026-09-06/07,
which are certainly the same work: **five of the seven score 0.00** on title
similarity and three share no file at all.

The reason is that what joined them was a shape, not a vocabulary — 144·145·142
are all "named in code, never checked"; 136·123 are both "checks a file exists
and never reads it". Meanwhile the issues that *do* share the word `dashboard`
are, by issue 143's count, four different things. The word is not the signal.

**So stage 2 surfaces candidates and does not judge them.** It puts the
resolved project's open issue titles and their `## 안 고치면` lines into the
request context, and the reader — model or person — names the overlap. No
threshold, no numeric rule, and stage 2 still writes nothing.

Evidence: `memory/evidence/2026-09-07-overlap-detection-corpus-measurement.md`.

## Next Command

`/moduflow execute 104-project-aware-natural-language-request-orchestrator`
