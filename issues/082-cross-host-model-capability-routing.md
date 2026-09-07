# Issue 082: Cross-Host Model Capability Routing

**Status: superseded-by-112** — closed 2026-09-07 against `workspace/goal.md`. Issue 112 shipped the thing this asked for: `scripts/execution_host_adapter.py` registers `claude-code`, `codex` and `copilot-cloud-agent` behind three pure methods, and `model()` returns `{effort, model_hint}` per host. Cross-host capability routing exists; this file describes building it again. Kept for the record; do not implement from this file.
**Priority: p2**

## Summary

Extend ModuFlow's semantic `deep` / `balanced` / `fast` worker routing so its guidance is useful across Codex, Claude Code, and Gemini/Antigravity without making provider model names part of the durable worker schema.

## Source

- Type: user product direction / model-routing follow-up
- Link: local Codex session, 2026-07-10
- Date: 2026-07-10

## 안 고치면

아무도 막히지 않습니다 — 112가 도구별 어댑터로 이미 해결했습니다. **닫을 후보.**

## Opportunity

Issue 081 adds current GPT-5.6 examples, but ModuFlow is designed to run in more than one host. A user should express the importance, complexity, and repetition of work once; the host should receive an appropriate provider-specific starting point or a safe generic fallback.

## Scope

### In

- Define a versioned, host-capability profile for OpenAI/Codex, Anthropic/Claude Code, and Google/Gemini/Antigravity.
- Keep `CognitiveDemand` (`deep`, `balanced`, `fast`) as the only durable routing input.
- Produce host-specific model-family and reasoning guidance only when the current host is known; otherwise retain generic guidance.
- Add table-driven regression coverage for each host and the unknown-host fallback.
- Document that provider guidance is advisory and must be refreshed from official sources, not treated as a permanent model registry.

### Out

- Provider credentials, API calls, account detection, or automatic model switching.
- A permanent cross-provider price table or vendor-specific worker-plan fields.
- Changing Codex, Claude Code, or Antigravity installation/configuration.

## Acceptance Criteria

- Worker plans keep the same three semantic demand values on every host.
- Known host profiles render one clear recommended starting point and reasoning guidance for each demand tier.
- An unknown host emits platform-neutral guidance rather than an incorrect provider model name.
- Provider mappings are isolated to a maintainable profile/document surface with source and refresh metadata.
- Focused routing tests and `python3 scripts/release_check.py .` pass.

## Verification

Commands the executing agent runs to self-check before handing off.

- `python3 -m unittest tests.test_cognitive_demand_routing -v`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

Starting files/components for the executing agent.

- `scripts/worker_orchestrator.py`
- `commands/product-execute.md`
- `skills/superpowers-execution-bridge/SKILL.md`
- `tests/test_cognitive_demand_routing.py`
- `docs/host-adapter-guidance.md`

## Scope Fence

Do NOT touch provider credentials, live provider requests, pricing enforcement, or host application configuration. Do not replace semantic cognitive-demand routing with model slugs.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec, plan, design, or review off the books. Check the box and link the artifact when done.

- [ ] spec → `specs/082-cross-host-model-capability-routing/spec.md`
- [ ] plan → `specs/082-cross-host-model-capability-routing/plan.md`
- [ ] execute → host-capability profile, worker guidance, and regression tests
- [ ] review → `specs/082-cross-host-model-capability-routing/review.md`

## Related Issues

- blocks: `083-model-routing-evaluation-harness`, `084-worker-prompt-context-budget`
- blocked_by:
- duplicates:
- follows_up: `081-gpt-5-6-model-tier-guidance`
- supersedes:
- related: `030-worker-cognitive-demand-model-routing`, `079-plan-discipline-skill-matrix`

## Sessions

- 2026-07-10: User requested routing guidance that also covers Claude and Gemini/Antigravity.

## Links

- Spec: `specs/082-cross-host-model-capability-routing/spec.md`
- Status: `specs/082-cross-host-model-capability-routing/status.md`
- Sessions: `sessions/082-cross-host-model-capability-routing/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:spec 082-cross-host-model-capability-routing`
