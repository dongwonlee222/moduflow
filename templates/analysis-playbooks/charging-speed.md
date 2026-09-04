---
schema: moduflow.playbook.v1
id: pb-charging-speed
kind: playbook
title: 완속·급속 충전 분석 플레이북
applies_to_types: [analysis]
applies_to_channels: [report]
audiences: [internal]
retrieval_trigger: 완속·급속 충전 이용을 비교할 때
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
- CHK002 [auto] section:구분 기준
- CHK003 [review] 완속·급속 구분 기준이 원본 데이터의 충전기 유형 표기와 일치하는지 검토자가 확인합니다.
- CHK004 [auto] approved-copy:이 분석은 탐색적 결과이며 추가 검증이 필요합니다.
- CHK005 [review] 이용 패턴 차이를 사용자 선호로 단정하기 전에 장소나 시간대 같은 다른 요인을 배제했는지 검토자가 확인합니다.
- CHK006 [auto] forbidden:반드시

## Reusable Patterns

- 기본 주장 종류: exploratory

- 필요 입력은 Sheet 탭, CSV/XLSX 내보내기, SQL 추출 결과, 로컬 파일 중 어느 형태로 제공되어도 동일하게 처리할 수 있도록 구성했습니다. 특정 벤더 도구에 종속되지 않는 입력 형태를 전제로 합니다.

- 완속과 급속을 구분한 뒤 각 유형별 이용 패턴과 구분 기준을 함께 기록하는 접근을 재사용 패턴으로 삼았습니다. 구분 기준이 데이터 출처에 명시된 표기와 일치하는지 먼저 확인했습니다.

## Do Not Repeat

- 완속과 급속 간 이용 차이를 장소, 시간대, 접근성 같은 다른 요인을 배제한 채 사용자 선호로 단정하지 않도록 주의가 필요합니다.

- 충전기 유형 표기 방식이 데이터 출처마다 다를 수 있다는 점을 확인하지 않은 채 구분 기준을 혼용하지 않도록 유의했습니다.

- 일부 지역이나 일부 기간의 관찰을 전체 경향으로 일반화하지 않는 것을 권장드립니다.

## Approved Copy Blocks

- 이 분석은 탐색적 결과이며 추가 검증이 필요합니다.
- 완속·급속 비교는 참고용 자료이며 단독으로 의사결정의 근거가 되지 않습니다.

## Approved Structures

- 문서는 요약, 구분 기준, 유형별 이용 패턴, 한계, 다음 단계 순서로 구성하는 것을 권장드립니다.

- 구분 기준 항목에는 완속과 급속을 나눈 기준과 그 기준의 출처를 함께 기재했습니다.

## Evidence

- 없음. 기본 템플릿입니다.

## Revision History

- 2026-09-04 기본 템플릿으로 생성했습니다.
