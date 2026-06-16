# Spec 011: Workflow Task Tracking (산출물=추적)

## Problem

이슈는 생성되지만 그 안의 워크플로우 단계(spec/plan/design/review)가 만드는 산출물이 작업항목으로 추적되지 않는다. 산출물이 "보이지 않게" 생성되어, 어디까지 했는지/무엇이 남았는지가 이슈에 드러나지 않는다.

## Goal

모든 산출물 생성 단계를 그 이슈 안에서 추적 가능한 task로 만든다. 추적 누락 0.

## Non-Goals

- 워크플로우 단계를 별도 top-level 이슈로 승격 (무한재귀 유발 → 금지).
- 0.2.5 loop seed 변경의 소급 이슈화 (이번 범위 밖).

## Design

### 단위 구분
- **이슈 = 1 deliverable**: 자기 라이프사이클을 가진 결과물.
- **워크플로우 task = 산출물 단계**: spec/plan/design/execute/review. 이슈 안 `## Workflow Tasks` 체크리스트에 위치, 각 task는 아티팩트 파일 링크 + 상태.

### 재귀 회피
"spec 작성"을 별도 이슈로 만들면 그 이슈도 spec이 필요 → ♾️. 단계는 task로만 두어 차단. 단계가 자체 deliverable로 커지면 그때만 새 이슈로 분리.

### 적용 지점
- `templates/issues/issue.md`: `## Workflow Tasks` 섹션 표준화.
- `commands/product-issue.md`: Do 단계 + Granularity Rule.
- `skills/index/SKILL.md`: Behavior #10 — spec/plan/design/review 실행 시 해당 task box + 링크 갱신.

## Acceptance

- 새 이슈가 템플릿에서 Workflow Tasks를 상속.
- product:spec/plan/design/review 실행이 이슈의 해당 task를 갱신하도록 규칙화.
- 버전 0.2.6 동기화 + validate 통과.
- 본 변경이 이슈 011 + 본 spec으로 추적됨(도그푸딩).

## Status

Done. 0.2.6 (originally PR #2, closed unmerged; product-only changes revived).
