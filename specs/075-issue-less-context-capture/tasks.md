# Tasks: 075-issue-less-context-capture (v2)

Plan: `specs/075-issue-less-context-capture/plan.md`
Status: ready-for-execute · Parallel-eligible: A1 ∥ B1 ∥ C1, then A2+A3 ∥ B2 ∥ C2
Merge order: C1 → A1 → A2 → A3 → B1 → B2 → C2 → D1

## Stream A — linkage checker + gate repair

- [ ] A1. `scripts/linkage_check.py` module (branch/trailer resolution, path classification, declaration blame validation) + `tests/test_linkage_check.py` (FakeRunner; error-path tests mandatory) — depends: none
- [ ] A2. `release_check.py` repair: explicit merge-base, remove both silent `except Exception: pass` blocks, integrate `find_unlinked_behavior_commits`, CI fetch depth in `.github/workflows/ci.yml`, `tests/test_release_check.py` — depends: A1
- [ ] A3. `.moduflow/humans.json` + `releases/no-issue-declarations.md` + blame validation + declaration listing in `human-review.ko.md` via `scripts/project_pr.py` + tests — depends: A1, A2
- [ ] A-gate. Self-application: this issue's own branch passes the new linkage gate

## Stream B — promote + issue template

- [ ] B1. `templates/issues/issue.md`: add `## Verification`, `## Entry Points`, `## Scope Fence` sections (backward-compatible — parsers must not require them on old issues) — depends: none
- [ ] B2. `scripts/project_promote.py` (record→issue, `promoted_to` in place, `Promoted-from` on issue, AI-field prefill or `TODO(blocking-execution)`) + `commands/product-promote.md` + `tests/test_project_promote.py` covering all 4 record kinds — depends: B1, C1

## Stream C — capture normalization + retention

- [ ] C1. Shared frontmatter contract (`kind`, `date`, `summary`, `retrieval_trigger`, `promoted_to`, `superseded_by`) + ADD/UPDATE/SUPERSEDE/NOOP write discipline documented in `commands/product-decision.md`, `product-inbox.md`, `product-memory.md`, `product-knowledge.md` — depends: none
- [ ] C2. `commands/product-status.md` unpromoted-record count/oldest surfacing + 2-release retention archive (frontmatter `archived:`, file stays, queryable list) in `scripts/project_memory.py` or `project_retention.py` + tests — depends: C1, A3

## Stream D — closeout

- [ ] D1. 074 case writeup against v2 mechanisms + docs sweep (no v1 capture-tier references remain; `commands/product-release.md` gate description updated) — depends: Stream A, Stream B

## Verification per task

- Code tasks (A1/A2/A3/B2/C2): focused unittest files, FakeRunner pattern; gate error paths tested (Global Constraint 2).
- Doc tasks (C1/B1/D1): `validate_project_artifacts.py` + reviewer read.

## Gates recap

test (`unittest discover`) → self-application (A-gate) → review (`product:review 075`, adversarial re-check of HIGH-1/2/3 closure) → release (version bump, empty declarations file). Rollback: revert the merge commit; new files are additive.
