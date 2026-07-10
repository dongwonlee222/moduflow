---
schema: moduflow.production-record.v1
id: 2026-07-10-summer-banner
kind: production_record
title: Summer banner
issue_id: 001-summer-banner
deliverable_type: banner
channel: home-popup
audiences: [customer, internal]
variant: mobile
lifecycle: published
owner: marketing
created: 2026-07-10
updated: 2026-07-10
playbook_refs: [banner-mobile]
retrieval_trigger: when creating a mobile event banner
---

## Artifacts

- [Final banner](assets/banner-final.svg) — final · customer

## Source Inputs

- Summer charging campaign brief and mobile home-popup dimensions.

## Decisions

- Use a black card layout because it keeps copy contrast and composition stable.
- Keep customer-facing Korean copy as editable text outside generated imagery.

## Failed Attempts

- Small Korean text inside the phone image broke and became unreadable.
- Character appearance changed between image-generation iterations.

## Reusable Patterns

- Use generated imagery for the scene and editable UI text for final copy.
- Review mobile crop and text legibility before approval.

## Do Not Repeat

- Do not render final localized copy directly into generated pixels.
- Do not assume character consistency across separate generations.

## Playbook Updates

- banner-mobile — approved by Dongwon Lee on 2026-07-10: validated on mobile

## External Copy

Charge this summer and receive the event benefit.

## Internal Reporting Copy

The selected variant prioritizes mobile legibility and repeatable production.
