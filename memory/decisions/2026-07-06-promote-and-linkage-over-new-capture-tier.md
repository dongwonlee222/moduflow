---
id: 2026-07-06-promote-and-linkage-over-new-capture-tier
kind: decision
title: Promote And Linkage Over New Capture Tier
issue_id: 075-issue-less-context-capture
spec: specs/075-issue-less-context-capture/spec.md
source_event: three-subagent-panel-review
source_artifacts: [memory/evidence/2026-07-06-issue-less-context-benchmark.md, memory/evidence/2026-07-06-ai-native-context-benchmark.md, specs/075-issue-less-context-capture/adversarial-review.md]
retrieval_trigger: when revisiting capture/promotion design, adding new capture commands, or when a teammate joins and the reversal conditions might trigger
review_after: 2026-08-06
supersedes: [2026-07-06-use-issue-less-context-tiers]
superseded_by: []
storage_policy: git-canonical
mirror_targets: []
owner: Dongwon Lee
date: 2026-07-06
tags: [context, workflow, issue-tracking, moduflow, ai-operator]
summary: 075 drops the new 5-type capture tier and product:capture command; it delivers commit-issue linkage convention, a repaired release gate, product:promote with human Git-identity approval, and AI-first issue fields, reusing the four existing capture commands.
rationale: The operator is an AI agent, so issue-creation cost is near zero and capture friction is not the constraint — the constraints are the self-approval loop, missing machine-checkable diff-to-issue linkage, and the human PM's attention. Four of the five proposed context types already exist as commands (decision, inbox, memory, knowledge).
evidence: Adversarial review verified 38 existing commands including product-decision/memory/knowledge/inbox, no frontmatter in the issue template, no sessions/ directory, silent-pass holes in release_check.py, and ~75 issues in 24 days of agent-driven velocity. Two benchmarks (human-tools and AI-native) converged on capture-free/promotion-human-gated.
alternatives: Keep v1 capture-tier spec with amendments; split 075 into gate-repair and context-cleanup issues.
reversal_conditions: If a real teammate (human) joins and needs a capture surface distinct from the existing commands, or if normalizing the four existing commands proves messier than one unified entry point, revisit product:capture.
confidence: high
---

# Promote And Linkage Over New Capture Tier

Supersedes [[2026-07-06-use-issue-less-context-tiers]] — the typed-tier idea is absorbed: the types already exist as `product:decision`, `product:inbox`, `product:memory`, `product:knowledge`; what was missing is promotion, linkage, and a human gate, not a new tier.

## Decision

075 delivers, in order of importance:

1. Machine-checkable commit/branch ↔ issue linkage convention (branch `codex/<issue-id>-*` or commit trailer), release_check rebuilt on it with hard failure on git errors.
2. `product:promote`: existing record → issue with automatic bidirectional links.
3. Human approval via Git identity for no-issue declarations; declarations listed in the human-review packet.
4. AI-first issue template fields: verification, entry points, scope fence.
5. Normalization (shared frontmatter, ADD/UPDATE/SUPERSEDE/NOOP write discipline) of the four existing capture commands — no new command, no new tier.

Real-time threshold detection is explicitly out — it belongs to `072-lifecycle-hooks-automation`.
