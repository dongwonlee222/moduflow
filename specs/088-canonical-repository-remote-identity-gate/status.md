# Status: Canonical Repository/Remote Identity Gate

Issue: `088-canonical-repository-remote-identity-gate`
Phase: pr
Updated: 2026-07-16

## Implemented

- Added one canonical `git.identity` parser, credential-safe Git URL normalizer, Git/provider inspector, capability matrix, operation decision CLI, and artifact-link classifier.
- Added explicit profile proposal/write behavior; legacy `git.remote` is a confirmation candidate only.
- Recorded and verified ModuFlow canonical identity: `github.com/dongwonlee222/moduflow`, `origin`, `main`, `active`.
- Added report-only identity evidence to doctor and status/repo-sync output.
- Added first-write hard stops for execute, commit, push, GitHub Issue sync, PR preflight, and release command flow.
- GitHub Issue/PR workflows resolve explicit canonical `owner/repo`; stale issue/PR/release handoff links block provider writes.
- Added artifact validation warnings for undeclared non-canonical read links and errors for non-canonical write handoffs.
- Review fixed three safety gaps: generic providers cannot advertise GitHub writes/releases, accidental parent Git roots block writes, and local-only/generic projects cannot select GitHub API commit fallback.

## Verification

- `python3 -m unittest discover -s tests -p 'test_*.py'` — 527 tests passed.
- Focused identity/link/issue suites — 40 tests passed after the generic-provider capability fix.
- Focused identity/Git handoff suites — 35 tests passed after Git-root and API-fallback fixes.
- `python3 scripts/spec_consistency.py . --issue-id 088-canonical-repository-remote-identity-gate` — 0 errors, 0 warnings.
- `python3 scripts/validate_moduflow.py .` — passed, 137 required files checked.
- `python3 scripts/validate_project_artifacts.py .` — valid, 0 errors.
- `python3 scripts/release_check.py .` — valid; validation, linkage, lint, security, version bump, tests, and doctor checks passed.
- Live `release` identity decision — `allowed: true`, status `match`, project root and provider repository/default branch/archive/fork evidence matched.

## Review

- Verdict: code/spec approved after fixes; no unresolved critical or important code findings.
- Constitution: v1.0 checked; no violation remains after isolating the 088 scope on a dedicated branch with an issue-linked commit.
- Review artifact: `specs/088-canonical-repository-remote-identity-gate/review.md`.
- Visual evidence: `memory/dashboard.html`, `memory/issue-088-canonical-repository-remote-identity-gate.html`.
- Converge: 17 AC entries are `unverifiable` because the implementation is uncommitted and the numbered AC parser returned `parseable:false`; direct review/test evidence is recorded separately.
- Independent subagent review was unavailable under the active execution constraints; the same QA/spec/constitution concerns were reviewed inline and the limitation is explicit.

## Non-Blocking Findings

- Artifact audit reports nine existing external GitHub links without explicit `reference` or `mirror` wording. They are read-only warnings, not write-handoff errors; cleanup can be handled during review or a follow-up documentation pass.
- The original worktree's staged and unrelated unstaged changes were preserved. The 088 scope was isolated into a clean worktree from `origin/main`, and unrelated changes were excluded.
- GitHub issues `#18`–`#24` mirror local issues `088`–`094`; historical completed issues were not bulk-created.

## Next

`product:pr 088-canonical-repository-remote-identity-gate`
