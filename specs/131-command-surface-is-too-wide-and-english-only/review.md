# Review: Command Surface Is Too Wide And English Only — Stage 1

Issue: 131-command-surface-is-too-wide-and-english-only

Stage 1 only. Stage 2 (the nine Korean/English phrase pairs) is blocked on issue
104 and is not reviewed here. The issue therefore stays open.

## What shipped

`559a605`. 63 files: 29 commands and 7 skills hidden with one frontmatter line,
11 commands rewritten Korean-first with a `## 사용 예시` section, the hub given
an `## Argument Resolution` section and a rewritten quick list, `product:decision`
given one-sentence intake and the five display labels, `## Next Command` lines
across `commands/` and `templates/` switched to `/moduflow <name>`, and both
manifests bumped to 0.3.68.

## Did it work

- 17 new tests in `tests/test_command_surface_stage1.py`, all green. They were
  written first and recorded RED at 59 subtest failures.
- Full suite: 1905 tests, OK, 282s. Run again after the documentation pass, same
  result.
- `python3 scripts/release_check.py .` → `valid: true`, zero failing gates.
- `git diff --stat`: no file under `scripts/` changed, and no state file changed.

## What the tests actually protect

The load-bearing pair is `test_exactly_the_named_commands_are_hidden` and
`test_every_command_is_reachable_through_the_hub`. The first is only legitimate
while the second passes; if reachability regresses, the first has removed
capability rather than narrowed a menu. They are in the same file for that
reason.

`test_a_new_command_must_declare_its_visibility` fails when a command is added
without deciding whether it is listed. That is deliberate friction — the defect
this issue fixes is a surface that grew from 7 to 41 without anyone deciding.

## Three things found while doing it, all corrected

- **`caveats` does not exist.** The issue's display-label table listed it, and
  `commands/product-decision.md` listed it as a required field. It appears in
  neither `scripts/project_knowledge.py` nor `scripts/project_memory.py`. It was
  a documented field written by nothing. Replaced with `reversal_conditions`,
  which decision records actually carry, in the issue, the spec, the test and
  the command.
- **The first "which commands are real" measurement was wrong.** A grep for
  inline `python3 scripts/*.py` reported `loop` and `inbox` as prose-only; they
  call `project_intake.py` in a shape that grep missed. Re-measured before any
  of it reached an artifact.
- **Inline YAML comments were removed from the frontmatter.** The first pass
  wrote `user-invocable: false  # 131: ...`. Valid YAML, but the host's parser
  behaviour with a trailing comment was not verified, and a misparse would
  silently un-hide all 36. The rationale lives in the spec instead — one place,
  not 36.

## Known gaps, stated rather than discovered later

- **Codex is unverified.** `user-invocable` is a Claude Code key. Whether
  `.codex-plugin` honours it is 확인 못 함. If it does not, Codex still shows 41.
  A degradation, not a break.
- **The menu render is not covered by any test.** The tests assert the
  frontmatter this repository controls. The mechanism was verified by reading
  the host binary's own schema description and two of its code paths; that
  evidence is in the spec, not in a test, because this repository cannot execute
  the host's menu.
- **439 `product:*` references remain in prose.** Only `## Next Command` lines
  were converted. Notation will disagree until a later pass.
- **Two commands write "decisions".** `product:decision` calls
  `project_knowledge.py --kind decision`; the decision records written this
  session went through `project_memory.py --kind decision`. Two stores, one
  word. This is the first overlap in this product measured by intent rather
  than by a shared import, and it is a candidate for the consolidation issue
  that does not exist yet. Not fixed here.

## The criterion that has not been checked

The acceptance criteria say the owner should complete one decision, one memory
write and one status check without consulting a command list, and that this is
the only criterion that matters. It cannot be automated and has not been done.
Until he tries it, this issue is shipped, not proven.

## Next

`/moduflow loop` — stage 2 stays blocked on 104.
