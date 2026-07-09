# Issue 076: Fast Path Shaping Router

**Status: done** — created 2026-07-09, started 2026-07-09, done 2026-07-09.
**Priority: p1**

## Summary

Keep the normal "make an issue" path fast, while adding a lightweight shaping router that asks 1-3 questions only when a request is vague, risky, strategic, or too broad to turn into an agent-ready issue.

## Source

- Type: user product direction
- Link: local Codex session
- Date: 2026-07-09

## Opportunity

ModuFlow's value is clearest when it keeps AI agents aligned with product context without slowing down clear requests. The current loop already supports goal/spec/issue/plan/review, and users often expect the short path:

```text
"이슈 만들어줘" -> product:issue
```

That short path must stay short. The missing piece is a router that detects when the request is too vague, large, risky, or strategic for immediate issue creation and then asks the smallest useful number of questions before creating the issue/spec/goal.

Ouroboros highlighted the appeal of a Socratic, multi-agent question flow. ModuFlow should adapt that pattern for product execution: multiple perspectives generate questions, the coordinator compresses them into a small set of high-signal questions, and the answers become durable context for the rest of the loop.

## Scope

### In

- Fast-path routing: clear issue requests go directly to `product:issue` without interview.
- Shaping-path routing: ambiguous or broad requests ask 1-3 concise product questions before issue/spec creation.
- Panel-path routing: strategic/new-product/high-risk requests may use a Socratic LLM panel, but only the compressed questions are shown to the user.
- Routing criteria for fast vs shaping vs panel paths.
- Durable shaping artifact only when useful, likely `specs/<id>/interview.md`, `workspace/opportunities.md`, or an opportunity-linked equivalent.
- Promotion path from shaped answers to `product:goal`, `product:spec`, or `product:issue`.
- `product:loop` behavior that can recommend "create issue now" vs "ask one shaping question first".
- README/docs positioning that explains ModuFlow's method: spec-first planning, issue-driven execution, review-gated completion, evidence-based decisions, and Git-versioned memory.

### Out

- Replacing the existing goal/spec/issue/plan/review commands.
- Making interview mandatory before all issues.
- Exposing every subagent's raw chain of thought or unfiltered question list to the user.
- Building a large web onboarding product before the CLI/agent flow is proven.
- Adding a new database or SaaS dependency for interview state.
- Adding implementation-readiness gates; that belongs to `077-implementation-readiness-gate`.

## Acceptance Criteria

- Clear requests like "이슈 만들어줘: <specific task>" still create an issue without extra questions.
- Ambiguous requests trigger at most 1-3 shaping questions by default.
- Strategic/high-risk requests may trigger a panel path, but raw panel output is compressed before user display.
- Durable shaping records are created only when the shaping changes product context or should be reused later.
- The shaped artifact can be promoted into existing ModuFlow artifacts without duplicating context.
- `product:loop` can recommend fast-path issue creation, short shaping, or panel shaping based on request clarity and risk.
- README or user-facing docs describe the product-context method and adapter-based workflow sources accurately.

## Verification

Commands the executing agent runs to self-check before handing off.

- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

Starting files/components for the executing agent.

- `README.md`
- `commands/product-opportunity.md`
- `commands/product-goal.md`
- `commands/product-spec.md`
- `commands/product-issue.md`
- `commands/product-loop.md`
- `skills/index/SKILL.md`
- `skills/pm-execution-router/SKILL.md`
- `templates/`
- `scripts/`

## Scope Fence

Do NOT touch (files, behaviors, or decisions out of bounds for this issue).

- Do not remove or rename existing `product:*` commands.
- Do not make interview mandatory for all work.
- Do not introduce external storage.
- Do not hardcode host-specific model names for panel roles.
- Do not add frontend QA templates or execute readiness gates in this issue.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [x] spec → `specs/076-product-context-interview-and-readiness-loop/spec.md`
- [x] benchmark/update notes → link the 2026-07-08 Ouroboros/MeshKit benchmark or copy it into ModuFlow evidence if needed
- [x] plan → `specs/076-product-context-interview-and-readiness-loop/plan.md`
- [x] execute → local implementation changes
- [x] review → `specs/076-product-context-interview-and-readiness-loop/review.md`
- [x] pr → `specs/076-product-context-interview-and-readiness-loop/pr.md`
- [x] docs → README and command docs explain positioning, methods, and adapter sources
- [x] release → `specs/076-product-context-interview-and-readiness-loop/release.md`

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `020-user-facing-simple-loop-ux`, `031-goal-driven-autonomous-benchmarking-and-issue-generation`, `046-planning-artifact-templates`, `075-issue-less-context-capture`
- supersedes:
- related: `019-loop-kernel-and-state-model`, `067-upstream-adapter-absorption`, `073-project-constitution-steering`, `077-implementation-readiness-gate`, `079-plan-discipline-skill-matrix`

## Sessions

- 2026-07-09: User refined ModuFlow positioning: AI product-context loop using Spec Kit, Superpowers, Anthropic/Codex plugin adapters, Git-versioned Markdown/JSON records, and a Socratic panel-style interview inspired by Ouroboros.
- 2026-07-09: User corrected the product direction: interview must not become a required long process. Clear issue requests stay fast; shaping happens only when the request is vague, risky, strategic, or too broad.
- 2026-07-09: User set an operating principle for future optimization: use multiple real examples and regression tests when tuning routing/discipline behavior, not single-case intuition.

## Links

- Benchmark note: `/Users/dongwon.lee/workhub/company/projects/modu-charge/docs/moduflow-benchmark-ouroboros-meshkit-2026-07-08.md`
- Spec: `specs/076-product-context-interview-and-readiness-loop/spec.md`
- Status: `specs/076-product-context-interview-and-readiness-loop/status.md`
- Sessions: `sessions/076-product-context-interview-and-readiness-loop/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:spec 079-plan-discipline-skill-matrix`
