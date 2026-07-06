---
id: 2026-07-06-issue-less-context-benchmark
kind: evidence
title: Issue-Less Context Capture External Benchmark
issue_id: 075-issue-less-context-capture
spec: specs/075-issue-less-context-capture/spec.md
source_event: subagent-web-research
date: 2026-07-06
tags: [benchmark, context, issue-tracking, promotion-gates]
summary: External precedents for issue-less capture with promotion gates across GitHub Discussions, Linear Triage, Shape Up, ADR, Azure DevOps/Jira link gates, Zettelkasten, and OSS CI checks.
---

# Issue-Less Context Capture — External Benchmark

Researched 2026-07-06 via web-research subagent for issue `075-issue-less-context-capture`.

## Per-source findings

### 1. GitHub Discussions → Issues
- Conversion trigger: when a discussion becomes actionable (question → bug, idea → decision). One-click "Create issue from discussion"; the new issue keeps a reference to the source discussion. ([docs](https://docs.github.com/en/discussions/guides/best-practices-for-community-conversations-on-github))
- Empirical study: most conversions happen on **maintainer judgment**, not automatic rules. ([Springer](https://link.springer.com/article/10.1007/s10664-023-10366-z))
- Failure mode: reverse conversion (issue → discussion) reads as "ticket dismissed" — teams adopted canned responses explaining why. Conversion is a communication event. ([community thread](https://github.com/orgs/community/discussions/3197))
- Capture friction stays low because discussions need no labels/assignees; the de-facto promotion trigger is needing execution tracking (assignee, board).

### 2. Linear Triage / Asks
- All external intake becomes an **issue in a Triage quarantine state** — not a separate record type. Promotion = Accept; alternatives = Decline / merge Duplicate / Snooze. ([Linear docs](https://linear.app/docs/triage))
- Duplicate merge auto-transfers attachments and customer requests to the canonical issue — metadata survives promotion.
- Asks forms impose minimal structure at capture time while submitters never touch Linear. ([Asks](https://linear.app/docs/linear-asks))
- Inbox rot is prevented by **triage responsibility rotation** (a person, not a gate).

### 3. Shape Up (Basecamp)
- Ladder: raw idea → shaping (private) → pitch → bet. Only shaped pitches reach the betting table; the gate is "is risk sufficiently removed". ([ch.6](https://basecamp.com/shapeup/1.5-chapter-06), [ch.8](https://basecamp.com/shapeup/2.2-chapter-08))
- **No backlog**: unbet pitches are dropped, not tracked. "Important ideas come back." Re-promotion requires a person bringing it back with context. ([ch.7](https://basecamp.com/shapeup/2.1-chapter-07))
- Failure mode: organizational memory depends on individuals; advocate leaves → idea dies.

### 4. ADR
- Decisions captured ticket-less as markdown in-repo; approval flow **is** the PR merge. ([MS](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record), [adr.github.io](https://adr.github.io/))
- Bidirectional links: References section → tickets; implementation PRs → back-reference the ADR. AWS manages ADR states (proposed → approved → superseded). ([AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html))
- Death cause: nobody defines **when an ADR is mandatory or who reviews** — undefined triggers kill the institution. ([analysis](https://hidekazu-konishi.com/entry/architecture_decision_records_templates_and_operations.html))
- Notable: decision records survived as a first-class terminal artifact that never needs ticket promotion.

### 5. Jira / Azure DevOps link-enforcement gates
- Azure "Check for linked work items" branch policy: Required/Optional; bypass held by a small senior "Emergency Bypass" group, not individuals. ([docs](https://learn.microsoft.com/en-us/azure/devops/repos/git/branch-policies?view=azure-devops))
- Rollout failure pattern: enabling all policies at once triggers team revolt — **gradual adoption** (build → 1 reviewer → link required) is the norm. ([field guide](https://www.grizzlypeaksoftware.com/library/advanced-branch-policies-enforcing-code-quality-at-scale-ers5lz66))
- Jira smart commits link but cannot enforce; silent partial failures exist (commit succeeds, link silently fails). ([Atlassian](https://support.atlassian.com/jira-software-cloud/docs/process-issues-with-smart-commits/))
- Practitioner complaints: forced-ticket policies breed **one-line fake tickets**, empty umbrella tickets, and commit messages reduced to ticket numbers — gates check link existence, not link quality. ([HN 1](https://news.ycombinator.com/item?id=21295078), [HN 2](https://news.ycombinator.com/item?id=39882702))

### 6. Zettelkasten / Obsidian promotion ladder
- fleeting (1-2 sentences, speed-first) → review session triage: **promote or discard** → permanent (rewritten in own words — promotion cost is the quality filter) → project reference. ([forum](https://forum.zettelkasten.de/discussion/3142/fleeting-to-permanent-notes))
- Folder separation (Inbox/Literature/Permanent) gives visual raw-vs-polished distinction. Promotion is rewriting, not moving.
- Failure mode: skipping periodic review → infinite inbox pile-up. Discard being an explicit option is essential.

### 7. OSS CI "no code without issue" checks
- nearform check-linked-issues action: detects closing keywords; escape hatches = branch excludes, label excludes, and a **`no-issue` skip label** that auto-removes prior warning comments. ([repo](https://github.com/nearform-actions/github-action-check-linked-issues))
- danger.js at Artsy: `#trivial` self-declaration marker skips rules. ([danger.systems](https://danger.systems/js/))
- GitLab Danger bot: notice/warning/error tiers — **only error fails the pipeline**; single updated comment suppresses noise. ([GitLab](https://docs.gitlab.com/development/dangerbot/))

## ModuFlow 075 design takeaways

1. **Issue-compatible schema for issue-less records** (Linear): store capture records with issue-compatible frontmatter so promote is a state transition + ID issuance, with attachments/links auto-transferred.
2. **Machine-checkable promotion triggers** (ADR death cause): the 075 gates (code change, multi-session, needs execution) must be checkable fields judged by doctor/release-check, not maintainer mood.
3. **Staged gate rollout** (GitLab Danger, Azure rollout failures): support notice → warn → error graduation as config, even if this project starts at release-error.
4. **Auditable escape hatch** (nearform/danger.js/Azure): a self-declared approved-issue-less marker, with the release notes exposing the list of such declarations — a fake one-line issue is worse for traceability than an honest no-issue declaration.
5. **Auto-written bidirectional links at promote time** (GitHub/ADR): `promoted_to` on the record + `promoted_from` on the issue, written by the tool — manual linking will be skipped.
6. **Expiry/archive for unpromoted records** (Shape Up + Zettelkasten failure): auto-archive after N days/releases (Git keeps history); reactivation is an explicit human act with context; archive list stays queryable.
7. **`decision` is a terminal type** (ADR): a decision with no code change never requires promotion; a decision that triggers code change does.
8. **Rot prevention is an ops loop, not a gate** (Linear rotation, Zettelkasten review): status/goal-loop always shows unpromoted-record count and oldest age; doctor warns past thresholds.
