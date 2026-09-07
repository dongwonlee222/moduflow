# Issue 149: Registry Paths With A Tilde Resolve To Nowhere

**Status: backlog** — created 2026-09-07.
**Priority: p0**

## 요약

**등록된 프로젝트 3개가 전부 없는 경로를 가리킵니다.** `~/projects/ai-morning-brief`
라고 적힌 것이 `~`를 그대로 붙여서 `.../.portfolio/~/projects/ai-morning-brief`가
됩니다. 그런 폴더는 없습니다. **레지스트리는 `valid: true`로 통과하고**, 실패는
프로젝트를 실제로 쓰려는 순간에야 나옵니다. **오늘 사장님이 `/moduflow`를
치셨을 때 아무것도 안 된 이유입니다.**

## Summary

`~/projects/.portfolio/projects.json` registers three projects and all three
roots are unreachable. The loader does not expand `~`, joins the literal string
to the registry's parent directory, and reports the registry as valid anyway.

## Source

- Type: bug — 2026-09-07, 104를 끝내고 실제 레지스트리에 처음 돌려보다 발견
- Owner / decision maker: Dongwon Lee
- 사장님이 `/moduflow 현재 상태 확인해줘`를 치셨고, 그게 왜 안 되는지 쫓다 나왔습니다

## 안 고치면

등록된 프로젝트 3개를 아무 명령도 열 수 없습니다. 목표의 일곱 가지가 **전부** 막힙니다 — 어느 것도 프로젝트를 열지 못하면 시작이 안 됩니다.

## 원인

```
$ python3 -c "import sys;sys.path.insert(0,'scripts');import project_registry as pr
from pathlib import Path
reg = pr.load_project_registry(Path('/Users/idong-won/projects/.portfolio/projects.json'))
print('valid:', reg['valid'])
for p in reg['projects']: print(' ', p['id'], '->', p['root'])"

valid: True
  ai-brief     -> /Users/idong-won/projects/.portfolio/~/projects/ai-morning-brief
  portfolio-v2 -> /Users/idong-won/projects/.portfolio/~/projects/hire/portfolio-dongwon-v2
  ops          -> /Users/idong-won/projects/.portfolio/~/.claude/ops

$ python3 -c "from pathlib import Path
print('그 경로 :', Path('/Users/idong-won/projects/.portfolio/~/.claude/ops').exists())
print('진짜 경로:', Path('/Users/idong-won/.claude/ops').exists())"
그 경로 : False
진짜 경로: True
```

파일에는 `"path": "~/.claude/ops"`라고 적혀 있습니다. `_canonical_root`가
`registry_path.parent / path`로 이어 붙이는데 **`~`를 펼치지 않습니다.**

**두 가지가 겹쳐 있고, 둘 다 결함입니다.**

1. **`~`가 안 펼쳐진다.** 홈 경로를 `~`로 적는 건 이 저장소 문서 전반에서 쓰는
   표기입니다. 레지스트리만 안 받습니다.
2. **`valid: true`로 통과한다.** `load_project_registry`는 없는 루트를 진단하지
   않습니다. 실패는 `_resolved`가 `root.is_dir()`을 볼 때까지 미뤄지고, 그때는
   이미 사람이 명령을 친 뒤입니다. **레지스트리를 고칠 수 있는 시점에는 아무도
   문제를 안 알려줍니다.**

## Scope

### In

- 레지스트리의 `path`/`root`에서 `~`와 `~user`를 펼친다.
- 등록된 루트가 없으면 **레지스트리를 읽는 시점에 진단**을 낸다 — 어느 프로젝트,
  어느 경로, 무엇을 고쳐야 하는지 한국어로.
- `valid`가 그 진단을 반영할지 정한다. 후보 둘: 없는 루트를 `valid: false`로
  볼 것인가, 아니면 `valid: true` + 경고로 둘 것인가. **셋 중 하나만 깨졌을 때
  나머지 둘을 쓸 수 있어야 하므로** 후자가 유력하지만, 정하고 적어야 한다.
- 현재 `~/projects/.portfolio/projects.json`을 고친다. 지금 3개 다 죽어 있다.

### Out

- 레지스트리 스키마를 바꾸는 일. `path`(v1)와 `root`(v2)는 그대로 둔다.
- 상대경로 정책 전반. `~`만 이 이슈의 대상이다.
- `project_registry.resolve_project`의 반환 모양. 104가 방금 그 위에 붙었다.
- 프로젝트 등록 명령의 UX. 등록할 때 검사하는 건 별건이다.

## Known Limit

`~`를 펼쳐도 **다른 컴퓨터에서 같은 경로가 있으리라는 보장은 없습니다.** 이건
완료 조건 ②(다른 사람·다른 컴퓨터가 받아도 똑같이 동작)의 일부일 뿐이고,
`105`가 그 전체를 갖고 있습니다. 여기서 없애는 것은 **같은 컴퓨터에서조차 안
되는** 경우입니다.

## Acceptance Criteria

- `~/.claude/ops`로 등록된 프로젝트가 `/Users/<user>/.claude/ops`로 해석된다.
- 없는 루트가 **레지스트리를 읽는 시점에** 진단으로 나오고, 메시지가 프로젝트
  id와 실제로 찾은 경로를 한국어로 말한다.
- 셋 중 하나만 깨졌을 때 나머지 둘은 계속 해석된다 — 테스트로 단언.
- 현재 포트폴리오 레지스트리가 고쳐지고, 세 프로젝트 모두 해석된다.
- `python3 scripts/release_check.py .` 통과, 최상위 `valid` 확인.

## Verification

- 픽스처: `~`가 든 경로 → 홈으로 펼쳐져 해석됨.
- 픽스처: 없는 루트 하나 + 멀쩡한 루트 둘 → 진단 1건, 해석 2건.
- 픽스처: `~user` 형태 → 펼쳐지거나, 안 펼치기로 정했다면 그렇게 진단됨.
- 실제 `~/projects/.portfolio/projects.json`에 돌려서 3개 다 해석되는지 확인.
- `tests/test_project_registry.py`.

## Entry Points

- `scripts/project_registry.py` — `_canonical_root` (`~`가 안 펼쳐지는 자리),
  `_normalize_v1_project`, `_normalize_v2_project`, `load_project_registry`
  (진단이 없는 자리), `_resolved` (`root.is_dir()`로 뒤늦게 잡는 자리)
- `~/projects/.portfolio/projects.json` — 지금 깨져 있는 실물
- `scripts/request_routing.py` — `stage_resolve`, 이 결함을 드러낸 곳

## Scope Fence

`_resolved`의 늦은 `root.is_dir()` 검사를 **지우지 않는다.** 그건 마지막
방어선이고, 앞에서 진단을 낸다고 뒤를 열어 둘 이유가 없다.

레지스트리를 자동으로 고쳐 쓰지 않는다. 진단은 사람에게 무엇을 고칠지 말하고,
파일은 사람이 고친다 — 목표 「안 하는 것」의 "원격을 자동으로 고쳐 쓰지 않는다"와
같은 결이다.

## Workflow Tasks

- [ ] spec → `specs/<issue>/spec.md`
- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → `~` 펼치기, 읽는 시점 진단, `valid` 정책, 실물 레지스트리 수리
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- related: `102-project-registry-and-resolver` (done — 이 해석기를 만들었고,
  `~`는 다루지 않았다), `105-schema-migration-and-doctor-triage` (p0 — 다른
  컴퓨터에서 받았을 때 전반을 갖고 있다. 이건 같은 컴퓨터에서도 안 되는 부분),
  `141-adoption-reports-success-on-an-incomplete-setup` (같은 모양: 성공이라
  보고하고 나중에 깨진다),
  `104-project-aware-natural-language-request-orchestrator` (드러낸 곳)

## Next Command

`product:spec 149-registry-paths-with-a-tilde-resolve-to-nowhere`
