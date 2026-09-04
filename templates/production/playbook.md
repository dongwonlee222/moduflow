---
schema: moduflow.playbook.v1
id: <playbook-id>
kind: playbook
title: <title>
applies_to_types: [<type>]
applies_to_channels: [<channel>]
audiences: [<audience>]
retrieval_trigger: <when-this-playbook-should-be-retrieved>
version: 0.1
process_ref_kind: none
process_ref:
process_ref_version:
process_ref_missing:
  - process_ref: no external procedure recorded yet
status: candidate
approved_by:
approved_at:
source_records: [<production-record-id>]
review_after: <yyyy-mm-dd>
superseded_by: []
created: <yyyy-mm-dd>
updated: <yyyy-mm-dd>
---

## Reusable Patterns

- <candidate pattern>

## Do Not Repeat

- <candidate rule>

## Required Checks

Numbered, stable IDs. A `[review]` item is a reviewer assertion, never proof that the deliverable passed. An `[auto]` item is checked mechanically and supports only `section:<name>`, `forbidden:<text>` and `approved-copy:<text>`. Retire an item in place with `(retired)`; never renumber or reuse an ID for a different meaning.

- CHK001 [auto] section:Artifacts
- CHK002 [review] <what the reviewer confirms>

## Approved Copy Blocks

- <approved external or internal copy block>

## Approved Structures

- <approved content or layout structure>

## Evidence

- <source production record and result>

## Revision History

Raise `version` on every content change. Major when the change could alter the deliverable's outcome or acceptance — a Required Checks item added, retired or redefined, a different `process_ref`, an Approved Structures change, or a narrower type/channel/audience. Minor otherwise. A version never decreases.

- <yyyy-mm-dd> candidate created.
