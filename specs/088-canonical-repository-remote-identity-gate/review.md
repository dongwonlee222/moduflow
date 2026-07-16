# Review: Canonical Repository/Remote Identity Gate

Issue: `088-canonical-repository-remote-identity-gate`
Reviewer: coordinator inline review (independent subagent unavailable under active execution constraints)
Date: 2026-07-16
Verdict: code approved after fixes; PR handoff ready on an isolated branch
Spec compliance: pass by direct issue/spec/plan/test inspection; converge criterion-level audit will be refreshed from isolated commits
Quality: pass after three important safety fixes
Constitution: v1.0 checked — no violation; the behavior changes are isolated on `codex/088-canonical-repository-remote-identity-gate` with an `Issue: 088-canonical-repository-remote-identity-gate` commit trailer

## Scope

Reviewed the canonical identity parser, URL normalizer, Git/provider inspection, capability policy, profile projection, doctor/status reporting, execute/commit/push/GitHub write gates, artifact-link audit, command guidance, and focused tests against the issue and canonical spec.

## Findings

1. **Important — generic providers advertised GitHub write/release capability. Resolved.** `github_write` and `release` now require `provider == github`; a regression test proves a healthy generic remote can execute/commit/push but cannot create GitHub PRs or releases.
2. **Important — accidental parent Git roots could pass. Resolved.** The inspector now emits `git_root_mismatch`, reports mismatch status, and blocks every write capability when the observed Git root differs from the requested project root.
3. **Important — local-only/generic projects could select GitHub API commit fallback. Resolved.** `github_api_commit` now maps to the shared `github_write` capability, and the handoff checks it before calling `gh`.
4. **Important — linked worktrees were misclassified as locally unwritable. Resolved.** The handoff now resolves a `.git` worktree pointer to the actual Git directory before its non-destructive probe; the regression test was observed failing before the fix and passing afterward.

No unresolved critical or important code findings remain.

## Spec Compliance

- Canonical identity persists in `.moduflow/config.json` and projects into `.moduflow/project-profile.md` without replacing unrelated content.
- HTTPS, SSH URL, and SCP-style GitHub forms normalize to one credential-free identity; generic paths remain case-sensitive.
- Expected/observed Git, base-ref, provider, lifecycle, artifact-link, and capability evidence use the shared `moduflow.repository-identity.v1` result.
- Doctor/status remain read-only; execute, commit/push, GitHub Issue, PR, and release paths stop at their first write boundary according to operation-specific evidence.
- Current ModuFlow fetch, push, provider repository, default branch, archive state, fork state, and project root match the canonical profile.

## QA Evidence

- `python3 -m unittest discover -s tests -p 'test_*.py'` — 528 passed.
- Focused identity/link/GitHub issue suites — 40 passed after generic-provider fix.
- Focused identity/Git handoff suites — 35 passed after root and fallback fixes.
- `python3 -m unittest tests.test_project_git_handoff -v` — 8 passed after the linked-worktree fix.
- `python3 scripts/validate_moduflow.py .` — passed; 137 required files checked.
- `python3 scripts/validate_project_artifacts.py .` — valid; 0 errors.
- `python3 scripts/release_check.py .` — valid; every check passed.
- Live `release` identity decision — allowed, status `match`.

## Visual Handoff

- Dashboard: `memory/dashboard.html`
- Issue drill-down: `memory/issue-088-canonical-repository-remote-identity-gate.html`

## Converge

- `converge-evidence.json`: `no_evidence: false`; two issue-linked commits and the changed files are present.
- `converge.md`: 17 acceptance criteria recorded as `unverifiable` under the fixed parseability rule.
- The limitation is the numbered AC parser returning `parseable:false`, not missing implementation evidence; direct review and tests remain the criterion evidence.

## Non-Blocking Findings

- Artifact validation reports nine pre-existing external GitHub links without explicit `reference`/`mirror` wording; none is a write handoff.
- GitHub issues `#18`–`#24` now mirror local issues `088`–`094`; Git files remain canonical.

## Reference Improvements

Reference improvements: none found.

## Scope Isolation

- The 088 scope was copied through an isolated Git index into a clean worktree based on the latest `origin/main`.
- Existing staged user changes in the original worktree remain untouched.
- Unrelated GPT guidance and other pre-existing changes were excluded from this branch.

## Human Approval

- 2026-07-16: Dongwon Lee explicitly authorized Codex to complete PR #25 and the stacked PR #26 in the active Codex task.
- This satisfies Constitution C6 for the canonical merge transition; it does not waive CI or release gates.

## Next

`product:release 088-canonical-repository-remote-identity-gate`
