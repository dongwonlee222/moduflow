# Adversarial Review: 075 spec v1 (pre-rescope)

Date: 2026-07-06
Reviewer: adversarial-review subagent (AI-operator premise), claims spot-verified by the coordinating agent against the repo.
Verdict: **rescope required** — accepted by the user 2026-07-06; spec v2 rewritten accordingly.

## Verified factual findings

All load-bearing claims were checked directly against the repo before acceptance:

- `commands/` contains **38 commands**, including `product-decision.md`, `product-memory.md`, `product-knowledge.md`, `product-inbox.md` → 4 of the proposed 5 context types duplicated existing surfaces; `product:capture` would have been a second entry point to the same artifacts.
- `templates/issues/issue.md` has **no YAML frontmatter** (markdown sections) → the v1 "promotion is a state transition on issue-compatible frontmatter" premise was false for the current schema.
- `sessions/` directory **does not exist** → v1 storage table row was wrong; issue 075's `sessions/075-…/` link was dead.
- `scripts/release_check.py` swallows `git diff` failures (`except Exception: pass`, lines 51/61) → a gate built on the same pattern passes vacuously in CI (fetch-depth=1, no main ref); direct commits to main make `git diff main` empty, bypassing the gate entirely.
- Repo velocity: ~75 issues in 24 days, issue+spec+plan+review generated same-day by the agent → issue-creation cost for the operator is ~0; the imported "issues are heavy" premise came from human input friction that does not exist here.

## Findings (severity ranked)

1. **HIGH — v1 did not solve its own Problem statement.** Capture was opt-in and judged by the same agent that missed the 074 threshold; status/doctor warnings fire only when invoked; the release gate is a backstop, not the promised "flag while it happened". Real-time detection belongs to `072-lifecycle-hooks-automation`. The gate trigger must be **worktree diff + missing issue linkage**, not capture records.
2. **HIGH — self-approval loop.** The agent does the work, judges the gate, writes the approval marker, and authors the release notes that expose it — no technically required human act anywhere. nearform/danger escape hatches presume human social accountability that is absent in a 1-human+AI team. Fix: approval markers valid only under **human Git identity** (blame/PR-approval check), declarations surfaced in `human-review.ko.md` (the surface the human actually reads).
3. **HIGH — path heuristic structurally broken here.** `commands/*.md` are simultaneously docs and behavior (074's fix WAS command docs); docs-vs-code dichotomy fails both wide and narrow. No machine-checkable commit↔issue linkage convention existed at all. Fix: branch-name (`codex/<issue-id>-*`) or commit-trailer convention as the primary signal; release_check must use explicit merge-base and **error on git failure** instead of passing.
4. **MEDIUM — four contradictions with repo reality** (listed under verified findings above).
5. **MEDIUM — capture spam undefended.** 90-day archive is human-time; at agent velocity it just delays the flood. Retention should count releases; unpromoted/declaration lists belong in the human-review packet; capture volume caps warned by doctor.
6. **LOW — staged severity config is YAGNI** for this repo and an agent-editable bypass surface. Dropped.

## What survives into v2

- `product:promote` (existing records → issue, auto bidirectional links)
- Release-time hard gate (rebuilt on linkage convention + repaired diff plumbing)
- Human-identity approval channel
- AI-first issue fields (verification / entry points / scope fence) from the round-B benchmark
- Normalization of the four existing capture commands instead of a new tier/command
