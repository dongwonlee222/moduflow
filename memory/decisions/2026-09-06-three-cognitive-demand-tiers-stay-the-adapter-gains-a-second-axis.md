---
id: 2026-09-06-three-cognitive-demand-tiers-stay-the-adapter-gains-a-second-axis
kind: decision
title: Three cognitive-demand tiers stay; the adapter gains a second axis
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
tags: [112, host-adapter, model-tier]
summary: deep|balanced|fast is kept as the cognitive-demand vocabulary. The host adapter's model() returns two values — an effort level from the low/medium/high/xhigh/max ladder and a model hint — rather than one prompt line. OpenRouter's five-band cost_tier was considered and left open, not adopted. Decided 2026-09-06 for issue 112 T06.
rationale: No established vocabulary displaces three named tiers: fifteen projects surveyed and two tiers is actually the most common count among multi-vendor agent tools (aider main/weak, Cline Plan/Act, Goose lead/worker). Renaming would migrate 142 issues and buy nothing. But there IS a convention on shape, and this product was on the wrong side of it: every tool that separates task difficulty from model choice uses two axes, and ModuFlow had one field doing both jobs. That is the actual cause of COGNITIVE_DEMAND_GUIDANCE having to name gpt-5.6-sol — one field cannot say 'hard work' without naming something concrete. Adopting five bands would collapse the mapping table into an identity function, which is a real gain, but it costs a schema migration across 142 issues to remove one small table.
evidence: The literal array ["low","medium","high","xhigh","max"] is present in the shipped claude binary alongside effortLevel and twelve CLAUDE_CODE_EFFORT_LEVEL occurrences, verified 2026-09-06. MCP modelPreferences rationale quoted in docs/superpowers/specs/2026-09-05-issue-112-host-adapter-interface.md; not adopted because MCP sampling is deprecated as of revision 2026-07-28 (SEP-2577).
alternatives: Adopt OpenRouter cost_tier's five bands (low|medium|high|xhigh|max) so tiers and effort become the same value — left open, not rejected; the price is migrating 142 issues. Adopt MCP modelPreferences' three continuous 0-1 axes — rejected: heavier contract than three named tiers earn, and the feature is deprecated upstream.
reversal_conditions: Revisit if three tiers stop distinguishing anything in practice — specifically if balanced becomes a default nobody chooses deliberately, which the survey suggests is the common fate of a middle tier. Also revisit if a host appears whose effort vocabulary does not map onto the five-band ladder.
confidence: medium
---

# Three cognitive-demand tiers stay; the adapter gains a second axis

## Summary

deep|balanced|fast is kept as the cognitive-demand vocabulary. The host adapter's model() returns two values — an effort level from the low/medium/high/xhigh/max ladder and a model hint — rather than one prompt line. OpenRouter's five-band cost_tier was considered and left open, not adopted. Decided 2026-09-06 for issue 112 T06.

## Rationale

No established vocabulary displaces three named tiers: fifteen projects surveyed and two tiers is actually the most common count among multi-vendor agent tools (aider main/weak, Cline Plan/Act, Goose lead/worker). Renaming would migrate 142 issues and buy nothing. But there IS a convention on shape, and this product was on the wrong side of it: every tool that separates task difficulty from model choice uses two axes, and ModuFlow had one field doing both jobs. That is the actual cause of COGNITIVE_DEMAND_GUIDANCE having to name gpt-5.6-sol — one field cannot say 'hard work' without naming something concrete. Adopting five bands would collapse the mapping table into an identity function, which is a real gain, but it costs a schema migration across 142 issues to remove one small table.

## Evidence

The literal array ["low","medium","high","xhigh","max"] is present in the shipped claude binary alongside effortLevel and twelve CLAUDE_CODE_EFFORT_LEVEL occurrences, verified 2026-09-06. MCP modelPreferences rationale quoted in docs/superpowers/specs/2026-09-05-issue-112-host-adapter-interface.md; not adopted because MCP sampling is deprecated as of revision 2026-07-28 (SEP-2577).

## Alternatives

Adopt OpenRouter cost_tier's five bands (low|medium|high|xhigh|max) so tiers and effort become the same value — left open, not rejected; the price is migrating 142 issues. Adopt MCP modelPreferences' three continuous 0-1 axes — rejected: heavier contract than three named tiers earn, and the feature is deprecated upstream.

## Links

- Issue: 
- Spec: 

## Reversal Conditions

Revisit if three tiers stop distinguishing anything in practice — specifically if balanced becomes a default nobody chooses deliberately, which the survey suggests is the common fate of a middle tier. Also revisit if a host appears whose effort vocabulary does not map onto the five-band ladder.
