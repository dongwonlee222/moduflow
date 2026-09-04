---
schema: moduflow.playbook.v1
id: pb-cpo-change
kind: playbook
title: CPO 변화 분석 플레이북
applies_to_types: [analysis]
applies_to_channels: [report]
audiences: [internal]
retrieval_trigger: CPO 구성 변화를 확인할 때
process_ref_kind: none
process_ref:
process_ref_version:
process_ref_missing:
  - process_ref: 외부 절차가 아직 기록되지 않았습니다
version: 0.1
status: candidate
source_records: []
review_after: 2027-01-01
superseded_by: []
created: 2026-09-04
updated: 2026-09-04
---

## Required Checks

- CHK001 [auto] section:요약
- CHK002 [auto] section:관찰
- CHK003 [review] CPO 구성 변화의 시점 구분이 원본 데이터 출처와 일치하는지 검토자가 확인합니다.
- CHK004 [auto] approved-copy:이 분석은 탐색적 결과이며 추가 검증이 필요합니다.
- CHK005 [review] 특정 CPO를 지목하는 표현이 근거 없이 단정적으로 쓰이지 않았는지 검토자가 확인합니다.
- CHK006 [auto] forbidden:반드시

## Reusable Patterns

- 기본 주장 종류: exploratory

- 필요 입력은 Sheet 탭, CSV/XLSX 내보내기, SQL 추출 결과, 로컬 파일 중 어느 형태로 제공되어도 동일하게 처리할 수 있도록 구성했습니다. 특정 벤더 도구에 종속되지 않는 입력 형태를 전제로 합니다.

- CPO별 구성 비중의 변화를 시점 단위로 나열하고, 신규 진입이나 이탈로 보이는 구간을 별도로 표시하는 접근을 재사용 패턴으로 삼았습니다. CPO 명칭 표기가 시점마다 일관되게 유지되는지 먼저 확인했습니다.

## Do Not Repeat

- CPO 구성의 변화를 특정 CPO의 성과나 전략 판단으로 곧바로 연결하지 않도록 주의가 필요합니다.

- 명칭 표기 방식이 바뀐 경우를 실제 구성 변화로 오인하지 않도록 별도로 확인하는 것을 권장드립니다.

- 표본에 포함된 CPO의 수가 시점마다 달라지는 경우, 이를 밝히지 않은 채 비중만 비교하지 않도록 유의했습니다.

## Approved Copy Blocks

- 이 분석은 탐색적 결과이며 추가 검증이 필요합니다.
- CPO 구성 변화는 참고용 자료이며 단독으로 의사결정의 근거가 되지 않습니다.

## Approved Structures

- 문서는 요약, 구성 변화 그래프, 관찰, 한계, 다음 단계 순서로 구성하는 것을 권장드립니다.

- 관찰 항목에는 시점 간 구성 변화의 방향과 그 근거가 되는 데이터 출처를 함께 기재했습니다.

## Evidence

- 없음. 기본 템플릿입니다.

## Revision History

- 2026-09-04 기본 템플릿으로 생성했습니다.
