# Issue 139: Five Scripts Have A CLI That Nothing Reaches

**Status: superseded** — 2026-09-07에 닫고, 같은 날 다시 재서 **전제가 틀렸음을 확인한 뒤 닫은 채로 둡니다.** 아래 「2026-09-07 재측정」을 보십시오. 실제로 아무 데서도 안 불리는 것은 **334줄(2개)**이고, 그마저 `config/project-operation-entrypoints.json`에 등록돼 있어 확정이 아닙니다. 이 이슈의 전제("915줄이 죽은 코드")는 성립하지 않습니다.
**Priority: p3**

## 요약

자체 `main()` 과 CLI 를 가졌지만 어떤 커맨드·스킬·훅·스크립트도 부르지 않는
스크립트가 5개, 합계 915줄 있습니다. 파일 존재 목록과 분류 레지스트리, 그리고
자기 테스트에만 이름이 나옵니다.

전부 지우자는 이슈가 아닙니다. 하나씩 **연결할지 · 수동 도구로 문서화할지 ·
삭제할지** 정하는 것이 산출물입니다.

## Summary

Five scripts define a CLI (`main()` plus `if __name__ == "__main__"`) that no
command, skill, hook or sibling script invokes. They appear only in
`validate_moduflow.py`'s file-existence manifest, in
`config/project-operation-entrypoints.json` classification rows, and in their own
tests. None is documented in `docs/`, `README.md`, `AGENTS.md` or `INSTALL.md`.

## Source

- Type: audit of script reachability, 2026-09-06
- Owner / decision maker: Dongwon Lee
- **Correction — the reported list was wrong.** Ten scripts were reported as
  unreachable, ~3,350 lines. Five are reached and were removed; the verified
  figure is **five scripts, 915 lines**.

## 안 고치면

아무도 막히지 않습니다 — 안 불리는 스크립트 915줄이 있어도 동작에 영향이 없습니다. 다만 44,243줄 중 915줄이 죽은 코드라는 건 방향(가볍게)과 어긋납니다. **정리 대상이지 이슈는 아닙니다.**

## 2026-09-07 재측정 — 이 이슈의 숫자는 틀렸습니다

이 이슈를 닫은 뒤, 로드맵 3단계로 **14개를 하나씩 손으로 확인**했습니다.
결과가 세 번 다 달랐고, **마지막 하나만 맞습니다.**

| 언제 | 방법 | 결과 |
|---|---|---|
| 이 이슈 원문 | 정규식 | 5개 / **915줄** |
| 2026-09-07 오전 | 정규식 (범위 넓힘) | 14개 / **6,735줄** |
| 2026-09-07 오후 | 정규식 (실행 경로만) | 13개 / 5,929줄 — `request_routing` 같은 **오늘 직접 배선한 것까지** 고아로 찍음 |
| **2026-09-07 오후** | **손으로 하나씩** | **2개 / 334줄** |

### 왜 세 번 다 틀렸나 — 원인 확인

**이 저장소는 대부분 동적 로드로 잇습니다.** `import X` 도 `python3 X.py` 도
아닙니다:

```
scripts/release_check.py:382
  canonical_path_guard = load_script_module("canonical_path_guard", "scripts/canonical_path_guard.py")

scripts/project_doctor.py:87
  path = Path(__file__).resolve().parent / "project_loop.py"
  spec = importlib.util.spec_from_file_location("project_loop", path)
```

정규식은 이런 것을 못 봅니다. **탐지 방법이 틀렸지 코드가 죽은 게 아니었습니다.**

### 손으로 확인한 14개

| 스크립트 | 줄 | 부르는 곳 |
|---|---:|---|
| `commit_resolution` | 1,186 | `linkage_check` → `release_check` |
| `commit_graph` | 958 | `commit_resolution` |
| `project_operation_audit` | 974 | `release_check` |
| `project_loop` | 793 | `project_doctor` (동적 로드) |
| `spec_kit_pilot` | 762 | `release_check` |
| `mcp_server` | 442 | `.mcp.json` |
| `register_codex_personal_marketplace` | 340 | `project_doctor` 추천 · `docs/` 절차 |
| `capability_routing_simulation` | 305 | `validate_moduflow` 필수 파일 |
| `canonical_path_guard` | 240 | `release_check` — **2026-09-07에 실제로 커밋을 막았다** |
| `sync_spec_kit_templates` | 211 | `validate_moduflow` 필수 파일 |
| `version_bump` | 125 | `release_check` |
| `portfolio_doctor` | 65 | `validate_moduflow` 필수 파일 |
| **`issue_generator`** | **214** | `config/project-operation-entrypoints.json` 에 등록만. 실행 경로 없음 |
| **`telegram_agent_bridge`** | **120** | 같음 |

**12개는 쓰이고 있었습니다.**

### 그래서 이 이슈는 닫힌 채로 둡니다

닫은 이유("아무도 막히지 않는다")는 여전히 맞고, **근거로 든 숫자만 틀렸습니다.**
새 이슈로 만들지 않습니다 — 334줄이 아무것도 막지 않고, 그 둘조차 등록 파일에
이름이 있어 "죽었다"고 단정할 수 없습니다. 판단하려면 그 등록이 무엇을
뜻하는지부터 봐야 하고, 그건 아무도 기다리지 않는 일입니다.

**남기는 교훈**: "안 불린다"는 **탐지 결과이지 사실이 아닙니다.** 이 저장소에서는
동적 로드를 세지 않는 어떤 스캔도 틀립니다. 무엇을 지우기 전에 **손으로
확인하십시오.**


## Opportunity

Confirmed unreached, by grepping each name across `scripts`, `hooks`, `commands`,
`skills`, `workers`, `adapters`, `config`, `templates`, `overlays`, root `*.md`:

| Script | Lines | Only appears in |
| --- | --- | --- |
| `capability_routing_simulation.py` | 305 | manifest, entrypoints row, own test |
| `issue_generator.py` | 214 | entrypoints row, own test |
| `sync_spec_kit_templates.py` | 211 | manifest, two entrypoints rows, own test |
| `telegram_agent_bridge.py` | 120 | entrypoints row only |
| `portfolio_doctor.py` | 65 | manifest, canonical-path-literals row |

Removed from the reported list because they **are** reached:
`project_operation_audit.py` (974, `release_check.py:383-392` calls
`inspect_project`); `spec_kit_pilot.py` (762, `release_check.py:52-58`
subprocess); `canonical_path_guard.py` (240, `release_check.py:382`);
`version_bump.py` (125, `release_check.py:430-432` — the report guessed it was
run by hand, but the release gate invokes it programmatically);
`register_codex_personal_marketplace.py` (340, `project_doctor.py:399` emits it
as an operator recommendation).

## Scope

### In

- Decide per script: wire it up, document it as a manual tool, or delete it.
- Record the decision and its reason so the next audit does not re-derive it.
- For anything deleted, remove its manifest entry and its entrypoints row in the
  same change.

### Out

- Blanket deletion. Three of the five were built to satisfy specs 097, 098 and
  110; deleting them may discard evidence those specs cite.
- The five reached scripts above.
- Building a general dead-code detector. That is issue-shaped on its own.

## Known Limit

For some of these the honest answer to "why was this built" is no longer
recoverable from the repo, so the verdict will be a judgement rather than a
finding. That is a decision to record, not a defect to fix.

## Acceptance Criteria

- Each of the five has a written verdict: wired, documented, or deleted.
- Nothing is deleted while a manifest entry or entrypoints row still names it.
- `python3 scripts/release_check.py .` passes after each verdict is applied.
- Any script kept as a manual tool is named in a document a reader would find,
  not only in a test.
- A re-run of the reachability check finds no unreached CLI, or names the ones
  deliberately kept.

## Verification

Re-run the reachability grep across the executable and config directories and
compare against the recorded verdicts. `release_check.py` is the regression guard
for deletions, because it runs `project_operation_audit`.

## Entry Points

- `scripts/capability_routing_simulation.py`, `scripts/issue_generator.py`,
  `scripts/sync_spec_kit_templates.py`, `scripts/telegram_agent_bridge.py`,
  `scripts/portfolio_doctor.py`
- `scripts/validate_moduflow.py:84`, `:87`, `:194` — the existence manifest
- `config/project-operation-entrypoints.json:5`, `:6`, `:97`, `:107-108`
- `scripts/project_operation_audit.py:828` — `inspect_project`; `:877` computes
  `stale_entries`, `:932` folds them into `errors`, `:942` sets
  `valid = not errors`

## Scope Fence

`project_operation_audit.inspect_project` cross-checks the entrypoints config
against an AST scan of `scripts/`, a stale entry becomes an error, and
`release_check.py:392` gates on that result. Verified 2026-09-06: deleting a
script without deleting its row turns a passing release gate red. Delete the
script, the manifest entry and the row together, or not at all.

## Workflow Tasks

- [ ] plan → `specs/<issue>/plan.md` + `tasks.md`
- [ ] execute → apply the five verdicts
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- related: `131-command-surface-is-too-wide-and-english-only` (the visible
  surface; this is the invisible one)

## Next Command

`product:plan 139-five-scripts-have-a-cli-that-nothing-reaches`
