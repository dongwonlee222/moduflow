# Issue 011: Workflow Task Tracking (산출물=추적)

**Status: done** — shipped as 0.2.6 (same release commit 7fbb967 as issue 012); status.md shows only optional follow-ups. Status line added 2026-07-06 (issue 066 follow-up: files whose specs-link line matched the migration's `Status:` grep were skipped).

## Summary

Make every artifact-producing workflow step (spec, plan, design, review) a tracked task inside its owning issue, so no artifact is produced off the books. Shipped as ModuFlow 0.2.6.

## Source

- Type: user conversation (personal-memory 프로젝트 사용 중 발견)
- Link: "워크플로우를 이슈화 / 산출물 나오는 건 추적되는 작업으로"
- Date: 2026-06-16

## Context

ModuFlow 이슈는 만들어지지만, 그 안에서 `product:spec`·`product:plan`이 만드는 산출물(spec/plan 파일)은 작업항목으로 잡히지 않고 "그냥 파일"로만 생성됐다. 워크플로우 단계 자체가 보이지 않게 진행되는 문제. "산출물이 나오는 단계는 전부 추적되어야 한다"는 요구.

순진하게 "산출물=별도 이슈"로 가면 무한재귀(‘spec 작성’ 이슈도 spec이 필요)가 생긴다. 그래서 단위를 구분한다: 1 이슈 = 1 deliverable, 워크플로우 단계는 그 이슈의 task.

## Completed Today

- `templates/issues/issue.md`: `## Workflow Tasks` 섹션 추가 — spec/plan/execute/review + 아티팩트 링크 + 체크박스.
- `commands/product-issue.md`: Do #5(Workflow Tasks 체크리스트 추가) + Granularity Rule(1이슈=1결과물, 단계는 task).
- `skills/index/SKILL.md`: Behavior #10(산출물=추적, spec/plan/design/review 실행 시 해당 task box+링크 갱신).
- 버전 0.2.5 → 0.2.6 (`.claude-plugin` + `.codex-plugin` 매니페스트, codex 접미사 보존).
- `validate_moduflow.py` 통과 (116 파일).

## Decisions

- 1 이슈 = 1 deliverable. 워크플로우 단계(spec/plan/design)는 별도 top-level 이슈로 쪼개지 않고 이슈 안 task로 추적 → 무한재귀 회피.
- 산출물은 항상 추적되며, 추적 단위만 이슈의 task 리스트.
- 0.2.5(loop seed)는 별도 이슈로 백필하지 않음(이번 범위 밖). 다음 번호 011을 0.2.6에 사용.

## Acceptance Criteria

- 이슈 템플릿이 Workflow Tasks 섹션을 포함. ✅
- product:issue/index 규칙이 "산출물=추적 task"를 강제. ✅
- 버전 0.2.6 동기화 + validate 통과. ✅
- 본 변경 자체가 이슈로 추적됨(도그푸딩). ✅

## Workflow Tasks

- [x] spec → `specs/011-workflow-task-tracking/spec.md`
- [x] execute → 템플릿/커맨드/스킬 + 버전업 (0.2.6)
- [x] review → validate_moduflow.py 통과
- (plan 생략: small, well-scoped 규칙 변경)

## Links

- Note: 원래 PR #2로 제출됐으나 개인 ops 아티팩트 정리 중 unmerged로 닫힘. 본 제품 변경분만 0.2.6에서 부활.
- Status: `specs/011-workflow-task-tracking/status.md`

## Next Command

`product:status`
