# Issue 031: Goal-driven Autonomous Benchmarking and Issue Generation

**Status: done** — body and status.md say `Phase: done` (commit 1285183, `issue_generator.py` live). Status line added 2026-07-06 (issue 066 follow-up: files whose specs-link line matched the migration's `Status:` grep were skipped).

## Summary

ModuFlow의 제품 개발 자율성을 극대화하기 위해, 사용자가 상위 수준의 제품 목표(Goal)를 정의하거나 갱신했을 때 에이전트가 외부 모범 사례 및 기술 동향을 스스로 검색(벤치마킹)하고, 이를 달성하기 위한 구체적인 하위 작업들을 도출하여 새로운 Issue 아티팩트(`issues/0xx-*.md`)로 자동 작성 및 제안하는 기능을 구축합니다.

## Source

- Type: product improvement / Autonomous PM Agent
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

현재 ModuFlow는 이슈가 등록되면 `spec -> plan -> execute` 단계의 개발 과정을 잘 수행하지만, "어떤 기술 스펙을 도입해야 하는가", "이를 위해 구체적으로 어떤 이슈들을 쪼개서 등록해야 하는가"와 같은 PM 고유의 기획 영역은 사람이 개입하여 작성해야 합니다. 
상위 Goal이 있을 때 에이전트가 스스로 웹 검색을 통한 벤치마킹을 수행하고 필요한 이슈 후보들을 정밀하게 설계하도록 함으로써 진정한 '자율 개발 루프'에 진입할 수 있습니다.

## Scope

### In

- 사용자가 설정한 Goal과 현재 프로젝트 상태를 기반으로 외부 사례를 벤치마킹(웹 검색 연동)하는 CLI 명령어 또는 기능 구현
- 검색 결과를 요약 분석하여 마일스톤에 맞게 이슈를 나누는 Issue Generator 모듈 개발
- 도출된 이슈들을 ModuFlow 스키마(`issues/` 폴더 양식)에 맞는 마크다운 파일로 자동 생성
- 사용자가 에이전트가 제안한 이슈 리스트를 검토하고 수락/거절할 수 있는 피드백 UX 설계
- 이에 대한 단위 테스트 및 시나리오 검증

### Out

- 사용자의 최종 승인 없이 무조건적인 원격 git push 및 PR 생성 자동화 (안전성을 위한 Human-in-the-loop 유지)
- ModuFlow 범위 밖의 외부 프로젝트 기획 툴(Jira, Linear 등)과의 API 통합

## Acceptance Criteria

- 상위 Goal을 전달받아 벤치마킹을 수행하고 이슈 목록을 마크다운 파일들로 자동 생성해 내는 기능 동작 확인
- 생성된 이슈 파일들이 `issues/0xx-*.md` 표준 포맷을 준수하며 `project_doctor.py` 및 `validate_moduflow.py` 검증을 통과함
- 최소 1개 이상의 시나리오 테스트(테스트 Goal 입력 -> 벤치마킹 수행 -> 이슈 마크다운 빌드)가 완전히 동작하고 통과함

## Workflow Tasks

- [x] spec -> specs/031-goal-driven-autonomous-benchmarking-and-issue-generation/spec.md
- [x] plan -> specs/031-goal-driven-autonomous-benchmarking-and-issue-generation/plan.md
- [x] execute -> PR / commits
- [x] review -> review notes
- [x] 벤치마킹 및 이슈 자동 생성 로직 설계 및 구현
- [x] 생성된 이슈 파일들의 스키마 적합성 및 템플릿 구현
- [x] 단위 테스트 작성 및 전체 파이프라인 검증

## Links

- Spec: `specs/031-goal-driven-autonomous-benchmarking-and-issue-generation/spec.md`
- Status: `specs/031-goal-driven-autonomous-benchmarking-and-issue-generation/status.md`

## Next Command

`product:execute 031-goal-driven-autonomous-benchmarking-and-issue-generation`
