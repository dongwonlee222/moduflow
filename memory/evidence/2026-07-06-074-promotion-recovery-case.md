---
id: 2026-07-06-074-promotion-recovery-case
kind: evidence
title: 074 Promotion Recovery Case vs 075 v2 Mechanisms
issue_id: 075-issue-less-context-capture
spec: specs/075-issue-less-context-capture/spec.md
source_event: dogfooding-writeup
retrieval_trigger: when evaluating whether the 075 linkage gate and promote flow actually close the silent-threshold-crossing failure, or when a similar issue-less recovery happens again
date: 2026-07-06
tags: [case-study, promotion, linkage-gate, dogfooding]
summary: Walkthrough of the 074 issue-less recovery against the 075 v2 mechanisms, showing where each mechanism would have engaged and what remains for issue 072.
---

# 074 Promotion Recovery Case vs 075 v2 Mechanisms

## What happened (2026-07-06, pre-075)

1. A sandboxed-fetch warning was investigated with no issue — legitimate exploratory troubleshooting.
2. The fix grew into `scripts/project_sync.py` code, tests, and `commands/product-sync.md` / `product-status.md` doc-behavior changes — the threshold was crossed with no signal.
3. The agent retroactively authored issue 074 (perfect-looking, same-day) and shipped via PR #7. Recovery worked, but only because the agent chose to do it; nothing enforced it, and the human PM had no required decision point.

## Replay under 075 v2

- **Capture**: the troubleshooting notes would live in an existing record (e.g. `product:decision` / `product:memory`) — no new tooling needed, no obligation yet.
- **Threshold crossing**: still not detected in-session — that is explicitly `072-lifecycle-hooks-automation`'s job. 075 does not claim real-time detection (v1 did, falsely).
- **Release boundary (the enforced stop)**: the commits touch `scripts/` and `commands/*.md` → linkage gate requires resolution to an issue. The work was on branch `codex/074-sync-fetch-sandbox-handling`, so branch-name resolution **passes** — but only because the branch convention was followed. Had the fix been committed directly to `main` with no trailer, `release_check` now **fails** instead of silently passing (the old `git diff main` empty-set hole is closed).
- **Escape hatch**: shipping it issue-less would have required a declaration line in `releases/no-issue-declarations.md` blame-attributed to the human — the agent could request it, not mint it. The declaration would then appear in the release's `human-review.ko.md` packet.
- **Recovery cost**: with `product:promote`, converting the troubleshooting record into issue 074 is one command with `promoted_to`/`Promoted-from` links written automatically, instead of hand-authoring the issue and back-links.

## What 075 verifiably closes vs leaves open

Closed: silent-pass release plumbing; unlinked behavior commits shipping; agent-minted approvals; manual bidirectional linking.
Open (by design): in-session threshold detection (072); local blame cannot distinguish agent-vs-human on shared git identity — the GitHub PR-approval channel is the stronger form (documented in `.moduflow/humans.json` note and spec Risks).
