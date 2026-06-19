# Review: Simplify Command And Folder Surface

## Issue

`026-simplify-command-and-folder-surface`

## Decision

Approved. Issue 026 is complete and ready to hand off to Issue 027.

## What Was Reviewed

- Benchmark findings for lightweight tool adoption patterns.
- Plugin cache packaging boundary for planning and verification artifacts.
- Lightweight target-project footprint in `project_migrate.py`.
- README and `/product:start` guidance for created versus non-created folders.
- Doctor/status mode guidance that keeps raw mode labels in JSON while showing plain Korean user guidance.
- Completion handoff contract based on active goal and loop state.

## Acceptance Review

- Compact default command model is documented.
- The 18-folder source repo is explained as internal tooling, PM artifacts, assets, validation, and dependencies.
- Normal target projects create only PM/state folders and do not receive tool/runtime folders.
- Runtime plugin cache excludes `issues/`, `specs/`, `tests/`, and `sessions/`.
- `lightweight`, `dogfooding`, and `heavy` remain machine-readable but are translated for users.
- Completed ModuFlow actions are required to include a structured next-action handoff based on goal/loop state.

## Verification

- `python3 -m unittest tests.test_codex_personal_install -v` passed.
- `python3 -m unittest tests.test_project_migration -v` passed.
- `python3 -m unittest tests.test_validation_distribution -v` passed.
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Residual Risk

- The ModuFlow source repo still has 18 top-level folders. This is now documented as acceptable for the source/tool repo, but a future technical design can still reduce or regroup source folders if needed.
- Issue 025 still has a review gap around start/intake write behavior. Issue 026 covers the simplified surface and migration footprint, not all start/intake internals.

## Next Handoff

다음은 `027-reduce-approval-popup-friction` spec 정리가 맞습니다.

이유:
- 026은 구현과 review가 완료됐습니다.
- 사용자 경험상 다음으로 가장 큰 마찰은 승인 팝업과 반복 검증 실행입니다.
- Antigravity 피드백도 027에 직접 연결됩니다.

다음 액션:
1. `specs/027-reduce-approval-popup-friction/spec.md` 작성
2. `specs/027-reduce-approval-popup-friction/plan.md` 작성
3. 검증 스크립트 shell 호출을 줄이는 importable validation engine 방향을 설계

그 뒤 우선순위:
- 027: 승인/검증 피로도 줄이기
- 028: 실제 서브에이전트 백엔드
- 029: Antigravity 아티팩트 싱크

바로 가려면 제가 027 spec 작성부터 진행하면 됩니다.
