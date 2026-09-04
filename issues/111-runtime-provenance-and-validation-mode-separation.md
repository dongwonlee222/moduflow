# Issue 111: Runtime Provenance and Validation Mode Separation

**Status: done** — created 2026-08-21; started 2026-09-02; done 2026-09-04.
**Priority: p1**
**Blocked-by:**

## Summary

Separate source-release validation, installed-plugin self-check, and target-project Doctor semantics, and expose trustworthy runtime/package provenance in product status and Doctor output.

## Source

- Type: accepted external validation findings `F003` / `MF102-VALIDATION-MODE-CONFLATION` and `F004` / `MF102-RUNTIME-PROVENANCE-GAP`
- Review packet: `workspace/reviews/2026-08-21-issue-102-post-release-validation.json`
- Verified against: source `010eee8eeec37edd6902f2dd008e7164f715e7b1` and installed package `0.3.49+codex.20260810222010`
- Owner / decision maker: Dongwon Lee
- Current phase: implementation, inline self-review, 1,610 tests and source release gates passed; human integration review pending. Lifecycle remains active; required before the next plugin release.

## Opportunity

Source checks correctly expect Git history, tests, issues, and specs, but those assumptions make a healthy installed plugin look broken. At the same time, status and Doctor do not reveal which package and source revision the host actually loaded, so source success cannot prove runtime identity.

## Scope

### In

- Define explicit target roles for source release check, installed-plugin self-check, and target-project Doctor.
- Keep source release validation strict while making installed-package validation independent of `.git`, source tests, and repository-only artifacts.
- Make Doctor identify or reject an installed-cache target instead of reporting misleading project defects.
- Record and expose runtime version, resolved package path, source commit, installed-at, loaded-at, host/session, and provenance source.
- Represent unavailable provenance as `null` plus a reason; never infer or fabricate it from a nearby source checkout.
- Surface the same provenance contract through product status, Doctor, and relevant MCP responses.
- Have packaging/installation write immutable provenance metadata that the runtime can read without source-repository access.

### Out

- Canonical project path migration or capability enforcement.
- Weakening source release gates.
- Treating source commit equality as proof that a host reloaded the new package.

## Acceptance Criteria

- Source release check continues to require and validate source-only release artifacts.
- Installed-plugin self-check passes a valid cache package without requiring `.git`, issues, specs, or the full source test tree.
- Project Doctor validates only target projects and returns a clear target-role error or redirect for an installed cache.
- Product status, Doctor, and relevant MCP responses expose one consistent provenance schema.
- Runtime version, package path, source commit, installed-at, and loaded-at are shown when known; unknown values include explicit reasons.
- Installation writes provenance metadata atomically, and runtime reporting reads the metadata from the actually loaded package.
- Tests cover source checkout, valid installed cache, stale cache, missing metadata, and source/runtime mismatch.
- Issue 065 staleness detection remains valid and consumes rather than duplicates the new provenance fields.

## Verification

- Source, installed-package, and target-project mode contract tests.
- Provenance serialization and mismatch fixtures.
- Installed-cache smoke check for the packaged artifact.
- `python3 scripts/release_check.py .`

## Entry Points

- `scripts/release_check.py`
- `scripts/validate_moduflow.py`
- `scripts/project_doctor.py`
- `scripts/mcp_server.py` and `commands/product-status.md` (there is no `scripts/project_status.py` in the inspected source)
- plugin packaging and installation scripts
- MCP product/status response adapters

## Scope Fence

Do not relax source validation or report guessed provenance. This issue does not block Issue 103 implementation, but it must complete before the next plugin release.

## Workflow Tasks

- [x] spec draft → `specs/111-runtime-provenance-and-validation-mode-separation/spec.md` (Korean sidecar; approved 2026-09-02)
- [x] plan draft → `specs/111-runtime-provenance-and-validation-mode-separation/plan.md` (four inline streams; approved 2026-09-02)
- [x] execute → validation modes, provenance metadata/reporting, and tests; final verification in status.md
- [x] review → `specs/111-runtime-provenance-and-validation-mode-separation/review.md` (accepted 2026-09-04)

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up: `065-runtime-freshness-detection`, `102-project-registry-and-resolver`
- supersedes:
- related: `024-artifact-schema-and-doctor-gates`, `105-schema-migration-and-doctor-triage`

## Links

- Goal: `workspace/goal.md`
- Roadmap: `workspace/roadmap.md`
- Review packet: `workspace/reviews/2026-08-21-issue-102-post-release-validation.md`
- Finding source: `specs/102-project-registry-and-resolver/external-review-2026-08-21.json`
- Spec: `specs/111-runtime-provenance-and-validation-mode-separation/spec.md`
- Plan: `specs/111-runtime-provenance-and-validation-mode-separation/plan.md`
- Tasks: `specs/111-runtime-provenance-and-validation-mode-separation/tasks.md`
- Simulation matrix: `specs/111-runtime-provenance-and-validation-mode-separation/simulation-matrix.md`

## Sessions

- 2026-09-02: User requested the next plan and simulation testing after the priority refresh and role-reduction confirmation. Drafted spec/plan/tasks plus 12 offline scenarios and 2 separately authorized host observations. Existing partial source-file exclusion is retained. No implementation, installer execution, version bump, remote publication or completion claim is authorized by creating these drafts.

## Next Command

`product:review 111-runtime-provenance-and-validation-mode-separation` — review implementation and recorded source gates; authorize integration/publication separately. Actual host observations remain pending.
