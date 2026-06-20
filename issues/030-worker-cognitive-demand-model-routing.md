# Issue 030: Worker Cognitive Demand Model Routing

## Summary

모든 서브에이전트 워커가 `"TypeName": "self"` 로 고정되어 있어 작업 복잡도와 무관하게 동일한 모델이 사용됩니다. 워커 역할별 인지 요구 수준(cognitive demand)을 `deep / balanced / fast` 세 단계로 정의하여, 호스트 에이전트(Gemini/Claude/Codex)가 자신의 플랫폼에서 적합한 모델을 스스로 선택하도록 합니다. 모델명 하드코딩 없이 버전이 바뀌어도 수정이 불필요한 구조를 목표로 합니다.

## Source

- Type: product improvement / Antigravity feedback
- Link: conversation, 2026-06-20
- Date: 2026-06-20

## Lifecycle

- Phase: done
- Created: 2026-06-20
- Started: 2026-06-20
- Target End: 2026-06-20
- Completed: 2026-06-20
- Last Updated: 2026-06-20

## Opportunity

`worker_orchestrator.py`의 `subagent` 블록이 `TypeName: "self"` 만 지정하고 있어, spec-architect 같은 고난도 작업도 roadmap-planner 같은 단순 작업도 동일 모델로 처리됩니다. 비용·품질 최적화 기회를 놓치고 있습니다.

## Scope

### In

- 워커별 `cognitive_demand` 필드 정의 (`deep` / `balanced` / `fast`)
- `worker_orchestrator.py` 에 `CognitiveDemand` 필드 추가
- `workers/*.md` 8개 파일에 cognitive demand 및 근거 서술 추가
- `superpowers-execution-bridge/SKILL.md` 에 모델 자율 선택 지침 추가
- `product-execute.md` dispatch 카드에 cognitive demand 표시
- 호스트 에이전트가 실제로 다른 모델을 선택하는지 검증 테스트

### Out

- 특정 모델명 하드코딩
- 플랫폼별 모델 매핑 테이블 관리
- 모델 선택 강제(override) 메커니즘

## Acceptance Criteria

- `worker-plan.json` 의 각 task `subagent` 블록에 `CognitiveDemand` 필드 존재
- `workers/*.md` 8개 파일 모두 `cognitive_demand` 메타데이터 포함
- `superpowers-execution-bridge/SKILL.md` 에 `deep/balanced/fast` 해석 지침 포함
- dispatch 카드에 cognitive demand 및 선택 가이드 문구 노출
- 테스트: spec-architect(deep) 워커와 release-manager(fast) 워커를 각각 호출했을 때 에이전트가 다른 모델을 선택하는지 로그/출력으로 확인

## Workflow Tasks

- [x] spec -> specs/030-worker-cognitive-demand-model-routing/spec.md
- [x] plan -> specs/030-worker-cognitive-demand-model-routing/plan.md
- [x] execute -> PR / commits
- [x] review -> review notes
- [x] add cognitive_demand to WORKER_COGNITIVE_DEMAND dict in worker_orchestrator.py
- [x] update subagent block with CognitiveDemand field
- [x] update workers/*.md with cognitive_demand metadata (8 files)
- [x] update superpowers-execution-bridge/SKILL.md with model selection guide
- [x] update product-execute.md dispatch card
- [x] write test script verifying model self-selection behavior
