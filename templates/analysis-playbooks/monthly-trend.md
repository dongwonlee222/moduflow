---
schema: moduflow.playbook.v1
id: pb-monthly-trend
kind: playbook
title: 월별 추세 분석 플레이북
applies_to_types: [analysis]
applies_to_channels: [report]
audiences: [internal]
retrieval_trigger: 월별 이용 추세를 확인할 때
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
- CHK002 [auto] section:한계
- CHK003 [auto] approved-copy:이 분석은 탐색적 결과이며 추가 검증이 필요합니다.
- CHK004 [review] 추세 해석이 계절성 요인이나 데이터 누락 구간을 충분히 고려했는지 검토자가 확인합니다.
- CHK005 [review] 그래프의 축과 구간 표기가 원본 데이터 출처와 일치하는지 검토자가 확인합니다.

## Reusable Patterns

- 기본 주장 종류: exploratory
- 기본 측정 단위: 월별 집계값

- 필요 입력은 Sheet 탭, CSV/XLSX 내보내기, SQL 추출 결과, 로컬 파일 중 어느 형태로 제공되어도 동일하게 처리할 수 있도록 구성했습니다. 특정 벤더 도구에 종속되지 않는 입력 형태를 전제로 합니다.

- 시계열 데이터를 월 단위로 정렬한 뒤 구간별 관찰과 이상치 유무를 함께 기록하는 접근을 재사용 패턴으로 삼았습니다. 월과 월을 비교할 때는 동일한 집계 기준을 유지했는지 먼저 확인했습니다.

## Do Not Repeat

- 단일 월의 급등락만으로 원인을 단정하지 않도록 주의가 필요합니다.

- 계절성이나 영업일수 차이 같은 구조적 요인을 배제한 채 추세를 해석하지 않도록 유의했습니다.

- 데이터 수집이 누락된 구간을 실제 추세 변화로 오인하지 않도록 별도로 표시하는 것을 권장드립니다.

## Approved Copy Blocks

- 이 분석은 탐색적 결과이며 추가 검증이 필요합니다.
- 월별 추세는 참고용 자료이며 단독으로 의사결정의 근거가 되지 않습니다.

## Approved Structures

- 문서는 요약, 추세 그래프, 구간별 관찰, 한계, 다음 단계 순서로 구성하는 것을 권장드립니다.

- 각 구간별 관찰 항목에는 해당 구간에서 확인된 변화와 그 변화를 뒷받침하는 근거를 함께 기재했습니다.

## Evidence

- 없음. 기본 템플릿입니다.

## Revision History

- 2026-09-04 기본 템플릿으로 생성했습니다.
