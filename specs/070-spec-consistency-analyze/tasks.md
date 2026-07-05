# Tasks: Spec Consistency Analyze

Issue: `070-spec-consistency-analyze`
Plan: `specs/070-spec-consistency-analyze/plan.md`

## Stream A — Checker

- [ ] Section/bullet/token helpers (fence-aware)
- [ ] Coverage check (token overlap, "possibly uncovered" warns)
- [ ] Vague-term lint (no-digit bullets only)
- [ ] Structural tracing (streams both directions, missing AC, empty tasks)
- [ ] Artifact-presence info findings + JSON report + CLI

## Stream B — Docs

- [ ] `commands/product-plan.md` Next recommendation
- [ ] `commands/product-execute.md` soft pre-check note

## Stream C — Tests

- [ ] All AC cases + ordering stability + fence exclusion
- [ ] `scripts/release_check.py` module list

## Verification

- [ ] RED → GREEN; full discover; release_check
- [ ] Dogfood smoke on specs/069

## Next

`product:execute 070-spec-consistency-analyze`
