---
name: business-plan
description: Use when ModuFlow needs business-document artifacts such as business plans, market-entry analysis, Lean Canvas, business models, customer hypotheses, persona scenarios, pitch outlines, validation plans, Korean 사업계획서, 시장 진입 분석, 해외 진출 검토, 사업성 보고서, 수익성 검토, 의사결정 메모, PPT, or PDF.
---

# Business Plan Skill

Turn business ideas and business document requests into Git-native Markdown artifacts, reviewable assumptions, decision records, validation plans, and ModuFlow issue/spec candidates.

## Role

This skill is a pre-execution bridge:

```text
business idea or business-document request
-> opportunity shaping
-> document type routing
-> business-plan or market-entry-analysis artifacts
-> persona scenarios and diagrams
-> review
-> validation plan
-> project memory record
-> issue/spec/roadmap candidates
-> optional PDF/PPTX export delegation
```

Keep ModuFlow's source of truth in Git-native Markdown. Treat PDF and PPTX files as export artifacts, never as the primary editable source.

## Trigger Phrases

Use this skill when the user asks for:

- business plan, one-page plan, Lean Canvas, business model, pitch deck outline, validation plan
- market-entry analysis, market entry report, business feasibility report, go-to-market report, profitability review, decision memo
- persona, customer persona, user scenario, customer journey, market/customer hypothesis
- Korean: 사업계획서, 사업구상, 사업 아이디어, 비즈니스 모델, 린 캔버스, 시장 진입 분석, 해외 진출 검토, 사업성 보고서, 수익성 검토, 의사결정 메모, 고객 가설, 시장 가설, 페르소나, 사용자 시나리오, 피치덱, PPT, PDF

If the request is only a raw idea, route through `product:opportunity` first. If the user wants work tracking, create issue/spec candidates after the plan artifacts.

## Document Type Router

Choose the smallest document recipe that matches the decision:

| Request | Recipe | Primary Output |
| --- | --- | --- |
| 사업 아이디어, 사업계획서, BM | `business-plan` | `business-plan.md` |
| 시장 진입, 해외 진출, 국가별 진출 검토 | `market-entry-analysis` | `market-entry/report.md` |
| 수익성, 단가, 마진, 손익분기점 | `profitability-review` | `calculation-model.md` plus decision memo |
| 투자자/파트너용 요약 | `pitch-outline` | `deck-outline.md` |
| 실행 여부 판단 | `decision-memo` | `decision.md` |

For `market-entry-analysis`, read `../../templates/business-plan/market-entry-analysis.md`, `calculation-model.md`, `source-checklist.md`, `writing-style.md`, and `pdf-quality-gate.md` before drafting.

## Workflow

```text
USER
 |
 | business idea / planning request
 v
@ModuFlow
 |
 | route
 v
product:opportunity
 |
 | shape problem, customer, alternatives, why-now
 v
moduflow:business-plan
 |
 | draft source artifacts
 v
business/<slug>/
  brief.md
  lean-canvas.md
  persona-scenarios.md
  business-plan.md or market-entry/report.md
  validation-plan.md
 |
 | review mode
 v
Subagent Review
 |
 | synthesize and revise
 v
business/<slug>/
  review-summary.md
  issue-candidates.md
 |
 | convert
 v
ModuFlow issues / specs / roadmap
 |
 | optional export
 v
business/<slug>/exports/
  business-plan.pdf or market-entry-report.pdf
  pitch-deck.pptx
```

## Artifact Set

Create or update these files under `business/<slug>/`:

```text
brief.md
assumptions.md
lean-canvas.md
persona-scenarios.md
business-plan.md
calculation-model.md
source-list.md
validation-plan.md
decision.md
issue-candidates.md
```

For `market-entry-analysis`, create:

```text
business/<slug>/
  brief.md
  assumptions.md
  source-list.md
  calculation-model.md
  market-entry/report.md
  decision.md
  validation.md
  issue-candidates.md
  exports/
```

When export is requested, also create:

```text
executive-summary.md
deck-outline.md
exports/
```

When review is requested, also create:

```text
reviews/market-review.md
reviews/product-review.md
reviews/risk-review.md
review-summary.md
```

Use bundled templates from the plugin root at `templates/business-plan/`. From this skill file, resolve them as `../../templates/business-plan/`.

## Writing Style Gate

For Korean business reports, use polite formal endings suitable for executive or partner-facing documents.

Required tone examples:

- `검토했습니다`
- `확인했습니다`
- `예상됩니다`
- `필요합니다`
- `권장됩니다`

Avoid plain declarative report endings such as `한다`, `이다`, `필요하다`, or `권고한다` in narrative sentences. Plain labels inside tables or headings are acceptable only when they are not complete prose sentences. Read `../../templates/business-plan/writing-style.md` before drafting Korean deliverables.

## Source Of Truth

Canonical:

```text
business/<slug>/*.md
```

Export artifacts:

```text
business/<slug>/exports/*.pdf
business/<slug>/exports/*.pptx
```

Do not edit generated PDFs or PPTX files as the primary source. Revise Markdown first, then export again.

## Persona And Scenario Requirements

`persona-scenarios.md` should feed the customer journey, sequence diagram, validation plan, and issue candidates.

Include:

- primary persona
- secondary persona
- buyer or decision maker when different from the user
- situation and trigger
- current workaround
- desired outcome
- step-by-step user scenario
- success criteria
- failure and edge scenarios
- scenario-to-feature mapping
- scenario-to-validation mapping

## Diagram Requirements

Diagrams help both humans and AI agents reason about structure. Use Mermaid-compatible text by default.

Must-have:

- Sequence Diagram: customer/product/operations/payment/support/partner flow
- Customer Journey Map: awareness, consideration, first use, payment, repeat, referral
- Hypothesis Validation Map: assumption -> method -> success criteria -> decision
- Risk Priority Matrix: impact x uncertainty
- Persona Map or Scenario Flow

Nice-to-have:

- Stakeholder Map
- Business Model Flow
- Operating Process Map
- Competitive Positioning Map

Prefer:

```text
sequenceDiagram
journey
flowchart TD
mindmap
quadrantChart
```

Do not build rendering or linting in this skill. Mermaid rendering, image export, or PPT/PDF embedding can become a separate issue if needed.

## Review Modes

Light:

- Main agent drafts and self-checks.
- Use for quick internal idea shaping.

Standard:

- Market Reviewer
- Product/PO Reviewer
- Risk Reviewer

Use by default when the user asks for 검증, 리뷰, 투자자용, 외부 공유, PDF, or PPT.

Full:

- Market Reviewer
- Customer/Problem Reviewer
- Business Model Reviewer
- Product/PO Reviewer
- Risk Reviewer
- Deck/PDF Reviewer

Use for external submission, investor/partner review, major strategic decisions, or explicit deep validation.

Subagents find gaps and risks. The main agent owns synthesis, final edits, and consistency.

## Memory And Decision Capture

After a business document is approved or materially revised, record durable project memory. Korean routing note: 프로젝트 메모리에 최종 산출물, 의사결정, 근거를 남겨야 합니다.

- `deliverable`: final report, PDF, deck, or decision memo path
- `decision`: go / no-go / defer decision, rationale, alternatives, reversal conditions
- `evidence`: key source pack, benchmark, calculation model, or interview notes

Use project-local memory so the business context remains portable when a project is copied, cloned, or moved. Recommended command: `product:memory write --kind deliverable --title "<document title>" --summary "<decision-ready summary>"`.

## Export Delegation

Prepare export-ready Markdown:

- `executive-summary.md`
- `deck-outline.md`
- `business-plan.md`

Then delegate:

- PPTX/deck creation: Presentations plugin
- PDF creation or layout verification: Documents or PDF plugin
- visual QA for exported files: PDF plugin

This skill defines content and structure. It does not implement rendering.

For Korean PDF exports, check `../../templates/business-plan/pdf-quality-gate.md` before handoff.

## Handoff

After creating artifacts:

- Use `product:issue` for validation tasks or execution work.
- Use `product:spec` when a product/feature PRD is ready.
- Use `product:roadmap` when timing or sequencing is needed.
- Use `product:review` before external sharing or export.

Always end with the next recommended ModuFlow command.
