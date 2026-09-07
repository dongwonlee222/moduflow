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
2. **Stage 2, overlap.** The open question below has to be answered first.
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

- PM: the overlap threshold (Open Questions) is the owner's call and blocks step 2.
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

- **What counts as high-confidence overlap.** Title similarity is the cheap
  answer and probably wrong — two issues can share a title and be different
  work, and the same work gets described two ways. This blocks step 2 and needs
  a stated rule plus a measurement against the 148 live issues before anything
  is built on it. Recommend measuring first: run three candidate rules over the
  corpus and count how many pairs each one calls the same.

## Next Command

`/moduflow execute 104-project-aware-natural-language-request-orchestrator`
