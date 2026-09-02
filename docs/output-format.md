# ModuFlow Purpose-First Output Rule

This is a bundled ModuFlow rule for user-facing PR descriptions and work reports, not a personal memory or a rule limited to the ModuFlow development repository. It applies across supported hosts and target projects.

## Required Order

After a short outcome/status sentence when useful, explain:

1. **왜 필요한지 / Why Needed** — why the work matters to the user or project.
2. **해결해야 할 문제 / Problem** — the concrete current defect, inconvenience or gap, with its evidence or an explicit assumption.
3. **기대 효과 / Expected Benefits** — what should improve for the user. Label anticipated benefits as expected; measured results need evidence.

Then present implementation details, verification, remaining risk and the next action. Use plain language. An issue number, changed-file list, technical feature name or passing-test count is not a substitute for the first three points.

For a full PR or report, include the three labeled sections. For a brief progress/status update, compress them into a short sentence or a few lines; do not expand a simple acknowledgement or machine-readable JSON into a report. Existing project-specific report templates may retain their layout while placing this rationale first.

## Sources and Missing Information

Use the selected project's issue, spec and approved request as evidence. Do not copy another project's rationale or infer user benefits from implementation details alone. Missing information stays `미기록 / Not recorded`; fill or explicitly flag it before presenting a review-ready PR. A draft with missing rationale is not ready for approval.

`project_pr.py` copies explicit `## Why Needed`, `## Problem`, `## Expected Benefits` sections (or their Korean labels above), using the issue first and the matching spec as fallback per field. Other legacy formats require the author to summarize their actual evidence into those sections. The generator preserves source language; the author writes the final Korean review summary without changing its meaning.

## Example

- **왜 필요한지:** 배포 후 실제로 어떤 플러그인이 실행 중인지 판단할 수 있어야 합니다.
- **해결해야 할 문제:** 정상 설치를 개발용 기준으로 검사해 오류로 판정하고, 원본 수정과 현재 실행 상태를 구분하지 못했습니다.
- **기대 효과:** 불필요한 재설치와 잘못된 적용 완료 보고를 줄일 수 있습니다. 감소량을 측정한 결과는 아직 없습니다.

This rule changes explanation structure only. It does not authorize writes, lifecycle transitions, merge, publication or installation. Report source changes, remote integration, deployment and actual host application separately.
