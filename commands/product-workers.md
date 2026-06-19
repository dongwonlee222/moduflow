---
description: Generate a worker plan and parallel execution decision for an issue.
argument-hint: "<issue id>"
---

# /product:workers

Create an issue-local worker plan.

## Do

1. Verify `specs/<issue>/tasks.md` exists.
2. Run `scripts/worker_orchestrator.py <issue> --write`.
3. Review `specs/<issue>/worker-plan.md`.
4. Use parallel workers only when the plan is `parallel-eligible`.
5. Keep shared-state, migration, schema, config, and overlapping expected-file work sequential unless explicitly approved.
6. Prefer task metadata when the split is not obvious:

```text
- [ ] Implementation: update planner [files: scripts/worker_orchestrator.py]
- [ ] QA: verify routing [files: tests/test_worker_orchestration.py] [depends: T01]
- [ ] Release: update config [files: .codex-plugin/plugin.json] [shared_state: true]
```

## Output

- `specs/<issue>/worker-plan.json`
- `specs/<issue>/worker-plan.md`

## Next

- `/product:execute <issue>` when the worker plan is accepted.
- `/product:plan <issue>` if the tasks need to be split more clearly.
