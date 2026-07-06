# Plan: Issue-Less Work Traceability (075 v2)

Issue: `075-issue-less-context-capture`
Spec: `specs/075-issue-less-context-capture/spec.md` (v2, rescoped 2026-07-06)
Prev: spec v2 · Next: `product:execute 075-issue-less-context-capture`

## Global Constraints

Binding on every task — workers must honor these verbatim:

1. **Only one new command**: `product:promote`. No `product:capture`, no new context tier. Capture work modifies the four existing command docs only.
2. **Gate code never passes silently**: any git subprocess failure inside linkage/release checking returns an error result. `except Exception: pass` is banned in gate paths.
3. **Records never move**: promotion writes `promoted_to` in place; supersession uses `superseded_by`, never file deletion or relocation.
4. **`commands/*.md` classify as behavior**, not docs, in path classification.
5. **Human-identity grounding**: a no-issue declaration validates only against `git blame`/PR-approval of a configured human identity; the identity config itself validates the same way (its blame must be human). No agent-writable escape.
6. **Linkage logic lives in an importable module** (`scripts/linkage_check.py`), not inline in `release_check.py` — issue 072's hooks will import it.
7. **Naming**: issue ids resolve from branch `codex/<issue-id>-*` (regex on the full id, e.g. `codex/075-issue-less-context-capture-gate`) or commit trailer line `Issue: <issue-id>`. Trailer wins on conflict.
8. Frontmatter keys for records: `kind`, `date`, `summary`, `retrieval_trigger`, optional `promoted_to`, `superseded_by`. Exactly these names.

## Work Streams

### Stream A — linkage checker + gate repair (first milestone, blocking release semantics)

- **A1. `scripts/linkage_check.py`** (new module)
  - Functions: `resolve_issue_for_commit(sha)` (branch-name + trailer resolution), `classify_changed_paths(paths)` → `behavior | neutral` (behavior: `scripts/`, `commands/`, `skills/`, `templates/`, `.github/workflows/`, plugin manifests), `find_unlinked_behavior_commits(merge_base, head)`, `validate_no_issue_declaration(file, line_no, human_identities)` via `git blame --line-porcelain`.
  - **Interfaces (produces)**: pure functions returning result dicts with `ok | error` status; consumed by A2, C2, and later 072.
  - Tests: `tests/test_linkage_check.py` — FakeRunner pattern from `test_project_sync.py`; branch/trailer/conflict/error cases.
- **A2. `release_check.py` repair + integration**
  - Replace the two silent `except Exception: pass` blocks (lines ~51, ~61) with explicit error results; compute diff from explicit merge-base (`git merge-base HEAD origin/main`, fetch main when shallow); call A1's `find_unlinked_behavior_commits`; fail on unlinked behavior commits without a valid declaration.
  - CI: set `fetch-depth: 0` (or targeted fetch of main) in `.github/workflows/ci.yml` so merge-base exists.
  - **Interfaces (consumes)**: A1 module. **Produces**: gate result consumed by release flow and `product:release` docs.
- **A3. Human-identity config + declaration channel**
  - `.moduflow/humans.json`: list of human git identities (name/email). Self-grounding check: config file's own blame must resolve to a listed human or the initial human commit; agent-authored edits invalidate it.
  - Declaration location decision (open question from spec): **dedicated file** `releases/no-issue-declarations.md`, one marker line per declaration (`<date> <path-or-scope> — <reason>`), blame-validated per line. Chosen over release-notes-source because blame granularity is per-line and the file has a single purpose.
  - `human-review.ko.md` generation (in `project_pr.py`) includes the release's declarations.
  - **Interfaces (produces)**: declaration file format consumed by A2 validation and C2 packet rendering.

### Stream B — promote + issue template (parallel to A)

- **B1. Issue template AI-first fields**
  - `templates/issues/issue.md`: add `## Verification` (commands the executor runs), `## Entry Points` (starting files), `## Scope Fence` (do-not-touch) sections with `{{...}}` placeholders.
  - **Interfaces (produces)**: template consumed by B2 prefill and by `product:issue` docs.
- **B2. `product:promote`**
  - `scripts/project_promote.py`: `--record <path> --write` → parse record frontmatter/body, create `issues/<new-id>-<slug>.md` from template (summary/source/links prefilled; Verification/Entry Points/Scope Fence prefilled when derivable, else `TODO(blocking-execution)`), write `promoted_to: <issue-id>` into record frontmatter in place, `Promoted-from: <record-id>` into the issue's Source/Links.
  - `commands/product-promote.md`: promotion requirement vs readiness ("works as an AI prompt") guidance, exact script invocation.
  - Tests: `tests/test_project_promote.py` — each of the 4 record kinds, link bidirectionality, in-place preservation.
  - **Interfaces (consumes)**: B1 template, C1 frontmatter contract.

### Stream C — capture normalization + retention (parallel; C1 early — it defines the frontmatter contract)

- **C1. Frontmatter + write-discipline docs** across `commands/product-decision.md`, `product-inbox.md`, `product-memory.md`, `product-knowledge.md`
  - Document shared keys (Global Constraint 8) and ADD/UPDATE/SUPERSEDE/NOOP discipline (check existing records before creating; NOOP when nothing new).
  - **Interfaces (produces)**: frontmatter contract consumed by B2 and C2. Doc-only task; scripts unchanged.
- **C2. Status surfacing + release-count retention**
  - `commands/product-status.md`: show unpromoted-record count and oldest age.
  - Archive mechanics in `scripts/project_memory.py` (or a small `project_retention.py` if memory.py ownership conflicts with parallel work): records with no `promoted_to` older than **2 releases** move state to archived (frontmatter `archived: <date>`, file stays; queryable list command).
  - **Interfaces (consumes)**: C1 contract, A3 declaration format (for packet listing).

### Stream D — closeout (sequential, after A+B)

- **D1. 074 case writeup + docs sweep**: walk 074 against v2 mechanisms in `specs/074-sync-fetch-sandbox-handling/` cross-reference or `memory/evidence/`; update `commands/product-release.md` gate description; verify no doc still references v1 capture tier.

## Parallelism & Merge Order

- Parallel-eligible: **A1 ∥ B1 ∥ C1** (disjoint files), then **A2+A3 ∥ B2 ∥ C2**.
- Merge order: C1 → A1 → A2 → A3 → B1 → B2 → C2 → D1 (contract-definers first; gate before consumers).
- Same-file risk: `release_check.py` only in A2; `project_pr.py` only in A3; status command doc only in C2. `project_memory.py` in C2 only — if retention lands elsewhere, declare before dispatch.

## Gates

- **Test gate**: `python3 -m unittest discover tests` green; new tests for every task with code.
- **Self-application gate**: this issue's own branch must satisfy the new linkage check (`codex/075-issue-less-context-capture-*`) — the gate ships by passing itself.
- **Review gate**: `product:review 075` with qa + spec-compliance workers; adversarial reviewer re-checks HIGH-1/2/3 closure specifically.
- **Deploy gate**: plugin version bump; `release_check` (new version) green; declarations file empty at ship.
- **Rollback**: single revert of the merge commit restores prior gate behavior; new module/script files are additive; template additions are backward-compatible (old issues without the new sections remain valid — parser must not require them).

## Non-Goals Reminder (from spec)

Real-time session detection (072), staged severity, wall-clock archive, capture command/tier — out. Do not reintroduce under any task.
