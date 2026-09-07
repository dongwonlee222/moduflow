# Issue 150: Issue Numbers Collide And Nothing Refuses

**Status: backlog** — created 2026-09-07.
**Priority: p1**

## 요약

**이슈 번호가 둘씩 겹쳐 있는데 검사기가 통과시킵니다.** `030`이 둘, `127`이
둘입니다. `127`은 오늘 merge에서 생겼고, `030`은 그 전부터 있었습니다.
지금은 넷 다 끝난 이슈라 막히는 게 없습니다. 그런데 **열린 이슈끼리 겹치면
104의 겹침 후보가 잘못된 이슈를 가리킵니다** — 후보는 번호로 식별합니다.

## Summary

Two issue numbers are used twice each, and `validate_project_artifacts.py`
returns `valid: true` on the tree that contains them. Nothing at creation time
refuses a number that is already taken.

## Source

- Type: bug — 2026-09-07, 원격 커밋을 merge 하다 발견
- Owner / decision maker: Dongwon Lee

## 안 고치면

번호가 겹친 이슈를 도구가 구분하지 못합니다. 목표의 일곱 가지 중 **이슈**가 막힙니다.

## 원인

```
$ ls issues/*.md | sed 's/.*issues\/\([0-9]*\)-.*/\1/' | sort | uniq -d
030
127

$ for f in issues/030-*.md issues/127-*.md; do
    printf "%s — " "$(basename $f)"; grep -m1 -o "Status: [a-z-]*" "$f"; done
030-project-memory-layer.md              — Status: superseded-by-
030-worker-cognitive-demand-model-routing.md — Status: done
127-completed-issues-keep-their-execution-binding.md — Status: done
127-recurring-data-update-playbook-routing.md        — Status: done

$ python3 scripts/validate_project_artifacts.py . | python3 -c "import json,sys;print(json.load(sys.stdin)['valid'])"
True
```

`127`은 오늘 만들어졌습니다. 이 저장소에서 `127-completed-issues-keep-their-execution-binding`
을 2026-09-06에 만들었고, 다른 세션이 2026-09-07에 원격에 
`127-recurring-data-update-playbook-routing`을 올렸습니다. 양쪽 다 번호를
고를 때 **상대를 볼 수 없었습니다** — 원격을 fetch 하지 않으면 다음 번호는
로컬 최댓값에서 나옵니다.

`030`은 merge 이전부터 있었습니다. **merge가 이 문제를 만든 게 아니라
드러냈습니다.**

### 검사기가 왜 못 잡나

`scripts/project_registry.py`에는 프로젝트 id 중복을 잡는 규칙이 있습니다
(`PROJECT_ID_DUPLICATE`). **이슈 번호에는 같은 것이 없습니다.**
`project_issue_schema.list_normalized_issues`는 `issue_id`(번호+슬러그 전체)로
정렬할 뿐, **번호만 겹치는 것은 서로 다른 id**로 봅니다.

### 지금 무엇이 걸리나

넷 다 `done`/`superseded`이므로 오늘 막히는 것은 없습니다. **열린 이슈끼리
겹치면 달라집니다** — 104의 `overlap_candidates`가 이슈를 번호로 식별하고,
`chosen_issue`도 번호로 받습니다. 겹친 번호를 넘기면 어느 쪽에 붙을지가
정렬 순서에 달립니다.

## Scope

### In

- 번호가 겹치면 검사기가 실패한다. 메시지가 두 파일 이름을 다 말한다.
- 이슈를 만들 때 다음 번호를 정하는 곳에서 이미 쓰인 번호를 거부한다
  (`project_promote.next_issue_number`, `issue_generator.py`, 그리고
  `commands/product-issue.md`의 지시문).
- **원격을 보지 않고 번호를 고르는 것**을 어떻게 다룰지 정한다. 이것이 오늘
  `127`이 겹친 실제 이유이고, 로컬 검사만으로는 다시 일어난다.
- 지금 겹친 넷을 어떻게 할지 정한다 — 아래 Out 참고.

### Out

- **끝난 이슈 넷의 번호를 바꾸는 일.** `done` 이슈는 다른 이슈의
  `Related Issues`, 커밋 메시지, `specs/<issue-id>/` 폴더 이름에서 참조됩니다.
  번호를 바꾸면 그 참조가 전부 끊깁니다. 이 이슈는 **새 충돌을 막는 것**이고,
  기존 넷은 예외로 통과시킬지 별도로 정합니다.
- 이슈 id 체계를 번호에서 다른 것으로 바꾸는 일. 그건 훨씬 큰 결정입니다.
- `specs/` 폴더 이름 정리.

## Known Limit

로컬 검사는 **이미 겹친 것**을 잡습니다. 두 사람이 동시에 같은 번호를 고르는
것은 로컬에서 못 막습니다 — 그건 원격을 보거나, 번호를 나중에 배정하거나,
번호를 안 쓰는 방법뿐입니다. 이 이슈는 앞의 둘을 다룹니다.

## Acceptance Criteria

- 번호가 겹친 트리에서 검사가 실패하고, 메시지가 두 파일을 다 이름 짓는다.
- 기존 넷(`030` 둘, `127` 둘)은 통과한다 — 라이브 트리로 단언.
- 새 이슈를 만들 때 이미 쓰인 번호가 거부된다.
- 원격 미확인 상태에서 번호를 고르는 경우의 처리가 한 곳에 적히고, 명령
  문서가 그것을 가리킨다.
- `python3 scripts/release_check.py .` 통과, 최상위 `valid` 확인.

## Verification

- 픽스처: 같은 번호 두 파일 → 실패, 두 이름이 메시지에 나옴.
- 픽스처: 기존 넷과 같은 모양(둘 다 `done`) → 통과.
- 라이브 트리 전체 → 새로 실패하는 파일 0건.
- `tests/test_project_issue_schema.py`.

## Entry Points

- `scripts/project_issue_schema.py` — `list_normalized_issues`, 번호 검사가 없는 곳
- `scripts/project_registry.py` — `PROJECT_ID_DUPLICATE`, 같은 일을 하는 기존 규칙
- `scripts/project_promote.py:67` — `next_issue_number`
- `scripts/issue_generator.py` — 두 번째 번호 배정 경로 (아무도 안 부름)
- `commands/product-issue.md` — 사람/모델이 번호를 고르는 지시문

## Scope Fence

끝난 이슈의 번호를 바꾸지 않는다. `specs/<issue-id>/` 폴더와 커밋 메시지와
다른 이슈의 `Related Issues`가 그 번호를 가리킨다.

번호가 겹쳤다고 릴리스를 막지 않는다 — 오늘 넷이 겹친 채로 `valid: true`이고,
그 넷은 아무것도 안 막는다. 새 충돌만 막는다.

## Workflow Tasks

- [ ] spec → `specs/<issue>/spec.md`
- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → 중복 검사, 번호 배정, 원격 미확인 처리, 기존 넷 예외
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- related: `120-silent-status-fallback-in-issue-parser` (같은 층에서 조용히
  잘못된 값을 받아들이는 문제),
  `104-project-aware-natural-language-request-orchestrator` (done — 겹침 후보를
  번호로 식별하므로, 열린 이슈가 겹치면 여기가 먼저 틀린다),
  `142-the-per-issue-artifact-set-is-named-but-never-required` (같은 모양:
  규칙이 있는데 검사가 없다)

## Next Command

`product:spec 150-issue-numbers-collide-and-nothing-refuses`
