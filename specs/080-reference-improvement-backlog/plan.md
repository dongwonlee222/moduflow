# Reference Improvement Backlog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a project-local backlog for reference repo/template improvement candidates discovered during normal ModuFlow work.

**Architecture:** Add a Markdown backlog template under `templates/workspace/`, a small stdlib Python CLI that can dry-run or append records to `workspace/reference-improvements.md`, and command guidance that keeps the backlog optional and separate from active execution scope.

**Tech Stack:** Markdown templates, Python stdlib, unittest, ModuFlow Git-native artifacts.

---

## Global Constraints

- Do not open or mutate external GitHub repositories.
- Do not make reference-improvement records release blockers.
- Keep the record shape append-only and readable in plain Markdown.
- Dry-run mode must not write files.
- Duplicate title/source pairs should not append a second record.
- Keep promotion explicit: records may mention a promotion target, but only `product:promote` or a user-approved workflow creates normal issues.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — capture CLI | Superpowers TDD | The append/no-write/duplicate behavior needs executable tests. |
| B — template distribution | git-native artifact model | The backlog is a Git-versioned workspace artifact. |
| C — command routing | pm-execution-router | Capture points live in plan/execute/review/status/loop/promote flow. |
| D — verification | verification-before-completion | New package surface must pass validation and release checks. |

## File Structure

- Create `scripts/project_reference_backlog.py`: build/dry-run/write candidate records.
- Create `tests/test_project_reference_backlog.py`: test dry-run, write, duplicate handling, and CLI behavior.
- Create `templates/workspace/reference-improvements.md`: copyable backlog surface.
- Modify `scripts/validate_moduflow.py`: require the new template and script.
- Modify `tests/test_validation_distribution.py`: assert the new files are in the distributable surface.
- Modify `commands/product-plan.md`, `commands/product-execute.md`, `commands/product-review.md`, `commands/product-status.md`, `commands/product-loop.md`, and `commands/product-promote.md`: document when to capture, surface, and promote.
- Update 080 issue/status/tasks/roadmap artifacts.

## Tasks

### Task 1: RED Tests For Reference Backlog CLI

**Files:**
- Create: `tests/test_project_reference_backlog.py`

- [ ] **Step 1: Add tests**

Add tests that load `scripts/project_reference_backlog.py` and verify:

```python
entry = project_reference_backlog.build_entry(
    title="Backoffice table filters need empty state",
    source="github:webn77/ai-native-backoffice-ui/components/table",
    gap="The reference table has filter states but no empty-result example.",
    recommendation="Add empty-result Storybook and fixture examples.",
    issue_id="080-reference-improvement-backlog",
    today="2026-07-09",
)
```

Expected fields include `status == "candidate"`, `priority == "p2"`, origin spec path `specs/080-reference-improvement-backlog/spec.md`, and a stable ID beginning with `ref-2026-07-09-`.

- [ ] **Step 2: Verify RED**

Run:

```bash
python3 -m unittest tests.test_project_reference_backlog -v
```

Expected: fail because `scripts/project_reference_backlog.py` does not exist yet.

### Task 2: GREEN Implementation

**Files:**
- Create: `scripts/project_reference_backlog.py`

- [ ] **Step 1: Implement entry builder**

Implement `slugify`, `build_entry`, and `render_entry_markdown` with only stdlib modules.

- [ ] **Step 2: Implement write behavior**

Implement `load_or_create_backlog`, `append_entry`, and duplicate detection based on `Title` + `Source reference`.

- [ ] **Step 3: Implement CLI**

Add arguments:

```text
<project-path>
--title
--source
--gap
--recommendation
--issue-id
--priority
--status
--promotion-target
--date
--write
```

Dry-run prints JSON. Write mode appends Markdown and prints JSON with `written: true` or `duplicate: true`.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
python3 -m unittest tests.test_project_reference_backlog -v
```

Expected: pass.

### Task 3: Template And Distribution Validation

**Files:**
- Create: `templates/workspace/reference-improvements.md`
- Modify: `scripts/validate_moduflow.py`
- Modify: `tests/test_validation_distribution.py`

- [ ] **Step 1: Add failing distribution test**

Assert `REQUIRED_FILES` includes:

```python
{
    "templates/workspace/reference-improvements.md",
    "scripts/project_reference_backlog.py",
}
```

- [ ] **Step 2: Add template and validation entries**

Create the backlog template and add both new files to `REQUIRED_FILES`.

- [ ] **Step 3: Verify**

Run:

```bash
python3 -m unittest tests.test_validation_distribution -v
python3 scripts/validate_moduflow.py .
```

Expected: pass.

### Task 4: Command Guidance And Dogfood

**Files:**
- Modify: `commands/product-plan.md`
- Modify: `commands/product-execute.md`
- Modify: `commands/product-review.md`
- Modify: `commands/product-status.md`
- Modify: `commands/product-loop.md`
- Modify: `commands/product-promote.md`
- Create/Modify: `workspace/reference-improvements.md`

- [ ] **Step 1: Add command guidance**

Document capture moments in plan/execute/review, optional surfacing in status/loop, and explicit promotion through product:promote.

- [ ] **Step 2: Dogfood one record**

Run:

```bash
python3 scripts/project_reference_backlog.py . --issue-id 080-reference-improvement-backlog --title "Frontend QA templates need target-project examples" --source "local:078-frontend-qa-template-pack" --gap "The template pack is reusable, but target-project examples should be collected after real usage." --recommendation "Promote after two frontend projects reuse the pack and reveal stable examples." --write
```

Expected: creates or appends `workspace/reference-improvements.md`.

### Task 5: Review, Verification, And Packaging

**Files:**
- Modify: `issues/080-reference-improvement-backlog.md`
- Create: `specs/080-reference-improvement-backlog/tasks.md`
- Modify: `specs/080-reference-improvement-backlog/status.md`
- Modify: `.claude-plugin/plugin.json`

- [ ] **Step 1: Update artifacts**

Mark issue tasks and status evidence with completed verification.

- [ ] **Step 2: Run full verification**

Run:

```bash
python3 -m unittest tests.test_project_reference_backlog -v
python3 -m unittest tests.test_validation_distribution -v
python3 -m unittest discover -s tests -v
python3 scripts/spec_consistency.py . --issue-id 080-reference-improvement-backlog
python3 scripts/validate_moduflow.py .
python3 scripts/validate_project_artifacts.py .
python3 scripts/release_check.py .
```

Expected: all commands pass.

## Self-Review

- Spec coverage: all seven acceptance criteria map to Tasks 1-5.
- Placeholder scan: no plan step uses unresolved implementation placeholders.
- Type consistency: CLI argument names match the spec and tests.
