---
description: Generate a worker plan and parallel execution decision for an issue.
argument-hint: "<issue id> [--host claude-code|codex|copilot-cloud-agent]"
user-invocable: false
---

# /product:workers

Create an issue-local worker plan — **or say why one cannot be made.**

## Do

1. Verify `specs/<issue>/tasks.md` exists.
2. Run `scripts/worker_orchestrator.py <issue> --write`.
3. Read the result's `status` **before** looking for the files. Two of the three
   statuses write nothing, and that is a normal outcome, not a failure.
4. Review `specs/<issue>/worker-plan.md` when the status is `ok`.
5. Use parallel workers only when the plan is `parallel-eligible`.
6. Keep shared-state, migration, schema, config, and overlapping expected-file
   work sequential unless explicitly approved.
7. Prefer task metadata when the split is not obvious:

```text
- [ ] Implementation: update planner [files: scripts/worker_orchestrator.py]
- [ ] QA: verify routing [files: tests/test_worker_orchestration.py] [depends: T01]
- [ ] Release: update config [files: .codex-plugin/plugin.json] [shared_state: true]
```

## 세 가지 결과 (issue 112)

| status | 무슨 뜻인가 | 파일 | 다음 |
| --- | --- | --- | --- |
| `ok` | 시킬 수 있는 일이 있고 경계도 분명함 | 씀 | `/moduflow execute <issue>` |
| `needs_plan` | 할 일은 있는데 **어떤 파일을 건드릴지 안 적혀 있음** | **안 씀** | `/moduflow plan <issue>` |
| `not_applicable` | **남은 구현 작업이 없음.** 명세가 끝난 것 | **안 씀** | `/moduflow status` |

**거절은 정상 결과입니다. 오류가 아닙니다.** 종료 코드도 0입니다.

`needs_plan`이면 무엇이 모자란지 작업 번호별로 나옵니다. 두 가지를 구분합니다 —
경계를 **안 쓴 것**과, 썼는데 **파서가 못 읽는 형태로 쓴 것**은 고칠 게 다릅니다.

이 게이트가 없던 시절 명세 001의 유일한 작업은 `Commit and push.` 였고, 모두플로는
거기에 작업 공간을 파주고 `Expected files: none`을 지시문에 적어서 **"바로 실행
가능"**이라고 보고했습니다. 그런 걸 안 만드는 게 거절의 목적입니다.

## 도구 지정

계획에 들어가는 브랜치 이름·모델 지정은 **도구마다 다릅니다.** 기본값은
`claude-code`이고, `.moduflow/config.json`의 `execution.host`로 바꾸거나 실행할 때
`--host`로 덮어씁니다.

```bash
python3 scripts/worker_orchestrator.py <issue> --write --host codex
```

**짐작하지 않습니다.** 목록에 없는 도구는 거절하고 어댑터를 만들라고 합니다 —
짐작해서 틀리면 틀린 값이 조용히 계획 파일에 박히고, 그게 모든 계획에 `codex/`가
들어가 있던 이유입니다.

## Output

status가 `ok`일 때만:

- `specs/<issue>/worker-plan.json` (`moduflow.worker-plan.v2`)
- `specs/<issue>/worker-plan.md`

## Next

- `/moduflow execute <issue>` — 계획을 받아들일 때
- `/moduflow plan <issue>` — `needs_plan`이거나 작업을 더 쪼개야 할 때
- `/moduflow status` — `not_applicable`일 때
