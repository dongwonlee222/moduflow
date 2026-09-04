---
name: data-analysis-bridge
description: Use when ModuFlow needs product metrics, KPI definitions, metric diagnostics, dashboards, reports, market sizing, or data-backed roadmap/spec decisions.
---

# Data Analysis Bridge

Every analysis must connect to an issue or roadmap decision.

값을 빠짐없이 근거와 함께 남기기 위해, 각 실행(run) 기록은 아래 필드를 모두 채웁니다. 필드가 비어 있으면 나중에 원인을 되짚기 어려워지므로, null이나 빈 값도 항상 명시적으로 기록하고 그 이유를 함께 남깁니다. 값이 단순히 비어 있는 채로 남는 필드는 없습니다.

## Run Record Fields

**Identity and playbook**
- `issue_id` — 실제 이슈 ID이거나 `unassigned`
- `playbook_ref` — 사용한 플레이북 ID와 버전

**Question**
- `decision_question` — 이 실행이 뒷받침하는 의사결정
- `claim_class` — `exploratory` / `profitability` / `causal` 중 정확히 하나

**Population and measure**
- `population` — 대상 정의와 비교 기준
- `measure` — 분자(numerator), 분모(denominator), 단위(unit)

**Time**
- `time_window` — 시작일, 종료일, 라벨, 단위(grain)
- `maturity` — 데이터 성숙도 상태

**Scope**
- `filters` — 적용한 필터
- `exclusions` — 제외한 항목

**Cost**
- `costs` — 적용 여부(applicable), 항목(items), 알 수 없는 항목(unknown_items), 사유(reason)

**Method**
- `method` — 수행 단계(steps)와 사용 도구(tooling)

**Provenance**
- `sources` — 데이터 출처 바인딩
- `execution_evidence` — 실행 근거; 확보하지 못한 항목은 `missing`에 사유와 함께 명시합니다

**Verification**
- `checks` — 점검 항목과 결과

**Result**
- `outputs` — 등록된 산출물
- `conclusion` — 결론
- `caveats` — 유의사항
- `decision_refs` — 연결된 의사결정 기록

**State**
- `run_state`, `validation_state`, `approval_state`, `decision_state` — 네 가지 독립 상태
- `approval_ref` — 승인 근거 경로

**History**
- `state_history` — 상태 변경 이력
- `supersedes`, `change_reason` — 이전 실행 대체 관계와 그 사유
- `follow_up` — 후속 확인 의도(스케줄이 아닙니다)

점검(`checks`) 결과는 ModuFlow가 직접 수행한 검증이 아니라 작성자의 진술(assertion)입니다. `profitability` 또는 `causal` 실행에서 `pass`로 기록하려면 이미 존재하는 근거(evidence reference)가 있어야 합니다.

Save findings to `analysis.md` and metric definitions to `metrics.md`.

