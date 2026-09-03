# 프로젝트 자료를 다른 작업에서도 찾고 검증하기 위한 등록부

Issue: `090-project-knowledge-and-artifact-registry` · Refs #20
Owner / decision maker: Dongwon Lee
Phase: [PR #47](https://github.com/dongwonlee222/moduflow/pull/47) merged as 8869afa after CI and explicit owner approval; 0.3.57 published/installed. See release.md for final delivery proof.
Next: source handoff. The PR-preparation narrative below is historical; it does not supersede the final release evidence or assert company adoption/host prompt-skill loading.

## 왜 필요한지

여러 프로젝트와 채팅을 오가더라도 이전 작업이 사용한 보고서·정의·결정 근거를 다시 찾을 수 있어야 합니다. 090은 사람과 AI가 함께 사용하는 프로젝트 자료 목록과 짧은 위키를 제공합니다.

## 해결해야 할 문제

파일이 저장돼 있어도 어느 자료가 최신 기준인지, 승인본인지, 다른 작업에서도 열 수 있는지 알기 어렵습니다. 로컬에만 있는 파일 때문에 공유가 된 것으로 오해하거나, 관련 없는 문서까지 모두 읽게 됩니다. 결과 파일만 저장하고 자료 목록·이슈 연결이 빠지는 문제도 있습니다.

## 기대 효과

- 프로젝트를 선택한 뒤 이름·목적·언제 읽는지로 필요한 자료만 찾습니다.
- 원본 링크, 기준일, 담당자, 초안/승인/대체 상태를 구분합니다. 오래된 승인본을 최신 자료로 오해하지 않습니다.
- 새 작업은 짧은 위키/자료 목록부터 읽고, 선택한 원문만 엽니다. 원문은 기존 위치에 두며 복사하지 않습니다.
- 등록을 선택한 저장은 결과·목록·이슈 링크를 함께 반영하고, 실패 시 기존 transaction의 복구 절차를 사용합니다.
- 공유된 Git 기준으로 다른 worktree에서 읽을 수 있는지 검증합니다. 비공개 원본이나 외부 링크가 있다는 이유만으로 접근 가능하다고 판단하지 않습니다.

예: “이 프로젝트의 지난 분석 근거를 찾아줘” → 자료 목록에서 기준일·상태 확인 → 해당 자료만 열기. 실제 회사 프로젝트 적용 전이므로 시간 절감이나 사용 효과는 아직 측정하지 않았습니다.

## 구현 범위

- `workspace/knowledge.md` 짧은 위키, `workspace/artifacts.md` 단일 자료 등록부; Markdown 내부 JSON 메타데이터를 한 parser로 해석합니다.
- 프로젝트/자료 ID, 검색 결과 제한·누락 표시, 선택적 원문 조회, 고정된 Git commit 기준 읽기.
- 기존 103 엔진에 한정된 `artifact-register` 경로 추가; 새로운 엔진·lock·DB·scheduler 없음.
- knowledge CLI의 명시적 등록, Validator/Doctor 및 패키지 연결. 기존 기록과 미등록 저장 동작 보존.
- 소스 버전 `0.3.57`, Codex manifest `0.3.57+codex.20260810222010`. 설치된 `0.3.56` 캐시는 변경하지 않음.

## 검증

구현 원본은 `594575b`, 승인 기준은 `22c01c9`입니다. 원본 구현 브랜치를 변경하지 않고 PR 브랜치에 squash 통합하며, 정식 Issue trailer와 버전 상승을 같은 feature commit에 넣습니다.

- 통합 커밋 `c89fc65`: 집중 **317개 통과(13.531초)**, S01–S14 및 임시 패키지 CLI 포함.
- 통합 후 전체 **1,680개 통과(290.354초)**, 릴리스 검사 **13개 항목 모두 통과**. 패키지·프로젝트·권한/경로 검사와 9개 완료조건 정합성 검사도 통과했습니다.
- 원본의 이슈 연결·버전 정책 실패는 정식 이슈 연결과 버전 상승을 포함한 통합 커밋에서 해결했습니다. 원본 브랜치와 실패 이력은 보존했고 검사 코드를 완화하지 않았습니다.
- GitHub CI는 PR 생성 후 별도 확인 대상입니다. 로컬 통과를 원격 CI 통과로 표시하지 않습니다.
- 근거: `specs/090-project-knowledge-and-artifact-registry/integration-verification.md`, `status.md`, `simulation-matrix.md`, `implementation-review.md`.

## 하지 않은 것 / 승인 경계

- 모든 채팅이 자동으로 기억하거나 모든 저장을 자동 등록하는 기능은 아닙니다. 자료 등록과 필요한 자료를 읽는 절차를 사용해야 합니다.
- 새 대시보드 UI는 086/092, 분석 실행 이력은 091의 범위입니다. 회사 계산 규칙이나 실제 데이터는 넣지 않았습니다.
- 실제 프로젝트/새 Codex·Claude 세션 적용, 원격 main 병합, 배포·설치 및 외부 원문 접근은 미수행입니다.
- 111의 실사용 관찰과 단일-active lifecycle 제약은 유지합니다. 090 구현 완료를 이유로 111을 완료로 바꾸거나 상태 검사를 완화하지 않습니다.
- 원본 구현 worktree의 종료 후 자동 동기화 파일과 기존 Issue 103 미커밋 계획은 PR에 포함하지 않습니다.

## 롤백

배포 전에는 기존 설치를 그대로 유지합니다. 배포 후 코드 되돌리기가 필요하면 먼저 기존 103 복구로 미완료 거래를 확인한 뒤 승인된 코드 변경을 되돌립니다. 자료 목록·원본·안정 ID·복구 증거는 삭제하지 않습니다. 실제 배포/롤백은 별도 승인 대상입니다.
