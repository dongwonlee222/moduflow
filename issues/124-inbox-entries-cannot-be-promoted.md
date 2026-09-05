# Issue 124: Inbox Entries Cannot Be Promoted

**Status: backlog** — created 2026-09-05.
**Priority: p1**

## 요약

`product:promote`는 인박스를 입력 종류로 명시해놓고 실제로는 받지 못합니다. frontmatter 있는 파일 1개 = record 1개를 전제하는데, `workspace/inbox.md`는 frontmatter 없는 파일 하나에 항목이 계속 쌓이는 구조입니다. 그래서 인박스에서 이슈로 가는 경로가 **구조적으로 막혀 있습니다.**

## Summary

`commands/product-promote.md` names `inbox` as one of four promotable record
kinds, but `scripts/project_promote.py` addresses a record as one file with YAML
frontmatter. `workspace/inbox.md` has no frontmatter and holds many entries in
one file, so no inbox entry can be promoted. The documented capture-to-issue path
does not exist for the capture surface most likely to hold new work.

## Source

- Type: found while asking how ModuFlow tracks a bug reported through the inbox
- Owner / decision maker: Dongwon Lee
- Date: 2026-09-05

## Opportunity

Measured on this repository on 2026-09-05:

```
$ python3 scripts/project_promote.py . --record workspace/inbox.md
{"ok": false,
 "errors": ["record has no YAML frontmatter (--- fences required); refusing to promote"]}
```

`product-promote.md` states the rule this blocks:

> Promote a record when the work it describes changes code, a command, or
> policy, or needs execution tracking.

Nearly every inbox entry meets that bar, and none of them can reach it.

The observable cost is in the file. `workspace/inbox.md` currently holds five
unhandled findings — a `product:migrate` dashboard bug, a `product:impact`
reverse-lookup gap, a `canonical_path_guard` generalisation, the numeric-ledger
primitive, and a GitHub mirror drift note. **All five sit under the `## Handled`
heading**, which is where entries land when there is no next step to move them
to. Misfiling is the symptom; the missing path is the cause.

The two record shapes are genuinely different and the fix has to choose:

| | promotable records | inbox |
| --- | --- | --- |
| unit | one file | one entry inside a shared file |
| identity | file path | none — no id, no anchor |
| metadata | YAML frontmatter | prose |
| lifecycle | file gains a link on promotion | entry needs an in-place marker |

## Scope

### In

- One addressable way to name a single inbox entry, and a promote path that
  accepts it.
- Write the issue link back into the entry in place, so the original wording
  survives — the convention `## Handled` already follows.
- Decide and document where an entry that has become an issue lives: marked in
  place, or moved under a heading that means "promoted", not "handled".

### Out

- Rewriting the inbox into one-file-per-entry. That would make promotion trivial
  and destroy the append-and-read-in-one-place property the surface exists for.
- Auto-promotion. The promotion threshold and readiness judgement stay human;
  `product-promote.md` is explicit that a hollow issue is worse than none.
- Reclassifying the five entries already in the file. Do that with the new path
  once it exists, not by hand as part of building it.

## Acceptance Criteria

- A single inbox entry can be named and promoted, and the resulting issue links
  back to it.
- The entry keeps its original wording and gains a marker naming the issue.
- Promotion of a non-promotable entry (not yet shaped) is refused with the same
  readiness language the existing script uses, not a new vocabulary.
- `decision`, `memory` and `knowledge` promotion behaviour is unchanged.
- The five existing entries remain readable and are not silently rewritten.

## Verification

- Fixture inbox with several entries: promote the second, assert only that entry
  is marked and the others are byte-identical.
- Refusal fixture for an unshaped entry.
- Regression over the existing frontmatter record kinds.

## Entry Points

- `scripts/project_promote.py` — the frontmatter requirement
- `commands/product-promote.md` — names `inbox` as a record kind
- `commands/product-inbox.md` — the capture side
- `workspace/inbox.md` — the live surface, five entries misfiled under `## Handled`

## Scope Fence

Do not solve this by making the inbox look like the other record kinds. The
inbox is a single append-only page on purpose; the promote path adapts to it.

## Workflow Tasks

- [ ] spec → `specs/124-inbox-entries-cannot-be-promoted/spec.md`
- [ ] plan → `specs/124-…/plan.md` + `tasks.md`
- [ ] execute → entry addressing, promote path, in-place marker
- [ ] review → `specs/124-…/review.md`

## Related Issues

- related: `123-empty-declarations-file-disables-linkage-warning`,
  `125-bootstrap-dashboard-missing-active-issue-section`

## Next Command

`product:spec 124-inbox-entries-cannot-be-promoted`
