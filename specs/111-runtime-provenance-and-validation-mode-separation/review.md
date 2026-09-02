# Review: Issue 111

Issue: `111-runtime-provenance-and-validation-mode-separation`
Owner: Dongwon Lee
Source: approved `spec.md` / `plan.md`; current user approval, 2026-09-02.
Phase: inline self-review and final source verification complete; human integration approval pending.
Next command: `product:review 111-runtime-provenance-and-validation-mode-separation`.

## Findings

- Inline self-review only; no independent reviewer or human merge approval is claimed.
- Fixed the staged-manifest symlink write path before package validation, and preserved runtime evidence on MCP dispatch errors.
- Corrected the existing downstream security/lint test fixture to identify its source role; source/release gates were not weakened.
- No unresolved must-fix finding from the reviewed Issue 111 implementation. Real-host observations and explicit merge/publication approval remain outstanding.

## Visual Handoff

- No frontend/UI behavior changes in Issue 111; desktop/mobile screenshots are not applicable.
- Existing generated project views: `memory/dashboard.html` and `memory/issue-111-runtime-provenance-and-validation-mode-separation.html`. They are local read models, not installation evidence.
- Start human review with `human-review.ko.md`, then the canonical spec/status/review and GitHub diff.

## Plan Review and Approval

The user approved the four-stream plan with “ㅇㅇ 이제 다음 뭐 할까 진행 하자고”. Baseline focused regression: 137 tests passed in 73.664 seconds. This records plan approval only, not approval of unwritten code, actual installation or publication.

## Start Preflight

The first state-transition attempt used a custom idempotency key instead of the required derived semantic key and was rejected before mutation. The corrected attempt reached projected validation and exposed two preparation requirements: the loop's prior Issue 103 branch binding must move to Issue 111, and the issue's linked review artifact must exist. Preserve these failed attempts as evidence; do not bypass projected validation. Implementation stays in the existing worktree on an Issue 111 branch.

## Implementation Review

Direct inline self-review of the changes from `40b1219` through `517ec64`, with no subagent or independent-review claim. Reviewed the provenance reader, installer staging/publication, validator role selection, Doctor/MCP consumers, unit/simulation tests and release instructions.

| Acceptance | Inspected evidence | Disposition |
|---|---|---|
| AC1 | Explicit modes, source requirements unchanged, installed payload digest; S01–S03 | Implemented; final release gate recorded in status |
| AC2 | Guard before Git-parent/registry/recovery calls; S04/S05/S12 | Covered, including source dogfooding and empty projects |
| AC3 | Shared reader, typed receipt values and explicit null reasons; S06/S07 and error-path tests | Covered; dispatch-error finding fixed below |
| AC4 | Prepared cache, fsync/replace receipt, validation before publication; S08/S09 | Covered; no claim of atomic host-config activation |
| AC5 | One startup snapshot, packaged persistent MCP and fresh CLI; S10 | Process proof only; host skill reload unknown |
| AC6 | Existing 065 fields retained; separate inventory and parse diagnostics; S11 | Covered; newest cache never selected as runtime |
| AC7 | Twelve isolated scenarios with synthetic projects/homes; packaged imports and diagnostic sentinels | 12 scenarios passed; no real installation |
| AC8 | Release/upgrade guidance and separate release evidence stages | Remote/publication/R01/R02 remain pending |

### Findings Resolved

- Important: a symlinked staged manifest could be followed before payload validation. A failing test reproduced an external fixture write; reject payload links before staged manifest writes. Covered by installer tests.
- Important: a project-context exception escaped status/Doctor handlers as JSON-RPC `-32603` without runtime evidence. Added a failing test, then preserved the same snapshot in `error.data.runtime_provenance`. MCP plus simulations passed 45 tests after the fix.
- Test compatibility: the legacy security/lint integration fixture had no source identity and now stopped at the intentionally earlier role guard. Reproduced its `KeyError: security_check`; identified the fixture as synthetic source in `b5c3ce3`. The focused regression passed, preserving both security and syntax assertions without bypassing the source guard.

No unresolved must-fix finding from this self-review. This is not a human merge approval or proof of actual host adoption. The release gate initially rejected the prior HEAD because its version bump was still uncommitted; `517ec64` commits the prepared 0.3.55 manifests. Re-run the gate on that commit rather than waiving it.
Final verification: source release check passed on `517ec64`; the full suite after fixture correction (`b5c3ce3`) passed all 1,610 tests in 337.291s, including nested release-check regressions. Ready for human/PR review. No independent reviewer, remote CI, publication or real-host application is claimed.
