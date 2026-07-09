# Frontend QA Template Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reusable frontend QA planning templates that fill the readiness dimensions introduced by issue 077.

**Architecture:** Add framework-agnostic Markdown templates under `templates/frontend-qa/`, wire them into command/skill guidance, and add validation coverage so the template pack remains part of ModuFlow's distributable surface.

**Tech Stack:** Markdown templates, Python validation list, unittest, ModuFlow Git-native artifacts.

---

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

- Do not install or assume Storybook, MSW, Playwright, React, Vue, Next.js, or any framework.
- Templates must be copyable and short enough to use inside `specs/<issue>/frontend-qa/`.
- Every template must include issue/spec traceability fields.
- 078 owns evidence shapes only; 077 owns readiness gate behavior.
- Keep command guidance conditional: frontend-only templates are not mandatory for backend-only or docs-only issues.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — templates | writing-plans + frontend QA review | Template wording must be consistent, copyable, and framework-agnostic. |
| B — validation | Superpowers TDD + focused unittest | New distributable files should be locked by tests before adding to validation. |
| C — command guidance | product-design + review | Design/prototype/review docs need to expose the right handoff moments. |
| D — verification | verification-before-completion | Template pack completion needs fresh validation and release-check evidence. |

## File Structure

- Create `templates/frontend-qa/README.md`: pack overview, required/optional/not-applicable matrix, copy guidance.
- Create `templates/frontend-qa/api-contract-mapping.md`: endpoint/data contract mapping.
- Create `templates/frontend-qa/storybook-required-states.md`: component/screen state list.
- Create `templates/frontend-qa/msw-fixture-catalog.md`: fixture catalog for mocked API states.
- Create `templates/frontend-qa/playwright-smoke-matrix.md`: route/action/assertion smoke coverage matrix.
- Create `templates/frontend-qa/qa-evidence-checklist.md`: final evidence checklist for review.
- Modify `scripts/validate_moduflow.py`: add the new template files to `REQUIRED_FILES`.
- Modify `tests/test_validation_distribution.py`: assert the frontend QA templates are part of the required distribution surface.
- Modify `commands/product-plan.md`, `commands/product-design.md`, `commands/product-prototype.md`, `commands/product-review.md`: add concise references to the template pack.
- Modify `skills/design-prototype-bridge/SKILL.md`: mention frontend QA pack when design/prototype work will become implementation.
- Update 078 issue/status/tasks/roadmap artifacts.

## Interfaces

- Template consumers copy from:

```text
templates/frontend-qa/<template>.md
```

- Recommended destination in a project issue:

```text
specs/<issue>/frontend-qa/<template>.md
```

- Required template fields:

```markdown
Issue: `<issue-id>`
Spec: `<spec path>`
Owner:
Reviewer:
Status: draft|ready|not_applicable
```

## Tasks

### Task 1: Validation Coverage

**Files:**
- Modify: `tests/test_validation_distribution.py`
- Modify: `scripts/validate_moduflow.py`

- [ ] **Step 1: Write failing validation test**

Add a test that checks `validate_moduflow.REQUIRED_FILES` includes:

```python
expected = {
    "templates/frontend-qa/README.md",
    "templates/frontend-qa/api-contract-mapping.md",
    "templates/frontend-qa/storybook-required-states.md",
    "templates/frontend-qa/msw-fixture-catalog.md",
    "templates/frontend-qa/playwright-smoke-matrix.md",
    "templates/frontend-qa/qa-evidence-checklist.md",
}
self.assertTrue(expected.issubset(set(validate_moduflow.REQUIRED_FILES)))
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
python3 -m unittest tests.test_validation_distribution -v
```

Expected: new test fails because the required list does not include the frontend QA templates.

- [ ] **Step 3: Add files to validation list**

Add the six template paths to `scripts/validate_moduflow.py` under the existing `templates/` group.

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
python3 -m unittest tests.test_validation_distribution -v
```

Expected: the new validation-list test passes once files exist.

### Task 2: Template Pack

**Files:**
- Create: `templates/frontend-qa/README.md`
- Create: `templates/frontend-qa/api-contract-mapping.md`
- Create: `templates/frontend-qa/storybook-required-states.md`
- Create: `templates/frontend-qa/msw-fixture-catalog.md`
- Create: `templates/frontend-qa/playwright-smoke-matrix.md`
- Create: `templates/frontend-qa/qa-evidence-checklist.md`

- [ ] **Step 1: Create README**

Include:

- pack purpose
- copy destination
- required/optional/not-applicable matrix
- reminder that 077 owns readiness gate behavior

- [ ] **Step 2: Create five templates**

Each template must include traceability fields, concise tables, and a `Review Notes` section. Do not include framework-specific imports or commands.

- [ ] **Step 3: Run validation**

Run:

```bash
python3 scripts/validate_moduflow.py .
```

Expected: passes and includes the new required files.

### Task 3: Command And Skill Guidance

**Files:**
- Modify: `commands/product-plan.md`
- Modify: `commands/product-design.md`
- Modify: `commands/product-prototype.md`
- Modify: `commands/product-review.md`
- Modify: `skills/design-prototype-bridge/SKILL.md`

- [ ] **Step 1: Update `product:plan`**

Add a short reference under implementation readiness inputs:

```text
For frontend work, copy the relevant templates from `templates/frontend-qa/` into `specs/<issue>/frontend-qa/`.
```

- [ ] **Step 2: Update design/prototype docs**

Mention Storybook required states and QA evidence checklist as handoff surfaces when design/prototype work is headed toward implementation.

- [ ] **Step 3: Update review docs**

Ask reviewers to check frontend QA template-derived evidence for UI/API-backed browser work.

- [ ] **Step 4: Update design bridge skill**

Point design/prototype bridge users to `templates/frontend-qa/` when UI work needs implementation handoff.

### Task 4: Dogfood, Review, And Verification

**Files:**
- Create: `specs/078-frontend-qa-template-pack/tasks.md`
- Modify: `specs/078-frontend-qa-template-pack/status.md`
- Modify: `issues/078-frontend-qa-template-pack.md`
- Modify: `workspace/roadmap.md`

- [ ] **Step 1: Update 078 artifacts**

Mark plan/execute/review states as they complete. Record validation evidence in status.

- [ ] **Step 2: Run full verification**

Run:

```bash
python3 -m unittest tests.test_validation_distribution -v
python3 scripts/spec_consistency.py . --issue-id 078-frontend-qa-template-pack
python3 scripts/validate_moduflow.py .
python3 scripts/validate_project_artifacts.py .
python3 scripts/release_check.py .
```

Expected: no errors. Existing optional memory warnings are acceptable.

## Self-Review

- Spec coverage: all seven acceptance criteria map to Tasks 1-4.
- Placeholder scan: no template placeholders use `TBD`; empty fields are intentional user-fill fields.
- Type consistency: template paths match the validation list and command guidance.
