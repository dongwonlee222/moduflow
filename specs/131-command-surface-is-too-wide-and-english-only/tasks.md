# Tasks: Command Surface Is Too Wide And English Only — Stage 1

Issue: 131-command-surface-is-too-wide-and-english-only

## Ready

- [ ] 없음 — 1단계 작업은 모두 끝났습니다.

## In Progress

- [ ]

## Done

- [x] T01 — `tests/test_command_surface_stage1.py`, 17 tests, recorded RED at 59
      subtest failures before any code change
- [x] T02 — `user-invocable: false` on the 29 hidden commands
- [x] T03 — `user-invocable: false` on the 7 hidden skills
- [x] T04 — the 11 visible `description` lines rewritten Korean-first
- [x] T05 — a `## 사용 예시` section on each of the 11, one Korean and one
      English invocation
- [x] T06 — `## Argument Resolution` in `commands/moduflow.md`: exact match on
      `product-<arg>.md`, then `<arg>.md`, then natural-language routing
- [x] T07 — hub quick list rewritten to the eleven, grouped by when each is used
- [x] T08 — the five Korean display labels in `commands/product-decision.md`
- [x] T09 — one-sentence intake, at most one follow-up question
- [x] T10 — `## Next Command` lines in `commands/` and `templates/` switched to
      `/moduflow <name>`
- [x] T11 — full suite 1905 OK, `release_check.py` valid, both manifests 0.3.68

## Blocked

- [ ] Stage 2 — the nine Korean/English phrase pairs. Blocked on issue 104,
      which owns routing and follows 112. Not startable in this pass.
- [ ] The one criterion that matters — the owner completing a decision, a memory
      write and a status check without consulting a command list. Cannot be
      automated; waiting on him to try it.
