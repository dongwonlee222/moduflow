# Status: Issue 111

Issue: `111-runtime-provenance-and-validation-mode-separation`
Owner: Dongwon Lee
Source: approved `plan.md`; user approval on 2026-09-02.
Phase: PR #45 merged; 0.3.56 published/installed after #46 integration and successful main CI; CLI/MCP verified, R01/R02 fresh-host observations pending.
Next command: `product:status` in a fresh host task, then record R01/R02 outcomes.

Current authority: [joint 0.3.56 release record](../060-cross-agent-output-format-convention/release.md). The older PR/approval/publication-pending entries below are historical handoff snapshots. The issue is not automatically marked done: direct installed CLI/MCP observations do not satisfy a fresh Codex/Claude task's host observation. Unavailable source Git metadata and host fields remain explicit.

## Verification

- Prior implementation verification: 1,610 tests passed on `b5c3ce3` in 337.291s; source release check passed after the evidence commit `8229170`.
- Current PR handoff: fresh full suite on `8229170` passed on 2026-09-02: `python3 -m unittest discover -s tests -q`, 1,610 tests in 359.621s, exit 0, no skipped tests. Process-local bundled Git environment matches the final implementation verification below; implementation code is unchanged.
- Offline coverage: S01–S12 and packaged CLI/MCP smoke passed; these are not actual Codex/Claude host observations.
- GitHub identity/auth/API preflight passed for `dongwonlee222/moduflow`, base `main`; local commit/push capability is `local-git-write`.
- Source release check on review-document commit `83b338e`: exit 0, all 13 checks passed.
- Branch push and Draft PR creation completed: https://github.com/dongwonlee222/moduflow/pull/45. Remote CI was pending at this handoff; latest-head checks on the PR are the live authority. Human merge approval, publication and installation are not complete.

## PR Authorization — 2026-09-02

The user approved proceeding after the parallel planning handoff. This authorizes the prepared Issue 111 branch push, Draft PR and CI verification, not merge, release or installation. The existing 25 untracked Issue 103 plans remain excluded. Parallel 090/086 planning uses other worktrees and is not part of this PR.

## Evidence — 2026-09-02

- Baseline: 137 tests passed in 73.664s. Distribution tests invoke the large source release suite twice; subsequent focused checks exclude these two recursive integration wrappers until final verification.
- RED: new runtime suite failed with 11 failures and 2 errors: missing reader, missing explicit mode keyword and source subprocess reached for a cache target.
- GREEN: 13 new runtime/mode tests passed; runtime + release unit tests 34 passed, validator-focused 9 passed, existing cache distribution 3 passed.
- The canonical start transaction applied as `txn-7e5518bb96b35e50d79840c7496209d2`; projected and post-apply validation passed. Preceding rejected attempts and preparation corrections are described in `review.md`.
- Workspace remains the existing linked worktree. Issue-specific branch: `codex/111-runtime-provenance-and-validation-mode-separation`.

## Remaining

R01/R02 in fresh Codex/Claude tasks remain unperformed. Merge, publication and installation are complete and verified separately; the new CLI/MCP process evidence is recorded in the joint release. No second publication or repeated implementation is needed. Do not treat unknown host prompt-skill loading as passed or overwrite the valid installed receipt to fill missing Git provenance.

## Stream B Evidence

- RED: five installer tests failed for missing receipts, conflicting-version overwrite, invalid-payload exposure and missing atomic/Git-evidence helpers.
- GREEN: installer/runtime/operation-audit suite passed 59 tests. A further symlink test then reproduced an external-manifest write before payload rejection; moving link validation before staged manifest writes fixed it. The expanded suite passed 60 tests.
- Cache tests use temporary homes only. Repeated identical packages retain receipt bytes; conflicting versions and invalid payloads never replace/activate the prior cache. New receipt writes are classified as package-maintenance.

## Stream C Evidence

- RED: new consumer/inventory checks failed with 5 failures and 2 errors (9 existing inventory tests remained green).
- GREEN: full MCP, Doctor, installed-staleness and runtime suites passed 82 tests in 1.439s.
- Source/package identity no longer comes from a selected project or newest cache. MCP initialization and subsequent status/Doctor calls share injected startup evidence. Wrong-target checks run before parent Git/project discovery; valid unrelated-plugin projects remain project targets.

## Stream D Evidence

- Source under verification: `517ec64`; source version `0.3.55`. The 25 unrelated untracked Issue 103 plans remain unstaged and preserved.
- `python3 -m unittest tests.test_runtime_provenance_simulation -v`: exit 0, 12 scenarios passed in 4.363s. Final MCP/error-path plus simulation run: `python3 -m unittest tests.test_mcp_server tests.test_runtime_provenance_simulation -q`, exit 0, 45 tests in 4.500s.
- Inline review found a missing runtime object on internal MCP dispatch errors. RED raised `KeyError: data`; GREEN retains startup evidence in JSON-RPC error data. See `review.md`.
- `python3 scripts/release_check.py .`: exit 0, valid=true, all 13 checks passed on `517ec64`. An earlier attempt failed only the HEAD version-bump gate while the 0.3.55 edits were uncommitted; it was not waived.
- `python3 scripts/validate_project_artifacts.py .`: exit 0, valid=true, errors=[]; pre-existing optional/dependency warnings remain.
- `python3 scripts/project_lifecycle.py . --drift`: exit 0, [].
- `python3 scripts/spec_consistency.py . --issue-id 111-runtime-provenance-and-validation-mode-separation`: exit 0, 8 acceptance checks, 0 findings.
- `git diff --check`: exit 0 before the release-preparation commit; repeat after evidence edits.
- The first quiet full-suite run was interrupted (exit 130) after review added the dispatch-error regression, not recorded as passed. The last sampled stack was in an existing live `gh auth status` preflight. A new verbose full-suite run on the committed implementation is the final authority; do not infer a hang cause or passing result from that stack alone.
- The verbose run exposed an existing security/lint regression fixture that was not a source target. The new early source guard correctly rejected it before downstream checks; the test then raised `KeyError: security_check`. `b5c3ce3` identifies that synthetic fixture as a source, retaining both security and syntax assertions. Focused regression passed (1 test, 0.723s). The final full rerun uses bundled native Git via process-local PATH/GIT_EXEC_PATH/GIT_TEMPLATE_DIR; no host configuration or test selection was changed.
- That pre-fix verbose run finished with 1,610 tests in 567.758s, exit 1, exactly one error in the security/lint fixture. Retained as failure history, not counted as a pass.

### Observed Synthetic Package

Created and validated from `tests.runtime_provenance_fixture.make_distribution` via `copy_plugin_cache` in a temporary home on `517ec64`; temporary directory cleaned after inspection. This is an offline fixture, not a deployed package or the source commit's full distribution digest.

| Field | Actual observation |
|---|---|
| Package version | `0.2.0+codex.test` |
| Injected installation time | `2026-09-02T00:00:00Z` |
| Payload SHA-256 | `346bbfeff98bf94a3e3b506527f580936e08596d0310c8170335b005772f149e` |
| Receipt / installed self-check | valid / true |
| Receipt source commit / dirty | null / null; `source_not_git_checkout` (synthetic fixture) |
| Evidence error codes / exit | [] / 0 |
| Actual host loading | Not observed; not implied by any simulation |
## Final Local Verification

- Final full suite on `b5c3ce3`: `python3 -m unittest discover -s tests -v` with the process-local bundled Git environment described above — exit 0, **1,610 tests passed in 337.291s**. Includes the repaired downstream security/lint fixture and both nested release-check regressions; no tests skipped or removed.
- Lifecycle/state/dashboard are refreshed through Issue 103's atomic API, not direct JSON edits. The legacy structural router still recommends execute for an active issue with complete spec/plan/tasks; that is not authorization to repeat implementation or publish. The human next action is implementation review; review-lifecycle refinement remains Issue 113.
- Final evidence transaction: `txn-4d457511ed8638cc47c65f1f4b3dc54e` applied with projected/post-apply validation true (earlier checkpoint: `txn-ab4884a1f626a10d714923c0eb7ffe7b`). After evidence edits, artifact validation passed with 0 errors / 21 existing warnings, lifecycle drift [], spec consistency 8 checks / 0 findings, and `git diff --check` exit 0.

## Real-Host Observations R01/R02 — recorded 2026-09-04

Performed during the 0.3.62 release. Package path, version, process startup and host skill loading are recorded separately; an unobserved field stays unobserved rather than passing.

### R01 — Codex

| Field | Observation |
| --- | --- |
| Installed package | `~/.codex/plugins/cache/personal/moduflow/0.3.62+codex.20260904022744` |
| Version reported by the host | `0.3.62+codex.20260904022744`, after restarting the Codex process |
| Version reported before restart | **`0.3.57`**, in a newly opened task inside the already-running process, while every path on disk already resolved to 0.3.62 |
| Source evidence | Receipt `payload_sha256` `f628b458c169f3bd…96ffbe`, `source_commit` `faa5ff3`, `source_dirty` true (untracked Issue 103 plan documents present in the build worktree) |
| CLI startup | Observed working: `product:status` returned a full report |
| MCP process | **Still not directly observed.** `product:doctor` was run in Codex on 2026-09-04 and returned a full report, but its output does not state whether it was invoked through the `moduflow_doctor` MCP tool or through the skill/CLI path, so MCP startup cannot be claimed from it |
| New-package code actually executing | **Observed.** The Codex Doctor report includes an `분석 실행 기록 미초기화` line. That gate did not exist in 0.3.57; it was added with Issue 091 and ships first in 0.3.62. Its presence evidences the new package's code running, independently of the reported version string |
| Installed package self-check | 199 files passed in installed mode; project artifacts valid with zero errors; lifecycle drift none; no incomplete transactions |
| Provenance honesty | The report surfaced `faa5ff3`의 dirty source without prompting, matching the receipt |
| Host prompt-skill loading | Observed indirectly: the report rendered ModuFlow's own status format. No direct host-exposed skill evidence was available |

The negative observation is the substantive one. A new task is not a new process, and the process keeps the package it loaded at start. This is the failure mode this issue exists to make visible, reproduced under controlled conditions. `docs/release-checklist.md` step 7 was corrected from "start a new Codex task" to "restart the Codex process" as a direct result.

### R02 — Claude

Observed in the Claude session that performed the release, which began before the local plugin link was moved from 0.3.57 to 0.3.62. The three layers separate cleanly and disagree with each other, which is the distinction this issue requires.

| Layer | Observation |
| --- | --- |
| Host registration | Present. ModuFlow skills appeared in the session's skill listing at start |
| MCP process | **Failed.** `moduflow (CONNECTION_CLOSED)` at session start; no ModuFlow MCP tool was available for the whole session |
| Prompt skills | Loaded, but from the pre-switch package. The session started while `~/.claude/plugins/local/moduflow` still pointed at 0.3.57, and a running session does not re-read the link |

### Package-level check, separate from either host

Both packages were started directly and probed over stdio, outside any host:

| Package | Handshake | Reported version | Tools |
| --- | --- | --- | --- |
| `0.3.62+codex.20260904022744` | `initialize` returned, exit 0, empty stderr | `0.3.62+codex.20260904022744` | 5 |
| `0.3.57+codex.20260810222010` | `initialize` returned, exit 0, empty stderr | `0.3.57+codex.20260810222010` | 5 |

Tools in both: `moduflow_status`, `moduflow_issues`, `moduflow_issue_get`, `moduflow_doctor`, `moduflow_ready`.

R02's MCP failure is therefore **not** a package defect. The server starts and answers correctly when launched directly; the failure occurred in the host's own startup path and its cause is not observable from inside the failed session. One unverified lead is recorded without being claimed: `.mcp.json` interpolates `${CLAUDE_PLUGIN_ROOT}`, and both manifests point at that same file, so a host that does not set that variable would resolve an empty path. Whether Codex sets it was not tested.

### What remains unobserved

- Codex MCP process startup. `product:doctor` in a fresh Codex process would supply it.
- Direct host-exposed prompt-skill package evidence on either host. Neither host offered a field stating which package its loaded skills came from; this stays unknown rather than inferred from a matching version string.
