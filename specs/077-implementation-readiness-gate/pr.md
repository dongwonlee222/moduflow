# PR 핸드오프: 077-implementation-readiness-gate

## 요약

`product:execute` 전에 구현 준비도를 점검하는 report-only gate를 추가했습니다. API 계약, 테스트 전략, Storybook/MSW/Playwright 기준, 권한 모델, 릴리즈/롤백 검증이 충분한지 확인하고, 심각한 누락이 있으면 기본 루프가 `product:plan`으로 되돌아가도록 합니다.

핵심 변경:

- `scripts/project_execution.py`에 `--readiness` 모드와 `implementation-readiness.json` writer를 추가했습니다.
- `scripts/project_loop.py`가 execute 단계에서 `not_ready` readiness 결과를 보면 `product:plan <issue>`을 추천합니다.
- `commands/product-execute.md`, `product-plan.md`, `product-loop.md`에 readiness 흐름을 문서화했습니다.
- `skills/superpowers-execution-bridge/SKILL.md`에 실행 전 readiness handoff를 연결했습니다.
- readiness checker/loop routing 테스트를 추가했습니다.
- `.claude-plugin/plugin.json` 버전을 `0.3.20`으로 올렸습니다.

## PR 정보

- 브랜치: `codex/077-implementation-readiness-gate`
- PR: https://github.com/dongwonlee222/moduflow/pull/14
- 권장 base: `codex/079-plan-discipline-skill-matrix`
- 이유: 077은 079의 `Recommended Discipline` plan surface 위에서 실행 전 readiness를 이어받는 스택 작업입니다.
- 리뷰어: `Dongwon Lee`
- 상태: Draft PR 생성됨
- 병합 조건: 079 merge 또는 base 정리, 사람 승인, PR diff 확인, 필요한 상태 체크 통과

## 사람이 먼저 볼 것

- 한글 검토 패킷: `specs/077-implementation-readiness-gate/human-review.ko.md`
- 이슈: `issues/077-implementation-readiness-gate.md`
- 스펙: `specs/077-implementation-readiness-gate/spec.md`
- 계획: `specs/077-implementation-readiness-gate/plan.md`
- readiness artifact: `specs/077-implementation-readiness-gate/implementation-readiness.json`
- 리뷰 노트: `specs/077-implementation-readiness-gate/review.md`

## 검증

- `python3 -m unittest tests.test_project_execution -v` 통과.
- `python3 -m unittest tests.test_project_loop -v` 통과.
- `python3 -m unittest discover -s tests -v` 통과, 450 tests.
- `python3 scripts/spec_consistency.py . --issue-id 077-implementation-readiness-gate` 통과, findings 0.
- `python3 scripts/validate_moduflow.py .` 통과.
- `python3 scripts/validate_project_artifacts.py .` 통과. 기존 optional memory warning만 있습니다.
- `python3 scripts/release_check.py .` 통과.

## 리뷰 결과

차단 이슈는 없습니다.

확인한 점:

- readiness 결과는 `ready`, `warning`, `not_ready`로 나뉩니다.
- v1은 report-only이며, `not_ready`가 실행을 자동으로 금지하지는 않습니다.
- frontend 전용 항목은 UI/API-backed browser scope가 있을 때만 적용됩니다.
- `product:loop`는 `not_ready`를 보면 `product:plan`으로 되돌립니다.
- 078의 frontend QA template pack 범위는 건드리지 않았습니다.

남은 리스크:

- v1 checker는 deterministic keyword 기반입니다. 실제 사례가 쌓이면 false positive/negative를 regression test로 보강해야 합니다.
- 079가 아직 draft라 077 PR은 stacked PR로 만드는 것이 안전합니다.

## 다음 액션

1. PR diff를 확인합니다.
2. 079가 main에 merge되면 077 base를 main으로 정리하거나 rebase합니다.
3. `human-review.ko.md` 기준으로 사람이 검토합니다.
4. 괜찮으면 approve/merge합니다.
