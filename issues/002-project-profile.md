# Issue 002: Project Profile

**Status: done** — `scripts/project_profile.py` shipped in the 0.1.x era; status.md shows all verification passed. Status line added 2026-07-06 (issue 066 follow-up: files whose specs-link line matched the migration's `Status:` grep were skipped).

## Summary

Create a standard project profile layer for product context, environments, integrations, ownership, and operating notes.

## Source

- Type: product direction
- Link: user conversation
- Date: 2026-06-11

## Opportunity

Multi-project work needs consistent project metadata so agents and teammates know where a project lives, who owns it, how it is deployed, and which links matter.

## Scope

### In

- Add project profile template.
- Add environment and integration metadata conventions.
- Update `.moduflow/config.json` path support.
- Document sensitive data rules.

### Out

- Storing credentials, secrets, signed documents, or private personal data.

## Acceptance Criteria

- Each ModuFlow project can describe owner, repo, docs, environments, deployment targets, and integrations.
- Sensitive data is explicitly excluded.
- Profile fields are usable by status, doctor, and portfolio flows.

## Links

- Spec: `specs/002-project-profile/spec.md`
- Status: `specs/002-project-profile/status.md`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:spec 002-project-profile`
