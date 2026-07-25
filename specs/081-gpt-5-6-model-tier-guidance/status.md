# Status: GPT-5.6 Model Tier Guidance

Issue: 081-gpt-5-6-model-tier-guidance

**Status: done** — created 2026-07-10, started 2026-07-10, done 2026-07-10.

## Current State

Implementation, review notes, focused regression tests, and release check are
complete. Awaiting merge.

History worth knowing: this work sat in an uncommitted working tree from
2026-07-10 until 2026-07-25 — marked done in the issue file but present in no
commit, and therefore absent from the 0.3.26 release. It was recovered onto
`codex/081-gpt-5-6-model-tier-guidance` on 2026-07-25, reviewed, and prepared
for PR.

## Verification

Re-run at branch head on 2026-07-25:

| Check | Result |
| --- | --- |
| `python3 -m unittest discover -s tests` | 582 passed, `OK` |
| `python3 scripts/release_check.py .` | `valid: true`, zero errors |
| `python3 scripts/spec_consistency.py . --issue-id 081-gpt-5-6-model-tier-guidance` | 0 errors, 1 info (`tasks.md is missing`) |
| `python3 scripts/project_lifecycle.py . --drift` | `[]` |

Original focused run: `python3 -m unittest tests.test_cognitive_demand_routing -v`
passed.

## Review

Original review: pass, no blocking findings. A PR-time addendum was added on
2026-07-25 — see `specs/081-gpt-5-6-model-tier-guidance/review.md`,
Korean sidecar `specs/081-gpt-5-6-model-tier-guidance/review.ko.md`.

One accepted finding: `COGNITIVE_DEMAND_GUIDANCE` is appended to every generated
worker prompt unconditionally, so hosts that are not OpenAI still receive the
GPT-5.6 guidance (~110-150 chars of inert text per prompt). Not a blocker — the
phrasing is conditional — and issues `082` (host-aware routing) and `084`
(prompt context budget) are the registered fixes. This is the concrete reason to
sequence `082` before `083`.

## Follow-ups registered

- `082-cross-host-model-capability-routing`
- `083-model-routing-evaluation-harness` (blocked by 082)
- `084-worker-prompt-context-budget` (blocked by 082)

## Next Command

`product:pr 081-gpt-5-6-model-tier-guidance`
