# Spec: Project-Aware Natural-Language Request Orchestrator

Issue: 104-project-aware-natural-language-request-orchestrator

## Problem

Every part of this pipeline exists and nothing runs them in order.

`project_registry.resolve_project` finds the project. `project_intake` routes a
loose request. `capability_routing` picks a capability. `execution_routing`
(issue 112, done today) decides whether the work is dispatchable.
`project_lifecycle_transaction` commits state atomically.

A person typing `/moduflow 로그인은 이메일부터 가기로 했어` reaches none of that
as a sequence. The hub reads its own alias table, picks a `product:*` command,
and that command starts from scratch — it does not know which project resolved,
whether an issue already covers this, or what the capability router decided.

**The ordering is the product.** Resolve the project before reading project data:
skip that and every later step runs against the wrong repository. Check for an
existing issue before creating one: skip that and the same work is filed twice.
Neither ordering is enforced anywhere today.

## Users

The owner, typing a sentence instead of remembering a command. Secondary: any
agent handling a request on his behalf, which needs the same order and the same
refusals.

## Goals

- One request in, one `moduflow.request-routing.v1` result out, through the
  existing `/moduflow` entry point.
- The five stages always run in the safe order, and each one can stop the
  pipeline.
- Ambiguity asks exactly one question and writes nothing before the answer.
- Project A's request never reads Project B's issues, records or playbooks.

## Non-Goals

- A second public entry point. `/moduflow` stays the only one; issue 131 settled
  the surface and this must not widen it.
- Replacing the router or capability adapters from issue 097, or the execution
  decision from 112. This sequences them; it does not re-implement them.
- A host-specific subagent runtime, or any worker completion state of its own.
  112's adapter boundary owns the host and `worker_orchestrator` owns dispatch.
- Cross-project raw record search.
- Automatic execution when the project is ambiguous or a capability's permission
  is not `allowed`.
- A new issue for every revision. A revision attaches to the existing issue.
- **The nine Korean/English phrase pairs from issue 131 stage 2.** They land on
  top of this once it exists, as a table this router consumes — not as a second
  router. See Sequencing.

## The pipeline

Five stages. Each returns the same result shape with a different `stage` and may
set `status` to stop.

```
request
  ↓
1  resolve      which project?            → ambiguous → ask one question, stop
  ↓
2  overlap      already an issue?         → high confidence → attach, do not create
  ↓
3  capability   which adapter?            → not allowed → report, stop
  ↓
4  execution    is it dispatchable?       → needs_plan / not_applicable → stop
  ↓
5  commit       verify, then transact     → validation fails → roll back, stop
```

**Stage 1 runs before any project file is read.** That is the whole reason the
order is fixed rather than convenient: `project_registry.resolve_project` already
exists, and today nothing forces a caller through it first.

**Stage 4 is issue 112's result, consumed unchanged.** A `needs_plan` here is the
same refusal `product:workers` gives, reported through this contract rather than
re-derived.

## Requirements

### R1 — The contract

Schema `moduflow.request-routing.v1`. Required fields, all present in every
result regardless of status:

- `schema`, `request_id`, `request`
- `project`: resolved id, or null with `status: ambiguous`
- `stage`: `resolve` | `overlap` | `capability` | `execution` | `commit`
- `status`: `ok` | `ambiguous` | `refused` | `blocked`
- `action`: what this request resolves to — `attach`, `create_candidate`,
  `record`, `report`, or null
- `issue`: the linked issue id, or a candidate, or null
- `overlap_candidates`: the resolved project's open issues, in issue-id order —
  `{issue, title, priority, blocked_without_this}` each. **Added 2026-09-07**,
  during step 2. It was not in this list when the spec was written because the
  plan still expected stage 2 to return a verdict; the corpus measurement
  removed the verdict and left the candidates, and they need somewhere to land.
  Empty list, never null, for the same reason `written` is.
- `capability`: the 097 routing result, or null
- `execution`: the 112 routing result, or null
- `question`: exactly one, non-null only when `status` is `ambiguous`
- `written`: files actually written, empty for every non-`ok` status
- `next_command`

`written` is empty on refusal for the same reason 112 made it explicit: a reader
must be able to assert that nothing happened, not infer it.

### R2 — Resolve before reading

No project file is opened before stage 1 returns a project. A test asserts this
by resolving against a fixture with two registered projects and confirming that
a request naming neither reads from neither.

Ambiguity asks **one** question and performs zero writes and zero capability
calls. Two questions is a defect — issue 129 settled that for decision requests
and the same rule applies here.

### R3 — Overlap attaches, it does not duplicate

Stage 2 searches only the resolved project's issues, then its approved playbooks
and production records, then approved shared playbooks. Never another project's.

A revision, resize, compression or copy edit of existing work attaches to that
issue. Only a genuinely independent deliverable produces `create_candidate`, and
a candidate is a proposal — this stage never writes an issue file.

**Amended 2026-09-07 — who decides "same work".** As written this required the
stage to recognise a revision, which means judging overlap. It cannot: measured
over 147 issues and 10,731 pairs, no rule separates same-work pairs from
unrelated ones, and five of seven confirmed pairs score 0.00 on title
similarity. So the stage returns `overlap_candidates` and the reader — model or
person — names the overlap, which comes back as `chosen_issue`. Attach and
`create_candidate` still exist and still mean what they meant; what changed is
that stage 2 is not the one choosing between them.

**A named id must be a candidate.** `chosen_issue` pointing at anything other
than one of this project's open issues is `refused`, not attached. This is R5's
sharpest edge and the one place where the caller, rather than the resolver, is
the party reaching across. Asserted, and asserted by sabotage: reading a sibling
project's issue directory fails six tests in this suite.

Evidence: `memory/evidence/2026-09-07-overlap-detection-corpus-measurement.md`.

### R4 — Capability and execution are consumed, not re-derived

Stage 3 calls `capability_routing` and passes through its adapter id, reason,
permission, availability and output artifact verbatim. Stage 4 calls
`execution_routing`. Neither result is reinterpreted; a disagreement between them
is a defect in this issue, not something to smooth over.

At most one capability is invoked, with scoped context, stated prohibitions, and
the expected output artifact.

### R5 — Isolation

A request resolved to project A must not surface project B's raw issues,
records, brand copy or local playbooks. Asserted with Korean and English fixtures
in both directions, because a leak that only shows in one language is a leak.

### R6 — Commit through the transaction

Stage 5 validates the output against its artifact type when one is configured,
then commits canonical and derived state through issue 103's transaction. A
validation failure rolls back and reports; it never leaves half-written state.

## Sequencing — 131 stage 2 lands on this

Issue 131 deferred nine Korean/English phrase pairs and five single English words
because building them earlier meant writing this router twice. Once R1–R4 exist,
that work is a phrase table this pipeline consumes at stage 1. It is not in this
spec's scope, and this spec must leave a place for it: the request text reaches
stage 1 unparsed, so a table can be applied there without touching stages 2–5.

## Acceptance Criteria

- One natural-language request returns the complete contract through `/moduflow`,
  with every R1 field present.
- An ambiguous project asks exactly one question, writes nothing, and calls no
  capability. Asserted by mock, not by inspection.
- A high-confidence overlap yields `action: attach` with the existing issue id.
  A new deliverable yields `create_candidate` and writes no issue file.
- The capability result records adapter id, reason, permission, availability,
  issue id and output artifact, and never claims execution that did not happen.
- A project A request exposes no project B content, in Korean and in English.
- A successful output passes artifact verification when configured and updates
  the issue, state views and production record in one transaction.
- A `needs_plan` from stage 4 stops the pipeline with `written: []`.
- No new top-level command file appears. A test compares the command filename set.
- The existing intake, shaping and capability-routing suites stay green.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification Strategy

- Five scenarios from the source request: existing-campaign revision, new-project
  deliverable, ambiguous project, unavailable capability, state-write failure.
- Project A/B isolation fixtures in Korean and English.
- A mock asserting zero project reads before stage 1 returns.
- A mock asserting zero writes and zero capability calls on `ambiguous`.
- The command filename set, frozen.
- Full suite and `release_check`.

## Risks

- **This is a sequencer, and a sequencer's failure mode is silent reordering.**
  If a later change calls stage 3 before stage 1, nothing crashes — it just runs
  against an unresolved project. The mock-based ordering tests are the only
  defence, and they must assert call order, not just outcomes.
- **Five stages, five existing modules, and none of them was written to be
  called in sequence.** Their result shapes do not match, and the temptation
  will be to normalize them here. R4 forbids reinterpreting; passing through
  verbatim is uglier and keeps the disagreement visible.
- ~~`capability_routing` returned `outcome: none` for a decision request.~~
  **Resolved 2026-09-07 during plan.** `none` means "continue in ModuFlow and
  load no specialist", which is correct — recording a decision is ModuFlow's own
  work. Measured across five requests: `결정으로 남겨줘` → `none`,
  `이 화면 디자인 좀 봐줘` → `delegate` to `product-design` (availability
  `unavailable`, so `current_stage` is null and a fallback sentence is
  returned), `지표 분석해줘` → `delegate`, `명세 검토해줘` → `none`,
  `출시 준비해줘` → `none`. The router recognises requests correctly. **Stage 3
  must treat `none` as a normal outcome**, not a failure to route — reading it
  as failure would refuse every request ModuFlow handles itself.

## Open Questions

- What counts as "high confidence" overlap in R3. Title similarity is the cheap
  answer and it is probably wrong. The plan must state a rule and a measurement.
- Whether stage 5's artifact verification is configured per artifact type or per
  project. Issue 145 is adding a verification-section rule and the two should
  agree on where verification is declared.

## Next Command

`/moduflow plan 104-project-aware-natural-language-request-orchestrator`
