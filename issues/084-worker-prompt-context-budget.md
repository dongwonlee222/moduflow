# Issue 084: Worker Prompt Context Budget

**Status: backlog** — created 2026-07-10.
**Priority: p3**
**Blocked-by: `082-cross-host-model-capability-routing`**

## Summary

Reduce redundant worker prompt context while preserving the task contract, relevant project decisions, and host-specific routing guidance required to complete work safely.

## Source

- Type: user product direction / model-routing follow-up
- Link: local Codex session, 2026-07-10
- Date: 2026-07-10

## Opportunity

Model routing only saves money if the worker prompt itself does not repeatedly inject long, overlapping instructions. Smaller, better-selected prompts reduce latency and token spend while making the worker's actual task easier to find.

## Scope

### In

- Inventory worker-prompt sections and identify duplicated routing, policy, and memory content.
- Define a context budget and deterministic inclusion order: task contract first, required constraints, relevant decisions, then concise host guidance.
- Deduplicate repeated guidance while preserving links to the canonical source material.
- Add regression tests that verify required task/constraint content survives prompt reduction.

### Out

- Removing safety, scope-fence, or verification instructions to hit a token target.
- Summarizing private repository context through external calls.
- Changing model routing policy itself; that is owned by Issue 082.

## Acceptance Criteria

- Worker prompts have a documented, deterministic section order and budget policy.
- Repeated model-tier and project-policy text is emitted once or referenced compactly.
- Required task contract, scope fence, verification commands, and directly relevant decisions remain present in generated prompts.
- Tests show prompt content shrinks on representative plans without losing required fields.
- Focused tests and `python3 scripts/release_check.py .` pass.

## Verification

Commands the executing agent runs to self-check before handing off.

- `python3 -m unittest tests.test_cognitive_demand_routing -v`
- `python3 -m unittest discover -s tests -p 'test_*worker*prompt*.py' -v`
- `python3 scripts/release_check.py .`

## Entry Points

Starting files/components for the executing agent.

- `scripts/worker_orchestrator.py`
- `scripts/project_execution.py`
- `commands/product-execute.md`
- `skills/superpowers-execution-bridge/SKILL.md`
- `tests/`

## Scope Fence

Do NOT turn context trimming into an instruction-removal mechanism. Preserve user intent, project constraints, and validation requirements ahead of token reduction.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec, plan, design, or review off the books. Check the box and link the artifact when done.

- [ ] spec → `specs/084-worker-prompt-context-budget/spec.md`
- [ ] plan → `specs/084-worker-prompt-context-budget/plan.md`
- [ ] execute → prompt budget policy, generator changes, and regression tests
- [ ] review → `specs/084-worker-prompt-context-budget/review.md`

## Related Issues

- blocks:
- blocked_by: `082-cross-host-model-capability-routing`
- duplicates:
- follows_up: `081-gpt-5-6-model-tier-guidance`
- supersedes:
- related: `038-worker-context-memory-path-injection`, `030-worker-cognitive-demand-model-routing`

## Sessions

- 2026-07-10: User chose the balanced model as the default; prompt-cost control was identified as the companion improvement for predictable everyday use.

## Links

- Spec: `specs/084-worker-prompt-context-budget/spec.md`
- Status: `specs/084-worker-prompt-context-budget/status.md`
- Sessions: `sessions/084-worker-prompt-context-budget/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:spec 084-worker-prompt-context-budget`
