# PR 핸드오프: 079-plan-discipline-skill-matrix

## 요약

`product:plan`이 앞으로 각 작업 stream마다 어떤 Superpowers discipline 또는 ModuFlow adapter skill을 써야 하는지 명시하도록 문서/스킬 지침을 개선했습니다.

핵심 변경:

- `commands/product-plan.md`에 `Recommended Discipline` 섹션을 필수 가이드로 추가했습니다.
- `skills/superpowers-execution-bridge/SKILL.md`에 discipline catalog와 추천 기준을 추가했습니다.
- `skills/pm-execution-router/SKILL.md`에 spec 이후 plan 단계에서 추천 discipline을 드러내야 한다는 연결 규칙을 추가했습니다.
- 079 자체 plan이 `Recommended Discipline` matrix를 포함하도록 dogfood했습니다.
- 077 readiness gate와 078 frontend QA template scope는 건드리지 않았습니다.

## PR 정보

- 브랜치: `codex/079-plan-discipline-skill-matrix`
- PR: https://github.com/dongwonlee222/moduflow/pull/13
- 리뷰어: `Dongwon Lee`
- 상태: Draft PR 생성됨
- 병합 조건: 사람 승인, PR diff 확인, 필요한 상태 체크 통과

## 사람이 먼저 볼 것

- 한글 검토 패킷: `specs/079-plan-discipline-skill-matrix/human-review.ko.md`
- 이슈: `issues/079-plan-discipline-skill-matrix.md`
- 스펙: `specs/079-plan-discipline-skill-matrix/spec.md`
- 계획: `specs/079-plan-discipline-skill-matrix/plan.md`
- 리뷰 노트: `specs/079-plan-discipline-skill-matrix/review.md`

## 검증

- `python3 scripts/spec_consistency.py . --issue-id 079-plan-discipline-skill-matrix` 통과, findings 0.
- `python3 scripts/validate_moduflow.py .` 통과.
- `python3 scripts/validate_project_artifacts.py .` 통과. 기존 optional memory warning만 있습니다.
- `python3 scripts/release_check.py .` 통과.

## 리뷰 결과

차단 이슈는 없습니다.

확인한 점:

- `product:plan`에 `Recommended Discipline` 섹션 요구사항과 예시 매트릭스가 추가됐습니다.
- Superpowers bridge에 writing-plans, TDD, product-design, data-analysis, Storybook/MSW, Playwright/QA, review, verification-before-completion 추천 기준이 들어갔습니다.
- PM router에는 spec 이후 plan이 추천 discipline을 드러내야 한다는 연결 규칙이 들어갔습니다.
- 079 자체 plan이 `Recommended Discipline` 섹션을 포함해 dogfood 역할을 합니다.
- 077 readiness gate와 078 frontend QA template scope는 건드리지 않았습니다.

남은 리스크:

- v1은 문서/프롬프트 규칙입니다. 실제 자동 추천 엔진은 아직 없습니다.
- 추천 기준은 human-readable 형태라 당장 parser 검증은 하지 않습니다. 실제 plan 사례가 더 쌓이면 regression test로 고정할 수 있습니다.
- 기존 과거 plan들은 수정하지 않았습니다.

## 다음 액션

1. PR diff를 확인합니다.
2. `human-review.ko.md` 기준으로 사람이 검토합니다.
3. 괜찮으면 approve/merge합니다.
4. merge 후 `product:release 079-plan-discipline-skill-matrix`를 진행합니다.
