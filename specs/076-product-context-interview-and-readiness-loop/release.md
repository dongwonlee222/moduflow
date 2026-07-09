# Release: 076-product-context-interview-and-readiness-loop

Issue: `076-product-context-interview-and-readiness-loop`
Version: `0.3.18`
Date: 2026-07-09
PR: `https://github.com/dongwonlee222/moduflow/pull/12`
Merge commit: `eaf3a492d8506782e4d012c0b1b08c936160cd76`

## Summary

Released Fast Path Shaping Router.

ModuFlow now keeps clear issue requests fast while routing vague, risky, or strategic product requests through short shaping or compressed panel-style questioning.

## User-Facing Changes

- Clear requests like `README 문구 개선 이슈 만들어줘` continue directly to `product:issue`.
- Ambiguous product-context requests like `모두플로 인기가 없는 이유 개선해줘` route to short shaping with at most 1-3 questions.
- Strategic product-direction requests like `AI 작업 루프 제품 전략 다시 정리해줘` route to panel shaping through `product:opportunity`.
- README now explains ModuFlow as a product-context execution loop that uses Spec Kit, Superpowers, Anthropic Knowledge Work Plugins, and Codex workflow adapters.
- Follow-up issues `077`-`080` are registered for readiness gates, frontend QA templates, plan discipline matrices, and reference improvement backlog.

## Verification

- `python3 -m unittest tests.test_project_intake.ProjectIntakeTests -v` — passed, 13 tests OK.
- `python3 scripts/validate_moduflow.py .` — passed.
- `python3 scripts/validate_project_artifacts.py .` — passed with only the existing optional memory warning.
- `python3 scripts/release_check.py .` — passed.
- GitHub CI for PR #12 — passed.

## Human Review

- Korean review packet: `specs/076-product-context-interview-and-readiness-loop/human-review.ko.md`
- PR body was updated to Korean-first review text before merge.
- Human approval: Dongwon Lee requested moving past Draft and merging after the Korean review surface was fixed.

## Rollback

Revert merge commit `eaf3a492d8506782e4d012c0b1b08c936160cd76`.

Rollback impact:

- Removes the `fast` / `short` / `panel` intake metadata from `scripts/project_intake.py`.
- Reverts command docs and README positioning changes.
- Removes issues `076`-`080` and 076 planning/review/release artifacts added by the PR.

## Post-Release Checks

- Try these representative routes after merge:
  - `python3 scripts/project_intake.py 'README 문구 개선 이슈 만들어줘' .`
  - `python3 scripts/project_intake.py '모두플로 인기가 없는 이유 개선해줘' .`
  - `python3 scripts/project_intake.py 'AI 작업 루프 제품 전략 다시 정리해줘' .`
- Confirm fast path still has `question_count: 0`.
- Confirm short/panel paths cap `question_count` at 3.

## Next

`product:spec 079-plan-discipline-skill-matrix`
