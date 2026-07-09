---
description: Promote a capture record (decision/inbox/memory/knowledge) into a Git-native issue.
argument-hint: "<record-path> [--issue-id id] [--write]"
---

# /product:promote

Convert an existing record into an issue when the work crosses the promotion threshold. Records never move — links are written both ways automatically.

## When Promotion Is Required

Promote a record when the work it describes:

- changes code, a command, or policy (`commands/*.md` classify as behavior, not docs), or
- needs execution tracking (assignee, branch, review, release gate).

A decision with no code change is terminal — it never requires promotion.

## When Promotion Is Ready

Readiness = "the issue works as an AI prompt":

- scope is known,
- acceptance checks are verifiable,
- entry points (starting files) are known.

If promotion is **required but not ready**, shape the record first (UPDATE it with scope, checks, entry points) — do NOT create a hollow issue. Early unshaped issues measurably lower agent merge rates. The script marks underivable sections `TODO(blocking-execution)`; an issue with those markers is not executable yet.

## Script

Dry-run first (prints the planned issue JSON, writes nothing):

```bash
python3 scripts/project_promote.py . --record memory/decisions/2026-07-06-use-issue-less-context-tiers.md
```

Apply:

```bash
python3 scripts/project_promote.py . --record memory/decisions/2026-07-06-use-issue-less-context-tiers.md --write
```

Reference-improvement entries live in `workspace/reference-improvements.md`.
Promote them only after shaping the entry into an executable record with scope,
checks, and entry points; do not treat every captured reference suggestion as
issue-worthy by default.

Options:

- `--issue-id <id>`: explicit issue number or full id (default: next `NNN` in `issues/` + kebab-case title slug)
- `--date <YYYY-MM-DD>`: source date for the issue (default: record `date`)

## What The Script Writes (both directions, automatically)

- `issues/<id>.md` from `templates/issues/issue.md`: summary/source prefilled from the record, `Promoted-from: <record-id>` under Source, and the AI-first sections (`Verification`, `Entry Points`, `Scope Fence`) derived from record fields where possible, else `TODO(blocking-execution)`.
- `promoted_to: <issue-id>` inserted into the record frontmatter **in place** — the record file is never moved, renamed, or rewritten beyond that one line.

Do not write these links by hand — manual linking gets skipped.

## Refusals (no writes)

- record already has a non-empty `promoted_to` (promote once; supersede with `superseded_by` if the record itself is outdated)
- record has no YAML frontmatter (fix the record per the capture command contracts first)
- target issue file already exists

## Next

- `/product:spec <issue-id>` to shape the promoted issue
- `/product:roadmap` when the promotion changes priority
