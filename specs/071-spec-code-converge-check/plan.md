# Plan: Spec-Code Converge Check (071)

Issue: `071-spec-code-converge-check`
Spec: `specs/071-spec-code-converge-check/spec.md` (mechanism-benchmark hardened, 2026-07-06)
Prev: spec · Next: `product:execute 071-spec-code-converge-check`

## Global Constraints

Binding on every task — workers honor these verbatim:

1. **Single parser**: the AC list and plan Global Constraints are parsed exactly once, in the evidence script; the judge, the report writer, and the tasks.md appender all consume that parsed output (`converge-evidence.json`). No second parser anywhere (OpenSpec #498 lesson).
2. **Write surface**: the converge pass writes ONLY `specs/<id>/converge.md` (append dated section) and, when high/medium findings exist, the `## Converge Findings (auto)` section of `specs/<id>/tasks.md`. It MUST NOT modify `spec.md` or `plan.md` in any way, nor rewrite, renumber, reorder, or delete any existing task line.
3. **Byte-for-byte no-op**: a fully converged run leaves tasks.md byte-identical and never emits an empty findings header.
4. **Exit codes**: `project_converge.py` exits non-zero on git or bundle failure, identically in `--json` and human modes (OpenSpec #1311 lesson). Git failures surface as explicit errors, never empty results (075 constraint carried over).
5. **No silent caps**: bundle limits (default: 30 files / 200KB total content) always set an explicit `truncated` field that the report must surface.
6. **CV line grammar** (fixed): `- [ ] CV-<n> [<severity>] <finding> — <source-ref>, from converge <date>` where source-ref is `AC#<k>`, `GC#<k>` (plan Global Constraint), or `unrequested:<path>` for unrequested-behavior findings *(amended 2026-07-06 during 071 self-converge: the original grammar omitted a source form for unrequested items — caught by converge run 1, CV-1)*. Dedup key = normalized finding text + source-ref; re-runs never re-append a finding whose CV item is still unchecked.
7. **Severity**: high | medium | low; violations of plan Global Constraints are automatically high; emission order high→low.
8. **Verdict vocabulary** (fixed): `converged | missing | partial | contradicting | unverifiable` per AC, plus `unrequested[]` and `bundle_gaps[]`. `missing` = commits exist but no code satisfies the AC; `no-evidence` = no resolvable commits, report only, no judging.
9. **Judge independence**: the subagent judging an issue must not be the agent that implemented it (where the host allows); inline fallback (coordinator judges + limitation recorded in converge.md) mirrors product:review's rule.
10. **Command surface**: one new command doc `product-converge.md`; not added to the default mental model (026). `linkage_check.py` is imported, never modified.

## Interfaces (contracts between tasks)

- **Evidence JSON** (`specs/<id>/converge-evidence.json`, produced by A1, consumed by B1 judge and A2 report/append):
  ```json
  {"schema": "moduflow.converge-evidence.v1", "issue_id": "…", "generated": "<date arg>",
   "commits": [{"sha": "…", "subject": "…", "source": "trailer|merge-subject"}],
   "files": [{"path": "…", "content": "…", "truncated": false}],
   "acceptance_criteria": [{"id": "AC#1", "text": "…", "parseable": true}],
   "global_constraints": [{"id": "GC#1", "text": "…"}],
   "truncated": false, "no_evidence": false, "errors": []}
  ```
- **Judgment JSON** (produced by the judge per B1's schema, consumed by A2):
  ```json
  {"schema": "moduflow.converge-judgment.v1",
   "verdicts": [{"ac_id": "AC#1", "verdict": "…", "severity": "high|medium|low|", "evidence_quote": "…", "note": "…"}],
   "unrequested": [{"behavior": "…", "file": "…", "severity": "…"}],
   "bundle_gaps": ["…"]}
  ```
- Unparseable AC lines arrive with `"parseable": false` and MUST be emitted by the judge as `unverifiable` (never dropped).

## Work Streams

### Stream A — deterministic engine

- **A1. Evidence collection** (`scripts/project_converge.py --issue-id <id> --evidence [--json] [--date <iso>]`)
  - Commit resolution: scan `git log --format=%H%x00%s%x00%B` for trailer `Issue: <id>` and merge subjects mentioning `codex/<id>` (branch deleted post-merge is fine); import `linkage_check` helpers where they fit. Collect touched files (`git show --name-only`), read **current** file contents with caps (GC5), parse spec AC (checkbox and prose-bullet forms) and plan Global Constraints. Write evidence JSON.
  - Tests (`tests/test_project_converge.py`, FakeRunner + tmpdir): trailer hit, merge-subject hit, no commits → `no_evidence: true` + exit contract, caps → `truncated: true`, prose-bullet AC parsed, git failure → non-zero exit + error entry.
- **A2. Report + append** (`--apply-judgment <judgment.json>` mode)
  - Appends dated section to converge.md (never overwrites prior sections); appends high/medium CV lines to tasks.md per GC6 grammar with dedup against existing unchecked CV items; byte-for-byte no-op path (GC3); low severity report-only.
  - Tests: append idempotency (same judgment twice → single CV set), no-op leaves tasks.md byte-identical, dated sections accumulate, checked-off CV item allows a recurring finding to re-append (it regressed).
  - **Interfaces**: consumes Evidence + Judgment JSON; owns converge.md/tasks.md writes exclusively.

### Stream B — judgment + workflow integration (B1 parallel with A2 once A1's schema lands)

- **B1. Judgment contract + command doc**
  - `templates/converge-judgment-prompt.md`: the judge's instruction (input = evidence JSON only; prefer `unverifiable` over guessing; output = Judgment JSON schema above).
  - `commands/product-converge.md`: standalone flow (evidence → dispatch judge subagent with prompt template → `--apply-judgment`), inline fallback rule (GC9), no-evidence handling, non-gate framing, note that it works on released issues.
- **B2. Review auto-run integration**
  - `commands/product-review.md`: converge runs as the final evidence step of review; converge.md path added to review evidence list; failure/no-evidence does not block review verdict (non-gate) but must be reported.

### Stream D — fixtures + dogfood (after A+B)

- **D1. Fixtures + dogfood run**
  - Test fixtures: a mini spec+code pair where an AC is unimplemented (`missing`), code has an extra behavior (`unrequested`), and one AC is untestable from the bundle (`unverifiable` exercised) — spec AC requirement.
  - Dogfood: run the full flow on issue 075 (real trailers + merged branch), commit its converge.md as the first production run.
  - Docs sweep: roadmap/status guidance mentions converge exists.

## Parallelism & Merge Order

- A1 first (defines Evidence schema). Then **A2 ∥ B1** (A2 owns script/report files; B1 owns template + command docs — disjoint). Then B2, then D1.
- Same-file ownership: `project_converge.py` and its tests → Stream A only; command docs → Stream B only; `product-review.md` → B2 only.

## Gates

- **Test**: `python3 -m unittest discover tests` green; every code task ships focused tests including exit-code and no-op paths.
- **Self-application**: D1's dogfood run on 075 must complete end-to-end and its converge.md committed; if it finds real gaps in 075, they append to 075's tasks.md — that is the feature working, not a failure.
- **Review**: `product:review 071` (with the new auto-run — converge runs on 071 itself as part of its own review).
- **Deploy**: version bump in completion commit; `release_check .` green (linkage gate applies to this branch: `codex/071-*` + trailers).
- **Rollback**: revert merge commit; all new files additive; product-review.md change is a doc step easily reverted.

## Non-Goals Reminder

No release gate, no repo-wide scan, no spec/plan edits, no second parser — see spec Non-Goals; do not reintroduce under any task.
