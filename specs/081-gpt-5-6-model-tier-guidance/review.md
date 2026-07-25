# Review: GPT-5.6 Model Tier Guidance

Issue: 081-gpt-5-6-model-tier-guidance

## Verdict

Pass.

## Findings

No blocking findings.

## Checks

- The durable ModuFlow schema remains `deep` / `balanced` / `fast`.
- GPT-5.6 model names appear only as current OpenAI examples and starting points.
- Pro mode and `max` reasoning are documented as selective quality-first options, not automatic defaults.
- Regression tests cover all three GPT-5.6 examples in generated worker prompts and docs.

## Verification

- `python3 -m unittest tests.test_cognitive_demand_routing -v` passed.
- `python3 scripts/release_check.py .` passed with `valid: true`.

## PR-time review addendum (2026-07-25)

Reviewer: Claude Opus 5, coordinator-inline. Added when the work was recovered
from an uncommitted working tree and prepared for PR; the original review above
predates that recovery.

Re-verified at branch head:

- `python3 -m unittest discover -s tests` — 582 passed, `OK`.
- `python3 scripts/release_check.py .` — `valid: true`, zero errors.
- `python3 scripts/spec_consistency.py . --issue-id 081-...` — 0 errors,
  1 info (`tasks.md is missing`).

### Finding: guidance text is injected regardless of host — accepted, tracked

`WORKER_COGNITIVE_DEMAND` stays semantic, and the docs are explicit that the
GPT-5.6 names are a current mapping rather than schema. But
`COGNITIVE_DEMAND_GUIDANCE` is appended to **every** generated worker prompt
unconditionally, so a worker running on Claude Code or Gemini still receives
OpenAI model guidance:

| Demand | Prompt text |
| --- | --- |
| `deep` | 190 chars |
| `balanced` | 180 chars |
| `fast` | 146 chars |

The pre-081 text was roughly 40 chars, so this adds ~110-150 chars per worker
prompt on hosts where it cannot apply.

Accepted as an interim state rather than a blocker: the phrasing is conditional
("If using OpenAI GPT-5.6"), so it is not wrong on other hosts, only inert. The
two follow-ups this issue registered are exactly the fix — `082` makes routing
host-aware, and `084` covers worker prompt context budget. This finding is the
concrete argument for sequencing `082` ahead of `083`.

### Observation: tests pin provider model names

`tests/test_cognitive_demand_routing.py` asserts `gpt-5.6-sol` / `terra` /
`luna` appear in both generated prompts and the docs. That deliberately keeps
code and documentation in sync, at the cost of requiring test edits whenever the
model family changes. Intentional, noted so the coupling is not a surprise later.

### Note: `tasks.md` absent

Non-blocking (`info`). The issue file carries the workflow tasks and the work is
complete; a retroactive `tasks.md` was not fabricated for the PR.

### Verdict

Pass. No blocking findings. Ready for PR.
