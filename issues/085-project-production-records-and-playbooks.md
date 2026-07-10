# Issue 085: Project Production Records and Playbooks

**Status: active** — created 2026-07-10, started 2026-07-10.
**Priority: p1**

## Summary

Add a project-local production knowledge model for recurring deliverables such as event pages, banners, home popups, PR articles, press releases, ad creatives, partnership proposals, Alimtalk, SMS, and Push messages.

## Source

- Type: user product direction
- Link: local Codex session, 2026-07-10
- Owner / decision maker: Dongwon Lee
- Date: 2026-07-10

## Opportunity

ModuFlow records what an issue delivered, but recurring production work also needs to preserve why a version was selected, what failed, which wording or layout can be reused, and what future work must avoid. Generic work logs and memory notes are too weakly structured to reliably improve the next production cycle.

## Product Decision

Keep the workflow inside ModuFlow, but keep every project's actual production records and playbooks inside that project's repository. ModuFlow owns the schema, templates, commands, validation, retrieval, and promotion workflow; each project owns its brand language, source inputs, artifacts, failures, and approved patterns.

## Scope

### In

- Define a project-local `Production Record` linked to its source issue and arbitrary artifact locations or external URLs.
- Standardize sections: `Artifacts`, `Source Inputs`, `Decisions`, `Failed Attempts`, `Reusable Patterns`, `Do Not Repeat`, and `Playbook Updates`.
- Add structured fields for deliverable type, channel, audience, lifecycle state, owner, dates, source issue, and linked playbook.
- Separate external/media/customer-facing copy from internal reporting copy within the same production record.
- Support event pages, banners, home popups, PR/press, ad creatives, partnership proposals, Alimtalk, SMS, and Push without hardcoding one company's content into ModuFlow.
- Define project-local playbooks as approved reusable knowledge, distinct from per-job production records.
- Require explicit human approval before a candidate pattern is promoted into a playbook or copied across projects.
- Provide natural-language and command guidance for registering a completed or in-progress production artifact.
- Preserve project portability: Git Markdown remains canonical; external indexes and dashboards are derived views.

### Out

- A central database that owns production knowledge outside project repositories.
- Requiring source assets to live in a fixed folder; registered links and metadata are canonical.
- Automatically promoting a single failure or model-generated suggestion into a playbook.
- Sharing brand copy or internal learnings across projects without explicit human approval.
- Building the dashboard UI; that is Issue 086.

## Acceptance Criteria

- A project can register a recurring deliverable even when its final asset lives in a different local folder or an external service.
- Every production record contains the seven standard sections and links to its source issue when one exists.
- Records distinguish deliverable type, channel, audience, external copy, and internal reporting copy.
- Playbooks contain only human-approved reusable patterns and `Do Not Repeat` rules, with source-record links.
- Project A and Project B can use the same ModuFlow schema while keeping their records and playbooks fully separate.
- Search/retrieval can find records by project, type, channel, audience, issue, pattern, or failure.
- Validation detects missing artifact links, dangling issue/playbook references, and unapproved playbook promotion.
- Focused tests and `python3 scripts/release_check.py .` pass.

## Verification

Commands the executing agent runs to self-check before handing off.

- `python3 -m unittest tests.test_project_memory -v`
- `python3 scripts/validate_project_artifacts.py .`
- `python3 scripts/release_check.py .`

## Entry Points

Starting files/components for the executing agent.

- `scripts/project_memory.py`
- `commands/product-memory.md`
- `templates/memory/entry.md`
- `skills/pm-execution-router/SKILL.md`
- `scripts/validate_project_artifacts.py`
- `tests/test_project_memory.py`

## Scope Fence

Do NOT force projects to reorganize existing asset folders. Do not store sensitive internal drafts in a shared/global ModuFlow package. Do not make external databases or vector indexes canonical.

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec, plan, design, or review off the books. Check the box and link the artifact when done.

- [x] spec → `specs/085-project-production-records-and-playbooks/spec.md` (+ `spec.ko.md`)
- [x] plan → `specs/085-project-production-records-and-playbooks/plan.md` + `tasks.md`
- [x] execute → production record/playbook schema, commands, validation, and tests
- [x] review → `specs/085-project-production-records-and-playbooks/review.md`
- [x] dogfood → banner and press-release records plus an approved banner playbook in `tests/fixtures/production-project/`

## Related Issues

- blocks: `086-project-aware-production-library-dashboard`
- blocked_by:
- duplicates:
- follows_up: `030-project-memory-layer`, `040-automatic-memory-candidate-capture`
- supersedes:
- related: `033-business-document-workflow`, `038-worker-context-memory-path-injection`, `043-memory-relationship-capture-prompts`, `075-issue-less-context-capture`

## Sessions

- 2026-07-10: User defined recurring production knowledge requirements across event, banner, PR, advertising, partnership, Alimtalk, SMS, and Push work.
- 2026-07-10: User decided records and playbooks must be project-local; ModuFlow provides only the reusable capability and schema.

## Links

- Spec: `specs/085-project-production-records-and-playbooks/spec.md`
- Status: `specs/085-project-production-records-and-playbooks/status.md`
- Sessions: `sessions/085-project-production-records-and-playbooks/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`product:pr 085-project-production-records-and-playbooks`
