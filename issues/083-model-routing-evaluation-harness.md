# Issue 083: Model Routing Evaluation Harness

**Status: backlog** — created 2026-07-10.
**Priority: p3**
**Blocked-by: `082-cross-host-model-capability-routing`**

## Summary

Create a repeatable evaluation harness that tests whether ModuFlow's model-routing guidance improves quality, latency, and token cost for representative worker tasks before the guidance is promoted or changed.

## Source

- Type: user product direction / model-routing follow-up
- Link: local Codex session, 2026-07-10
- Date: 2026-07-10

## Opportunity

Model names and provider tradeoffs change quickly. Without a small, repeatable evaluation set, routing decisions become documentation intuition: users cannot tell whether `balanced` is delivering quality close to `deep`, or whether `fast` is saving enough time and spend to justify its use.

## Scope

### In

- Define a curated, versioned task fixture set covering planning, targeted code changes, review, and repetitive transformation work.
- Define comparable outcome fields: task success/quality rubric, elapsed time, input/output/reasoning tokens when available, and estimated cost when pricing metadata is supplied.
- Add a local/offline report format and a documented opt-in path for real provider runs.
- Establish promotion rules for changing a host profile based on evidence rather than a single anecdote.

### Out

- Automatic live runs against paid provider accounts.
- Claiming cross-provider winner rankings without comparable, consented measurements.
- Replacing normal unit and release validation with model evaluation.

## Acceptance Criteria

- The fixture set and scoring rubric are versioned in the repository.
- A command can generate an evaluation report from recorded run data without provider credentials.
- Reports distinguish measured facts from estimated cost and unavailable telemetry.
- The documented promotion rule covers quality regression, latency, and cost before a mapping changes.
- Focused tests and `python3 scripts/release_check.py .` pass.

## Verification

Commands the executing agent runs to self-check before handing off.

- `python3 -m unittest discover -s tests -p 'test_*model*evaluation*.py' -v`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

Starting files/components for the executing agent.

- `scripts/worker_orchestrator.py`
- `commands/product-benchmark.md`
- `knowledge/benchmarks/`
- `tests/`
- `docs/host-adapter-guidance.md`

## Scope Fence

Do NOT send production prompts or repository data to a provider automatically. Real-provider measurement must remain explicit, opt-in, and independently budgeted.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec, plan, design, or review off the books. Check the box and link the artifact when done.

- [ ] spec → `specs/083-model-routing-evaluation-harness/spec.md`
- [ ] plan → `specs/083-model-routing-evaluation-harness/plan.md`
- [ ] execute → fixtures, report generator, and focused tests
- [ ] review → `specs/083-model-routing-evaluation-harness/review.md`

## Related Issues

- blocks:
- blocked_by: `082-cross-host-model-capability-routing`
- duplicates:
- follows_up: `081-gpt-5-6-model-tier-guidance`
- supersedes:
- related: `031-goal-driven-autonomous-benchmarking-and-issue-generation`, `030-worker-cognitive-demand-model-routing`

## Sessions

- 2026-07-10: User asked what actually improves for users when model routing is introduced; a measurable quality/cost feedback loop was identified as the next safeguard.

## Links

- Spec: `specs/083-model-routing-evaluation-harness/spec.md`
- Status: `specs/083-model-routing-evaluation-harness/status.md`
- Sessions: `sessions/083-model-routing-evaluation-harness/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:spec 083-model-routing-evaluation-harness`
