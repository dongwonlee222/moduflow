---
kind: benchmark
title: Agentic execution governance trend — ModuFlow, Spec Kit, Codex, Claude, and Copilot
date: 2026-09-01
issue_id: "112-execution-planner-and-backend-boundary"
decision_supported: "Issues 112-114 execution ownership and roadmap scope"
sources:
  - https://github.github.com/spec-kit/reference/agentic-sdd.html
  - https://github.github.com/spec-kit/concepts/complex-features.html
  - https://github.github.com/spec-kit/upgrade.html
  - https://github.com/github/spec-kit/blob/main/docs/history.md
  - https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/custom-agents
  - https://developers.openai.com/api/docs/guides/latest-model
  - https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - https://code.claude.com/docs/en/agent-sdk/python
---

# Agentic Execution Governance Trend (2026-09-01)

## Question

Is the proposed boundary—ModuFlow as the canonical management/control layer, Spec Kit as an optional read-only validator, Superpowers as the execution discipline, and the active coding host as the actual agent runtime—consistent with current official agentic-development direction?

## Bottom Line

Yes, with one important constraint: the direction is current because it separates durable intent, validation, execution, and approval, not because it adds another orchestration engine. The current official sources favor durable artifacts, agent-independent integrations, small bounded work units, host-native subagent delegation, scoped tools/context, and explicit review gates. They also warn against unnecessary subagents and duplicated mutable sources of truth.

This supports Issues 112-114. It does not support a new ModuFlow task runtime, automatic parallelism, or full Spec Kit adoption.

## Official-Source Findings

| Pattern | Official evidence | Implication for ModuFlow |
| --- | --- | --- |
| Durable, agent-independent artifacts | Spec Kit 1.x describes specs, plans, and tasks as durable artifacts and supports many coding-agent integrations. | Keep Git-native ModuFlow artifacts canonical and make host choice replaceable. |
| Quality gates are not implementation state | Spec Kit says custom checklists are reviewer-owned; checked criteria do not mean implementation is complete. `analyze` is read-only. | Separate requirements approval, implementation completion, review, and merge states. |
| Large work should be bounded before delegation | Spec Kit recommends limiting task/phase scope first, then subagents for parallel tasks, and only then decomposing further. | Generate workers only for concrete executable tasks; do not turn every checkbox into a worker. |
| Subagents belong to the runtime | GitHub Copilot SDK delegates custom agents in isolated contexts with scoped prompts/tools and lifecycle events. Claude Agent SDK exposes programmatic subagents, hooks, permissions, budgets, and session controls. | ModuFlow should emit a host-neutral routing contract, not implement a competing dispatcher. |
| Parallelism is conditional | OpenAI's current multi-agent guidance limits the benefit to complex work that divides cleanly into independent workstreams. | Select inline for simple/shared-state work and SDD only for bounded independent streams. |
| Over-delegation is a known failure mode | Anthropic warns that current Claude models may overuse subagents and explicitly recommends direct work for simple, sequential, single-file, or shared-context tasks. | Make non-delegation a first-class result, not a fallback failure. |
| Governance should reference one live source | Spec Kit's upgrade guidance uses runtime resolution against one constitution and warns that edit-in-place propagation conflicts with composition. | Keep one canonical ModuFlow spec/plan/tasks set; link execution detail instead of copying lifecycle state. |
| Upgrades require explicit integration handling | Spec Kit's 1.x upgrade flow treats agent integrations as managed, separately upgradeable assets and preserves repository specs. | Review exact selected templates/version/SHA before replacing the 0.16.1 adapter pin. |

## What Is Actually Recent

- Spec Kit reached `1.0.0` on 2026-08-21 and reports an integration architecture designed to work across agents rather than bind the process to one model.
- Spec Kit's current workflow includes optional clarification, checklist, analysis, and convergence gates around the core spec/plan/tasks/implement path.
- OpenAI documents multi-agent as useful for complex, cleanly divisible independent workstreams rather than as a universal default.
- Anthropic exposes subagents, permissions, hooks, task budgets, and session lifecycle through the host SDK while separately warning about excessive delegation.
- GitHub Copilot SDK exposes custom agents as runtime-owned isolated sessions with scoped tools and streamed lifecycle events.

These are converging product directions, but they are not proof of one universal industry standard. The conclusion is an inference from official product architectures and guidance.

## Alignment Assessment

| Proposed decision | Assessment | Reason |
| --- | --- | --- |
| ModuFlow owns issue/spec/roadmap/state | aligned | Durable Git artifacts survive agent and session changes. |
| Spec Kit provides selected read-only validation | aligned | `clarify`, `checklist`, and `analyze` are quality-oriented; full `implement` would duplicate execution ownership. |
| Superpowers SDD owns TDD/review discipline | aligned | Bounded task execution with review fits the official small-scope/delegation direction. |
| Codex/Claude/Copilot own actual agent runtime | strongly aligned | Current hosts already expose subagents, tools, permissions, sessions, and lifecycle events. |
| ModuFlow creates another dispatcher | not aligned | It duplicates runtime features and increases stale state, cost, and false execution claims. |
| Every checkbox becomes a worker | not aligned | Official guidance treats gates, reviewer checklists, and implementation tasks as different concepts. |
| Full Spec Kit lifecycle inside ModuFlow | not aligned | It creates independent spec/plan/tasks/implement truth and upgrade ownership. |

## Decisions for the Roadmap

1. Issue 112 must make `inline` a normal successful execution decision and reserve `superpowers-sdd` for bounded implementation streams.
2. Worker-plan generation must fail closed when implementation tasks lack concrete files/globs or valid dependencies.
3. Issue 113 must keep `implementation_done`, review findings, human approval, and merge evidence separate.
4. Issue 114 must preserve the four-function allowlist and exact pin/hash model while reviewing the Spec Kit 1.x changes.
5. Issue 104 must depend on Issue 112 so the natural-language orchestrator consumes one stable execution-routing contract.

## Planning Gate

Issue 112's plan is not complete until its spec explicitly covers:

- positive non-delegation (`inline`) behavior;
- worker-task semantic filtering;
- required file/dependency boundaries;
- one selected backend with no dispatch claim;
- canonical artifact ownership;
- host-neutral adapter fixtures for Codex, Claude Code, and Copilot;
- compatibility with Issue 103 transactions and existing readiness/capability gates.

## Non-Adoptions

- No ModuFlow scheduler, queue, agent tree, or worktree engine.
- No automatic fleet/parallel mode.
- No full Spec Kit runtime or `.specify` project lifecycle.
- No unpinned upstream templates.
- No automatic reviewer or exception approval.
