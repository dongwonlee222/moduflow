# Release Preparation: Issue 111 / 0.3.55

Issue: `111-runtime-provenance-and-validation-mode-separation`
Owner: Dongwon Lee
Source: approved `spec.md` / `plan.md`; implementation `517ec64`; `status.md` / `review.md`.
Phase: local release preparation; not published or installed.
Next command: `product:review 111-runtime-provenance-and-validation-mode-separation`.

## What Changes

Source, installed-package and target-project validation now have explicit roles. Status/Doctor/MCP report evidence for their executing package and process. The installer stages and validates a receipt-bearing package without replacing a conflicting existing cache.

ModuFlow does not gain an execution engine, scheduler or host watcher. Missing host/skill-load evidence stays unknown.

## Evidence Stages

| Stage | Status | Evidence / remaining gate |
|---|---|---|
| Implementation | Complete locally | `a1e5ae6`, `aac78e5`, `a7ccdca`, `517ec64`; fixture correction `b5c3ce3` |
| Focused tests | Passed | 45 final MCP/simulation tests; earlier stream evidence in status |
| Offline simulations | Passed | S01–S12; synthetic projects and fake homes only |
| Packaged CLI/MCP smoke | Passed | Temporary installed layout, isolated imports, persistent MCP and fresh CLI |
| Full source tests | Passed | Fresh PR verification on `8229170`: 1,610 tests, 359.621s, exit 0; no skipped tests |
| Source release check | Passed | Repeated on `83b338e`: exit 0, all 13 checks, including strict source/version/security/linkage gates |
| Review | Inline self-review complete | Not independent or human merge approval; see review |
| Remote PR | Draft created | https://github.com/dongwonlee222/moduflow/pull/45; issue branch pushed |
| Remote CI | Pending at handoff | Use latest-head checks on PR #45, not this static snapshot, for the current result |
| Merge | Not performed | Requires explicit human integration approval |
| Publication | Not performed | Requires human approval; Issue 103's previous approval does not authorize this release |
| Installed package | Not performed | Real user caches/registrations have not been changed |
| Codex R01 / Claude R02 | Not performed | Fresh-host observations follow separately authorized installation |

The source manifests are `0.3.55` (Claude) and `0.3.55+codex.20260810222010` (Codex). The retained build suffix is not an installation date, host-load timestamp, or publication claim. Use a new explicitly selected build suffix at publication if required by the existing cachebuster workflow.

## Approved Publication Procedure — Not Yet Executed

1. Finish human implementation review, integrate the PR and confirm remote CI.
2. Re-run the source release check on the exact approved source. Select a clean approved source snapshot for packaging: the current worktree contains 25 unrelated untracked plans that must be preserved, not deleted or silently shipped. Preserve old package paths and registration/link values.
3. After explicit installation approval, package/install that source. Validate the returned cache with `--mode installed --json`; retain the receipt and payload digest.
4. Start fresh Codex/Claude tasks for R01/R02. Record process path/version/startup separately from any host-provided skill-load evidence. Unavailable fields remain unavailable.

## Rollback

Before installation, retain the previous approved cache and host registration/link values. On preparation failure, do not activate the failed package. On later activation failure, report the failing stage and, with explicit approval, restore the retained registration/link values and verify a restarted process. This is not a promise of atomic host-config rollback.

Never delete a conflicting cache, edit its immutable receipt or hard-reset a dirty source worktree. Source rollback is an explicit revert of Issue 111 commits, not removal of existing user changes. Keep the current worktree and its 25 pre-existing untracked Issue 103 plans.
