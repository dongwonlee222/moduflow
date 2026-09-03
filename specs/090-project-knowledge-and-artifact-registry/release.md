# ModuFlow 0.3.57 — Project Knowledge and Artifact Registry

Issue: `090-project-knowledge-and-artifact-registry` · Owner: Dongwon Lee.
Source: approved implementation and explicit 2026-09-03 PR #47 merge/publication/installation approval; see implementation-approval.md.
Phase: implemented, merged, published and installed; canonical Issue 090 completed through the existing transaction. Actual company adoption and fresh Codex/Claude prompt-skill loading are not claimed.
Next: hand off the verified source; remaining implementation priority is 091 → 086 → 092. No next issue is started by this release.

## Purpose and Scope

Preserve discoverable project evidence across tasks: a short wiki, one material metadata catalog, selected-source reads and bounded issue-linked registration. Original documents and company standards remain outside the plugin. The expected benefit is less lost context and more verifiable handoffs, not automatic chat memory or a new execution engine.

## Integration Method

Original implementation `594575b` remains on `codex/090-knowledge-registry-plan`. Its committed changes are squash-integrated into `codex/090-knowledge-registry-integration` so the reviewed source is represented by a correctly issue-linked feature commit, while the original work/history remain available. The source manifests move together from 0.3.56 to 0.3.57 under the repository's pre-1.0 patch policy. No original commit is amended/rebased/deleted.

## Evidence Layers

| Layer | Current state |
| --- | --- |
| Implementation | A1–D2 handed off at 594575b; implementation self-review and integration inspection recorded |
| Focused/synthetic/package checks | Integrated source: 317 passed in 13.531s, including S01–S14 and temporary packaged CLI |
| Full integrated regression / release gates | c89fc65: 1,680 passed in 290.354s; complete release check valid=true, all 13 checks passed |
| Remote PR / CI | [PR #47](https://github.com/dongwonlee222/moduflow/pull/47) merged at 2026-09-03T02:28:12Z as 8869afa3e9e7f0a2f89bd9ea8b77c67ee0480495; PR-head CI passed 1,680 tests in 163.793s and all release checks |
| Exact merged source | [Main CI 33707750960](https://github.com/dongwonlee222/moduflow/actions/runs/33707750960) passed; fresh local complete release check passed all 13 checks on 8869afa; its tree equals tested PR head 0e2ab59 |
| Publication | [v0.3.57](https://github.com/dongwonlee222/moduflow/releases/tag/v0.3.57), published 2026-09-03T02:31:40Z; tag resolves to 8869afa3e9e7f0a2f89bd9ea8b77c67ee0480495 |
| Codex installation | 0.3.57+codex.20260810222010 installed at 2026-09-03T02:31:39.706210+00:00; exact cache explicit installed validation passed, 0 errors / 0 warnings |
| Claude local connection | Existing local link updated to the same validated 0.3.57 distribution; no marketplace installation or fresh Claude-host load claimed |
| Newly launched CLI / MCP | Both exit 0 and identify the installed cache/version. CLI startup 02:32:00.884637Z; MCP startup 02:32:26.917084Z on 2026-09-03; MCP initialize/status agree |
| Canonical completion | txn-0183cd493b66664aea8eebcba03644db applied complete → done; follow-up txn-0f295f85e881c50fd4b96e524248943f preserves the 111 loop cursor. Both projected/post-apply validations passed |
| Real project / fresh host use | Not performed; synthetic handoff is not real-host evidence |

The incoming source's two release-policy failures remain historical evidence and are superseded by observed passing integrated gates. No original history or gate code was rewritten. The 25 prior Issue 103 untracked plans, company data and original implementation post-stop writes are excluded from the release. 111 real-host observations and active cursor remain unchanged; this release does not mark R01/R02 passed.

## Archive, Receipt and Role Evidence

The source archive was exported only from committed 8869afa. Its tar commit ID and release tag match that commit. Archive SHA-256 `88b6edd1b537b082fb52eade0d70f9accea1b40ca11460287c099cebff0a6f28` matches GitHub's uploaded asset digest (2,366,765 bytes). Installed payload SHA-256 `eda5dd63be2682fcae11ceacea55d60e2d4d60211a7f7853063b1a5e03683d70` matches the valid immutable receipt. A separate fake-home installer/installed-validator preflight also passed before real activation.

The export intentionally has no .git. An extra attempt to validate that directory with --mode source returned TARGET_ROLE_MISMATCH because this mode requires a Git checkout; it is not recorded as a passed source check. The actual merged Git worktree passed source validation and all release gates; the prepared and actual caches passed explicit installed validation. No checker was changed or bypassed. The receipt honestly retains source_commit/source_dirty=null with source_not_git_checkout reasons; archive provenance is recorded separately, not invented in the receipt. The retained Codex build suffix is not an installation timestamp.

The published package is immutable. Completion/evidence-only commits after the tag update repository records, not the already validated package. A fresh CLI/MCP proves a process started from the cache; host/session remain unknown and do not prove that this or another AI conversation reloaded its prompt skills.

Completion bookkeeping observation: the current completion renderer clears the loop cursor and marks that loop done even when another canonical issue remains active. Read-only inspection caught this after completing the separately implemented 090. A bounded follow-up through the existing loop transaction restored active 111/active loop without changing any issue, state or dashboard bytes. Project validation then passed with lifecycle_drift=[]. This is an explicit projection reconciliation, not a claim that the generic completion renderer or consensus coverage was redesigned; retain this case for the existing 113 lifecycle review scope. No code change or new issue was introduced in delivery.

## Rollback and Adoption

The prior 0.3.56 source/cache and all older caches remain intact. Before activation, preserved Codex configuration, personal marketplace JSON and the exact user/Codex/Claude symlink targets in an owner-only persistent release directory outside Git. Configuration and marketplace files compare byte-identically with their backups after installation. Only the intended cache and links were activated; default-checkout files and other task worktrees were not edited.

Before a later approved downgrade, recover unfinished transactions through the existing 103 interface. Restore only the recorded settings/link values or use an explicitly approved validated package; never remove user catalogs, source artifacts, IDs or transaction evidence. Project adoption begins with missing-only initialization, reviewed share-safe metadata and explicit registration; it does not crawl existing company folders. No company source or business metric was placed in the plugin.
