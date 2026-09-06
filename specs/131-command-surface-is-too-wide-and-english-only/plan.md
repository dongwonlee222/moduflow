# Plan: Command Surface Is Too Wide And English Only — Stage 1

Issue: 131-command-surface-is-too-wide-and-english-only

## Approach

Four changes, in this order, each with its test written first.

1. **Hide 29 commands and 7 skills** by adding one `user-invocable: false` line
   to existing frontmatter. Verified mechanism, spec section "Mechanism". No file
   moves, renames or deletions.
2. **Rewrite the 11 visible descriptions in Korean-first form**, each carrying an
   English action word, a Korean input example and an English input example. The
   owner asked for this explicitly on 2026-09-06: "설명하고 어떻게 사용하는지
   예시도 넣어두라고". The `description` frontmatter holds the one-line Korean
   summary; the examples live in a `## 사용 예시` section in each file and in the
   hub's quick list.
3. **Teach the hub to dispatch on its first argument** — `/moduflow inbox` reads
   `commands/product-inbox.md` and follows it. This must land in the same change
   as step 1, or hiding becomes removing.
4. **Replace the five field names with Korean display labels** at every point a
   reader sees them, and make `product:decision` accept one sentence.

Steps 1 and 3 are the reported complaint. Steps 2 and 4 are what make the
remaining menu usable rather than merely short.

## Work Streams

- PM: the visible list is settled (spec R1, confirmed by the owner 2026-09-06).
  Copy review of the eleven Korean descriptions stays with the owner.
- Design: none — this is a text surface.
- Data: none. No stored key changes; a test asserts it.
- Implementation: frontmatter edits across 36 files, one `## 사용 예시` section
  in 11 files, hub dispatch rules in `commands/moduflow.md`, display labels
  wherever `project_memory.py` output reaches a reader, one-sentence intake in
  `commands/product-decision.md`.
- QA: tests below, written RED first.
- Release: version bump and `release_check.py`. Behaviour commits carry an
  `Issue:` trailer.

## Verification

Written before the code, each asserted to fail first.

- `test_command_visibility_split` — exactly 29 named commands carry
  `user-invocable: false`, exactly 12 do not. Named sets, so a new command
  without a visibility decision fails the suite.
- `test_skill_visibility_split` — 7 hidden, 4 listed, same shape.
- `test_no_command_was_renamed` — the command filename set matches a frozen
  literal; any addition, removal or rename fails.
- `test_memory_record_schema_unchanged` — the stored keys match a frozen literal.
- `test_every_command_reachable_through_hub` — all 41 names resolve through the
  hub's documented rule, including the 29 hidden ones.
- `test_issue_and_issues_are_distinct` — the resolution order does not collapse
  them.
- `test_visible_commands_are_korean_first` — each of the 11 has a `description`
  starting with Hangul and a `## 사용 예시` section containing one Korean and one
  English example line.
- `test_no_bare_field_names_in_user_facing_output` — `rationale`,
  `alternatives`, `caveats`, `retrieval_trigger`, `evidence` never appear as bare
  field names in reader-facing strings.
- `test_one_sentence_decision` — a fixture with a recoverable reason asks nothing;
  one without asks exactly one question.
- `python3 scripts/release_check.py .`, `valid` checked at the top level.

Not automatable, and stated so it is not mistaken for covered: whether the host
actually renders the shortened menu. The tests assert the frontmatter this
repository controls; the mechanism itself was verified by reading the host
binary and is recorded in the spec.

## Rollback

Every change is additive text in tracked Markdown. `git revert` of the execute
commit restores the 41-entry menu exactly; nothing was moved or deleted, so there
is no data to restore and no migration to undo.

The one non-revertible effect is habit: once the owner learns `/moduflow inbox`,
reverting brings back a menu he has stopped reading. That is an argument for
getting the eleven descriptions right, not for hesitating on the mechanism.

## Next Command

`/product:execute 131-command-surface-is-too-wide-and-english-only`
