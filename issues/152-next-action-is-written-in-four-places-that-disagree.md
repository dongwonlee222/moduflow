# Issue 152: "다음에 뭐 하지"가 네 군데에 따로 적혀 있다

**Status: done** — 2026-09-07에 만들고 같은 날 끝냈습니다. 읽는 순서 · 배너 · 낡음 보고.
**Priority: p1**

## 요약

**"다음에 뭐 하지"를 네 군데가 각자 답합니다.** 지금 이 순간
`state.json`은 `product:status`라 하고, 로드맵은 `151`이라 하고,
`loop-state.json`도 `product:status`라 하고, 이슈 파일 **137개**가 각자 자기
`Next Command`를 갖고 있습니다. **어느 것이 정본인지 아무 데도 안 적혀 있습니다.**

## Summary

Four surfaces answer "what next" independently and none is declared canonical.
Today they disagree: the state file and loop state both say `product:status`
while the roadmap's ordered plan says issue 151.

## Source

- Type: bug — 2026-09-07, 소유자 지적: *"이거 다음에 뭐 하고 뭐하고 등등
  왜 이런 결정을 했는지 등등"* — 이슈 관리가 흩어져 있다는 지적
- Owner / decision maker: Dongwon Lee

## 안 고치면

다음 세션이 어디를 봐야 할지 모릅니다. 목표의 일곱 가지 중 **로드맵**이 막히고, 완료 조건 ①(새 세션이 파일만 읽고 이어서 일한다)이 깨집니다.

## 원인

```
$ python3 -c "import json;print(json.load(open('.moduflow/state.json'))['next_command'])"
product:status

$ grep -m1 "^- \[ \] \*\*1\." workspace/roadmap.md
- [ ] **1. `151` — spec-kit을 켤 수 있게**

$ python3 -c "import json;print(json.load(open('workspace/loop-state.json')).get('next_command'))"
product:status

$ grep -c "^## Next Command" issues/*.md | grep -c ":1"
137
```

**넷이 각자 답하고, 오늘 실제로 서로 다릅니다.**

### 그리고 루프 상태가 낡은 채로 방치돼 있습니다

읽는 순서만 정하고 낡은 값을 그대로 두면 **여전히 틀린 것을 보여줍니다.**
`workspace/loop-state.json` 실측 (2026-09-07):

```
loop_id     : trustworthy-execution-and-project-knowledge-20260716   ← 7월 16일 시작
objective   : "...dashboard views."                                  ← 7월 목표
issue_ids   : 27개 — 그중 082·092·114 는 2026-09-07 에 닫힘
attempts    : product:review 111-...  last_changed_at 2026-09-02
status      : done
```

**목표를 오늘 다시 썼는데 루프의 `objective` 는 7월 것 그대로**입니다. 그리고
세션 시작 배너는 `hooks/session_start.py:104-106` 에서 **루프를 먼저** 봅니다.
로드맵이 오늘 것이고 루프가 7월 것인데, 배너는 7월 것을 먼저 읽습니다.

`state.json`과 `loop-state.json`은 트랜잭션이 씁니다 — 활성 이슈가 없으니
`product:status`가 맞습니다. 로드맵은 사람이 정한 순서입니다 — `151`이 맞습니다.
**둘 다 자기 층에서는 맞는데, 읽는 사람에게는 모순입니다.**

### 왜 이렇게 됐나

각각이 다른 이유로 생겼고, 아무도 "어느 것이 정본인가"를 정하지 않았습니다.

| 어디 | 무엇이 씀 | 무엇을 답함 |
|---|---|---|
| `.moduflow/state.json` | 트랜잭션 | **기계가 아는 다음 단계** (활성 이슈의 라이프사이클) |
| `workspace/loop-state.json` | 트랜잭션 | 같음 — state.json의 사본에 가깝다 |
| `workspace/roadmap.md` | 사람 | **사람이 정한 순서** |
| `issues/*.md` × 137 | 사람/템플릿 | 그 이슈 안에서의 다음 |

**층이 다른 것이지 중복이 아닙니다.** 문제는 **읽는 순서가 안 정해진 것**입니다.

## Scope

### In

- **읽는 순서를 정하고 한 곳에 적는다.** 후보: 로드맵이 사람의 의도이므로
  먼저 보고, 로드맵이 비었을 때 `state.json`으로 내려간다.
- 정한 순서를 **`product:status`와 세션 시작 배너가 따르게** 한다. 지금 배너는
  `loop-state`를 먼저 보고 `state.json`으로 떨어진다
  (`hooks/session_start.py:104-106`) — 로드맵은 안 본다.
- 넷이 **서로 모순일 때 무엇을 보여줄지** 정한다. 감추지 말고 "로드맵은 A,
  상태는 B"라고 둘 다 말하는 편이 낫다.
- 로드맵의 순서 항목과 이슈 id를 잇는다. 지금은 로드맵에 이슈 번호가 글로만 있다.
- **낡은 루프 상태가 낡은 채로 남는 이유를 고친다.** 손으로 한 번 갱신하는 것은
  답이 아니다 — 한 달 뒤 같은 상태가 된다. 최소한 둘 중 하나가 필요하다:
  목표가 바뀌면 루프의 `objective` 가 어긋났다고 말하거나, 닫힌 이슈가
  `issue_ids` 에 남아 있으면 그것을 보고하는 것.
- **낡음을 감추지 않는다.** 배너나 `product:status` 가 루프를 보여줄 때, 그 값이
  언제 것인지(`updated_at`)와 어긋난 항목이 있는지를 같이 말한다.

### Out

- **네 곳 중 하나를 없애는 일.** 층이 달라서 각자 이유가 있다. `state.json`은
  기계가 쓰고 로드맵은 사람이 쓴다. 합치면 132가 말하는 것과 반대 방향이 된다.
- 이슈 137개의 `Next Command` 줄을 지우는 일. 그건 이슈 안의 다음이지 프로젝트의
  다음이 아니다.
- 로드맵 형식을 바꾸는 일. 지금 형식으로 충분하다.
- `dashboard.md`의 Next Command 절 — 지금 비어 있고, 이 이슈가 정하는 순서에
  따라 채워지거나 빠진다.
- **루프 상태를 자동으로 다시 쓰는 일.** 어긋났다고 **말하는 것**까지가 이
  이슈이고, 사람이 정한 값을 기계가 고쳐 쓰는 것은 아래 Scope Fence가 금한다.
- `scripts/project_loop.py` (793줄, 아무도 안 부름). 로드맵 3단계가 그 14개를
  읽는 일을 갖고 있다. 여기서 미리 판단하지 않는다 — 관련이 있어 보이지만
  **확인하지 않았다.**

## Known Limit

읽는 순서를 정해도 **사람이 로드맵을 갱신 안 하면 낡습니다.** 오늘 로드맵이
636줄 낡은 채로 있었던 것이 그 예입니다. 이 이슈가 없애는 것은 "어디를 볼지
모르는 상태"이지 "본 곳이 낡은 상태"가 아닙니다.

## Acceptance Criteria

- 읽는 순서가 한 곳에 문장으로 적히고, `product:status`와 세션 시작 배너가
  그것을 가리킨다.
- 로드맵과 `state.json`이 다를 때 **둘 다 보인다** — 하나가 다른 하나를 조용히
  덮지 않는다.
- 루프의 `objective` 가 `workspace/goal.md` 와 어긋나면 보고된다.
- `issue_ids` 에 닫힌 이슈가 남아 있으면 보고된다 — 오늘 기준 최소 3건
  (`082`·`092`·`114`).
- 루프를 보여줄 때 `updated_at` 이 같이 나온다.
- 세션 시작 배너가 로드맵의 다음 항목을 말한다.
- 로드맵의 각 순서 항목이 이슈 id를 갖는다.
- 이슈 137개의 `Next Command`는 그대로 — 라이브 트리로 단언.
- `python3 scripts/release_check.py .` 통과, 최상위 `valid` 확인.

## Verification

- 픽스처: 로드맵과 `state.json`이 다른 프로젝트 → 둘 다 보고됨.
- 픽스처: 로드맵이 없는 프로젝트 → `state.json`으로 내려감, 예외 없음.
- 라이브 트리에서 세션 시작 배너를 만들어 `151`이 나오는지 확인.
- `tests/test_hooks_session_start.py`, `tests/test_project_lifecycle.py`.

## Entry Points

- `hooks/session_start.py:104-106` — `loop` → `state` 순으로만 보는 곳
- `commands/product-status.md` — 무엇을 읽는지 적힌 곳
- `workspace/roadmap.md` — 사람이 정한 순서
- `.moduflow/state.json` · `workspace/loop-state.json` — 트랜잭션이 쓰는 곳
- `scripts/project_lifecycle.py` — `next_command`를 계산하는 곳

## Scope Fence

**네 곳을 하나로 합치지 않는다.** 기계가 쓰는 것과 사람이 쓰는 것을 한 파일에
넣으면, 트랜잭션이 사람의 순서를 덮어쓴다. 132가 지적하는 "보호가 거꾸로"와 같은
방향의 실수가 된다.

로드맵을 기계가 자동으로 갱신하지 않는다. 순서는 사람이 정하는 것이다.

## Workflow Tasks

- [x] execute


## Related Issues

- related: `132-the-canonical-status-line-has-no-protection` (정본과 사본의
  관계를 다루는 같은 층),
  `143-four-different-things-are-called-the-dashboard` (같은 병이 이름 쪽에서
  나타난 것 — 넷이 같은 이름을 쓴다),
  `125-bootstrap-dashboard-missing-active-issue-section` (대시보드가 활성 이슈를
  못 보여준 건)

## Next Command

`product:spec 152-next-action-is-written-in-four-places-that-disagree`
