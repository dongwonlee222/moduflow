# Issue 139: Five Scripts Have A CLI That Nothing Reaches

**Status: backlog** — created 2026-09-06.
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
