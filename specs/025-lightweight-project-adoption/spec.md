# Spec: Lightweight Project Adoption

## Issue

`025-lightweight-project-adoption`

## Source Request

User request to lightly improve ModuFlow's footprint in target projects, so that target projects remain clean and light (similar to POKit2's thin-residue style).

## Owner

Dongwon Lee

## Phase

spec

## Problem

Currently, initializing ModuFlow in a project via `/product:start` or migration copies all tool scripts, commands, templates, and skills directly into the project root. This makes target repositories heavy, cluttered with implementation code, and difficult to upgrade when ModuFlow gets updated upstream.

## Goals

- Define a **lightweight mode** for target projects where only durable state and PM artifacts (`.moduflow/`, `workspace/`, `issues/`, `specs/`, `knowledge/`, `workflow/`) are kept in the project.
- Keep execution engine assets (`commands/`, `skills/`, `scripts/`, `templates/`) inside the central ModuFlow plugin/tooling repository.
- Update `/product:start`, `/product:migrate`, and `/product:doctor` to respect and validate the lightweight mode.
- Distinguish between **dogfooding mode** (used within ModuFlow's own repository) and **lightweight mode** (used in adopted target projects).

## Non-Goals

- Completely removing templates and scripts from the ModuFlow repository itself (dogfooding mode is preserved for ModuFlow development).
- Forcing immediate migration of already initialized projects.

## Design

### Project Modes
1. **Dogfooding Mode** (ModuFlow source repo):
   - All directories (`commands/`, `skills/`, `scripts/`, `templates/` + PM artifacts) must exist and be validated.
2. **Lightweight Mode** (Adopted target projects):
   - Only durable state and PM artifact directories must exist.
   - The tool does not copy `commands/`, `skills/`, `scripts/`, or `templates/` into the target project.
   - `product:doctor` verifies that required PM folders exist but does not expect tool/scripts folders.

### Tool Updates
- **`project_doctor.py`**:
  - Detects the mode: If the project path matches the ModuFlow repository, it runs in `dogfooding` mode. Otherwise, it runs in `lightweight` mode.
  - In `lightweight` mode, it skips checks for `commands/`, `skills/`, `scripts/`, and `templates/`.
- **`project_migrate.py` / `project_intake.py`**:
  - Initializing or migrating a project in lightweight mode only writes `.moduflow/`, `workspace/`, and basic templates for PM documents (copied on demand or referenced from the central location).

## Acceptance Criteria

- A new project can be initialized via `product:start` in lightweight mode, resulting in only `.moduflow/`, `workspace/`, `issues/`, `specs/`, and `knowledge/` folders.
- `product:doctor` passes cleanly in a lightweight project directory without complaining about missing commands/skills/scripts.
- `product:doctor` reports the active mode (`lightweight` vs `dogfooding`).
- ModuFlow validation (`validate_moduflow.py`) passes in the source repository (dogfooding mode).

## Next Command

`/product:plan 025-lightweight-project-adoption`
