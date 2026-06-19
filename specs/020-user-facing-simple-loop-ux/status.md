# User-Facing Simple Loop UX Status

## Phase

Released; 021 Git binding and execution backend is next.

## Completed

- Bumped ModuFlow base version to `0.2.7` and refreshed Codex cache to `0.2.7+codex.20260618122055`.
- Completed review with natural-language routing examples, rg checks, full tests, validators, and release check.
- Created release notes for 020 simple loop UX.
- Updated `/moduflow`, `product:status`, and `product:loop` command docs for concise aliases.
- Updated ModuFlow routing skills for `상태`, `다음`, `다음 실행`, `이거 해줘`, and guarded `완료`.
- Updated README examples to lead with the simple Codex surface.
- Drafted implementation plan for hub/status/loop docs, routing skills, validation, and state handoff.
- Created spec for the small natural-language command surface: `상태`, `다음`, `이거 해줘`, and `완료`.
- Defined read-only versus mutation behavior so simple commands do not unexpectedly change files.
- Mapped aliases to existing `product:*` commands without replacing advanced direct commands.
- Captured acceptance criteria for concise status, one-step next recommendation, guarded completion, and low-friction intake.

## In Progress

- Released and handed off to issue 021.

## Blockers

- None.

## Follow-Ups

- Decide whether alias routing can be tested as docs-only rules or needs a small script-level router fixture.
- Coordinate richer intake behavior with issue 022 after this simple UX surface lands.

## Verification

- `rg -n "상태|다음|이거 해줘|완료" commands README.md` passed.
- `rg -n "active_issue_id|attempts|needs_decision|다음 실행" commands/product-loop.md` passed.
- `rg -n "이거 해줘|완료|다음 실행|guarded|direct.*product" skills/index/SKILL.md skills/pm-execution-router/SKILL.md` passed.
- `python3 -m unittest discover -s tests -v` passed (46 tests).
- `python3 scripts/validate_project_artifacts.py .` passed.
- `python3 scripts/validate_moduflow.py .` passed.
- `python3 scripts/release_check.py .` passed.

## Next Command

`product:spec 021-git-binding-and-execution-backend`
