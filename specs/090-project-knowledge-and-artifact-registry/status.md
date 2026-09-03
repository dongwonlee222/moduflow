# Issue 090 Implementation Evidence

Issue: `090-project-knowledge-and-artifact-registry` · Owner: Dongwon Lee
Authority: [implementation approval](implementation-approval.md), 2026-09-02 user approval.
Phase: A1–D2 implementation and evidence ready for integration review; full regression 1,678 passed / 2 release-policy failures. Release policy remains blocked. Canonical lifecycle remains backlog and shared cursor remains 111 by instruction.
Next: integration owner reviews this local implementation and resolves release linkage/version plus lifecycle conditions; no release or lifecycle mutation is authorized here.

## Why Needed / Problem / Expected Benefits

Another project/task needs to find the material used by earlier work. Scattered paths and ambiguous approval/original states are insufficient. The expected benefit is scoped, selective retrieval and verified issue linkage without source duplication; no measured adoption benefit is claimed.

## A1 — Schema and Missing-Only Initialization

- Integrated authorized `22c01c9` by fast-forward from `7779b42`; no default checkout/cache or other worktree changed.
- RED: new schema tests failed because the parser was absent; existing initialization missed the two workspace files. Separate archived-plan test proved policy was lost when apply omitted its context.
- GREEN: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_project_knowledge_registry tests.test_project_knowledge tests.test_project_memory -q` — 76 tests passed, 1.490s, exit 0.
- Added sole fenced-JSON parser, stable ID/metadata/link/supersession checks, sanitized rejection, six-section wiki and catalog templates. Missing-only initialization reports partial failure and preserves nested context/policy across plan/apply.
- Legacy nested-path regression exposed omitted apply-context; fixed by carrying the validated context in the plan and checking capability on apply. No permission gate was removed.
- New feature simulations, transaction extension, full regression and package/release checks are not yet executed. No remote publication/installation or actual company/host trial.

## B1 — Project-Scoped Selective Reads

- RED: eight facade tests failed before implementation. A further duplicate-ID test proved that an invalid duplicate could incorrectly leave a valid winner; parser now rejects both.
- GREEN: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_project_knowledge_registry tests.test_project_knowledge tests.test_project_memory -q` — 85 tests passed, 3.017s, exit 0.
- Added read envelopes, metadata-only search, explicit source selection, safe no-follow descriptor reads, pinned Git tree/blob reads, link/period/availability diagnostics, and visible result/home omissions.
- Real temporary Git tests prove dirty local content and author-only uncommitted content do not replace committed sources. External/private locators are handoffs, never automatically fetched.
- S01–S14 remain a distinct D2 simulation gate; no full regression/package completion claim yet.

## C1 — Issue-Linked Transaction and Failure Recovery

- RED: seven initial adapter tests failed before the bounded action existed; added tests exposed missing prerequisite detection and failure to detect a source changed during apply or replaced with identical bytes.
- GREEN: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_project_knowledge_registry tests.test_project_knowledge_registry_transaction tests.test_project_knowledge tests.test_project_memory tests.test_project_lifecycle_transaction tests.test_project_lifecycle_transaction_storage -q` — 289 tests passed, 8.973s, exit 0.
- Existing 103 lock/journal/storage handles the bounded catalog/owning-issue/new-output branch. Shared lifecycle projections are unchanged byte participants; caller-supplied target bytes are never consumed by the registration facade.
- Four target replacements injected before and after (eight cases) roll back and retry successfully. Simulated process interruption is recovered through the existing public recovery operation. Source changes remain external and are never undone; registration is rolled back instead.
- Source fingerprints bind observable inode/device and content; checks run at planning, under lock and after apply. Same-ID amendments require explicit opt-in and preserve surrounding prose. Missing transaction initialization fails preview before lock creation.
- Integration found the projected context omitted the explicit-root authority marker needed by permission-checked reads. It now preserves only that recognized marker, retaining policy checks and omitting resolver prose. The regression asserts real read authorization instead of requiring the authority input to be absent.
- Synthetic fixture setup was corrected to include existing transaction prerequisites and a real numeric issue without a bogus `none` dependency. No validator, policy or transaction gate was weakened.
- Remaining: C2 user entrypoints, D1 integration, D2 expanded simulations/full/package gates. No merge, release, installed-cache or company data changes.

## C2 — Explicit Creation and CLI

- RED: legacy result lacked `registered`; opt-in creation parameter and CLI read/register switches were absent. Real subprocess tests then found explicit-root contexts use empty-string IDs, not null; the read facade now represents that compatibility context as unbound/null.
- GREEN: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_project_knowledge tests.test_project_memory tests.test_project_knowledge_registry tests.test_project_knowledge_registry_transaction -q` — 103 tests passed, 5.429s, exit 0.
- Opt-in knowledge creation uses C1 before writing an original; repeat is noop. Existing memory source bytes/IDs/relationships are retained. Legacy saves retain old fields and add `registered=false`.
- CLI exposes metadata inspection/query, exact-ID source reads, committed refs, JSON registration preview, explicit write and explicit amendment. Read and write modes cannot be mixed; source reads require IDs. Knowledge/memory command guidance explains prerequisites, unbound identity, retained preview IDs, partial initialization and saved/unregistered versus shared/approved.
- Remaining D1/D2 gates are not reported as passed.

## D1 — Shared Diagnostics and Distribution Surface

- RED: Validator/Doctor exposed no registry summary, ignored malformed present catalogs and skipped the 21st broken link behind the default result limit. Package checks omitted the parser/templates/tests. A proposed facade mutation classification was rejected by the existing audit because the facades deliberately perform no direct mutation; those incorrect entries were removed instead of weakening the auditor.
- GREEN: focused D1 + knowledge/transaction tests: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_project_doctor tests.test_project_operation_audit tests.test_release_check tests.test_project_knowledge_registry_transaction -q` — 108 tests passed, 5.942s, exit 0. Dedicated registry diagnostic/inventory tests passed 4/4. Package and project validators pass on the source tree.
- Operation audit: valid, 94 classified, zero unclassified/unguarded/stale/duplicate/configuration findings. Canonical path guard: valid, 25 classified and zero prohibited/unclassified/stale/duplicate findings. The new package-source template path has one exact classification; target paths still use the resolved workspace role.
- Validator/Doctor call the canonical read facade once with an unbounded validation limit; they do not parse the catalog again. Missing optional wiki/catalog yields initialization guidance, present malformed metadata is an error, and each entry retains separate metadata/availability/freshness/share axes. Doctor now passes its supplied nested project context through validation.
- Distribution inventory includes the runtime parser and both templates; source-only inventory includes three registry test/fixture modules. Release focused test command now includes both behavior suites.
- The complete release check is intentionally still failing two integration-owned policy gates: behavior commits `3cd88b1` and `2420417` lack accepted issue linkage in their commit messages, and 0.3.56 has no version bump. No history rewrite, version or release action was authorized; the integration task was notified directly. These failures are not represented as feature-test failures or changed into exceptions.

## D2 — Observed Simulations and Self-Review

- S01–S14 and a temporary packaged CLI smoke test pass. The [simulation matrix](simulation-matrix.md) records actual assertions, the metadata/selected-source read trace and disposable Git OIDs. This is a real local Git/worktree simulation, not an installed-host observation.
- Final focused command: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_project_knowledge tests.test_project_memory tests.test_project_knowledge_registry tests.test_project_knowledge_registry_transaction tests.test_project_knowledge_registry_simulation tests.test_project_lifecycle_transaction tests.test_project_lifecycle_transaction_storage -q` — **317 tests passed in 12.692s, exit 0** on 2026-09-03, including all D2 fixes.
- [Implementation self-review](implementation-review.md) maps AC1–AC9 and records PM/spec, privacy and transaction boundaries. It is explicitly the implementer's own review, not independent/subagent review. AC9 remains partial because release-policy readiness is not satisfied.
- Regression fixes reuse the shared issue-ID validator, reject incomplete/orphan metadata and draft approval/empty issue-list violations, reject URL token fragments, provide safe relative diagnostic locations, fail non-object CLI JSON cleanly, preserve concurrent initialization files with exclusive creation, and preserve original issue bytes when appending backlinks.
- Release test inventory includes the simulation module; distribution source inventory requires it without shipping test files as runtime assets. Packaged smoke constructs a disposable distribution and synthetic target outside the source checkout; installed cache is untouched.
- Spec consistency: 9 criteria checked, zero flagged and zero error/warning/info findings. Diff whitespace check passes. Final operation/path/project/package audit results are recorded below with the full-suite outcome.

## Final Gate Record — 2026-09-03

Full command: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` — **1,680 tests in 477.722s, exit 1: 1,678 passed, 2 failed**. The two failures are `ValidationDistributionTests.test_release_check_succeeds_for_current_repo` and `ValidationDistributionTests.test_release_check_uses_importable_validation_for_safe_checks`, both asserting the release check's aggregate `valid` flag. The separate complete release result identifies only the linkage/version policy failures below; no feature assertion failed. The earlier quiet run was interrupted for progress diagnosis after about 5.5 minutes and is not counted as completed evidence. The completed verbose run uses the final D2 runtime code.

| Check | Observed result |
| --- | --- |
| Operation ownership audit | Valid; 94 classified; 0 unclassified, unguarded, stale, duplicate or configuration errors |
| Canonical path guard | Valid; 25 classified; 0 unclassified, prohibited, stale or duplicate findings |
| Project artifact validator | Valid; errors=[] |
| Package validator, explicit source mode | Valid; errors=[] |
| Spec consistency | 9 criteria checked; 0 flagged; 0 error/warning/info findings |
| Diff whitespace | Exit 0 |

Release check: `valid=false`; only accepted-issue-linkage and version-bump policy checks fail. Project/package validation, canonical paths, operation ownership, provenance, lint, security, focused release tests, Doctor and required release/upgrade documents pass. Exact policy errors name commits `3cd88b1`/`2420417` and unchanged version 0.3.56. Existing history and policy were not altered to conceal these failures.

Protected scope: no changes since approved `22c01c9` in `.moduflow`, `workspace`, `.claude-plugin` or `.codex-plugin`; no company data, default checkout, other task worktree, installed-cache, remote push/PR/merge or publication changes. New local commits use the approved 090 branch and an explicit Issue trailer. Integration owns release linkage/version and the single-active lifecycle reconciliation.
