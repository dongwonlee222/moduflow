# Project Profile Spec

## Problem

Multi-project work needs a consistent way to describe project context, ownership, environments, deployment targets, documentation links, and integrations. Without a profile, agents and teammates must infer project facts from scattered files or conversation history.

## Users

- Project owners setting up ModuFlow.
- Agents running `product:status`, `product:doctor`, and future portfolio views.
- Team members onboarding to a project.

## Goals

- Add standard project profile files.
- Keep secrets and sensitive documents out of Git.
- Make project metadata easy for doctor and portfolio flows to read.
- Preserve existing files during profile generation.

## Non-Goals

- Storing credentials, API keys, personal private data, signed documents, or legal originals.
- Replacing environment managers, deployment tools, or password managers.
- Enforcing enterprise permissions.

## Artifact Structure

```text
.moduflow/
  project-profile.md
  environments.json
  integrations.json
```

## Requirements

- `scripts/project_profile.py` supports dry-run by default.
- `scripts/project_profile.py --write` creates missing profile files only.
- Existing profile files are never overwritten.
- `project_doctor.py` reports profile initialization and missing profile files.
- `.moduflow/config.json` supports `profile`, `environments`, and `integrations` paths.
- `product:profile` documents usage and sensitive data rules.

## Acceptance Criteria

- A new project can generate profile metadata files with `--write`.
- A project with existing profile files keeps their content unchanged.
- Doctor output includes `profile.initialized` and `profile.missing`.
- Validator requires the new command, script, and templates.

## Sensitive Data Rules

- Store links or labels, not secrets.
- Do not store credentials, tokens, private keys, signed originals, seals, identity documents, or direct personal contact/payment identifiers.
- Use environment variable names or secret manager references when needed.

## Next Command

`product:plan 002-project-profile`
