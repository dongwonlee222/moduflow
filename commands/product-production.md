---
description: Capture, search, retrieve, and approve project-local recurring production knowledge.
argument-hint: "[project path] [--init|--new-record|--search|--retrieve|--validate|--decide-playbook]"
---

# /product:production

Manage recurring production records and human-approved playbooks for banners, event pages, PR, ads, proposals, Alimtalk, SMS, Push, and similar deliverables. Keep source assets where they already live; register project-relative paths or `https` links.

## Flow

1. Initialize optional project-local paths without overwriting existing content:

```bash
python3 scripts/project_production.py <project-path> --init
```

2. Capture a record linked to an issue or explicit source context:

```bash
python3 scripts/project_production.py <project-path> --new-record --title "Summer banner" --issue-id 123-summer-event --type banner --channel home-popup --audience customer --lifecycle draft --retrieval-trigger "when creating mobile banners" --variant mobile
```

Open the returned Markdown file and complete `Artifacts`, `Source Inputs`, `Decisions`, `Failed Attempts`, `Reusable Patterns`, `Do Not Repeat`, `Playbook Updates`, `External Copy`, and `Internal Reporting Copy`.

3. Search or retrieve scoped context:

```bash
python3 scripts/project_production.py <project-path> --search "mobile banner" --type banner --channel home-popup --audience customer
python3 scripts/project_production.py <project-path> --retrieve --type banner --channel home-popup --audience customer --limit 5
```

4. Review a candidate playbook and record an explicit named-human decision:

```bash
python3 scripts/project_production.py <project-path> --decide-playbook approve --record-id 2026-07-10-summer-banner --playbook-id banner-mobile --approved-by "Dongwon Lee" --reason "validated on mobile" --decided-at 2026-07-10
```

`approve`, `reject`, and `defer` all append an audit entry. Approval succeeds only when `--approved-by` exactly matches a name or email in `.moduflow/humans.json`.

## Result Actions

- `created`: a new template was written.
- `noop`: the existing generated record is byte-for-byte unchanged.
- `update_required`: a matching populated record already exists; open and update it manually.

## Rules

- Git Markdown inside the selected project is canonical.
- Never move source assets just to register them.
- Never promote model-generated patterns without explicit human approval.
- Never mix or scan sibling projects.
- External indexes and dashboards are derived views.

## Next

Run `product:production --search "mobile banner" --type banner --channel home-popup` before the next similar production task.
