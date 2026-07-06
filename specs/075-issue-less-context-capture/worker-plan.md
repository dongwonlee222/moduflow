# Worker Plan: 075-issue-less-context-capture

Mode: `sequential`
Parallel eligible: `false`

## Tasks

| ID | Worker | Group | Status | Files | Depends | Task |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | `qa-reviewer` | `group-1` | ready | - | - | A1. `scripts/linkage_check.py` module (branch/trailer resolution, path classification, declaration blame validation) + `tests/test_linkage_check.py` (FakeRunner; error-path tests mandatory) — depends: none |
| T02 | `qa-reviewer` | `sequential` | ready | - | - | A2. `release_check.py` repair: explicit merge-base, remove both silent `except Exception: pass` blocks, integrate `find_unlinked_behavior_commits`, CI fetch depth in `.github/workflows/ci.yml`, `tests/test_release_check.py` — depends: A1 |
| T03 | `qa-reviewer` | `group-1` | ready | - | - | A3. `.moduflow/humans.json` + `releases/no-issue-declarations.md` + blame validation + declaration listing in `human-review.ko.md` via `scripts/project_pr.py` + tests — depends: A1, A2 |
| T04 | `implementation-worker` | `group-2` | ready | - | - | A-gate. Self-application: this issue's own branch passes the new linkage gate |
| T05 | `qa-reviewer` | `group-1` | ready | - | - | B1. `templates/issues/issue.md`: add `## Verification`, `## Entry Points`, `## Scope Fence` sections (backward-compatible — parsers must not require them on old issues) — depends: none |
| T06 | `qa-reviewer` | `sequential` | ready | - | - | B2. `scripts/project_promote.py` (record→issue, `promoted_to` in place, `Promoted-from` on issue, AI-field prefill or `TODO(blocking-execution)`) + `commands/product-promote.md` + `tests/test_project_promote.py` covering all 4 record kinds — depends: B1, C1 |
| T07 | `implementation-worker` | `sequential` | ready | - | - | C1. Shared frontmatter contract (`kind`, `date`, `summary`, `retrieval_trigger`, `promoted_to`, `superseded_by`) + ADD/UPDATE/SUPERSEDE/NOOP write discipline documented in `commands/product-decision.md`, `product-inbox.md`, `product-memory.md`, `product-knowledge.md` — depends: none |
| T08 | `qa-reviewer` | `group-1` | ready | - | - | C2. `commands/product-status.md` unpromoted-record count/oldest surfacing + 2-release retention archive (frontmatter `archived:`, file stays, queryable list) in `scripts/project_memory.py` or `project_retention.py` + tests — depends: C1, A3 |
| T09 | `release-manager` | `group-3` | ready | - | - | D1. 074 case writeup against v2 mechanisms + docs sweep (no v1 capture-tier references remain; `commands/product-release.md` gate description updated) — depends: Stream A, Stream B |

## Isolation

- T01: `codex/075-issue-less-context-capture-t01`
- T02: `codex/075-issue-less-context-capture-t02`
- T03: `codex/075-issue-less-context-capture-t03`
- T04: `codex/075-issue-less-context-capture-t04`
- T05: `codex/075-issue-less-context-capture-t05`
- T06: `codex/075-issue-less-context-capture-t06`
- T07: `codex/075-issue-less-context-capture-t07`
- T08: `codex/075-issue-less-context-capture-t08`
- T09: `codex/075-issue-less-context-capture-t09`

## Merge Order

- T01 → T02 → T03 → T04 → T05 → T06 → T07 → T08 → T09

## Worker Inventory

- All worker files are covered by routing rules.

## Risks

- Task 2 touches shared state: A2. `release_check.py` repair: explicit merge-base, remove both silent `except Exception: pass` blocks, integrate `find_unlinked_behavior_commits`, CI fetch depth in `.github/workflows/ci.yml`, `tests/test_release_check.py` — depends: A1
- Task 6 touches shared state: B2. `scripts/project_promote.py` (record→issue, `promoted_to` in place, `Promoted-from` on issue, AI-field prefill or `TODO(blocking-execution)`) + `commands/product-promote.md` + `tests/test_project_promote.py` covering all 4 record kinds — depends: B1, C1
- Task 7 touches shared state: C1. Shared frontmatter contract (`kind`, `date`, `summary`, `retrieval_trigger`, `promoted_to`, `superseded_by`) + ADD/UPDATE/SUPERSEDE/NOOP write discipline documented in `commands/product-decision.md`, `product-inbox.md`, `product-memory.md`, `product-knowledge.md` — depends: none

## Next Command

`product:execute 075-issue-less-context-capture`
