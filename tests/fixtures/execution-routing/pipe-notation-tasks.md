# Tasks: Pipe Notation Fixture

Issue: `fixture-pipe-notation`

Three lines copied from `specs/103-.../tasks.md` and `specs/110-.../tasks.md`
with only the checkbox changed from `[x]` to `[ ]`. The wording and the
notation are theirs; the open box is this fixture's. Every task in 103, 109 and
110 is checked off, so those files return `not_applicable` today and the
`| Files: …` form they authored can no longer reach Gate 2 from the corpus
(spec 112 §1, measured 2026-09-05). `worker_orchestrator.METADATA_RE` does not
match this form.

## Stream A — Transaction core (from 103)

- [ ] **A1** Define `LifecycleIntent`, deterministic transaction/idempotency identity, plan/result envelopes, hashes, and reusable fixtures with RED/GREEN contract tests. | Files: scripts/project_lifecycle_transaction.py, tests/lifecycle_transaction_fixture.py, tests/test_project_lifecycle_transaction.py
- [ ] **A2** Add canonical target selection, pure renderers, nested/decoy coverage, and complete private projected-root validation. | Files: scripts/project_lifecycle_transaction.py, scripts/project_lifecycle.py, scripts/project_loop.py, scripts/validate_project_artifacts.py, focused tests | Depends: A1

## Stream A — Policy, Resolver, and Audit (from 110)

- [ ] **A2** Attach additive policy fields to every resolver route and surface them in Doctor/portfolio reads. | Files: scripts/project_registry.py, tests/test_project_registry.py, scripts/project_doctor.py, tests/test_project_doctor.py, scripts/project_portfolio.py, tests/test_project_portfolio.py | Depends: A1
