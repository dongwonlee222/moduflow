---
kind: benchmark
title: Cross-Agent Output Format Benchmark
issue_id: 060-cross-agent-output-format-convention
spec:
decision_supported: A single project-root AGENTS.md as the shared output-format convention read natively by Antigravity, Claude Code, and Codex
date: 2026-07-05
confidence: medium
sources:
  - https://www.conventionalcommits.org/en/v1.0.0/
  - https://blog.buildbetter.ai/agents-md-complete-guide-for-engineering-teams-in-2026/
  - https://antigravitylab.net/en/articles/antigravity/antigravity-2026-features-april
  - https://antigravity.google/docs/agent-manager
  - https://agentpedia.codes/blog/user-rules
---

# Cross-Agent Output Format Benchmark

## Question

How should ModuFlow make Antigravity, Claude Code, and Codex present issue/status output the same way, given they currently improvise independently and the user has to relearn three different "reading habits"?

## Current Gap

Each of the three tools already has a distinct, internally-consistent style (see "Observed Styles" below), but nothing declares which style fits which situation, and there is no single file all three tools are guaranteed to read. The `001`–`040` issue-schema drift (three incompatible `Status`/`Phase` conventions, discovered while working `059-auto-fetch-in-repo-sync`) is the direct evidence: without a shared convention doc, each agent/session invents its own.

## Observed Styles (user-supplied, 2026-07-05)

### Antigravity

- Numbered section headers with an emoji per section (`2. 📝 개발 완료 및 승인 단계`).
- Bulleted items with inline code-styled badges for IDs and state transitions: `` `056-...` `` `(backlog → done 예정)`.
- Nested sub-bullet with a **bold label prefix** (`**내용**: ...`) before the explanation — labels the sentence before you read it.
- Closes with a bolded **추천 경로** (recommended path) paragraph, then a direct yes/no question ("해당 브랜치로 전환할까요?").
- **Vertical rhythm is deliberate, not incidental** (user confirmed 2026-07-05: this was designed, not just a structural choice):
  - Blank line after every section header, before the first sentence.
  - **Loose list** (blank line between items) when each bullet carries a nested multi-line sub-bullet — one visual "block" per item, so eye can rest between blocks.
  - **Tight list** (no blank lines) when items are single-line facts with no nested content (the plain backlog list) — density is fine when there's nothing to separate.
  - Extra vertical gap (more than one blank line) between unrelated sections (e.g. before a new numbered section) — signals "topic changed," not just "next item."
  - A horizontal rule (`---`) before the closing recommendation block — visually separates "information" from "the decision being asked of you."
- Strength: scanability for a *decision* — the reader can skim badges/labels and only read prose for the one item they care about; the whitespace rhythm does half of that work before the reader even parses the words.

### Claude Code (this session)

- Box-drawing ASCII panel (`╭─ 🧭 ... ─╮`) for a fixed-shape status snapshot (project/branch/phase).
- Tables for anything with 2+ comparable fields across rows.
- Emoji as a status semaphore (🟢/🟡/🔴/⚪), not decoration.
- Strength: fixed-width alignment makes a snapshot glance-able; a table beats prose when the same 3 fields repeat across N items.

### Codex

- Opens with a one-line declarative result ("경기 연천 처리 완료했습니다.") — no header, no preamble.
- Two flat labeled sections, `변경:` and `검수:`, each a short list of file-links and bare numeric facts (`추가승용 비율: 0.95`, `pokit-doctor 통과: pass 62 / fail 0 / warning 3`).
- No closing question — ends on the last verification fact.
- Strength: fastest to read when the task is *already done* and the reader only needs to confirm what changed and that checks passed — no decision is being asked of them.

## External Patterns

### AGENTS.md as a cross-tool convention file

By 2026, `AGENTS.md` at a project root is read natively by Claude Code, OpenAI Codex CLI, Cursor, Aider, Devin, GitHub Copilot, Gemini CLI, Windsurf, and Amazon Q. Antigravity added native `AGENTS.md` support in v1.20.3 (2026-03-05); when both `AGENTS.md` and `GEMINI.md` exist, `GEMINI.md` overrides on conflicting rules but `AGENTS.md` is still read as the shared foundation. This is a materially different position than ModuFlow was in when `029-antigravity-artifact-sync-connector` was scoped (2026-06-19): back then, "how do we get one file all three tools read" had no clean answer. Now there is one.

Relevant pattern for ModuFlow: a single `AGENTS.md` at the moduflow project root, not per-tool docs, is the highest-leverage place to state output-format rules — every one of the three tools in this benchmark reads it without a connector or sync step.

### Conventional Commits

`type(scope): short description` is now expected by AI coding assistants specifically because it's parseable, not just readable — commit history becomes a changelog input, not only a log. The generalizable rule: a format convention pays off more when it's cheap for a downstream *program* to parse (matches ModuFlow's own `Status:` line pattern in issues).

### BLUF (bottom-line-up-front)

Not tool-specific, but present in all three observed styles above (Antigravity's 추천 경로, Codex's opening completion line, Claude's phase line first). Confirms it's already the de facto shared instinct — just not written down anywhere all three tools read.

## Recommended ModuFlow Shape

Don't force one visual style (box art vs numbered list vs flat labeled section) — each fits a different *situation*, not a different *tool*:

| Situation | Best-fit shape | Seen in |
|---|---|---|
| Snapshot of fixed fields (project/branch/phase) | box panel or table | Claude |
| N comparable items needing a decision | numbered/bulleted list with inline status badges + closing recommendation + question | Antigravity |
| Task already done, reader just confirms | flat labeled sections (`변경:`/`검수:`), no closing question | Codex |

The convention doc (`AGENTS.md`) should codify the **situation → shape** mapping above, not pick a single winner. It should also state the three things all three already share by instinct: bottom-line-first, label-before-explain (bold key before prose, whether that's a Markdown table header, a bold badge, or a `key:` line), and **deliberate whitespace rhythm**:

- blank line after a header, before content
- loose list (blank line between items) when items carry nested/multi-line content; tight list (no blank lines) when items are single flat facts
- an extra blank line or a `---` rule between unrelated sections/blocks, especially right before a closing recommendation or question

This last point was missing from the first draft of this benchmark — spacing was treated as incidental formatting rather than a designed part of the Antigravity example. It is not decoration; it is what lets a reader tell "one item" from "the next item" and "information" from "the ask" without re-reading.

## Decision

Scope `060-cross-agent-output-format-convention`'s deliverable as a project-root `AGENTS.md` (not a `docs/` sub-page) so Antigravity, Codex, and Claude Code all pick it up natively without a connector. Use the situation → shape table above as the spec's core content.

## Next Action

`product:spec 060-cross-agent-output-format-convention`
