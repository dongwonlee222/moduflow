# Spec: GPT-5.6 Model Tier Guidance

Issue: 081-gpt-5-6-model-tier-guidance

## Problem

ModuFlow's worker dispatch model intentionally stores semantic cognitive demand levels instead of model slugs. OpenAI GPT-5.6 now has a clear `sol` / `terra` / `luna` family split and reasoning controls, so agents need current guidance without turning ModuFlow artifacts into OpenAI-specific config.

## Solution

Keep `deep` / `balanced` / `fast` as the canonical ModuFlow values. Add GPT-5.6 as a current host-specific example:

| CognitiveDemand | GPT-5.6 starting point | Reasoning guidance |
| --- | --- | --- |
| `deep` | `gpt-5.6-sol` | high/xhigh; use max or pro mode only for quality-first gates after comparison |
| `balanced` | `gpt-5.6-terra` | medium; compare one level lower on representative tasks |
| `fast` | `gpt-5.6-luna` | low or none for latency-sensitive/high-volume work |

## Design Decisions

- Do not change worker metadata or JSON schema.
- Do not make pro mode automatic.
- Treat OpenAI GPT-5.6 mapping as current guidance, not a permanent schema contract.
- Keep prompts outcome-focused and put model/reasoning choices in host config or request parameters where supported.

## Acceptance Criteria

- `commands/product-execute.md` documents the GPT-5.6 mapping.
- `skills/superpowers-execution-bridge/SKILL.md` documents the same optional mapping.
- `scripts/worker_orchestrator.py` generated prompts include the matching GPT-5.6 example for each tier.
- `tests/test_cognitive_demand_routing.py` verifies all three examples.

## Next Command

`product:review 081-gpt-5-6-model-tier-guidance`
