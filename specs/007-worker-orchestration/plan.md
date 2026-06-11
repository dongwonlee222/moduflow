# Plan: Worker Orchestration

Issue: `007-worker-orchestration`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

## Approach

Add a provider-neutral worker planner that reads issue tasks, assigns ModuFlow workers, evaluates basic parallel safety, and writes issue-local plan artifacts.

## Work Streams

- PM: define issue, spec, and command behavior.
- Implementation: add worker orchestration script and tests.
- QA: validate assignment, sequential risk, and write behavior.
- Release: update command docs, README, package validator, and state.

## Verification

- `python3 -m unittest tests.test_worker_orchestration -v`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/worker_orchestrator.py 007-worker-orchestration --write`
- `python3 scripts/release_check.py .`

## Rollback

Remove `product:workers`, worker orchestration script/tests, and generated worker plan artifacts.

## Next Command

`product:execute 007-worker-orchestration`
