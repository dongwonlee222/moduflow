# Issue 123: Empty Declarations File Disables The Linkage Warning

**Status: backlog** — created 2026-09-05.
**Priority: p1**

## 요약

세션 종료 훅이 "이슈에 연결되지 않은 코드 변경"을 경고해야 하는데, `releases/no-issue-declarations.md`가 **존재하기만 하면** 무조건 면제합니다. 내용을 읽지 않습니다. 그 파일은 선언 0건인 헤더뿐이고, 파일 스스로 "대부분의 릴리즈에서 비어 있어야 한다"고 적어뒀습니다. **정상 상태가 검사를 끄는 구조**입니다.

## Summary

`hooks/on_stop.detect_unlinked` exempts every unlinked behavior change as soon as
`releases/no-issue-declarations.md` exists on disk. It never parses the file, so
an empty declarations file — the documented normal state — permanently silences
the warning it guards.

## Source

- Type: found while answering "does anything stop work without an issue?"
- Owner / decision maker: Dongwon Lee
- Date: 2026-09-05

## Opportunity

```python
# hooks/on_stop.py:274
if (project_root / NO_ISSUE_DECLARATIONS_RELPATH).is_file():
    return {"unlinked": [], "errors": [], "reason": "no-issue-declaration"}
```

Existence only. Measured on this repository on 2026-09-05 with two genuinely
unlinked behavior files in the working tree:

| State of `releases/no-issue-declarations.md` | `detect_unlinked` result |
| --- | --- |
| present (0 declarations, header only) | `reason: no-issue-declaration`, `unlinked: []` |
| temporarily moved away | `reason: unlinked-behavior-changes`, `unlinked: ['scripts/project_migrate.py', 'templates/workspace/dashboard.md']` |

The detection works. It is simply never reached.

The file's own blockquote says: *"This file should hold zero declarations at most
releases — an entry here is the exception, not the norm."* So the intended steady
state is exactly the state that disables the check.

**The correct implementation already exists in a sibling.**
`scripts/release_check.py:213` reads "non-empty, non-heading lines" of the same
file rather than testing for its presence. The hook should use that, not a new
parser.

This is one layer of a three-layer bypass found in the same pass. The other two,
recorded here so the whole picture is in one place:

- No git hooks are installed, so nothing checks before a write or a commit.
- `release_check.run_linkage_gate` inspects `merge_base..HEAD`. On `main`,
  `merge_base` equals `HEAD`, so it examines 0 commits and returns `ok: True`.
  Four commits were made to `main` on 2026-09-05 with no `Issue:` trailer and
  the gate passed every time. Whether that is a defect or the expected cost of
  working outside the branch/PR flow is a human decision, not part of this issue.

## Scope

### In

- Parse the declarations file instead of testing for its existence, reusing
  `release_check`'s existing line reader rather than writing a second one.
- Exempt only the paths an actual declaration covers; everything else still warns.
- A test that an empty declarations file does not suppress the warning, and one
  that a real declaration does suppress the path it names.

### Out

- Blame-validating declarations in the hook. `validate-declaration` already
  exists for the release gate; the stop hook is a warning, not a gate, and
  should stay fast.
- Installing git hooks or changing the merge-base range. Those are the other two
  layers and belong to their own decision.
- Changing the declaration file format.

## Acceptance Criteria

- An empty or header-only declarations file produces `unlinked-behavior-changes`,
  not `no-issue-declaration`.
- A declaration naming a path suppresses the warning for that path only.
- A missing declarations file behaves as it does today.
- The hook reuses `release_check`'s reader; no second parser is introduced.
- `hooks/on_stop.py` stays inside its existing time budget.
- `python3 scripts/release_check.py .` stays at 14 of 14.

## Verification

- Fixture repository with unlinked behavior changes and, in turn: no file, an
  empty file, a header-only file, a file with one matching declaration, and a
  file with one non-matching declaration.
- `tests/test_hooks_on_stop.py` regression run.

## Entry Points

- `hooks/on_stop.py:274` — the existence check
- `hooks/on_stop.py:216` — `detect_unlinked`
- `scripts/release_check.py:213` — the reader to reuse
- `releases/no-issue-declarations.md`
- `tests/test_hooks_on_stop.py`

## Scope Fence

Fix the check. Do not turn the stop hook into a gate — it warns once per
fingerprint by design (`.moduflow/state/.linkage-warned`), and that stays.

## Workflow Tasks

- [ ] spec → `specs/123-empty-declarations-file-disables-linkage-warning/spec.md`
- [ ] plan → `specs/123-…/plan.md` + `tasks.md`
- [ ] execute → parser reuse, path-scoped exemption, tests
- [ ] review → `specs/123-…/review.md`

## Related Issues

- related: `124-inbox-entries-cannot-be-promoted`,
  `099-vendor-and-host-sync-drift-detection`,
  `096-read-shaped-commands-that-write`

## Next Command

`product:spec 123-empty-declarations-file-disables-linkage-warning`
