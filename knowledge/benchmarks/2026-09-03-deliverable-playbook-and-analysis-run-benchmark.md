---
kind: benchmark
title: Deliverable-scoped playbooks and reproducible analysis runs — Spec Kit, Agent Skills, and provenance practice
issue_id: "091-reproducible-analysis-runs-and-template-pack"
spec: specs/091-reproducible-analysis-runs-and-template-pack/spec.md
decision_supported: "Whether per-project, per-deliverable process and verification belong in an extended ModuFlow playbook, an external skill, or a new template layer"
date: 2026-09-03
confidence: medium
sources:
  - https://github.com/github/spec-kit
  - https://github.com/github/spec-kit/blob/main/templates/commands/checklist.md
  - https://github.com/github/spec-kit/blob/main/templates/commands/constitution.md
  - https://github.com/github/spec-kit/blob/main/spec-driven.md
  - https://developer.microsoft.com/blog/spec-driven-development-spec-kit/
  - https://github.com/anthropics/skills
  - https://github.com/agentskills/agentskills
  - https://agentskills.io/home
  - https://github.com/topics/data-provenance
  - https://github.com/topics/data-lineage
  - https://github.com/bashebr/ai-native-sdlc
  - https://github.com/DrDroidLab/PlayBooks
  - https://github.com/braintree/runbook
  - https://github.com/aws-samples/achieving-operational-excellence-using-automated-playbook-and-runbook
  - https://github.com/topics/prompt-management
  - https://www.braintrust.dev/articles/best-prompt-management-tools-2026
---

# Deliverable Playbook and Analysis Run Benchmark (2026-09-03)

## Question

The user wants recurring work requests to stop being re-explained every time, scoped per project and per deliverable type, carrying both a process and a verification harness, with document form and approved copy staying consistent. Should that live in an extended `moduflow.playbook.v1`, in an external agent skill, or in a new analysis-template layer proposed by the Issue 091 draft?

## Bottom Line

Split it. Current practice puts **procedure** in portable, versioned, agent-loadable skill packages and puts **approval, evidence and named quality gates** in human-owned repository documents. ModuFlow should reference a procedure rather than invent a second procedure format, and should own the approval and gate records that a skill cannot own.

This retires the separate `templates/analysis/` layer proposed in the Issue 091 draft. It does not authorize a document-generation framework, a lineage engine, or full Spec Kit adoption.

## External Findings

| Pattern | Observed evidence | Implication for ModuFlow |
| --- | --- | --- |
| Immutable principles live in one referenced document | Spec Kit's constitution holds non-negotiable project principles captured once and referenced by every later phase | `workspace/constitution.md` already fills this role; do not add a second principles authority per deliverable |
| Quality gates are reviewer-owned checklists, not implementation state | Spec Kit's `checklist` command generates sequentially numbered items (`CHK001`) described as "unit tests for English" for a chosen domain such as UX or security | The playbook's missing harness should be a named, numbered, human-owned checklist per deliverable type, not an automatic pass |
| Templates are plain, inspectable, version-controlled Markdown in the repository | Spec Kit stores templates under `.specify/templates/` as Markdown | Keeping playbooks as Git-native Markdown in the project is current practice, not legacy |
| Procedure is packaged as a portable, on-demand skill | The Agent Skills format packages procedural knowledge as a folder with a required `SKILL.md` plus optional scripts, references and assets, loaded only when a task matches | A deliverable's process belongs in a skill reference with a version, not in a new ordered-steps section invented here |
| Skill packaging is now a cross-vendor standard, not one vendor's feature | The format was released as an open standard at `agentskills.io` and is reported adopted across many agent platforms and marketplaces | A skill reference keeps ModuFlow host-neutral, matching the goal statement that execution tools stay replaceable |
| Documented provenance is moving from good practice to obligation | Data provenance and lineage are active GitHub topics, and EU AI Act enforcement from August 2026 is reported to require documented provenance for high-risk systems | Issue 091's pinned-source and method record is directionally right; ModuFlow records provenance and must not build a lineage engine |

Adoption figures for the skills ecosystem come from vendor and community write-ups rather than an audited source, so they indicate direction, not a measured market share. Treat the regulatory note the same way: it motivates recording provenance, and it is not a legal assessment of this project.

## Alignment Assessment

| Proposed decision | Assessment | Reason |
| --- | --- | --- |
| A separate `templates/analysis/` template layer | not aligned | Creates a second per-project template system beside playbooks and violates the single-parser principle |
| Analysis template becomes a playbook with `applies_to_types: [analysis]` | aligned | One per-project, per-deliverable carrier that already has version, approval, supersession and evidence |
| Playbook gains a `Required Checks` checklist section | aligned | Matches the reviewer-owned, numbered checklist pattern; keeps gates explicit and human-owned |
| Playbook embeds ordered process steps as new prose | not aligned | Duplicates what skill packages already carry portably and versioned |
| Playbook references a process by skill ref and version | aligned | Keeps ModuFlow a thin management layer and the procedure replaceable |
| Run record pins sources, method and evidence | aligned | Matches the provenance direction and the delivered 090 contract |
| ModuFlow builds lineage, scheduling or document generation | not aligned | Rebuilds replaceable tooling the roadmap already excluded |
| Prove on one deliverable type before generalizing | aligned | Spec Kit's own guidance bounds scope before expanding |

## Decisions for Issue 091

1. Drop the standalone `templates/analysis/` layer. The five accepted templates ship as default playbooks with `applies_to_types: [analysis]`, and a project overrides or adds by name.
2. Add a `Required Checks` section to the playbook as a numbered, human-owned checklist. A checked item is a reviewer assertion, never proof of a passing run.
3. Do not add an ordered-steps section. Add a `process_ref` field naming an external skill or document plus its version, with missing evidence recorded explicitly.
4. Keep the Issue 091 run record as the provenance carrier, and record which playbook version a run used.
5. Prove the two new playbook fields on one deliverable type — the weekly analysis report — before defining any other type.

## Non-Adoptions

- No second template system beside playbooks.
- No ordered-process format invented inside ModuFlow.
- No lineage engine, scheduler, or document generator.
- No automatic checklist pass, automatic approval, or cross-project playbook promotion; those remain with Issues 107 and 108.
- No dependency on an external skill being installed; absence is recorded, not assumed.

## Addendum — GitHub Prior Art and Our Gaps (2026-09-03)

Added after the owner asked whether an existing GitHub project already manages playbooks, so ModuFlow does not rebuild solved work.

### Three families, none a drop-in

| Family | Examples | Why it does not transfer |
| --- | --- | --- |
| Operational runbook automation | `DrDroidLab/PlayBooks`, `braintree/runbook`, the AWS runbook approval-gate sample, Azure Automation source control | Git versioning and approval gates are mature here, but each ships an execution engine and triggers. AWS's sample auto-approves when a wait period elapses, which is the opposite of this project's human-gate principle |
| Prompt library management | Langfuse, Agenta, Latitude, Promptfoo, Pezzo, Braintrust | Conceptually closest — version, approval, audit trail — but the registry is a hosted or self-hosted database. This project keeps Git Markdown canonical and adds no second store |
| AI-native SDLC skill packaging | `bashebr/ai-native-sdlc` | Structurally the nearest match: one skill folder installed to both Codex and Claude, `.codex-plugin/plugin.json` for team publishing, per-project Markdown artifacts scaffolded by `init_workflow.py`, human approval gates between phases, `production-gate.sh` blocking unauthorized deploys, `gate_ledger.py` keeping hash-chained approval records, and a `REVIEW.md` template defining pass criteria, evidence requirements and review limits. It covers software delivery phases, not per-deliverable approved copy and document form |

### Patterns worth adopting

1. **Validate a playbook change the way code is validated.** Braintrust runs evaluations from a GitHub Action whenever a prompt changes in a pull request. ModuFlow already has `scripts/release_check.py`; playbook-shape validation belongs there rather than in a new surface.
2. **Define what a version number means.** Prompt libraries use major for a substantive change and minor for a wording tweak. `moduflow.playbook.v1` has a `version` field with no stated rule, which matters now that Issue 091 pins the version a run used.

### Patterns deliberately not adopted

- A hash-chained approval ledger. With one author who is also the approver, a forgery-resistant ledger adds ceremony without adding trust.
- Any execution engine, trigger or scheduler.
- A registry database, hosted or self-hosted.
- Automatic approval after a timeout.

### Our gaps, ranked

| Gap | Severity | Owner |
| --- | --- | --- |
| **G1 — No path to a project's first playbook.** Defaults live in the plugin and are read-only; a project overrides by name, but nothing created that first project file. The user would have had to hand-author it, costing more than the explanation it replaces, which undermines the "second run needs only the window" promise at exactly the moment it must first pay off. `bashebr/ai-native-sdlc` closes the same gap with `init_workflow.py` scaffolding. A related regression was found at the same time: the run-to-playbook promotion agreed on 2026-09-03 was dropped during the spec's revision-2 rewrite | High | **Closed 2026-09-03** in Issue 091 R7 and Stream E1: scaffold a default into the project, and promote a completed run, both preview-first and `status: candidate` |
| **G2 — `version` has no defined semantics.** The field exists with no rule for when it changes, while Issue 091 pins it per run | Medium | Issue 115 |
| **G3 — A playbook change is not validated on change.** `release_check.py` covers the plugin's own assets; nothing checks a playbook edit in a target project | Medium | Issue 115 A3 for plugin assets; a target project's own CI is out of scope |
| **G4 — Checklist results have no home outside an analysis run.** Issue 091 stores results on the run record. For a non-analysis production deliverable, where a confirmed item is recorded is undefined | Low now, blocking later | Issue 108 |
| **G5 — Approval is editable by anyone with repo write.** Accepted for a single author; it would not hold for a team | Accepted limitation | Recorded, not scheduled |

### Assessment

The direction matches current practice: durable Git artifacts, human approval between phases, per-deliverable contracts, and validation treated as review rather than automation. Nothing found combines project-scoped isolation, deliverable-type approved copy, and Git-Markdown canonical storage the way this project needs, so there is no upstream to adopt wholesale. Where ModuFlow is behind is initialization and version discipline, not architecture. G1 is the one that changes near-term work.

## Next Action

Spec and plan revision 2 landed on 2026-09-03. Remaining from this benchmark: close G1 in Issue 091 Stream E1 and G2/G3 in Issue 115, then request implementation approval.
