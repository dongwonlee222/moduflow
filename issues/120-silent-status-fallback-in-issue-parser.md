# Issue 120: Silent Status Fallback in the Issue Parser

**Status: backlog** — created 2026-09-05.
**Priority: p2**

## 요약

이슈 파일의 상태 값을 못 읽으면 파서가 조용히 `backlog`로 바꿉니다. 오타 하나로 완료된 이슈가 말없이 백로그로 돌아갈 수 있고, 아무도 그 사실을 모릅니다.

## Summary

`markdown_status` in `scripts/project_issue_schema.py` returns `backlog` for any status it cannot recognize, with no diagnostic. A typo, a translated word, or a status outside `LIFECYCLE_STATES` is indistinguishable from an issue that really is in the backlog.

## Source

- Type: observation during Issue 119 work
- Owner / decision maker: Dongwon Lee
- Date: 2026-09-05
- Link: session review of `scripts/project_issue_schema.py` while answering why issue files are English-only

## Opportunity

`scripts/project_issue_schema.py:614`:

```python
return status if status in LIFECYCLE_STATES else "backlog"
```

Two ways in, both silent:

- `_markdown_status_token` matches `^\*\*Status:\s*([A-Za-z0-9_-]+)`. The character class is ASCII-only, so `**Status: 진행중**` does not match at all; the token is `None` and `markdown_status` returns `backlog`.
- A recognized-looking but invalid token (`Done`, `in-progress`, `compelte`) parses fine and is then replaced by `backlog`.

This violates constitution **C2 — no silent exceptions**. The failure is worse than a plain default because it is directional: it always lands on `backlog`, the state that means "not started". A `done` issue with a mistyped status silently reappears as unfinished work, and the lifecycle drift check will then agree with the wrong value because it reads the same parser.

The blast radius is wide: `project_lifecycle.py`, the readiness gate, the dashboard status column and grouping, and `moduflow_ready` all consume this one function (C8 — it is correctly the single parser, which is exactly why a silent fallback inside it spreads).

Nobody has hit this yet as far as the repository records show. It is registered now because it was found, not because it fired.

## Scope

### In

- Distinguish "no status line present" from "status line present but unrecognized". They are different facts today collapsed into one value.
- Report the unrecognized token — the raw text, the issue id, and the fact that a fallback was applied — through the schema validator's existing diagnostic channel.
- Decide and document whether a non-ASCII status token is a hard error or a reported fallback. The current regex silently rejects it; either behavior is defensible but it must be chosen, not inherited from a character class.
- Keep the default value itself if the decision is to keep it. This issue is about the silence, not about the choice of `backlog`.

### Out

- Adding, renaming, or translating lifecycle states. `LIFECYCLE_STATES` is unchanged.
- A second status parser. C8 stands: `markdown_status` remains the only one.
- Turning this into a release gate on its own. Whether the validator escalates is part of the decision above, not a foregone conclusion.
- Repairing existing issue files. No file is currently known to be affected; a scan is verification, not scope.

## Acceptance Criteria

- An issue whose status token is unrecognized produces a diagnostic naming the issue id and the raw token; the current silent substitution is gone.
- An issue with no status line at all is reported differently from one with an unrecognized token.
- A valid issue produces no new diagnostic and no behavior change, proven by the existing suites passing unchanged.
- The chosen behavior for a non-ASCII status token is documented where issue metadata is documented (`commands/product-issue.md`), not only in code.
- A scan of all current issue files reports how many, if any, are relying on the fallback today.
- `python3 scripts/release_check.py .` passes.

## Verification

- `python3 -m unittest tests.test_project_issue_schema`
- `python3 -m unittest discover -s tests`
- `python3 scripts/project_lifecycle.py . --drift` before and after, to confirm no drift is introduced or masked
- `python3 scripts/release_check.py .`

## Entry Points

- `scripts/project_issue_schema.py` (`markdown_status`, `_markdown_status_token`, `markdown_status_projection`)
- `scripts/project_lifecycle.py`
- `commands/product-issue.md`
- `tests/test_project_issue_schema.py`

## Scope Fence

Do not add a second status parser, do not change the lifecycle vocabulary, and do not "fix" issue files to make a scan come out clean. The point is that the parser says what it did.

## Workflow Tasks

- [ ] spec → `specs/120-silent-status-fallback-in-issue-parser/spec.md` (+ `spec.ko.md`)
- [ ] plan → `specs/120-silent-status-fallback-in-issue-parser/plan.md` + `tasks.md`
- [ ] execute → diagnostic path, tests, docs
- [ ] review → `specs/120-silent-status-fallback-in-issue-parser/review.md`

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `093-frontmatter-issue-schema-readiness-gate`
- supersedes:
- related: `048-artifact-lifecycle-sync`, `069-issue-dependency-and-priority`

## Sessions

- 2026-09-05: found while explaining why issue files carry English-only metadata. The ASCII-only status regex is the reason a Korean status token cannot work; the silent `backlog` fallback is the reason nobody would notice.

## Links

- Constitution: `workspace/constitution.md` C2, C8
- Goal: `workspace/goal.md`

## Next Command

`product:spec 120-silent-status-fallback-in-issue-parser`
