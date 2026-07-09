# Plan: Plan Discipline and Skill Matrix (079)

Issue: `079-plan-discipline-skill-matrix`
Spec: `specs/079-plan-discipline-skill-matrix/spec.md`
Prev: spec · Next: `product:execute 079-plan-discipline-skill-matrix`

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

1. **Recommendation only**: do not implement readiness blocking or execute gates in this issue.
2. **Host-agnostic wording**: name disciplines and adapter skills, not specific model names.
3. **No old-plan migration**: only update forward-looking command/skill docs and 079 artifacts.
4. **Human-readable first**: do not add a parser/schema until real plan examples prove the need.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — command docs | Spec Kit planning + writing-plans | `product:plan` must consistently instruct agents to include the matrix. |
| B — execution bridge | Superpowers discipline catalog | The bridge owns when writing-plans, TDD, review, and verification should be recommended. |
| C — router docs | ModuFlow PM router | Routing should say that planning surfaces recommended disciplines after spec creation. |
| D — verification | verification-before-completion | Completion needs fresh validation and release gate evidence. |

## Execution Mode

Inline coordinator implementation. The change is documentation/prompt guidance only, with no script behavior or parser changes. Subagents would add overhead and increase wording drift across adjacent docs.

## Interfaces

- `commands/product-plan.md` produces the plan-authoring contract.
- `skills/superpowers-execution-bridge/SKILL.md` produces the discipline catalog and trigger rules.
- `skills/pm-execution-router/SKILL.md` links `product:plan` routing to the matrix.
- `specs/079-plan-discipline-skill-matrix/plan.md` dogfoods the matrix for future examples.

## Tasks

### Stream A — product-plan command

**Files:**

- Modify: `commands/product-plan.md`

- [ ] Add `Recommended Discipline` as a required visible section for new plans.
- [ ] Include a compact example table with `Stream`, `Discipline / Adapter`, and `Reason`.
- [ ] State that the matrix is non-binding and does not replace 077 readiness gates.

### Stream B — Superpowers execution bridge

**Files:**

- Modify: `skills/superpowers-execution-bridge/SKILL.md`

- [ ] Add a `Recommended Discipline Catalog` section.
- [ ] List triggers for writing-plans, TDD, product-design, data-analysis, Storybook/MSW, Playwright/QA, review, and verification-before-completion.
- [ ] Include the data-backed tuning rule: collect examples, encode regression tests when executable, then adjust guidance.

### Stream C — PM execution router

**Files:**

- Modify: `skills/pm-execution-router/SKILL.md`

- [ ] Add a short note that after `product:spec`, `product:plan` should surface recommended disciplines for the issue/task streams.
- [ ] Keep wording separate from 076's fast/shaping/panel router.

### Stream D — Artifact state and validation

**Files:**

- Modify: `issues/079-plan-discipline-skill-matrix.md`
- Modify: `specs/079-plan-discipline-skill-matrix/status.md`
- Modify: `workspace/roadmap.md`
- Create: `specs/079-plan-discipline-skill-matrix/tasks.md`

- [ ] Create/update tasks checklist.
- [ ] Check the plan workflow task.
- [ ] Move 079 to execute-ready state.
- [ ] Run validation gates.

## Gates

- `python3 scripts/validate_moduflow.py .`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Rollback

Revert the 079 branch or the docs commit. No data migration, external state, or generated parser is introduced.
