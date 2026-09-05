# 이슈 120 명세: 이슈 파서의 조용한 상태 폴백

**상태:** 검토 대기 초안 — 2026-09-05 작성
**책임자:** 이동원
**갱신:** 2026-09-05

이슈: `120-silent-status-fallback-in-issue-parser`
다음: `product:plan 120-silent-status-fallback-in-issue-parser`

> 정본은 같은 폴더의 `spec.md`입니다. 이 문서는 한국어 읽기용 사이드카입니다.

## 1. 문제

`markdown_status`(`scripts/project_issue_schema.py:608`)는 인식하지 못한 상태를
전부 `backlog`으로 바꾸고 아무 말도 하지 않습니다.

```python
def markdown_status(text):
    status = markdown_status_projection(text)
    if status is None:
        return "backlog"
    if status.startswith("superseded"):
        return "superseded"
    return status if status in LIFECYCLE_STATES else "backlog"
```

`LIFECYCLE_STATES`는 `{active, backlog, done}` 셋뿐입니다. 서로 다른 사실 셋이
마지막 두 줄에서 하나로 뭉개집니다.

| 입력 | 현재 결과 | 실제 사실 |
| --- | --- | --- |
| `**Status:**` 줄 없음 | `backlog` | 메타데이터가 없다 |
| `**Status: 진행중**` | `backlog` | 토큰을 못 읽었다 — 정규식이 ASCII 전용 |
| `**Status: review**` | `backlog` | 읽었는데 유효하지 않아 버렸다 |
| `**Status: backlog**` | `backlog` | 진짜 백로그다 |

폴백에 **방향이 있다**는 게 위험한 지점입니다. 항상 "시작 안 함"을 뜻하는
`backlog`으로 떨어지므로, 오류가 진행을 과소보고하는 쪽으로만 작동합니다.

**2026-09-05에 실제로 발동했습니다.** 그날 오후 이슈 125가 존재하지 않는 상태인
`**Status: review**`로 만들어졌습니다. 파서가 `backlog`을 반환했고, 수정과 테스트가
끝난 작업이 시작도 안 한 것으로 보고됐습니다. 기록도 남지 않았습니다. 미완료 이슈를
세다가 원본 토큰과 파싱 결과를 나란히 찍어보고서야 드러났습니다.

같은 날 이슈 파일 125개를 전수 조사한 결과, 폴백에 걸린 파일은 정확히 하나(125,
이후 수정)였습니다. 나머지 비-`LIFECYCLE_STATES` 토큰 7개는 전부
`superseded-by-<id>` 형태이고 612행이 명시적으로 올바르게 처리합니다.

헌법 **C2 — 조용한 예외 금지**를 어깁니다. 파급이 넓은 이유는 역설적으로 C8을 잘
지켰기 때문입니다. `markdown_status`가 유일한 상태 파서라서, `project_lifecycle`·
준비도 게이트·대시보드 상태 열과 그룹핑·`moduflow_ready`가 같은 침묵을 그대로
물려받습니다.

## 2. 목표

1. 위 세 입력을 구분 가능한 결과 셋으로 가른다.
2. 폴백이 적용될 때마다 이슈 id와 원본 토큰을 담은 진단을 스키마 검증기의 기존
   채널로 낸다.
3. 비-ASCII 토큰을 오류로 볼지 보고된 폴백으로 볼지 **정하고 문서화한다** —
   아무도 의도해서 고르지 않은 문자 클래스에 맡겨두지 않는다.
4. 유효한 이슈의 동작은 하나도 바꾸지 않는다.

## 3. 비목표

- 라이프사이클 상태를 추가·개명·번역하지 않는다. `LIFECYCLE_STATES`는 그대로이고,
  125가 원했다는 이유로 `review`가 상태가 되지는 않는다.
- 두 번째 상태 파서를 만들지 않는다. C8 유지.
- 이것만으로 릴리즈 게이트를 만들지 않는다. 검증기가 진단에서 오류로 격상할지는
  6절에서 정할 사안이지 전제가 아니다.
- `backlog` 기본값 자체를 바꾸지 않는다. 이 이슈는 **침묵**에 관한 것이다.
- 이슈 파일을 고치지 않는다. 125는 발동을 발견했을 때 이미 수정했고, 전수 조사는
  검증이지 범위가 아니다.
- 정상 동작하는 `superseded-by-<id>` 경로를 건드리지 않는다.

## 4. 제안하는 해법

파서는 하나로 두고, 상태만 필요한 호출자에게는 반환값도 그대로 둡니다. 어떻게 그
값에 도달했는지 알아야 하는 호출자를 위해 더 자세한 진입점을 하나 추가합니다.

`markdown_status(text)`는 시그니처와 반환값을 **그대로** 유지하므로 호출자를 하나도
안 고칩니다. 새 `markdown_status_result(text)`가 상태에 더해 `reason`
(`ok`/`missing`/`unreadable`/`unrecognised`)과, 토큰이 있었다면 원본 토큰을
반환합니다. `markdown_status`는 그 위의 얇은 래퍼가 됩니다 — 구현 하나에 뷰 둘,
이렇게 C8을 지킵니다.

스키마 검증기는 자세한 쪽을 호출해서 `ok`가 아닌 경우를 이슈 id·원본 토큰과 함께
보고합니다. 도식은 `spec.md` 4절에 있습니다.

## 5. 검토한 대안

1. **인식 못 한 토큰에서 예외 발생 — 기각.** 오타 한 번에 `product:status`·
   대시보드·준비도 게이트가 동시에 죽습니다. 이 파서는 너무 많은 읽기 경로에
   올라가 있어 던지면 안 됩니다.
2. **`markdown_status` 안에서 경고 로그 — 기각.** 모든 이슈를 도는 루프에서 쓰는
   순수 함수입니다. 수백 줄이 찍히고 파서에 I/O가 들어갑니다.
3. **인식 못 하면 `None`을 반환하고 호출자가 판단 — 기각.** 변경 폭이 가장 넓습니다.
   1절에 나열한 호출자 전부에 분기가 필요하고, 하나라도 빠뜨리면 크래시입니다.
4. **`review`를 `LIFECYCLE_STATES`에 추가 — 기각. 그리고 이게 제일 솔깃한
   선택입니다.** 125는 통과하겠지만 아무것도 고쳐지지 않습니다. 다음에 지어낸
   단어가 똑같이 조용히 실패합니다. **어휘가 결함이 아닙니다.**

## 6. 결정 — 비-ASCII 상태 토큰

`_markdown_status_token`은 `[A-Za-z0-9_-]+`를 매칭하므로 `**Status: 진행중**`은
아예 매칭되지 않고 "줄 없음"으로 도착합니다. 사실과 다릅니다 — 상태 줄은 있습니다.

**결정: 비-ASCII 토큰은 오류가 아니라 보고되는 폴백**으로 하고, `missing`과 구분되는
`reason: unreadable`을 붙입니다. 근거:

- 대안 1과 일관됩니다. 이 파서는 아무것도 던지지 않습니다.
- `missing`과 `unreadable`은 조치가 다릅니다. 하나는 상태 줄을 쓰라는 뜻이고,
  다른 하나는 지원되는 어휘로 쓰라는 뜻입니다.
- 이 저장소는 설계상 이중언어입니다. 이슈 본문에 한국어 요약 섹션이 있고 스펙은
  `.ko.md` 사이드카를 냅니다. `**Status: 진행중**`이라고 쓴 사람은 **문서 자신의
  관행을 따라** 그것을 지원하지 않는 필드로 들어간 것입니다. 침묵이 아니라 메시지를
  받아야 합니다.

상태 이름 자체는 ASCII로 유지합니다(비목표). 이 결정은 입력을 진단하는 것이지
받아들이는 것이 아닙니다.

## 수용 기준

1. `markdown_status`는 모든 입력에 대해 오늘과 똑같이 반환하고, 기존 스위트가
   무수정으로 통과한다.
2. `markdown_status_result`가 `ok`·`missing`·`unreadable`·`unrecognised`를
   보고하고, 토큰이 있었다면 원본 토큰을 함께 담는다.
3. 상태 줄이 없는 파일과 인식 못 한 토큰이 있는 파일이 서로 다른 reason을 낸다.
4. `**Status: 진행중**`은 `missing`이 아니라 `unreadable`이다.
5. 실제로 발동했던 토큰 `**Status: review**`는 `unrecognised`를 내고 원본 토큰
   `review`를 보존한다.
6. `superseded-by-<id>`는 `ok`이고 `superseded`로 해소된다 — 변경 없음.
7. 검증기가 `ok`가 아닌 이슈마다 진단 하나를 이슈 id·원본 토큰과 함께 낸다.
   유효한 이슈는 진단을 늘리지 않는다.
8. 빈 문자열과 값이 비어 있는 상태 줄을 포함해 어떤 입력에도 예외를 던지지 않는다.
9. `commands/product-issue.md`가 지원 어휘와 "지원하지 않는 토큰은 보고되고
   `backlog`으로 처리된다"를 문서화한다.
10. `issues/` 전수 조사가 폴백 의존 건수를 보고하고, 머지 시점에 0이다.
11. `python3 scripts/release_check.py .`가 통과하고 라이프사이클 드리프트가
    전후로 동일하다.

## 검증 전략

- reason 4종과 빈 문자열·빈 값 경계에 대한 단위 테스트.
- `**Status: review**` 케이스는 합성이 아니라 **회귀 픽스처**입니다 —
  2026-09-05에 실제로 발동한 토큰입니다.
- `python3 -m unittest tests.test_project_issue_schema`
- `python3 -m unittest discover -s tests`
- `python3 scripts/project_lifecycle.py . --drift` 전후 비교
- `python3 scripts/release_check.py .`

## 리스크와 미해결 질문

- **아무도 안 읽는 진단은 침묵과 같습니다.** 검증기 출력이 사람이 보는 표면
  — 최소한 `product:doctor` — 에 닿아야 합니다. JSON 덩어리 안에만 떨어지면 이
  이슈는 침묵을 없앤 게 아니라 옮긴 것이 됩니다. 계획 단계에서 확인할 것.
- **검증기가 나중에 오류로 격상할지**는 의도적으로 열어뒀습니다. 진단을 먼저
  제대로 만드는 게 그 논의의 전제입니다.
- `unreadable` 케이스는 코퍼스에 실제 사례가 없습니다 — 측정이 아니라 정규식에서
  추론한 것입니다. 픽스처가 합성이라는 점을 명시해야 합니다.

## 사람이 승인해야 할 결정

- 6절의 비-ASCII 결정
- `review`를 어휘에 넣지 않는 것 — 125 같은 상태는 계속 실패합니다. 다만 이제
  조용히가 아니라 시끄럽게.
- 진단이 `product:doctor`에 노출되는 것이 이 이슈의 종료 조건인지, 후속인지

승인 후 다음 명령: `product:plan 120-silent-status-fallback-in-issue-parser`
