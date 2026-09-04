---
description: Run data or metric analysis for an issue/spec.
argument-hint: "<issue id> [question]"
---

# /product:analyze

Answer product questions with data.

같은 유형의 분석 요청이 반복될 때마다 클레임 종류, 측정 단위, 필수 점검 항목을 매번 새로 설명해야 하는 번거로움이 있었습니다. 플레이북을 먼저 선택하면 이 항목들이 자동으로 채워지므로, 두 번째 실행부터는 시간 범위(time window)와 실제 수치만 채우면 된다는 이점이 있습니다.

## Do

1. 플레이북을 이름으로 선택하는 것이 첫 단계입니다.
   - 프로젝트 쪽에 이름이 같은 플레이북이 있으면, 그 플레이북이 읽기 전용 기본값을 덮어씁니다(override).
   - 프로젝트 쪽에 새로운 이름의 플레이북이 있으면 단순히 추가됩니다.
   - 둘 다 없으면 이름이 비슷한 기본값으로 대체하지 않고, `PLAYBOOK_UNRESOLVED`로 즉시 중단합니다.
   - 기본 플레이북 다섯 개는 `monthly-trend`, `cpo-change`, `amount-band`, `charging-speed`, `policy-impact`입니다.
2. 선택된 플레이북은 클레임 클래스(`claim_class`), 측정 단위(`measure.unit`), 필수 점검(`Required Checks`) 골격, 기본 caveats, 문서 구조를 미리 채웁니다. 작성자는 시간 범위와 실제 수치만 채우면 됩니다.
3. Define decision question, source, grain, period, and decision.
4. 모든 실행(run)은 클레임 클래스를 정확히 하나만 선언합니다: `exploratory`, `profitability`, `causal` 중 하나입니다. 추세와 마진을 함께 묻는 질문은 두 개의 실행으로 나눕니다.
5. 적용(apply) 전에는 항상 미리보기(preview)를 먼저 확인합니다. 기본 동작은 읽기 전용 미리보기입니다.
6. Use Data Analytics capability when available.
7. Save findings to `specs/<issue>/analysis.md`.
8. Save KPI definitions or success metrics to `specs/<issue>/metrics.md`.

## States

네 가지 상태는 항상 분리해서 보고하며, 하나의 단어로 합쳐 보고하지 않습니다.

- `run_state` (`draft`/`completed`) — 분석 작업 자체의 완료 여부
- `validation_state` (`unvalidated`/`passed`/`failed`) — 필수 점검을 평가한 결과
- `approval_state` (`unapproved`/`approved`) — 사람이 근거를 남기고 승인했는지 여부
- `decision_state` (`decided`/`waiting_on_maturity`/`superseded`) — 이 실행이 뒷받침하는 의사결정의 처리 여부

완료(completed)는 검증(validated)이 아니며, 검증은 승인(approved)이 아닙니다.

승인(`approval_state=approved`)에는 이미 존재하는 근거 경로(evidence path)가 연결되어 있어야 하며, 작성자가 근거를 임의로 만들어내지 않습니다.

## Unassigned issue

담당 이슈가 없는 실행은 `issue_id: unassigned`로 보류 상태를 유지합니다. 이 상태에서도 완료와 검증은 가능하지만, 승인되거나 최종 결과로 제시될 수는 없습니다.

## Follow-up and costs

- 후속 확인 날짜(follow-up date)와 조건을 저장하는 것은 스케줄러를 등록하는 것이 아닙니다. 어떤 것도 자동으로 실행되지 않습니다.
- 알 수 없는 비용은 알 수 없음으로 기록하며, 0으로 처리하지 않습니다.

## Next

- `/product:spec` to update requirements
- `/product:roadmap` to adjust priority
- `/product:review` for data validation

