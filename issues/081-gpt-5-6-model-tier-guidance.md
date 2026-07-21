# Issue 081: GPT-5.6 Model Tier Guidance

**Status: done** — created 2026-07-10, started 2026-07-10, done 2026-07-10.
**Priority: p2**

## Summary

Update ModuFlow's subagent model-tier guidance for the OpenAI GPT-5.6 family while preserving the existing `deep` / `balanced` / `fast` semantic routing model.

## Source

- Type: user request / OpenAI docs refresh
- Link: local Codex session, official OpenAI model guidance checked 2026-07-10
- Date: 2026-07-10

## Opportunity

ModuFlow already avoids hardcoded worker model names, but the current guidance only says "most capable", "standard", and "fastest". GPT-5.6 introduces `sol` / `terra` / `luna`, plus `max` reasoning and pro mode, which map cleanly to ModuFlow's cognitive demand tiers if documented as current examples rather than durable schema.

## Scope

### In

- Add OpenAI GPT-5.6 starting-point guidance for `deep`, `balanced`, and `fast`.
- Keep `CognitiveDemand` as the durable worker-plan field.
- Update tests so generated worker prompts retain the current GPT-5.6 guidance.

### Out

- Replacing `deep` / `balanced` / `fast` with OpenAI-specific schema values.
- Changing API clients, SDK usage, pricing, or provider configuration.
- Enabling GPT-5.6 pro mode automatically.

## Acceptance Criteria

- `product:execute` explains the GPT-5.6 starting map.
- `superpowers-execution-bridge` explains the same map and keeps it optional/platform-specific.
- Generated worker prompts mention the GPT-5.6 example model for each cognitive demand tier.
- Existing cognitive-demand routing tests pass.

## Verification

Commands the executing agent runs to self-check before handing off.

- `python3 -m unittest tests.test_cognitive_demand_routing -v`
- `python3 scripts/release_check.py .`

## Entry Points

Starting files/components for the executing agent.

- `scripts/worker_orchestrator.py`
- `commands/product-execute.md`
- `skills/superpowers-execution-bridge/SKILL.md`
- `tests/test_cognitive_demand_routing.py`

## Scope Fence

Do NOT touch provider credentials, live API calls, pricing tables, or release packaging unless separately requested.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [x] spec → `specs/081-gpt-5-6-model-tier-guidance/spec.md`
- [x] plan → `specs/081-gpt-5-6-model-tier-guidance/plan.md`
- [x] execute → local changes in worker guidance and tests
- [x] review → `specs/081-gpt-5-6-model-tier-guidance/review.md`
- [x] update GPT-5.6 tier guidance in command and skill docs
- [x] update generated worker prompt guidance
- [x] update regression tests for GPT-5.6 tier examples

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `030-worker-cognitive-demand-model-routing`
- supersedes:
- related: `067-upstream-adapter-absorption`, `079-plan-discipline-skill-matrix`

## Sessions

- 2026-07-10: User asked to update ModuFlow after checking GitHub/OpenAI details for GPT-5.6.

## Links

- Spec: `specs/081-gpt-5-6-model-tier-guidance/spec.md`
- Review: `specs/081-gpt-5-6-model-tier-guidance/review.md`
- Status: `specs/081-gpt-5-6-model-tier-guidance/status.md`
- Sessions: `sessions/081-gpt-5-6-model-tier-guidance/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:review 081-gpt-5-6-model-tier-guidance`
