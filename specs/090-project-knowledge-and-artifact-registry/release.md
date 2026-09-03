# Issue 090 — Source Release Candidate

Issue: `090-project-knowledge-and-artifact-registry` · Owner: Dongwon Lee.
Source: approved 2026-09-03 integration/version/full-verification/PR request.
Phase: source candidate 0.3.57; final integrated gates pending. Not published or installed.
Next: verify integrated feature commit, then open a Draft PR against main. Main merge, publication and installation are not authorized by this request.

## Purpose and Scope

Preserve discoverable project evidence across tasks: a short wiki, one material metadata catalog, selected-source reads and bounded issue-linked registration. Original documents and company standards remain outside the plugin. The expected benefit is less lost context and more verifiable handoffs, not automatic chat memory or a new execution engine.

## Integration Method

Original implementation `594575b` remains on `codex/090-knowledge-registry-plan`. Its committed changes are squash-integrated into `codex/090-knowledge-registry-integration` so the reviewed source is represented by a correctly issue-linked feature commit, while the original work/history remain available. The source manifests move together from 0.3.56 to 0.3.57 under the repository's pre-1.0 patch policy. No original commit is amended/rebased/deleted.

## Evidence Layers

| Layer | Current state |
| --- | --- |
| Implementation | A1–D2 handed off at 594575b; implementation self-review and integration inspection recorded |
| Focused/synthetic/package checks | 317 passing in incoming-source recheck; integrated-source rerun pending record |
| Full integrated regression / release gates | Pending after versioned integration commit |
| Remote PR / CI | Pending |
| Main merge / publication / installation | Not authorized or performed |
| Real project / fresh host use | Not performed; synthetic handoff is not real-host evidence |

The incoming source's two release-policy failures remain in historical status evidence. Only actual integrated gate results may supersede them. 111 real-host observations and canonical cursor are unchanged. All prior Issue 103 untracked plans, company data, original implementation post-stop state writes, and installed caches are excluded.

## Rollback and Adoption

Keep existing 0.3.56 installation until publication is separately approved. Before any later downgrade, recover unfinished transactions using the existing 103 recovery interface. Revert only approved code changes; never remove user catalogs, source artifacts, IDs or transaction evidence. Project adoption begins with missing-only initialization, reviewed share-safe metadata and explicit registration; it does not crawl existing company folders.
