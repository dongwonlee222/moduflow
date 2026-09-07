# Issue 137: Non-Latin Titles Collapse The Generated Filename

**Status: backlog** — created 2026-09-06.
**Priority: p2**

## 요약

`slugify` 가 `[a-z0-9]` 밖 문자를 전부 버려서 한글 제목이 파일명에서
사라집니다. `"해외 4곳은 충전소 선택을 어떻게 푸는가"` 는 `4` 가 되고,
ASCII 가 아예 없는 제목은 `untitled` 이 됩니다.

이 저장소에도 실제 사례가 있습니다 — `memory/decisions/2026-09-06-112.md` 와
`2026-09-06-112-2.md`. 내용 검색은 되므로 데이터 손실이 아니라 디렉터리 목록을
색인으로 쓸 수 없게 되는 문제입니다.

## Summary

`slugify` strips every character outside `[a-z0-9]`, so a Korean title
contributes nothing to the generated filename. The same three-line function is
duplicated in `project_knowledge.py:52` and `project_memory.py:70`.

## Source

- Type: found while adopting the tool on a real project, filed in
  `workspace/inbox.md` 2026-09-06
- Owner / decision maker: Dongwon Lee
- **Correction:** the report cites `knowledge/benchmarks/2026-09-06-4.md`. That
  file is not in this repository — it was produced on the reporter's project. The
  behaviour reproduces exactly, and this repo has its own evidence below.

## 안 고치면

한글 제목이 파일명에서 사라져서 나중에 못 찾습니다. — 기록

## Opportunity

Both reported line numbers are correct and the regex is identical:

```python
slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
return slug or "untitled"
```

Called with the reported title it returns `"4"`; with `"측정 조건 정리"` it
returns `"untitled"`. In this repo, `memory/decisions/` holds
`2026-09-06-112.md` and `2026-09-06-112-2.md` — both Korean sentences about issue
112, distinguished only by a collision suffix.

**Correction — the two writers fail differently.** The report says same-day
Korean titles "collide on `<date>-<digit>`". Measured:

| Writer | Behaviour on a repeat name |
| --- | --- |
| `project_memory.py:281-285` | appends `-2`, `-3`, … and writes |
| `project_knowledge.py:199-202` | raises `FileExistsError`, writes nothing |

So knowledge artifacts hard-fail on the second Korean title of the day rather
than colliding. Neither path loses data. Three more copies of the regex exist
(`project_workflow.py:76`, `project_reference_backlog.py:26`,
`project_analysis_run.py:517` as `_slug`).

## Scope

### In

- One shared slug rule that keeps a non-Latin title recoverable — transliterate,
  keep the UTF-8 characters, or hash-plus-frontmatter. Anything but dropping it.
- Apply it to `project_knowledge.py` and `project_memory.py` at minimum, and say
  whether the other three copies adopt it.

### Out

- Renaming artifacts already on disk. A migration is separate.
- Changing the `<date>-` prefix or the collision-suffix mechanism.
- `project_intake.py:235`, a different function with its own domain fallback.

## Known Limit

Fixing the function does not fix existing filenames. `ls knowledge/benchmarks/`
stays partly unreadable until a rename migration runs, and renaming touches ids
referenced in frontmatter.

## Acceptance Criteria

- The reported Korean title produces a name distinguishable from another Korean
  title created the same day.
- A title with no ASCII no longer produces `untitled`.
- Two Korean titles on the same day produce two filenames, with no
  `FileExistsError` on the knowledge path.
- Existing files still resolve; the artifact's frontmatter still carries the full
  title.

## Verification

Unit tests over the slug function with the strings measured above, plus a write
test on each writer creating two Korean-titled artifacts on the same date.

## Entry Points

- `scripts/project_knowledge.py:52` — `slugify`; `:199` builds the filename,
  `:201` raises on collision
- `scripts/project_memory.py:70` — `slugify`; `:281` and `:353` build `base_id`
- `scripts/project_intake.py:235` — in-repo prior art: ASCII tokens with a
  domain-name fallback. Not the proposed fix, but the one slug function here that
  already refuses to emit nothing.

## Scope Fence

Do not solve this by requiring English titles. This is a Korean-first tool.

## Workflow Tasks

- [ ] plan → `specs/<issue>/plan.md`
- [ ] execute → shared slug rule and its call sites
- [ ] review → `specs/<issue>/review.md`

## Related Issues

- related: `131-command-surface-is-too-wide-and-english-only` (same Korean-first
  gap, user-facing side)

## Next Command

`product:plan 137-non-latin-titles-collapse-the-generated-filename`
