---
id: 2026-07-26-model-routing-check
kind: evidence
title: Cross-Host Model Routing — Runtime Check on Claude Code
issue_id: 082-cross-host-model-capability-routing
spec: null
source_event: local-runtime-verification
date: 2026-07-26
tags: [model-routing, cognitive-demand, worker-orchestrator, host-adapter, dogfooding]
summary: Ran the cognitive-demand routing path on a Claude Code host at commit 6bca2b4. Semantic routing works and emits neutral guidance first, but GPT-5.6 model names are hardcoded into the prompt-assembly path and reach 10/10 generated worker-plan prompts regardless of host.
---

# Cross-Host Model Routing — Runtime Check

Verified 2026-07-26 on a Claude Code host, local `main` at commit `6bca2b4`, working tree clean.
Run to answer a direct question before planning Issue 082: does ModuFlow's routing guidance
behave correctly when the host is not OpenAI?

## Commands run

| Command | Result |
| --- | --- |
| `python3 -m unittest tests.test_cognitive_demand_routing -v` | 13/13 OK |
| `python3 scripts/worker_orchestrator.py 093-frontmatter-issue-schema-readiness-gate --root .` | 10 tasks, 5 workers, demand `balanced` 8 / `fast` 2, `parallel.mode: sequential` (`eligible: false`), `next_command` emitted |
| `python3 scripts/worker_orchestrator.py 095-commit-issue-resolution-parity --root .` | `Missing tasks file: specs/095-.../tasks.md` — correct gate behaviour; no spec exists yet |

## Findings

- `scripts/worker_orchestrator.py:44` — all three `COGNITIVE_DEMAND_GUIDANCE` strings hardcode
  `gpt-5.6-sol` / `gpt-5.6-terra` / `gpt-5.6-luna`.
- `scripts/worker_orchestrator.py:294-298` — that string is concatenated into every
  `subagent.Prompt` unconditionally. The observed 10/10 rate is structural, not a sample.
- No host detection exists anywhere in the orchestrator (`grep host` returns one comment line).
- The same GPT-5.6 table is duplicated inline in `skills/superpowers-execution-bridge/SKILL.md`
  and `commands/product-execute.md` — three maintenance sites total.
- `docs/host-adapter-guidance.md` (103 lines), listed as an Issue 082 entry point, currently
  covers version bumping only and contains no model-routing content.
- Scope limit: verification stops at the worker-plan JSON. Whether these prompts reach a live
  subagent was not exercised — that runs through the `product:execute` path.

## Assessment against Issue 082 acceptance criteria

| Criterion | Status |
| --- | --- |
| Three semantic demand values preserved on every host | Met |
| Unknown host emits platform-neutral guidance, not a wrong provider model name | Met — the neutral clause (`use your standard production model`) leads; GPT appears in a conditional (`If using OpenAI GPT-5.6, ...`) |
| Provider mappings isolated to a maintainable profile surface | **Not met** — split across code constant, SKILL.md, and product-execute.md |
| Source and refresh metadata on provider guidance | **Not met** |

## Judgement

This is not misrouting. A Claude subagent follows the leading semantic clause and skips the
GPT branch. The real cost is prompt noise on every task, a three-site maintenance burden, and
a contradiction of the no-hardcode principle stated in `SKILL.md:80` itself. p2 is the right
priority.

Issue 081 is not a defect here. Issue 082's own Opportunity section frames it as the planned
generalization: *"Issue 081 adds current GPT-5.6 examples, but ModuFlow is designed to run in
more than one host."*

Concrete per-host values are wanted, not forbidden — 082 requires that "known host profiles
render one clear recommended starting point ... for each demand tier". What must change is
placement: one dated advisory profile carrying source and refresh metadata, with the neutral
fallback retained for unknown hosts, replacing three inline copies.

Open scoping question for the 082 plan: extend `docs/host-adapter-guidance.md` with a routing
section, or introduce a separate profile file. Not decided here.
