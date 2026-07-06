---
id: 2026-07-06-ai-native-context-benchmark
kind: evidence
title: AI-Native Context and Issue-Contract Benchmark
issue_id: 075-issue-less-context-capture
spec: specs/075-issue-less-context-capture/spec.md
source_event: subagent-web-research
date: 2026-07-06
tags: [benchmark, ai-agent, memory, issue-contract, promotion-gates]
summary: Second-round benchmark covering AI-native memory systems (Claude Code, Cursor, Devin, Letta/Mem0/Zep) and human-AI issue contracts (Linear agents, Copilot coding agent) — corrects the human-tool assumptions of the first benchmark.
---

# AI-Native Context & Issue-Contract Benchmark

Researched 2026-07-06 by two web-research subagents after the user observed the first benchmark (`2026-07-06-issue-less-context-benchmark.md`) covered only human-first tools while ModuFlow's primary operator is an AI agent.

## Round A — AI-native memory systems

- **Claude Code auto memory**: human-authored CLAUDE.md vs AI-authored memory split at file level; **hard cap** (MEMORY.md first 200 lines/25KB loaded) structurally forces curation; human control is post-hoc audit (view/edit/delete), no write gate. ([docs](https://code.claude.com/docs/en/memory))
- **Cursor Memories**: sidecar model observes chat, **proposes** memories; developer approves/rejects; only approved memories are used. Clearest AI-observe + human-gate example. ([changelog](https://cursor.com/changelog/1-0))
- **Devin Knowledge**: every entry carries a **retrieval trigger description** (when to recall) as a first-class field; Devin auto-proposes, human edits/rejects. Playbooks (task templates) vs Knowledge (standing facts) role separation. ([docs](https://docs.devin.ai/product-guides/knowledge))
- **AGENTS.md**: 60k+ repos, Linux Foundation; agent-readable repo files with nested directory scoping — same family as ModuFlow's Git-native artifacts. ([agents.md](https://agents.md/))
- **Letta sleep-time compute**: consolidation runs as an **async separate pass** by a dedicated memory agent, not inline during conversation. ([blog](https://www.letta.com/blog/sleep-time-compute/))
- **Mem0**: write path forces one of **ADD / UPDATE / DELETE / NOOP** after semantic dedup against existing memories — new-record is not the default operation. ([paper](https://arxiv.org/abs/2504.19413))
- **Zep/Graphiti**: contradicting facts **invalidate** (bi-temporal valid_at/invalid_at), never delete — supersede-don't-delete. ([paper](https://arxiv.org/abs/2501.13956))

## Round B — issues as human-AI contracts

- **Linear agents**: delegate to agent, human assignee keeps accountability; Triage Intelligence proposes team/assignee/duplicates with per-attribute auto-apply opt-in; all machine intake lands in **Triage staging state** — no separate draft-issue state exists anywhere in the market, staging states are reused. ([docs](https://linear.app/docs/agents-in-linear), [triage-intelligence](https://linear.app/docs/triage-intelligence))
- **Copilot coding agent empirics** (3,180 PRs, [arXiv](https://arxiv.org/html/2512.21426v1)): narrow scope +16.4%p merge rate, self-contained +16.7%p, implementation guidance +7.6%p, file pointers +6.4%p; **long descriptions −9~11%p**. All conditions met: 77.1% vs 45.9%. Official guidance: "consider whether the issue description works as an AI prompt".
- **Devin delegation**: one session per subtask, junior-engineer-sized (1–6h), contract complete **before** start (mid-session requirement additions degrade output); tickets seed sessions via integrations. ([guidelines](https://docs.devin.ai/essential-guidelines/instructing-devin-effectively))
- **Sentry→Linear**: agent does analysis, but **issue-creation conditions are human-owned alert rules** (severity/volume thresholds). ([cookbook](https://sentry.io/cookbook/fix-bugs-sentry-agent-linear/))
- **Piling problem**: approval queues exceeding human absorption capacity is the known failure mode of draft→approve→execute pipelines. ([mindstudio](https://www.mindstudio.ai/blog/piling-problem-ai-agent-workflows))

## Corrections to the first (human-tool) benchmark

1. **"Minimize capture friction" is the wrong goal for AI writers** — capture is free; the binding constraints are write gates (dedup operations) and read cost (context budget, PM attention).
2. **Write operations should be ADD/UPDATE/SUPERSEDE/NOOP** (Mem0), not append-only; decisions supersede rather than delete (Zep).
3. **Always-loaded index needs a hard cap** (Claude Code) — caps create curation pressure; uncapped durable layers never get curated.
4. **Records need retrieval triggers** (Devin) — "when should this be re-read" as required metadata.
5. **Promotion = AI proposal + human approve/edit/dismiss** (Cursor/Devin/Linear/Sentry unanimous) — human is approver-editor, not author; approval required only at the canonical transition, capture itself stays free.
6. **Promotion timing = execution-ready** ("works as an AI prompt": scope + verifiable AC + entry pointers); early issuance of unshaped work measurably lowers merge rates.
7. **Issue schema for AI executors**: verification commands, entry points, scope fence, self-containment; narrative background short by design.
8. **Protect the single PM via batching and caps**, not by removing approval: batched review queue, promotion-queue size as a visible status metric, retention tied to releases not wall-clock days.
