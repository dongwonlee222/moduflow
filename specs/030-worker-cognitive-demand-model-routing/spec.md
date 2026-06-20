# Spec: Worker Cognitive Demand Model Routing

Issue: 030-worker-cognitive-demand-model-routing

## Problem

`worker_orchestrator.py`가 생성하는 `subagent` 블록이 `TypeName: "self"` 만 포함합니다. spec-architect(복잡한 아키텍처 판단)와 release-manager(체크리스트 확인) 같이 인지 요구 수준이 전혀 다른 워커에 동일 모델이 사용됩니다. 비용·품질 최적화 기회를 놓치고 있습니다.

## Solution

모델명을 하드코딩하는 대신, 워커가 필요로 하는 **인지 요구 수준(cognitive demand)** 을 세 단계로 서술합니다. 호스트 에이전트는 이 설명을 읽고 자신의 플랫폼에서 현재 사용 가능한 최적 모델을 스스로 선택합니다.

## Cognitive Demand Levels

| 수준 | 의미 | 호스트에게 전달하는 지침 |
|---|---|---|
| `deep` | 깊은 추론, 아키텍처 설계, 전략 판단 | "가장 강력한 추론 모델을 사용하라" |
| `balanced` | 코딩, 검토, UX — 품질+속도 균형 | "표준 프로덕션 모델을 사용하라" |
| `fast` | 목록 정리, 체크리스트, 빠른 요약 | "가장 빠르고 가벼운 모델을 사용하라" |

## Worker Mapping

| 워커 | 수준 | 근거 |
|---|---|---|
| spec-architect | `deep` | 복잡한 요구사항 분석, 상충 트레이드오프 판단 |
| pm-strategist | `deep` | 비즈니스 전략, 다각도 이해관계자 판단 |
| implementation-worker | `balanced` | 코딩 능력 + 속도 균형 |
| qa-reviewer | `balanced` | 꼼꼼한 검토, 엣지케이스 탐지 |
| ux-flow-worker | `balanced` | 창의성과 분석 동시 필요 |
| release-manager | `fast` | 체크리스트 확인, 템플릿 기반 작업 |
| roadmap-planner | `fast` | 목록 정렬, 우선순위 계산 |
| data-reviewer | `fast` | 수치 요약, 패턴 보고 |

## Design Decisions

- 모델명 하드코딩 금지: 새 버전이 나와도 수정 불필요
- `CognitiveDemand` 필드는 호스트에 대한 **권고**이지 강제가 아님
- 호스트가 모델을 선택할 때 참고하는 자연어 설명도 함께 제공

## Acceptance Criteria

- `worker-plan.json` 각 task subagent 블록에 `CognitiveDemand` 필드 존재
- `workers/*.md` 8개 파일 모두 cognitive_demand 메타데이터 포함
- SKILL.md에 `deep/balanced/fast` 해석 지침 포함
- 테스트: deep vs fast 워커 dispatch 시 에이전트가 다른 모델을 선택함을 확인

## Next Command

`/product:plan 030-worker-cognitive-demand-model-routing`
