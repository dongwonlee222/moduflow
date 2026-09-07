# Issue {{issue_id}}: {{title}}

**Status: backlog** — created {{created_date}}.
**Priority: p2**
**Blocked-by:**

## 요약

{{summary_ko}}

<!-- One or two sentences in Korean. This is the dashboard's issue description
     and the source of the 한글 개요 panel. Leaving it empty makes the row read
     `EN` with a `한글 없음` flag. Do not add the issue to
     workspace/issue-descriptions.ko.json instead — that file is legacy. -->

## Summary

{{summary}}

## Source

- Type: {{type_token}} — {{source_type}}
  <!-- 129: 첫 낱말은 bug|feature|chore|spike 중 하나. 뒤 설명은 자유. -->
- Link: {{source_link}}
- Date: {{date}}

## 안 고치면

<!-- 이걸 안 고치면 누가 무엇을 못 하는지 한 문장.
     목표의 일곱 가지 — 히스토리·메모리·이슈·로드맵·플레이북·프로세스·스킬 —
     중 어디가 막히는지 말한다 (`workspace/goal.md` 「이슈를 거르는 법」).
     "아무도 막히지 않는다"가 답이면 이슈를 만들지 않는다. -->

{{blocked_without_this}}

## Opportunity

{{opportunity}}

## Scope

### In

- {{in_scope}}

### Out

- {{out_of_scope}}

## Acceptance Criteria

- {{acceptance_criteria}}

## Verification

Commands the executing agent runs to self-check before handing off.

- {{verification_commands}}

## Entry Points

Starting files/components for the executing agent.

- {{entry_points}}

## Scope Fence

Do NOT touch (files, behaviors, or decisions out of bounds for this issue).

- {{scope_fence}}

## Workflow Tasks

Every artifact-producing step is a tracked task here — never produce a spec/plan/design/review off the books. Check the box and link the artifact when done.

- [ ] spec → `specs/<issue-id>/spec.md`
- [ ] plan → `specs/<issue-id>/plan.md`
- [ ] execute → PR / commits
- [ ] review → review notes
- [ ] (add issue-specific implementation tasks below)

## Related Issues

- blocks:
- blocked_by:
- duplicates:
- follows_up:
- supersedes:
- related:

## Sessions

- {{session_log}}

## Links

- Spec: `specs/<issue-id>/spec.md`
- Status: `specs/<issue-id>/status.md`
- Sessions: `sessions/{{issue_slug}}/`
- Roadmap: `workspace/roadmap.md`

## Next Command

`/moduflow spec {{issue_id}}`
