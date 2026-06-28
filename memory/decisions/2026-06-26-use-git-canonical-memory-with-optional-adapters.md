---
id: 2026-06-26-use-git-canonical-memory-with-optional-adapters
kind: decision
title: Use Git canonical memory with optional adapters
issue_id: 034-memory-capture-and-sync-workflow
spec: specs/034-memory-capture-and-sync-workflow/spec.md
owner: Dongwon Lee
date: 2026-06-26
tags: [memory, team, pm, git, rag, langgraph, adapter]
supersedes: [2026-06-24-use-portable-project-memory]
summary: ModuFlow team memory should use Git-tracked Markdown as the canonical source while RAG, LangGraph, MCP, Google Drive, and external memory tools remain optional adapters for retrieval, orchestration, sync, and indexing.
rationale: Downloaded users, PMs, developers, and multiple computers need a portable source of truth that works without hosted infrastructure while still allowing richer retrieval and team workflows.
evidence: Issue 034 and its spec define memory candidates, approval, team review, external mirrors, and adapter boundaries based on the current ModuFlow memory prototype and reviewed memory tool patterns.
alternatives: Make Google Drive, vector DB, or external memory service the source of truth; capture every chat automatically.
reversal_conditions: A future team deployment requires a managed hosted canonical store with stronger access controls than Git can provide.
confidence: medium
---

# Use Git canonical memory with optional adapters

## Summary

ModuFlow team memory should use Git-tracked Markdown as the canonical source while RAG, LangGraph, MCP, Google Drive, and external memory tools remain optional adapters for retrieval, orchestration, sync, and indexing.

## Rationale

Downloaded users, PMs, developers, and multiple computers need a portable source of truth that works without hosted infrastructure while still allowing richer retrieval and team workflows.

## Evidence

Issue 034 and its spec define memory candidates, approval, team review, external mirrors, and adapter boundaries based on the current ModuFlow memory prototype and reviewed memory tool patterns.

## Alternatives

Make Google Drive, vector DB, or external memory service the source of truth; capture every chat automatically.

## Links

- Issue: 034-memory-capture-and-sync-workflow
- Spec: specs/034-memory-capture-and-sync-workflow/spec.md

## Reversal Conditions

A future team deployment requires a managed hosted canonical store with stronger access controls than Git can provide.
