---
name: business-plan
description: Use when ModuFlow needs to turn a business idea, startup concept, business plan request, Lean Canvas, business model, market/customer hypothesis, persona scenario, pitch deck outline, or validation plan into Git-native business artifacts and issue/spec candidates. Handles Korean requests such as 사업계획서, 사업구상, 사업 아이디어, 비즈니스 모델, 린 캔버스, 고객 가설, 시장 가설, 페르소나, 사용자 시나리오, 피치덱, PPT, or PDF.
---

# Business Plan Skill

Turn business ideas into Markdown source artifacts, reviewable diagrams, validation hypotheses, and ModuFlow issue/spec candidates.

## Role

This skill is a pre-execution bridge:

```text
business idea
-> opportunity shaping
-> business-plan artifacts
-> persona scenarios and diagrams
-> review
-> validation plan
-> issue/spec/roadmap candidates
-> optional PDF/PPTX export delegation
```

Keep ModuFlow's source of truth in Git-native Markdown. Treat PDF and PPTX files as export artifacts, never as the primary editable source.

## Trigger Phrases

Use this skill when the user asks for:

- business plan, one-page plan, Lean Canvas, business model, pitch deck outline, validation plan
- persona, customer persona, user scenario, customer journey, market/customer hypothesis
- Korean: 사업계획서, 사업구상, 사업 아이디어, 비즈니스 모델, 린 캔버스, 고객 가설, 시장 가설, 페르소나, 사용자 시나리오, 피치덱, PPT, PDF

If the request is only a raw idea, route through `product:opportunity` first. If the user wants work tracking, create issue/spec candidates after the plan artifacts.

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
  business-plan.md
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
  business-plan.pdf
  pitch-deck.pptx
```

## Artifact Set

Create or update these files under `business/<slug>/`:

```text
brief.md
lean-canvas.md
persona-scenarios.md
business-plan.md
validation-plan.md
issue-candidates.md
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

## Handoff

After creating artifacts:

- Use `product:issue` for validation tasks or execution work.
- Use `product:spec` when a product/feature PRD is ready.
- Use `product:roadmap` when timing or sequencing is needed.
- Use `product:review` before external sharing or export.

Always end with the next recommended ModuFlow command.
