# PR Handoff: 080-reference-improvement-backlog

## 요약

레퍼런스 repo, 템플릿, upstream 예시를 쓰다가 발견한 개선 후보를 active issue에 섞지 않고 `workspace/reference-improvements.md`에 남기는 흐름을 추가했습니다.

핵심 변경:

- `scripts/project_reference_backlog.py`: dry-run/write 가능한 reference improvement capture CLI.
- `templates/workspace/reference-improvements.md`: 프로젝트에 복사되는 backlog 템플릿.
- `commands/product-plan.md`, `product-execute.md`, `product-review.md`, `product-status.md`, `product-loop.md`, `product-promote.md`: 언제 후보를 캡처하고, 언제 optional context로만 보여주며, 언제 issue로 승격할지 안내.
- `tests/test_project_reference_backlog.py`, `tests/test_validation_distribution.py`: capture 동작과 배포 표면 검증.
- `workspace/reference-improvements.md`: 080 dogfood 후보 1건 기록.

## 검증

- `python3 -m unittest tests.test_project_reference_backlog -v` — pass, 6 tests.
- `python3 -m unittest tests.test_validation_distribution -v` — pass, 27 tests.
- `python3 -m unittest discover -s tests -v` — pass, 458 tests.
- `python3 scripts/spec_consistency.py . --issue-id 080-reference-improvement-backlog` — pass, 0 findings.
- `python3 scripts/validate_moduflow.py .` — pass, 133 required files.
- `python3 scripts/validate_project_artifacts.py .` — pass, optional memory warning only.
- `python3 scripts/release_check.py .` — pass.

## 리뷰 결과

- Blocking finding: 없음.
- Constitution: v1.0 checked — no violations.
- Reference improvements: `workspace/reference-improvements.md`에 dogfood 후보 1건 기록.
- Converge limitation: 커밋 전 evidence 수집이라 `specs/080-reference-improvement-backlog/converge.md`는 7개 AC를 low-severity `unverifiable`로 기록. 로컬 테스트/검증은 모두 통과.

## 리뷰 링크

- Dashboard: `memory/dashboard.html`
- Issue drill-down: `memory/issue-080-reference-improvement-backlog.html`
- Korean human-review packet: `specs/080-reference-improvement-backlog/human-review.ko.md`
- Review notes: `specs/080-reference-improvement-backlog/review.md`

## 승인

- Draft PR: https://github.com/dongwonlee222/moduflow/pull/16
- Human approval: 아직 없음.
- Merge gate: PR diff, status checks, reviewer approval 확인 후 merge.
