# Issue 140: Stop Hook Truncates The Head Of A Traceback

**Status: backlog** — created 2026-09-06.
**Priority: p2**

## 요약

종료 훅이 sync 서브프로세스 실패를 기록할 때 `detail[:300]` 으로 자릅니다
(`hooks/on_stop.py:189`). 파이썬 트레이스백은 예외 타입이 **맨 끝**에 있어서,
앞 300자를 남기면 스택만 남고 정체를 알려주는 줄이 사라집니다.

이슈 125 의 `ValueError` 가 오래 정체불명으로 남았던 이유가 이것입니다. 상한만
올리는 것으로는 해결되지 않습니다 — 남겨야 할 쪽은 꼬리입니다.

## Summary

`hooks/on_stop.py:189` logs the first 300 characters of the failed `--sync`
subprocess's stderr. That subprocess is a Python script, so its stderr on an
uncaught exception is a traceback whose identifying line comes last. The head cap
keeps the stack frames and drops the identity.

## Source

- Type: recorded as still-open in `issues/125-…:57-60` and in `workspace/inbox.md`
- Owner / decision maker: Dongwon Lee
- Evidence: issue 125's `ValueError: dashboard requires an Active Issue section`
  was hit at every session end and stayed unidentified because the log line was
  cut mid-traceback.

## 안 고치면

오류 기록의 앞 300자만 남아서 진짜 원인(맨 끝)이 잘립니다. — 기록

## Opportunity

```python
# hooks/on_stop.py:184-190
detail = (result.stderr or result.stdout or "").strip()
log_line(project_root, "error", f"sync exited {result.returncode}: {detail[:300]}")
```

The subprocess is spawned at `:168-176` as
`[python, project_lifecycle.py, <root>, "--sync"]` with `stderr=PIPE`.

**Correction.** Lines 249 and 265 share the *code pattern* — `detail[:300]` — but
not the defect. Their `detail` is stderr from `git status --porcelain -uall` and
`git rev-parse --abbrev-ref HEAD`, and git puts its identifying text first:
`fatal: not a git repository (or any of the parent directories): .git`, measured
2026-09-06 at 66 characters. A 300-character head cap hides nothing there.
Treating all three as one bug would record an unverified cause.

## Scope

### In

- Keep the tail of the detail at `:189`, since the exception type is at the end —
  or keep both ends with an elision marker, which survives a long git message and
  a long traceback without deciding which shape arrived.
- A test that a fabricated traceback longer than the cap still yields the
  exception type in the log line.

### Out

- **Raising the cap alone.** A larger head is still a head; a traceback longer
  than the new cap loses its identity the same way. The tail is what identifies
  the failure.
- Removing the cap. It exists so a large failure dump does not reach the log or a
  notification channel — the inbox records a 209KB case.
- Lines 249 and 265. Same cap, different payload shape; changing them needs its
  own check of what those commands emit on the failures that occur in practice.

## Known Limit

A tail-only cap loses the first frames, which is where the failing call site is.
For a deep traceback the log will name the exception but not where it was raised,
so it stays a pointer to a reproduction rather than a diagnosis.

## Acceptance Criteria

- A sync failure whose stderr is a 2KB traceback logs a line containing the
  exception type and message.
- The logged line stays bounded — no unbounded detail reaches the log.
- A short stderr (under the cap) is logged unchanged.
- Empty stderr with non-empty stdout still falls back to stdout, as today.
- Lines 249 and 265 are unchanged, or changed with their own recorded reason.

## Verification

Unit test over the log-building path with a fabricated long traceback string and
a short one, in the stop-hook tests.

## Entry Points

- `hooks/on_stop.py:184-190` — the sync failure log line
- `hooks/on_stop.py:168-176` — the subprocess that produces the traceback
- `hooks/on_stop.py:249`, `:265` — same pattern, git payloads, out of scope

## Scope Fence

Change how the detail is trimmed, not whether it is trimmed. Any fix that lets an
arbitrary-length string into the log has traded one failure for a worse one.

## Workflow Tasks

- [ ] execute → tail-preserving trim plus its test
- [ ] review → `specs/<issue>/review.md`

No spec or plan: a one-site log-trimming fix with a test is below the threshold
where a spec adds anything, per the S-grade bugfix exception.

## Related Issues

- related: `125-bootstrap-dashboard-missing-active-issue-section` (the bug this
  truncation hid; it records this defect as out of its own scope),
  `126-sync-refuses-the-drift-it-is-prescribed-for`

## Next Command

`product:execute 140-stop-hook-truncates-the-head-of-a-traceback`
