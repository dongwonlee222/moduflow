---
id: 2026-07-06-use-issue-less-context-tiers
kind: decision
title: Use Issue-Less Context Tiers
issue_id: 075-issue-less-context-capture
spec: specs/075-issue-less-context-capture/spec.md
source_event: user-design-discussion
source_artifacts: [issues/074-sync-fetch-sandbox-handling.md]
retrieval_trigger: superseded — read only for the history of why the 5-type tier was first chosen before the 2026-07-06 rescope
review_after: 2026-08-06
supersedes: []
superseded_by: [2026-07-06-promote-and-linkage-over-new-capture-tier]
storage_policy: git-canonical
mirror_targets: []
owner: Dongwon Lee
date: 2026-07-06
tags: [context, workflow, issue-tracking, moduflow]
summary: ModuFlow should allow issue-less work, but every durable context must be typed as session, inbox, note, decision, or issue and promoted when it changes product behavior or spans sessions.
rationale: Issue-only tracking is too heavy for normal exploration, questions, repo checks, and small operational work. Completely untracked issue-less work loses context. A typed context tier keeps low-friction work possible while preserving promotion gates for durable changes.
evidence: The 074 sync-fetch sandbox fix began as issue-less troubleshooting but crossed the threshold into code, tests, and command-documentation changes; it had to be recovered into a formal issue afterward.
alternatives: Keep issue-only tracking; allow untracked ad hoc work; require issues for every conversation.
reversal_conditions: If typed issue-less contexts create more overhead than issues or fail to improve recovery/promotion behavior, collapse back to a simpler inbox-first model.
confidence: medium
---

# Use Issue-Less Context Tiers

## Summary

ModuFlow should allow issue-less work, but every durable context must be typed as `session`, `inbox`, `note`, `decision`, or `issue`.

## Rationale

Issue-only tracking is too heavy for normal exploration, questions, repo checks, and small operational work. Completely untracked issue-less work loses context. A typed context tier keeps low-friction work possible while preserving promotion gates for durable changes.

## Evidence

The 074 sync-fetch sandbox fix began as issue-less troubleshooting but crossed the threshold into code, tests, and command-documentation changes. It had to be recovered into a formal issue afterward.

## Alternatives

- Keep issue-only tracking: strong traceability, too much friction.
- Allow untracked ad hoc work: low friction, loses durable context.
- Require issues for every conversation: simple rule, poor fit for real exploratory work.

## Links

- Issue: `075-issue-less-context-capture`
- Spec: `specs/075-issue-less-context-capture/spec.md`
- Recovery example: `issues/074-sync-fetch-sandbox-handling.md`

## Reversal Conditions

If typed issue-less contexts create more overhead than issues or fail to improve recovery/promotion behavior, collapse back to a simpler inbox-first model.
