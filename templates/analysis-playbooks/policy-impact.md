---
schema: moduflow.playbook.v1
id: pb-policy-impact
kind: playbook
title: 정책 변화 영향 분석 플레이북
applies_to_types: [analysis]
applies_to_channels: [report]
audiences: [internal]
retrieval_trigger: 정책 변화가 미친 영향을 확인할 때
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
- CHK002 [auto] section:정책 시점
- CHK003 [auto] section:대안 설명 배제
- CHK004 [review] 정책 시행 시점 전후 비교 구간이 대칭적으로 설정되었는지 검토자가 확인합니다.
- CHK005 [review] 정책 외 다른 요인(계절성, 동시 시행된 다른 정책 등)이 대안 설명으로 충분히 검토되었는지 검토자가 확인합니다.
- CHK006 [auto] approved-copy:이 분석은 인과관계를 시사하는 결과이며 통제되지 않은 요인이 남아 있을 수 있습니다.

## Reusable Patterns

- 기본 주장 종류: causal
- 기본 측정 단위: 정책 전후 비교값

- 필요 입력은 Sheet 탭, CSV/XLSX 내보내기, SQL 추출 결과, 로컬 파일 중 어느 형태로 제공되어도 동일하게 처리할 수 있도록 구성했습니다. 특정 벤더 도구에 종속되지 않는 입력 형태를 전제로 합니다.

- 정책 시행 시점을 기준으로 전후 구간을 나누고, 관찰된 변화와 함께 고려 가능한 대안 설명을 나란히 기록하는 접근을 재사용 패턴으로 삼았습니다. 인과 주장을 다루는 만큼 비교 구간의 대칭성과 대안 설명 배제 근거를 문서 안에 명시했는지 먼저 확인했습니다.

## Do Not Repeat

- 정책 시행 전후의 단순 비교만으로 인과관계를 단정하지 않도록 주의가 필요합니다.

- 동시에 발생한 다른 변화(계절성, 다른 정책, 외부 이벤트 등)를 배제하지 않은 채 관찰된 변화를 해당 정책의 효과로 귀속하지 않도록 유의했습니다.

- 비교 구간의 길이나 기준이 전후로 다르게 설정된 경우, 이를 밝히지 않은 채 결과를 비교하지 않는 것을 권장드립니다.

## Approved Copy Blocks

- 이 분석은 인과관계를 시사하는 결과이며 통제되지 않은 요인이 남아 있을 수 있습니다.
- 정책 영향 분석은 참고용 자료이며 단독으로 의사결정의 근거가 되지 않습니다.

## Approved Structures

- 문서는 요약, 정책 시점, 전후 비교, 대안 설명 배제, 한계, 다음 단계 순서로 구성하는 것을 권장드립니다.

- 대안 설명 배제 항목에는 검토한 대안 설명 목록과 각 설명을 배제하거나 배제하지 못한 이유를 함께 기재했습니다.

## Evidence

- 없음. 기본 템플릿입니다.

## Revision History

- 2026-09-04 기본 템플릿으로 생성했습니다.
