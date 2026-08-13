# Issue 100: Converge Audits Spec Compliance but Not Removal Residue

**Status: backlog** — created 2026-08-08.
**Priority: p1**
**Blocked-by:**

## Summary

`product:converge` grades code against acceptance criteria — what the change *added*. Nothing grades what the change *removed*: orphaned functions, dangling references, and monitors still pointing at deleted assets survive every existing gate.

## Source

- Type: finding from a dogfood audit (2026-08-08)
- Evidence: four real incidents in a single day, none caught by review or converge

## Problem

LLM agents avoid deletion. They comment out, disable behind a flag, or delete partially — then report "removed." Existing gates do not catch this because the remaining code still parses, still passes tests, and satisfies no acceptance criterion either way.

**Four incidents, one day (2026-08-08):**

| # | Removal | Residue | Found by |
| --- | --- | --- | --- |
| 1 | flag-server health check | `port_up()` left defined, 0 callers | user, by hand |
| 2 | `~/projects/_pipeline` archived | `path_check.sh` still monitored 2 paths in it | health check failing next day |
| 3 | `flag-server` LaunchAgent archived | same monitor still listed it | same |
| 4 | 22 skills archived | 6 chained skills referenced them (`contracts/` → `spec-build` → 5 more) | manual grep, 6 rounds |

Incident 4 is the important one: removal cascades. Archiving one skill broke references in six others, and each round of grep revealed the next layer. A one-shot check would have missed five of the six.

## Scope

- New worker: `residue-checker` alongside `qa-reviewer` in `workers/`
- `scripts/project_converge.py` — collect deleted/moved paths from the issue's commits as evidence
- `templates/converge-judgment-prompt.md` — add residue verdicts

Proposed checks (language-agnostic first, then per-language):

| Check | Detects |
| --- | --- |
| Definition with zero call sites, within the diff's blast radius | incident 1 |
| Reference to a path that no longer exists | incidents 2, 3 |
| Transitive reference scan until a fixpoint (not one pass) | incident 4 |
| Intentional retention without a stated reason | disabled-but-kept code with no comment explaining why |

## Do NOT touch

- `product:review`'s pre-merge gating role — this is post-merge audit, same as converge
- Blocking behavior — findings append to `tasks.md`, never gate
- Auto-deletion of anything found

## Workflow Tasks

- [ ] spec → `specs/<issue-id>/spec.md`
- [ ] plan → `specs/<issue-id>/plan.md`
- [ ] execute → PR / commits
- [ ] review → review notes

## Acceptance Criteria

1. Converge evidence includes paths deleted or moved by the issue's commits.
2. A definition left with zero call sites inside the change's blast radius is reported (incident 1 reproduces as a test case).
3. A reference to a removed path is reported (incidents 2–3 reproduce).
4. Reference scanning iterates to a fixpoint; a cascade of depth ≥ 2 is fully reported in one run (incident 4 reproduces).
5. Retained-but-disabled code with a stated reason is classified as intentional, not residue — the distinction is explicit in the verdict.
6. Insufficient evidence yields `unverifiable`, consistent with existing converge verdicts.

## Global Constraints

- Report only. No automatic removal.
- Must not fail closed on languages without a parser — degrade to `unverifiable` with the reason.
- Runs inside the existing converge flow; no new command surface.

## Links

- Spec: `specs/<issue-id>/spec.md`
- Status: `specs/<issue-id>/status.md`
- Related: 095 (commit-issue resolution parity — converge evidence collection)
