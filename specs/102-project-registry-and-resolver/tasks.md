# Tasks: Project Registry and Resolver

Issue: `102-project-registry-and-resolver`
Plan: `specs/102-project-registry-and-resolver/plan.md`
Status: active — implementation complete; final distribution and release verification in progress

## Stream A — Registry and Resolver Contract

- [x] **A1** Add `projects.v2` parser, normalized registry model, stable diagnostics, Unicode alias normalization, and root/path containment tests.
- [x] **A2** Add deterministic precedence, conflict warnings, ambiguous/unresolved results, candidate redaction, and negative project-I/O tests.

## Stream B — Compatibility and Portfolio

- [x] **B1** Add v1 read compatibility, deterministic migration proposals, selected-context materialization, explicit-root compatibility, and recent-selection state.
- [x] **B2** Move portfolio initialization/render/resolve/select flows and this repository's registry fixture to v2 after v1 tests pass.

## Stream C — Consumer Convergence

- [x] **C1** Converge intake, loop, lifecycle, Doctor, and migration on the shared context and configured workspace/issue/spec paths.
- [x] **C2** Converge production records, playbooks, memory/knowledge, dashboard panels, and MCP reads with Project A/B isolation.
- [x] **C3** Converge execution, PR, GitHub issue sync, promotion, repository audit, and issue generation writes on canonical paths.

## Stream D — Distribution and Verification

- [ ] **D1** Update package validation/release modules, run spec consistency, focused/full tests, project validation, lifecycle drift, release check, diff hygiene, and produce status/review evidence.

## Required Gates

- [ ] All 13 Issue 102 acceptance criteria have test or status evidence.
- [ ] `ambiguous` and `unresolved` perform zero candidate project-local content reads and zero writes.
- [ ] Existing Issue 093 configured-path/containment tests remain green.
- [ ] `projects.v1` fixture remains byte-identical after read/migration proposal.
- [ ] Project A/B nested-path fixtures show no issue, memory, record, playbook, or writer leakage.
- [ ] `python3 scripts/spec_consistency.py . --issue-id 102-project-registry-and-resolver` has no blocking error.
- [ ] Full test discovery passes.
- [ ] Project validation and release check are valid with `errors: []`.
- [ ] Lifecycle drift is `[]` and `git diff --check` is clean.

## Next Command

`product:status 102-project-registry-and-resolver`.
