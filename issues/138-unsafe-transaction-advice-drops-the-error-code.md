# Issue 138: Unsafe Transaction Advice Drops The Error Code

**Status: backlog** — created 2026-09-06.
**Priority: p3**

## 요약

트랜잭션 복구 진단이 `unsafe` 로 끝나면 doctor 는 언제나 같은 한 문장을
내놓습니다 — "`.moduflow/transactions` 권한과 control file 을 확인하라".
그런데 `unsafe` 에 도달하는 원인 코드는 열 개고 대부분 권한 문제가 아닙니다.

원인 코드는 JSON 페이로드에는 있는데 사람이 읽는 문장에는 없습니다. 게다가 그
디렉터리는 평상시 비어 있어서 그대로 따라간 운영자는 빈 폴더를 봅니다.
126과 같은 부류입니다 — 알면서 말해주지 않는 도구.

## Summary

When recovery diagnostics return `unsafe`, `project_doctor` emits one fixed
sentence regardless of cause. Ten distinct `error_code` values reach that branch;
the code is present in the JSON payload and absent from the prose the operator
reads. The named directory is correct but empty at rest.

## Source

- Type: found while reviewing diagnostics wording, 2026-09-06
- Owner / decision maker: Dongwon Lee
- **Correction — the reported cause is false and was checked.** The report said
  `project_doctor.py:867` names the wrong directory and that the real journals
  live in `workspace/transactions/`. They do not. Verified chain:
  `project_doctor.py:601` → `inspect_recovery_transactions`
  (`project_lifecycle_transaction.py:3927`) → `discover_recovery_workspaces`
  (`project_lifecycle_transaction_storage.py:573`) → `_open_recovery_transactions`
  (`:510`), which opens `.moduflow` then `transactions`. Journals
  (`_JOURNAL_NAME = "journal.json"`) live in `.moduflow/transactions/<id>/`.
  `workspace/transactions/*.json` is a different artifact — the public canonical
  evidence record written at `project_lifecycle_transaction.py:6297` and `:6410`.
  The diagnostic names the directory it actually reads.

## Opportunity

Three things make the advice unhelpful even though the path is right:

1. `recovery_diagnostics["error_code"]` is dropped **from the sentence**. Nine
   codes come from `_RECOVERY_STORAGE_CODES`
   (`project_lifecycle_transaction_storage.py:25-35`) — including
   `RECOVERY_MANIFEST_MISMATCH` and `RECOVERY_PAYLOAD_INVALID`, which are not
   permission problems — plus `RECOVERY_DIAGNOSTICS_UNAVAILABLE`.
2. `project_doctor.py:600-613` wraps the call in a bare `except Exception`
   (`:607`) that maps *any* failure to `unsafe`.
3. `.moduflow/transactions` is mode `0700` and holds only `lifecycle.lock` and
   in-flight workspaces, so at rest it is empty — confirmed here 2026-09-06. The
   operator sees nothing, while a same-named `workspace/transactions/` sits
   nearby holding 35 files.

## Scope

### In

- Put the `error_code` in the recommendation text.
- Give the permission wording only to codes where permissions are plausible; say
  something accurate for the rest.
- Narrow or classify the bare `except Exception` at `:607`.
- Say that an empty `.moduflow/transactions` is the normal state.

### Out

- Changing recovery behaviour, the storage layout, or either directory name.
- Emitting a recovery command for `unsafe`. Refusing to guess one is correct.
- The `incomplete` branch at `:852`, which already names the transaction id.

## Known Limit

Surfacing the code does not tell the operator what to do per code. Ten codes
would need ten written remedies, and some (`RECOVERY_PAYLOAD_MISMATCH`) may have
no operator-level remedy at all. This makes the report honest, not self-service.

## Acceptance Criteria

- The `unsafe` recommendation contains the `error_code`.
- A permissions-shaped code and a manifest-shaped code produce different text.
- `RECOVERY_DIAGNOSTICS_UNAVAILABLE` is not described as a permission problem.
- The text does not imply an empty `.moduflow/transactions` is a fault.
- `python3 scripts/release_check.py .` passes.

## Verification

Unit tests over the recommendation builder with a fabricated diagnostics dict per
code class, in `tests/test_project_doctor.py`.

## Entry Points

- `scripts/project_doctor.py:865-869` — the `unsafe` recommendation
- `scripts/project_doctor.py:607` — the bare `except Exception`
- `scripts/project_lifecycle_transaction_storage.py:25-35` — the nine codes
- `scripts/project_lifecycle_transaction_storage.py:510` —
  `_open_recovery_transactions`, which resolves the directory

## Scope Fence

Wording and classification only. If a fix requires touching the transaction
storage layer, it has left this issue.

## Workflow Tasks

- [ ] execute → recommendation text and the exception boundary
- [ ] review → `specs/<issue>/review.md`

No spec or plan: a diagnostics-wording fix with unit tests is below the threshold
where a spec adds anything, per the S-grade bugfix exception.

## Related Issues

- related: `126-sync-refuses-the-drift-it-is-prescribed-for` — same class one
  layer up: a refusal that does not help the reader act
- related: `129-issues-may-not-record-an-unproven-cause` — this issue's own
  reported cause was a guess, corrected in `## Source`

## Next Command

`product:execute 138-unsafe-transaction-advice-drops-the-error-code`
