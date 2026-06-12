# Validation And Distribution Spec

## Problem

ModuFlow now includes migration, profile, knowledge, portfolio, and workflow layers. Before it can be used reliably as a shared plugin, users need repeatable validation, upgrade, and release checks.

## Users

- Plugin maintainers preparing a release.
- Project owners validating a workspace before or after migration.
- Agents checking whether a portfolio workspace can be trusted.

## Goals

- Add project artifact validation beyond package file existence.
- Add portfolio registry validation.
- Add release checks that combine plugin validation, tests, project doctor, and documentation checks.
- Document install, upgrade, and release process.

## Non-Goals

- Remote package registry automation.
- Hosted SaaS control plane.
- Signing or notarizing release artifacts.

## Requirements

- `scripts/validate_project_artifacts.py` validates `.moduflow/config.json`, `.moduflow/state.json`, profile, knowledge, workflow, and workspace artifacts.
- `scripts/portfolio_doctor.py` validates `projects.json` entries and reports project status warnings.
- `scripts/release_check.py` runs package validation, unit tests, project doctor, project artifact validation, and release document checks.
- Release docs explain Codex/Claude update flow, cachebuster, validation, and rollback notes.
- `product:doctor`, `product:release`, and `product:sync` docs reference the strengthened checks.

## Acceptance Criteria

- A valid ModuFlow project returns no project artifact validation errors.
- Invalid state/config JSON returns validation errors.
- A portfolio with a missing project path reports a warning.
- Release check succeeds for the current repo.
- Validator requires the new scripts and docs.

## Next Command

`product:plan 006-validation-and-distribution`
