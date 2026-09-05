# Issue 122: Worker Plan Write Path Skips Repository Identity

**Status: backlog** — created 2026-09-05.
**Priority: p1**

## 요약

쓰기 경로가 둘인데 저장소 신원 검사는 하나뿐입니다. `project_execution.py`는
쓰기 전에 저장소 신원을 확인하고 거부되면 exit 3으로 멈추지만,
`worker_orchestrator.py`는 `capabilities.write`만 보고 그대로 씁니다. 지금 이
저장소가 바로 그 갈리는 상태입니다 — remote가 SSH alias라 신원이
`unverifiable`이고 `execute` 권한이 없는데, 한쪽 명령만 막힙니다.

## Summary

`project_execution.main` gates its write path on repository identity
(`scripts/project_execution.py:349-353`): it calls `inspect_repository_identity`,
evaluates `operation_decision(identity, "execute")`, and returns exit 3 without
writing when the decision is denied. `worker_orchestrator.write_worker_plan`
has no equivalent check — it enforces `capabilities.write`
(`scripts/worker_orchestrator.py:526`) and nothing else. Two sibling write paths
in the same package disagree about whether repository identity is authoritative.

## Source

- Type: gap found while verifying Issue 112's acceptance criteria against code
- Owner / decision maker: Dongwon Lee
- Date: 2026-09-05
- Split from: `112-execution-planner-and-backend-boundary`, where it was first
  written as acceptance criterion 14 and then separated because it is an
  independent defect that should not wait on 112's spec approval, plan and
  execution.

## Opportunity

Measured on this repository on 2026-09-05 (HEAD `a5657dd`):

```
identity status : unverifiable
capabilities    : read=True, execute=False, commit=False, push=False,
                  github_write=False, release=False
reasons         : fetch_remote_invalid — Observed repository URL could not be
                  safely normalized
                  push_remote_invalid — same
```

The remote is `git@github-evmodu:dongwonlee222/moduflow.git`; `github-evmodu` is
a local SSH alias that the identity normaliser cannot resolve to a canonical
host, so the repository is correctly classified as unverifiable.

Both commands were then run against that state:

| Command | Result |
| --- | --- |
| `project_execution.py . --issue-id 112-… --readiness --write` | exit 3, denied, `implementation-readiness.json` not created |
| `worker_orchestrator.py <issue> --write` | no identity check exists; proceeds |

Same repository, same moment, same class of local artifact write. One path
refuses and the other does not.

The gate is not decoration. `OPERATION_CAPABILITIES`
(`scripts/project_repository_identity.py:23`) maps `execute` to the `execute`
capability precisely so that generating execution artifacts in a repository
whose identity cannot be established is refused. A worker plan is exactly such
an artifact: it names worktrees, assigns workers and declares what is
dispatchable.

## Scope

### In

- Enforce repository identity in `worker_orchestrator.write_worker_plan`, using
  the same `inspect_repository_identity` / `operation_decision` pair and the
  same operation name that `project_execution` uses.
- Deny before any file is created, mirroring the existing exit-3 contract:
  return the decision document, write nothing.
- Add a guard test that fails if either write path loses its identity check, so
  the two cannot drift apart again.

### Out

- Changing what `inspect_repository_identity` considers verifiable. Making SSH
  aliases resolvable is a separate question and must not be smuggled in as a
  way to make this repository pass.
- The Issue 112 planner contract — filtering, boundary refusal, backend
  routing. This issue only adds the missing gate to the existing function.
- Auditing every other script for the same gap. If a sweep is wanted, file it
  from the guard test's findings rather than widening this issue.

## Acceptance Criteria

- `write_worker_plan` denies when `operation_decision` denies, and creates
  neither `worker-plan.json` nor `worker-plan.md`.
- The denial result is the same decision schema `project_execution` returns, so
  a caller can handle both identically.
- `capabilities.write` denial still precedes identity inspection, so an
  archived or read-only project short-circuits as it does today.
- A verifiable repository is unaffected: existing worker-plan generation keeps
  working with no signature change for callers that already pass.
- A guard test asserts that both write paths call the identity gate; removing
  it from either one fails the suite.
- `tests/test_worker_orchestration.py`, `tests/test_project_execution.py` and
  `python3 scripts/release_check.py .` stay green.

## Verification

- Fixture with an unverifiable remote: assert denial and assert no
  `worker-plan.*` exists on disk afterwards.
- Fixture with a verifiable remote: assert the plan is still produced.
- Write-denied (archived/read-only) context: assert the capability denial still
  wins and identity is not consulted.
- Guard test over both write paths.

## Entry Points

- `scripts/worker_orchestrator.py:520` — `write_worker_plan`
- `scripts/project_execution.py:349` — the reference implementation
- `scripts/project_repository_identity.py:679` — `operation_decision`
- `tests/test_worker_orchestration.py`, `tests/test_project_execution.py`

## Scope Fence

Add the missing gate; do not redesign the gate. If enforcing it turns out to
block ordinary local work, that is evidence for a separate discussion about
alias resolution, not a reason to weaken the check here.

## Workflow Tasks

- [ ] spec → `specs/122-worker-plan-write-path-skips-repository-identity/spec.md`
- [ ] plan → `specs/122-…/plan.md` + `tasks.md`
- [ ] execute → identity gate, denial contract, guard test
- [ ] review → `specs/122-…/review.md`

## Related Issues

- split_from: `112-execution-planner-and-backend-boundary`
- related: `110-project-operation-capability-enforcement`,
  `088-canonical-repository-remote-identity-gate`,
  `111-runtime-provenance-and-validation-mode-separation`

## Links

- Identity evidence: measured inline above, 2026-09-05
- Sibling implementation: `scripts/project_execution.py:349-353`

## Next Command

`product:spec 122-worker-plan-write-path-skips-repository-identity`
