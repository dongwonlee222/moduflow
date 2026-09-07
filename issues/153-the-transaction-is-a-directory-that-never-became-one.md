# Issue 153: 트랜잭션은 디렉터리가 되다 만 파일이다

**Status: backlog** — created 2026-09-07.
**Priority: p1**

## 요약

`project_lifecycle_transaction.py`는 **7,524줄에 최상위 심볼이 208개**입니다.
길어서 문제가 아닙니다 — pandas의 `frame.py`는 20,180줄인데 심볼이 4개고
읽힙니다. **한 파일이 열 가지 일을 해서** 문제입니다: 직렬화·저널·복구·투영
검증·잠금·상태 전이. 형제 파일 `_storage.py`가 4,167줄에 119개이니 **이미 한 번
쪼갠 결과인데도** 그렇습니다.

## Summary

Two modules, 11,691 lines, 327 top-level symbols. The split that already happened
produced a second oversized module, which suggests the axis was wrong. This issue
splits by concern into a package, keeping the public surface unchanged.

## Source

- Type: chore — 2026-09-07, 소유자 지적 *"소스가 너무 많아지면 관리하기
  어려워지는거 맞지"* 이후 실측
- Owner / decision maker: Dongwon Lee
- 조사 근거: 2026-09-07 서브에이전트 보고 (AGENTS.md의 「Module Size」에 요약)

## 안 고치면

한 파일에 개념 208개가 있어서 아무도 통째로 읽지 않습니다. 목표의 일곱 가지 중 **프로세스**가 막힙니다 — 고치려는 사람이 무엇을 건드리는지 모른 채 고칩니다.

## 원인

```
$ python3 - <<'EOF'
import ast, pathlib
for name in ("project_lifecycle_transaction","project_lifecycle_transaction_storage"):
    p=pathlib.Path(f"scripts/{name}.py"); src=p.read_text(); tree=ast.parse(src)
    top=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef))]
    pub=[n.name for n in top if not n.name.startswith("_")]
    cls=[n for n in top if isinstance(n,ast.ClassDef)]
    print(name, len(src.splitlines()),"줄  최상위",len(top)," 공개",len(pub)," 클래스",len(cls))
EOF
project_lifecycle_transaction         7524줄  최상위 208  공개 38  클래스 35
project_lifecycle_transaction_storage 4167줄  최상위 119  공개 36  클래스 20
```

**공개 74개, 내부(`_`) 253개.** 밖에서 쓰는 것은 4분의 1도 안 됩니다.

이름 첫 낱말로 묶으면 **106종**이 나옵니다 — `serialized`(10) · `projected`(10) ·
`recovery`(9) · `private`(9) · `verify`(7) · `validate`(6) · `journal`(5) …

클래스 35개 중 **14개가 예외**이고, 나머지 21개 중 **13개가 단계별 상태
클래스**입니다:

```
_PrivatePreimageState  → _PrivateStagedState → _PrivatePreparedState
→ _PrivateAppliedState → _PrivatePostValidatedState → _PrivateCompletedState
그리고 복구 경로용 한 벌 더:
_RecoveredJournalState · _RecoveredTransactionState · _RecoveredCleanupState
_PrivateRecoveryOutcome · _PrivateCleanupOutcome · _PrivateEvidenceBinding
```

**트랜잭션이 지나가는 단계마다 상태 클래스를 하나씩 만든 구조**입니다. 그 자체는
합리적인데, 한 파일에 다 넣은 것이 문제입니다.

### 이 판단의 근거

2026-09-07 조사: **줄 수 상한은 표준 관행이 아닙니다.** pylint의
`max-module-lines` 기본값 1000이 유일하게 기본으로 켜지는 것이고, Home Assistant는
*"가독성을 위해 강제하지 않는다"*는 주석과 함께 그 규칙을 끄고 4,258줄 모듈을
유지합니다. **진짜 기준은 개념 수**이며, 유일하게 모듈 크기에 의견을 가진 린터
(`wemake-python-styleguide`)도 줄이 아니라 **멤버 수(7)**로 잽니다.

## Scope

### In

- `scripts/lifecycle_transaction/` 패키지로 쪼갠다. 이음매는 이미 있다:
  예외 · 공개 계약(`LifecycleIntent`·`PlannedTarget`·`LifecycleTransactionPlan`) ·
  단계별 상태 · apply 경로 · recovery 경로 · storage.
- **공개 74개를 `__init__.py`로 그대로 내보낸다.** 밖에서 쓰는 코드는 한 줄도
  바뀌지 않아야 한다 — `import` 문 하나도.
- 쪼갠 뒤 각 모듈이 「Module Size」 기준(1,000줄 그리고 심볼 40개)을 넘지 않는지
  확인한다. 넘으면 축이 또 틀린 것이다.
- `_storage.py`의 축이 맞는지 다시 본다. 4,167줄에 119개면 그 쪼개기도 개념이
  아니라 다른 기준으로 나눴을 가능성이 있다.

### Out

- **동작을 바꾸는 일.** 이건 순수 이동이다. 함수 하나의 내용도 고치지 않는다.
  132가 트랜잭션의 *행동*을 갖고 있고, 이 이슈는 *배치*만 갖는다.
- 공개 API를 줄이거나 이름을 바꾸는 일. 74개가 많아 보여도, 줄이는 것은 별개
  결정이고 소비자 확인이 필요하다.
- 다른 다섯 개의 큰 모듈 (`project_memory` 2,958 · `project_issue_schema` 2,555 ·
  `spec_kit_adapter` 1,310 · `project_production` 1,199 ·
  `project_analysis_run` 1,068). AGENTS.md가 정한 대로 **그 파일을 다른 이유로
  건드릴 때** 쪼갠다.
- 줄 수 상한을 CI 게이트로 만드는 일. 경고로 남긴다 — 막으면 `_part2.py`가 생겨서
  지금보다 나빠진다.

## Known Limit

**쪼갠다고 가로지르는 변경에 필요한 맥락이 줄지는 않습니다.** 7,524줄을 470줄
16개로 나눠도 트랜잭션 전체를 이해해야 하는 변경은 여전히 전체를 읽어야 합니다.
얻는 것은 **한 번의 읽기가 완결되고 grep 결과 하나가 해석 가능해지는 것**이고,
그건 줄 수가 아니라 개념 분리에서 옵니다.

내부 심볼 253개가 서로 얼마나 얽혀 있는지는 **아직 안 봤습니다.** 이음매가
깨끗해 보이는 것은 이름 기준이고, 실제 의존은 다를 수 있습니다. 계획 단계에서
그것부터 재야 합니다.

## Acceptance Criteria

- `scripts/lifecycle_transaction/` 패키지가 생기고, 각 모듈이 1,000줄 또는 심볼
  40개 중 하나 아래다.
- **밖에서 쓰는 코드가 한 줄도 안 바뀐다** — `grep -rn "project_lifecycle_transaction"`
  의 결과가 import 경로를 포함해 그대로이거나, 바뀌었다면 그 목록이 리뷰에 있다.
- 동작이 안 바뀐다: 기존 테스트 전부 통과, 새 테스트 0건 추가.
- `validate_moduflow.py`의 모듈 크기 경고에서 이 두 파일이 빠진다.
- `_storage.py`의 축을 다시 본 결과가 리뷰에 적힌다 — 그대로 두든 바꾸든.
- `python3 scripts/release_check.py .` 통과, 최상위 `valid` 확인.

## Verification

- 쪼개기 **전후로 `python3 -m unittest discover -s tests` 결과가 같다** — 통과
  수까지.
- `python3 -c "import scripts.project_lifecycle_transaction as t; print(len(dir(t)))"`
  가 전후로 같다 (`__init__.py` 재수출 확인).
- 실제 전이를 한 번 돌려서 `applied`가 나오는지 — 픽스처가 아니라 이 저장소에서.
- `tests/test_project_lifecycle_transaction.py` 무수정 통과.

## Entry Points

- `scripts/project_lifecycle_transaction.py` — 7,524줄, 심볼 208
- `scripts/project_lifecycle_transaction_storage.py` — 4,167줄, 심볼 119
- `AGENTS.md` 「Module Size」 — 기준과 그 출처
- `scripts/validate_moduflow.py` `oversized_modules` — 경고를 내는 곳
- `tests/test_project_lifecycle_transaction.py` — 안 고치고 통과해야 하는 것

## Scope Fence

**함수 내용을 한 줄도 고치지 않는다.** 순수 이동이다. 옮기면서 "겸사겸사"
고치면, 테스트가 깨졌을 때 이동 때문인지 수정 때문인지 알 수 없다.

**공개 API를 줄이지 않는다.** 74개가 많아 보여도 이 이슈의 일이 아니다.

쪼갠 결과가 다시 기준을 넘으면 **축이 틀린 것이므로 멈추고 다시 본다.**
`_storage.py`가 그 전례다 — 한 번 쪼갰는데 119개짜리가 나왔다.

## Workflow Tasks

- [ ] spec → `specs/<issue>/spec.md`
- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → 내부 의존 측정 → 패키지 분할 → 재수출 → 경고 해소
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- related: `132-the-canonical-status-line-has-no-protection` — **행동**을 갖고
  있고 이 이슈는 **배치**를 갖는다. 132의 In 넷은 전부 동작 수정이라 쪼개기를
  덮지 않는다. 순서상 이 이슈가 먼저면 132가 작은 파일들 위에서 일하게 된다.
- related: `103-atomic-lifecycle-state-transaction` (done — 이 두 파일을 만든
  이슈)

## Next Command

`product:spec 153-the-transaction-is-a-directory-that-never-became-one`
