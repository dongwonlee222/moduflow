---
id: 2026-09-06-unregistered-host-refuses-rather-than-falling-back
kind: decision
title: Unregistered host refuses rather than falling back
issue_id: 
spec: 
source_event: 
source_artifacts: []
review_after: 
supersedes: []
superseded_by: []
depends_on: []
references: []
storage_policy: local
mirror_targets: []
owner: Dongwon Lee
date: 2026-09-06
tags: [112, host-adapter, execution]
summary: When execution routing runs on a host with no adapter, ModuFlow refuses and asks for an adapter. It does not fall back to a generic adapter that fills in blanks. Decided 2026-09-06 for issue 112 T06.
rationale: A generic fallback always works, and something that always works is never replaced — that is the exact mechanism that left a hardcoded codex/ worktree prefix in every worker plan regardless of host. Refusing makes the missing adapter visible at the moment it is missing. The owner runs Claude Code and Codex interchangeably, so both get adapters and neither is affected by the refusal path; the cost falls only on a third host, once, and is a one-time cost that buys a correct canonical artifact forever.
evidence: worker_orchestrator.py:408 writes codex/<issue>-<task> regardless of host; :50-66 pushes OpenAI model names into every task prompt via COGNITIVE_DEMAND_GUIDANCE applied at :388; docs/superpowers/specs/2026-09-05-issue-112-host-adapter-interface.md
alternatives: Generic fallback adapter — no worktree, no model hint, no subagent. Rejected: it removes the pressure to write a real adapter, reproducing the defect this issue exists to fix.
reversal_conditions: Reverse if the refusal blocks real work — specifically if someone hits it on a host they cannot write an adapter for. Also revisit if adapters turn out to be expensive to write; the decision assumes an adapter is three small methods.
confidence: medium
---

# Unregistered host refuses rather than falling back

## Summary

When execution routing runs on a host with no adapter, ModuFlow refuses and asks for an adapter. It does not fall back to a generic adapter that fills in blanks. Decided 2026-09-06 for issue 112 T06.

## Rationale

A generic fallback always works, and something that always works is never replaced — that is the exact mechanism that left a hardcoded codex/ worktree prefix in every worker plan regardless of host. Refusing makes the missing adapter visible at the moment it is missing. The owner runs Claude Code and Codex interchangeably, so both get adapters and neither is affected by the refusal path; the cost falls only on a third host, once, and is a one-time cost that buys a correct canonical artifact forever.

## Evidence

worker_orchestrator.py:408 writes codex/<issue>-<task> regardless of host; :50-66 pushes OpenAI model names into every task prompt via COGNITIVE_DEMAND_GUIDANCE applied at :388; docs/superpowers/specs/2026-09-05-issue-112-host-adapter-interface.md

## Alternatives

Generic fallback adapter — no worktree, no model hint, no subagent. Rejected: it removes the pressure to write a real adapter, reproducing the defect this issue exists to fix.

## Links

- Issue: 
- Spec: 

## Reversal Conditions

Reverse if the refusal blocks real work — specifically if someone hits it on a host they cannot write an adapter for. Also revisit if adapters turn out to be expensive to write; the decision assumes an adapter is three small methods.
