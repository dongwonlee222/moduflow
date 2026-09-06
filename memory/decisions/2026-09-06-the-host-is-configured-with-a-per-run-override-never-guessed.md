---
id: 2026-09-06-the-host-is-configured-with-a-per-run-override-never-guessed
kind: decision
title: The host is configured with a per-run override, never guessed
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
summary: The execution host comes from .moduflow/config.json with a default of claude-code, and any invocation may override it. It is never inferred from the environment. Host names reuse the existing EXECUTION_BACKENDS set in project_loop.py:21 rather than a new registry, which also settles the copilot vs copilot-cloud-agent spelling. Decided 2026-09-06 for issue 112 T09.
rationale: Guessing the host is the failure this issue exists to remove. A wrong guess writes a wrong value into a canonical artifact silently, which is exactly how codex/ ended up in every worker plan regardless of host. It also defeats the refusal decision: an unregistered host is supposed to stop, and a guess that lands on a registered name passes a gate that should have blocked. The owner runs Claude Code today and switches tools during the day — his words, 지금은 클로드인데 이것저것 한다 — so a configured default without an override would be wrong half the time, and an override without a default would mean typing the host on every command.
evidence: worker_orchestrator.py:408 hardcodes codex/<issue>-<task> regardless of host; project_loop.py:21 already defines EXECUTION_BACKENDS = {codex, claude-code, copilot-cloud-agent, openhands, manual, host-subagent} and git bindings already carry an execution_backend field
alternatives: Infer from environment variables or the running process — rejected: a wrong inference is silent and reproduces the defect. Per-invocation only, no default — rejected: the host must be typed on every command. Config only, no override — rejected: the owner switches tools within a day.
reversal_conditions: Revisit if the config field goes stale in practice — if plans start showing a host the owner was not using, the default is worse than no default. Also revisit if a host appears that EXECUTION_BACKENDS does not name.
confidence: medium
---

# The host is configured with a per-run override, never guessed

## Summary

The execution host comes from .moduflow/config.json with a default of claude-code, and any invocation may override it. It is never inferred from the environment. Host names reuse the existing EXECUTION_BACKENDS set in project_loop.py:21 rather than a new registry, which also settles the copilot vs copilot-cloud-agent spelling. Decided 2026-09-06 for issue 112 T09.

## Rationale

Guessing the host is the failure this issue exists to remove. A wrong guess writes a wrong value into a canonical artifact silently, which is exactly how codex/ ended up in every worker plan regardless of host. It also defeats the refusal decision: an unregistered host is supposed to stop, and a guess that lands on a registered name passes a gate that should have blocked. The owner runs Claude Code today and switches tools during the day — his words, 지금은 클로드인데 이것저것 한다 — so a configured default without an override would be wrong half the time, and an override without a default would mean typing the host on every command.

## Evidence

worker_orchestrator.py:408 hardcodes codex/<issue>-<task> regardless of host; project_loop.py:21 already defines EXECUTION_BACKENDS = {codex, claude-code, copilot-cloud-agent, openhands, manual, host-subagent} and git bindings already carry an execution_backend field

## Alternatives

Infer from environment variables or the running process — rejected: a wrong inference is silent and reproduces the defect. Per-invocation only, no default — rejected: the host must be typed on every command. Config only, no override — rejected: the owner switches tools within a day.

## Links

- Issue: 
- Spec: 

## Reversal Conditions

Revisit if the config field goes stale in practice — if plans start showing a host the owner was not using, the default is worse than no default. Also revisit if a host appears that EXECUTION_BACKENDS does not name.
