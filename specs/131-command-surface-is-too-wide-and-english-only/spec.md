# Spec: Command Surface Is Too Wide And English Only — Stage 1

Issue: 131-command-surface-is-too-wide-and-english-only

Stage 1 only. The nine Korean/English phrase pairs are stage 2 and wait on issue
104, per the sequencing section of the issue. Nothing here builds a router.

## Problem

The `/` menu lists 41 commands and 11 skills, every one described in English
using the product's internal vocabulary. The owner, who commissioned the product
and uses it daily, cannot pick from it. A human-in-the-loop product whose human
cannot read its own surface has failed at its premise.

Counts verified on this repository and on the installed plugin cache at
`~/.claude/plugins/cache/moduflow/moduflow/0.3.65`: 41 files in `commands/`,
11 directories in `skills/`. The installed copy carries the same 41 and 11, so
this is what the owner actually sees.

## Users

The owner, reading a `/` menu he did not write, deciding what to run next.
Secondary: anyone adopting ModuFlow who meets the menu before the product.

## Mechanism — verified, not assumed

Claude Code recognises a `user-invocable` key in command and skill frontmatter.
Its own schema description, read from the shipped binary at
`~/.local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe`:

> `user-invocable`: "If false, hides the slash command from users; only the
> model can invoke it via the Skill tool."

Two code paths confirm the two halves:

- **Menu listing.** `function tfs(e){return e.userInvocable!==!1 && !Tk(e)}`,
  used by `hSt` → `NY` to build the listed set. `false` filters the entry out.
- **Direct typing.** `if (s.userInvocable === !1) return f(d,
  "cmd_not_user_invocable"), {...  "This skill can only be invoked by Claude,
  not directly by users. Ask Claude to use the \"<name>\" skill for you." }`

The complete recognised frontmatter key list in that binary is `name`,
`description`, `model`, `allowed-tools`, `argument-hint`, `arguments`,
`disable-model-invocation`, `user-invocable`, `effort`, `shell`, `version`,
`when_to_use`, `paths`, `hooks`, `context`, `agent`, and others not relevant
here. `disable-model-invocation` is the mirror image and is **not** what this
spec uses.

**Consequence, approved by the owner 2026-09-06:** a hidden command can no
longer be typed as `/moduflow:product-<name>`. The owner's words: "moduflow
knowledge 최근 형태만 나두자고" — keep only the new form. This is the concrete
price of the compatibility promise the issue already dropped.

**What this buys:** no file is moved, renamed, or deleted. The change is one
frontmatter line per hidden command.

## Goals

- The `/` menu lists `/moduflow` plus eleven commands, each with a Korean-first
  description.
- `/moduflow <name>` reaches every one of the 41 commands, hidden ones included.
- Five internal field names never appear on screen as themselves.
- `product:decision` accepts one sentence and asks at most one question.
- Nothing is renamed, moved, or deleted.

## Non-Goals

- The nine Korean/English phrase pairs and the five single English words. Stage
  2, after issue 104. Building them here writes the router 104 owns.
- Deleting the 29 hidden command files. They keep working through the hub. A
  later cleanup may remove them; this spec does not.
- Whether a decision, once written, can be read. Issue 130.
- Translating stored artifacts, and the Korean-summary coverage gap.
- Final wording of every label. The owner reviews copy.

## Requirements

### R1 — Menu policy, chosen by what a person does

The issue's ten were picked by artifact type. The owner corrected that on
2026-09-06: "골이나 로드맵 등 써야 할 것들도 있는 거 아니야? 사용자가 해야 할
것들?" `goal` and `roadmap` are things a human *writes*, and they were hidden.

The list is therefore ordered by the sequence a person actually moves through:

| When | Commands |
| --- | --- |
| Once, at adoption | `start` `goal` `roadmap` |
| Every day | `status` `loop` `inbox` |
| Per issue | `issue` … `release` |
| As it comes up | `decision` `memory` `doctor` |

Twelve entries stay listed: `moduflow` plus

`product-start` · `product-goal` · `product-roadmap` · `product-status` ·
`product-loop` · `product-inbox` · `product-issue` · `product-decision` ·
`product-memory` · `product-doctor` · `product-release`

`spec`, `plan`, `execute` and `review` are **not** listed. They are the four
stages of one workflow and `product:loop` selects and runs the next one; a
person picking a stage by hand is working around the loop, not using it. This
also resolves the incoherence of listing two of the four, which the earlier
draft carried.

`benchmark` leaves the list: it is a research verb used occasionally, not part
of any of the four rows above.

The other 29 get `user-invocable: false` added to their existing frontmatter,
below `argument-hint`. Nothing else in those files changes:

`analyze` `benchmark` `converge` `dashboard` `design` `evidence` `execute`
`handoff` `issues` `knowledge` `migrate` `opportunity` `plan` `portfolio` `pr`
`production` `profile` `projects` `promote` `prototype` `report` `research`
`review` `risks` `spec` `sync` `update` `weekly` `workers`

### R2 — Four items on every visible entry

Each of the eleven carries a short Korean-first `description`, an English action
word for recognition, a Korean input example, and an English input example. The
`description` frontmatter field holds the Korean-first line; the examples go in
the body and in the hub's quick list.

### R3 — `/moduflow <name>` dispatch

`commands/moduflow.md` gains an explicit rule: when the first argument matches a
command name with or without the `product-` prefix, read
`commands/product-<name>.md` and follow it, passing the remaining arguments.
This is the hub dispatching on its argument — no new command file is created.

Resolution order, so `/moduflow issue` and `/moduflow issues` stay distinct:
exact match on `product-<arg>.md` first, then exact match on `<arg>.md`, then
the existing natural-language routing. No fuzzy matching; an unmatched first
argument falls through to routing rather than guessing.

### R4 — Display labels

Never show these keys to a reader. Stored keys are untouched.

| Stored key | Shown |
| --- | --- |
| `rationale` | 왜 이렇게 정했나요? |
| `alternatives` | 다른 선택은 무엇이었나요? |
| `reversal_conditions` | 언제 이 결정을 뒤집나요? |
| `retrieval_trigger` | 언제 다시 살펴보면 될까요? |
| `evidence` | 참고한 자료가 있나요? |

Owned by this issue; issue 130 cites them.

### R5 — One-sentence decision

`/moduflow 결정으로 남겨줘: 로그인은 이메일부터` produces a complete record.
Issue, reason, alternatives and evidence are inferred from the conversation and
the project's documents first. Exactly one question is asked, and only when the
reason is genuinely unrecoverable: `이 선택을 한 가장 큰 이유가 무엇이었나요?`

### R6 — Skills

Same treatment, same mechanism. Listed: `index`, `progress-dashboard`,
`roadmap-management`, `business-plan`. Hidden with `user-invocable: false`:
`data-analysis-bridge`, `design-prototype-bridge`, `git-native-artifact-model`,
`pm-execution-router`, `source-adapter-policy`, `spec-kit-validation-bridge`,
`superpowers-execution-bridge`.

A hidden skill is still loadable by the model, which is how the bridges are
reached today. None of them is meant to be typed.

## Acceptance Criteria

- Exactly 29 command files carry `user-invocable: false` and exactly 12 do not.
  A test asserts both sets by name, so adding a command without deciding its
  visibility fails.
- Exactly 7 skills carry `user-invocable: false` and exactly 4 do not, asserted
  the same way.
- The command filename set is byte-identical to the current one. A test compares
  it and fails on any addition, removal, or rename.
- No stored key changes. A test compares the memory record schema against the
  current one.
- Each of the eleven visible commands has a `description` whose first character is
  Hangul, and carries both a Korean and an English input example.
- `/moduflow <name>` reaches its handler for all 41 names, asserted one by one.
  Hiding must never become removing.
- `/moduflow issue` and `/moduflow issues` reach different handlers.
- No test asserts the `product:<name>` typed form. Its removal is intended.
- No user-facing string contains `rationale`, `alternatives`, `reversal_conditions`,
  `retrieval_trigger` or `reversal_conditions` as a bare field name.
- `product:decision` produces a complete record from one sentence on a fixture
  where the reason is recoverable, and asks exactly one question on a fixture
  where it is not.
- Every `## Next Command` line in `commands/` and `templates/` uses
  `/moduflow <name>`.
- The owner completes one decision, one memory write and one status check
  without consulting a command list. This is the only criterion that matters and
  it is checked by asking him.
- `python3 scripts/release_check.py .` passes, `valid` checked at the top level.

## Verification Strategy

- Fixture asserting the 30/11 and 7/4 splits by explicit name list.
- Fixture invoking all 41 names as `/moduflow <name>`.
- Fixture on the filename set and the memory record schema, asserting no rename.
- Fixture pair for the one-sentence decision: recoverable reason → no question;
  unrecoverable → exactly one.
- A scan of user-facing strings for the five bare field names.
- Manual: hand the menu to the owner.

Automated coverage cannot prove the menu renders correctly — that is the host's
behaviour, not this repository's. The tests assert the frontmatter this product
controls; the mechanism itself is verified above by reading the host binary.

## Risks

- **The mechanism is host-specific.** `user-invocable` is a Claude Code key.
  Codex ships from `.codex-plugin/plugin.json` and its handling is **확인 못 함**
  — not verified. If Codex ignores the key, its surface stays at 41. That is a
  degradation, not a break, and it must be stated in the plan rather than
  assumed away.
- **A hidden command is one the owner cannot type in a hurry.** Mitigated by
  `/moduflow <name>`, and only by that. If R3 is incomplete, R1 has removed
  capability rather than hidden it. R3 must land in the same change as R1.
- **439 `product:*` references** exist across `commands/`, `skills/` and `docs/`.
  Rewriting the `## Next Command` lines is in scope; the prose references are
  not, and the two will disagree until a later pass. Stated so the disagreement
  is a known state rather than a discovered defect.

## Open Questions

- **Confirm the twelve in R1.** The list changed from the issue's ten after the
  owner pointed out that `goal` and `roadmap` are authoring steps a person must
  perform. R1 states the reasoning; the owner reviews the names. One edit to
  change.
- Whether Codex honours `user-invocable`. Answer before the plan commits to a
  single mechanism for both hosts.

## Findings From This Pass — Not In Scope, Recorded So They Are Not Lost

Measured while choosing the list. None of these is fixed here.

- **Three different things are called "dashboard."** `workspace/dashboard.md`
  (progress), `product:dashboard` (the decision-graph dashboard, backed by
  `project_memory.py`), and the terminal dashboard `product:status` renders
  (`commands/product-status.md:114`). A person asking "show me the dashboard"
  can mean any of the three. This is a naming defect and deserves its own issue.
- **`product:start` has no script.** Verified twice: no file in `scripts/`
  matches `start` or `init`, and `commands/product-start.md` contains no script
  reference of any kind. It is the verb a person reaches for when setting a
  project up, and it is prose an agent interprets while the deterministic path is
  filed under `migrate`. Issue 141 owns this.
- **Thirteen commands reference no script at all**: `goal`, `roadmap`, `spec`,
  `issues`, `start`, `analyze`, `risks`, `design`, `update`, `weekly`,
  `evidence`, `prototype`, `opportunity`. For `goal`, `roadmap` and `spec` that
  is correct — they are authoring commands where the human writes and the tool
  guides. For the others it is unexamined. **No claim is made here that any of
  them is redundant.**
- **Eighteen groups of commands share a script**, the largest being
  `project_knowledge.py` (benchmark, decision, knowledge, report, research) and
  `project_memory.py` (dashboard, knowledge, memory, review). A shared storage
  layer under distinct verbs is the correct shape, not duplication. Establishing
  real overlap needs a measurement of user *intent*, which has not been done.
  Consolidation is deliberately not folded into this issue.
- **GitHub coverage is narrower than it looks.** `.moduflow/config.json` sets
  `github_sync: "optional"`; `project_github_issues.py` is one-way
  (git file → GitHub Issue, `--sync`) and never reads back. `product:status`
  reports remote ahead/behind through `project_sync.py`. Pull-request state and
  CI results are not checked anywhere in status.

## Next Command

`/product:plan 131-command-surface-is-too-wide-and-english-only`
