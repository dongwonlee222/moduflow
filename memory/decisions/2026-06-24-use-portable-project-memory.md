---
id: 2026-06-24-use-portable-project-memory
kind: decision
title: Use portable project memory
issue_id: 030-project-memory-layer
spec: 
owner: Dongwon Lee
date: 2026-06-24
tags: [memory, portability, moduflow]
summary: Use repo-local memory as the source of truth for project deliverables and decisions.
rationale: Projects must remain independent when copied, cloned, or moved.
evidence: Basic Memory and projectmem both favor local-first project memory patterns; external indexes should be rebuildable.
alternatives: External-only memory database
reversal_conditions: Search scale requires an optional external index.
confidence: medium
---

# Use portable project memory

## Summary

Use repo-local memory as the source of truth for project deliverables and decisions.

## Rationale

Projects must remain independent when copied, cloned, or moved.

## Evidence

Basic Memory and projectmem both favor local-first project memory patterns; external indexes should be rebuildable.

## Alternatives

External-only memory database

## Links

- Issue: 030-project-memory-layer
- Spec: 

## Reversal Conditions

Search scale requires an optional external index.
