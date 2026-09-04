---
schema: moduflow.playbook.v1
id: pb-amount-band
kind: playbook
title: 금액대별 사용자 분석 플레이북
applies_to_types: [analysis]
applies_to_channels: [report]
audiences: [internal]
retrieval_trigger: 금액대별 사용자 분포를 확인할 때
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
- CHK002 [auto] section:구간 정의
- CHK003 [review] 금액대 구간 경계가 원본 데이터의 구간 정의와 일치하는지 검토자가 확인합니다.
- CHK004 [auto] approved-copy:이 분석은 탐색적 결과이며 추가 검증이 필요합니다.
- CHK005 [review] 구간별 사용자 수 차이를 만족도나 충성도 같은 다른 지표로 임의 확대 해석하지 않았는지 검토자가 확인합니다.

## Reusable Patterns

- 기본 주장 종류: exploratory
- 기본 측정 단위: 구간별 사용자 수

- 필요 입력은 Sheet 탭, CSV/XLSX 내보내기, SQL 추출 결과, 로컬 파일 중 어느 형태로 제공되어도 동일하게 처리할 수 있도록 구성했습니다. 특정 벤더 도구에 종속되지 않는 입력 형태를 전제로 합니다.

- 사용자를 금액대 구간으로 나눈 뒤 구간별 분포와 구간 간 이동 여부를 함께 기록하는 접근을 재사용 패턴으로 삼았습니다. 구간 경계를 정의한 기준을 문서 안에 명시했는지 먼저 확인했습니다.

## Do Not Repeat

- 구간 경계를 임의로 조정해 원하는 결론에 맞추지 않도록 주의가 필요합니다.

- 특정 구간에 속한 사용자 수가 적다는 이유만으로 그 구간의 중요도를 낮게 단정하지 않도록 유의했습니다.

- 금액대 구간과 다른 속성(가입 시기, 이용 방식 등)의 상관관계를 근거 없이 인과관계로 서술하지 않는 것을 권장드립니다.

## Approved Copy Blocks

- 이 분석은 탐색적 결과이며 추가 검증이 필요합니다.
- 금액대별 분포는 참고용 자료이며 단독으로 의사결정의 근거가 되지 않습니다.

## Approved Structures

- 문서는 요약, 구간 정의, 구간별 분포, 한계, 다음 단계 순서로 구성하는 것을 권장드립니다.

- 구간 정의 항목에는 구간을 나눈 기준과 그 기준을 선택한 이유를 함께 기재했습니다.

## Evidence

- 없음. 기본 템플릿입니다.

## Revision History

- 2026-09-04 기본 템플릿으로 생성했습니다.
