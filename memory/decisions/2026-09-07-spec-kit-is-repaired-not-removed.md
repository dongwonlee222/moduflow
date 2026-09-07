---
id: 2026-09-07-spec-kit-is-repaired-not-removed
kind: decision
title: spec-kit 어댑터는 걷어내지 않고 살린다 — 안 쓰는 게 아니라 못 쓰는 것이었다
issue_id: 151-the-spec-kit-adapter-cannot-be-switched-on
spec: 
source_event: 2026-09-07 "스펙킷 사용이 안 되고 있던데 충격이다" — 실제로 켜서 확인
source_artifacts:
  - issues/151-the-spec-kit-adapter-cannot-be-switched-on.md
review_after: 
supersedes: []
superseded_by: []
depends_on: []
references:
  - specs/098-speckit-selective-validation-adapter/pilot-report.md
storage_policy: local
mirror_targets: []
owner: Dongwon Lee
date: 2026-09-07
tags: [spec-kit, weight, reversal]
summary: 같은 날 오전에 spec-kit 5,786줄을 걷어내자고 제안했다가 오후에 뒤집었다. 손으로 켜서 돌려보니 outcome ready가 나왔다 — 죽은 코드가 아니라 스위치가 없어서 못 켠 것이었다. 코드를 지우지 않고 무게를 줄이는 방법: 쓰면 무게가 아니다.
rationale: 걷어내자는 근거는 "꺼져 있고 켤 계획이 없다"였는데, 왜 꺼져 있는지를 안 봤다. _config_payload가 enabled False를 하드코딩해서 --configure --write로도 안 켜진다. 켜는 코드가 아예 없다. 손으로 설정 파일을 만들어 켜니 어댑터가 입력 파일 넷을 찾아 템플릿과 함께 넘겨준다.
evidence: python3 scripts/spec_kit_adapter.py . --issue-id 112-execution-planner-and-backend-boundary --request "spec kit analyze the spec" --host-available → outcome ready, function analyze, inputs [spec.md, plan.md, tasks.md, constitution.md], template vendor/spec-kit/0.16.1/commands/analyze.md. 명세가 없는 132에 돌리면 unavailable — 올바른 동작이다. grep "enabled.*=.*True" scripts/spec_kit_adapter.py → 출력 없음.
alternatives: 걷어낸다 — 5,780줄이 멀쩡하므로 기각. 그대로 둔다 — 4주간 아무도 몰랐고 doctor도 안 알려주므로 기각. 버전을 1.x로 올리며 같이 고친다 — 114의 범위이고 지금 할 일이 아니므로 분리.
reversal_conditions: 151을 고쳐 켤 수 있게 한 뒤, 실제 명세에 돌려서 쓸 만한 지적이 나오지 않으면 그때 걷어낸다. 파일럿 24/24는 합성 픽스처였고(보고서가 스스로 그렇게 적었다) 실제 유용성은 아직 미검증이다.
confidence: high
---

# spec-kit은 걷어내지 않고 살린다

## Summary

**같은 날 오전에 걷어내자고 제안했다가 오후에 뒤집었다.** 이 기록은 그 뒤집음의
이유다.

손으로 켜서 돌려보니 **`outcome: ready`** 가 나왔다. 5,786줄은 죽은 코드가 아니라
**스위치가 없어서 못 켠 것**이었다.

## Rationale

걷어내자는 근거는 **"꺼져 있고 켤 계획이 없다"** 였다. **왜 꺼져 있는지를 안
봤다.**

`_config_payload`가 `"enabled": False`를 하드코딩한다. `--configure --write`를
해도 꺼진 설정이 쓰인다. **켜는 코드가 아예 없다.** 켜려면 사람이
`.moduflow/capabilities.json`을 손으로 만들어야 하고, 그 방법은 어디에도 안 적혀
있다.

## Evidence

손으로 켠 뒤:

```
$ python3 scripts/spec_kit_adapter.py . \
    --issue-id 112-execution-planner-and-backend-boundary \
    --request "spec kit analyze the spec" --host-available
outcome : ready
function: analyze
inputs  : specs/112-.../spec.md, plan.md, tasks.md, workspace/constitution.md
template: vendor/spec-kit/0.16.1/commands/analyze.md
```

명세가 없는 `132`에 돌리면 `unavailable` — **올바른 동작이다.**

```
$ grep -n "enabled.*=.*True" scripts/spec_kit_adapter.py
(출력 없음)
```

## 이것이 오늘의 반복되는 모양이다

- **149** — `~`를 안 펼쳐서 등록된 프로젝트 셋을 다 못 열었다
- **151** — `enabled`를 못 켜서 5,786줄을 못 썼다

둘 다 **만들고, 통과시키고, 마지막 한 칸을 안 이은 것**이다. 테스트가 통과한다는
것이 쓰인다는 뜻이 아니다.

## Alternatives

- **걷어낸다** — 5,780줄이 멀쩡하므로 기각.
- **그대로 둔다** — 4주간 아무도 몰랐고 `doctor`도 안 알려주므로 기각.
- **1.x 올리기와 같이 고친다** — `114`의 범위다. 분리한다.

## Reversal Conditions

`151`을 고쳐 켤 수 있게 한 뒤 **실제 명세에 돌려서 쓸 만한 지적이 나오지 않으면
그때 걷어낸다.** 파일럿 24/24는 **합성 픽스처**였고 (보고서가 스스로
`Synthetic fixture latency: 0 ms; it is not presented as live performance`라고
적었다), 실제 유용성은 아직 미검증이다.
