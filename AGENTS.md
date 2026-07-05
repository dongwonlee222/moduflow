# AGENTS.md — ModuFlow Output Format Convention

This file is read natively by Antigravity (v1.20.3+), Claude Code, and Codex CLI. It governs how any of them writes ModuFlow artifacts (issues, specs, plans, PR/review notes, commit messages) and chat-facing status output.

Goal: not one mandated visual style, but a shared **situation → shape** mapping, so the same kind of content looks the same regardless of which tool wrote it. See `knowledge/benchmarks/2026-07-05-cross-agent-output-format-benchmark.md` for the evidence behind this, and `specs/060-cross-agent-output-format-convention/spec.md` for the full spec.

## Situation → Shape

| Situation | Shape | Why |
|---|---|---|
| Snapshot of fixed fields (project, branch, phase) | Box panel or table | Fixed-width alignment is glanceable; a table beats prose when the same fields repeat |
| N comparable items where the reader must decide something | Numbered/bulleted list, inline status badges (`` `id` `` `(state → state)`), bold label before each explanation (`**내용**:`), closing recommendation, then a direct question | Reader skims badges/labels and only reads prose for the item they care about |
| Task already done, reader just needs to confirm | Flat labeled sections (e.g. `변경:`, `검수:`), no closing question | Nothing to decide — end on the last verification fact, not a prompt |

Don't force one shape onto all three situations. A status snapshot forced into a decision-list format buries the fields; a completed-task report forced into a question format asks the reader something that was never in doubt.

## Shared Baseline (all situations)

1. **Bottom-line first.** State the result/status in the first line; explain after.
2. **Label before explanation.** A table header, a bold badge, or a `key:` prefix — the reader should know what a line is about before reading its content.
3. **Tables/checklists need 2+ comparable fields.** Don't reach for a table to describe one item.

## Whitespace Rhythm

Spacing is a signal, not decoration:

- Always one blank line after a header, before its content.
- **Loose list** (blank line between items) when each item carries a nested, multi-line explanation — one visual block per item, so the eye has somewhere to rest between items.
- **Tight list** (no blank lines) when items are flat, single-line facts with nothing nested — density is fine when there's nothing to separate.
- An extra blank line, or a `---` rule, between unrelated sections — signals "topic changed," not just "next item."
- A `---` rule before a closing recommendation or question — visually separates "information" from "the thing you're being asked."

## Worked Example: Before / After

**Before** (no shared convention — this actually happened across issues `001`–`040`, three incompatible status conventions in the same repo):

```
## Lifecycle
- Phase: done
```
```
(no status field at all)
```
```
**Status: done** — created 2026-07-01, started 2026-07-01, done 2026-07-01.
```

`project_lifecycle.py`'s parser only recognizes the third form, so the first two were silently read as `backlog` — misreporting roughly 20 already-completed issues.

**After** (this convention applied — one form, everywhere):

```
**Status: word** — created <date>, started <date>, done <date>.
```

Same rule generalizes beyond status lines: pick one shape per situation (see table above) and use it every time that situation recurs, so both humans and parsers can rely on it.

## Non-Goals

- This file does not define artifact-to-artifact sync rules between Antigravity's native files (`task.md`, `implementation_plan.md`) and ModuFlow's Git files — see `issues/029-antigravity-artifact-sync-connector.md`.
- This file does not define Korean/English language rules — see `issues/049-bilingual-artifact-view.md` and `issues/057-korean-human-review-packet.md`.
- This file does not retroactively migrate legacy issues `001`–`040` to the current `Status:` line format.
