# Plan: Project Constitution Steering (073)

Issue: `073-project-constitution-steering`
Spec: `specs/073-project-constitution-steering/spec.md`
Prev: spec · Next: `product:execute 073-project-constitution-steering`

## Global Constraints

*(Meta-note: this should be the last plan that authors its constraints fully inline — A1's deliverable replaces this pattern.)*

1. **No script logic changes**: the only script touched is `scripts/project_execution.py`, and only its review-handoff **string template** (adding the constitution-check line) — no behavior, no parsing, no enforcement code (user decision: template+doc scope).
2. **Extraction, not invention**: every v1.0 principle in the constitution draft must carry an origin reference resolving to a real issue/plan/convention (075/071/072 GCs, 067 model-tier, 049 sidecar, 060 boundary). A candidate without a traceable origin is dropped, not ratified.
3. **Ratification is the human's**: the draft ships with the amendment log's v1.0 entry marked `pending human ratification`; the approver field is filled only from the user's explicit approval (expected at PR review/merge). The agent never writes an approver name on its own authority.
4. **Unlogged-edit-void rule** stated in the constitution header with the revert path (`git log workspace/constitution.md` + revert unapproved commits).
5. **Jurisdiction line**: constitution = engineering principles; AGENTS.md = output/format conventions (060). The draft's header states this boundary.
6. **Korean sidecar** (`constitution.ko.md`) ships with the canonical file (049).
7. **Forward-only**: shipped plans (075/071/072) keep their inline GCs untouched.
8. Targeted `git add` only; commit trailers `Issue: 073-project-constitution-steering`; branch `codex/073-project-constitution-steering`.

## Execution mode

**Inline by coordinator, no worker split.** Rationale against the default host-subagent split: the surface is one governance document + five small doc touches; constitution drafting is judgment-class authorship (main-loop work per the model-tier policy), and worker dispatch overhead exceeds every task here. Recorded in loop-state as `execution_backend: manual`.

## Interfaces

- **Reference form** (produced by A1's header, consumed verbatim by B1's template wording): plan GC sections open with `Constitution v<X.Y> applies (workspace/constitution.md). Plan-specific additions:` — tightenings for one issue are *additions*, never amendments (spec risk 4 wording).
- **Compliance line** (produced by A1, consumed by B2): `Constitution: v<X.Y> checked — no violations` | `— violations: <C-refs>`.

## Tasks

### Stream A — the document

- **A1. `workspace/constitution.md` + `constitution.ko.md`** — header (version placeholder v1.0, ratification pending, amendment procedure, unlogged-edit-void + revert path, jurisdiction vs AGENTS.md); ~10 candidate principles C1..Cn (force, one-sentence rule, one-line rationale, origin ref) extracted from 075/071/072 GCs + 067/049/060/075 conventions; amendment log table with the pending-v1.0 row.

### Stream B — consumption wiring (after A1; wording depends on A1's reference form)

- **B1. Plan/spec templates**: `commands/product-plan.md` GC instruction → reference form + additions-only (+ the additions-not-amendments distinction); `commands/product-spec.md` → constitution-assumed note.
- **B2. Review surfaces**: `commands/product-review.md` + review-handoff template string in `scripts/project_execution.py` → compliance line (GC1 limits).
- **B3. Converge note**: one sentence in `commands/product-converge.md` (plan GCs are constitution-derived; enforcement unchanged).

### Stream D — closeout

- **D1. Self-application + handoff**: 073's own review uses the compliance line (first consumption of B2); status.md records that the *next* issue's plan is the reference-form dogfood (spec AC); review handoff; Draft PR carrying the ratification request as the explicit human-approval ask.

## Gates

- **Test**: full suite green (no code logic changed — suite is regression insurance for the project_execution.py template edit).
- **Self-application**: 073's review carries the first compliance line; ratification ask is explicit in the PR body.
- **Review**: `product:review 073` (converge auto-run included).
- **Deploy**: version bump in completion commit (docs+feat classification per content); release_check green (branch linkage).
- **Rollback**: revert merge; all additions are docs + one template string.
