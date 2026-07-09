# Plan: Fast Path Shaping Router (076)

Issue: `076-product-context-interview-and-readiness-loop`
Spec: `specs/076-product-context-interview-and-readiness-loop/spec.md`
Prev: spec · Next: `product:execute 076-product-context-interview-and-readiness-loop`

## Global Constraints

Constitution v1.0 applies (`workspace/constitution.md`). Plan-specific additions:

1. **Fast path remains default**: a bounded request must continue to return `create_issue` unless there is an active matching issue or a large multi-domain request.
2. **Question cap is explicit**: any shaping recommendation must expose `question_count <= 3` and must not store raw panel notes.
3. **No new artifact tier**: reuse issue/spec/opportunity/inbox mechanics; do not add a new `capture` command or database.
4. **079 boundary**: this issue may add a small `Recommended Discipline` note to docs/plan output, but the reusable skill-matrix engine belongs to `079-plan-discipline-skill-matrix`.
5. **Korean UX**: command docs should include Korean examples because the current adoption concern is Korean-language operator flow.

## Execution Mode

**Inline coordinator implementation, no worker split.** The implementation surface is a small routing helper plus command/skill docs and focused unit tests. Parallel workers would add overhead and risk wording drift across adjacent prompt files.

## Recommended Discipline

| Stream | Discipline / Adapter | Reason |
| --- | --- | --- |
| A — intake router | Superpowers TDD + ModuFlow PM router | Behavior change in `scripts/project_intake.py` needs focused tests first. |
| B — command/skill docs | Spec Kit style docs + Superpowers writing-plans | Prompt surfaces must describe the same routing contract as the code. |
| C — loop/status handoff | ModuFlow progress/dashboard conventions | Issue, status, and roadmap need to move to execute-ready state. |
| D — verification | Superpowers verification-before-completion | Full ModuFlow gates must pass before handoff. |

## Interfaces

- `scripts/project_intake.py` should keep schema `moduflow.intake-routing.v1` but add optional fields:
  - `shaping_path`: `fast|short|panel`
  - `shaping_reason`: short stable reason string
  - `question_count`: integer, `0..3`
  - `suggested_questions`: list of user-facing question strings, max length 3
  - `durable_context`: `none|issue|opportunity|spec_note`
- `product:loop` consumes those fields conceptually when recommending: create issue now, ask short shaping questions, or run panel shaping.
- `product:issue` consumes the fast-path rule: clear requests do not need interview.
- `product:opportunity` consumes the strategic/panel rule: broad product direction should shape opportunity/goal before implementation issues.

## Tasks

### Stream A — Intake router behavior

**Files:**

- Modify: `scripts/project_intake.py`
- Modify: `tests/test_project_intake.py`

- [ ] **A1. Add failing tests for fast, short-shaping, and panel routing**

  Add tests to `tests/test_project_intake.py`:

  ```python
  def test_route_intake_marks_clear_request_as_fast_path(self):
      with tempfile.TemporaryDirectory() as tmp:
          root = Path(tmp)
          (root / "workspace").mkdir()
          (root / "issues").mkdir()

          routed = project_intake.route_intake(root, "README 설치법 추가 이슈 만들어줘")

          self.assertEqual(routed["recommended_action"], "create_issue")
          self.assertEqual(routed["shaping_path"], "fast")
          self.assertEqual(routed["question_count"], 0)
          self.assertEqual(routed["suggested_questions"], [])
          self.assertEqual(routed["durable_context"], "issue")

  def test_route_intake_marks_ambiguous_request_as_short_shaping(self):
      with tempfile.TemporaryDirectory() as tmp:
          root = Path(tmp)
          (root / "workspace").mkdir()
          (root / "issues").mkdir()

          routed = project_intake.route_intake(root, "모두플로 인기가 없는 이유 개선해줘")

          self.assertEqual(routed["recommended_action"], "shape_then_issue")
          self.assertEqual(routed["shaping_path"], "short")
          self.assertGreaterEqual(routed["question_count"], 1)
          self.assertLessEqual(routed["question_count"], 3)
          self.assertEqual(routed["durable_context"], "opportunity")

  def test_route_intake_marks_strategy_request_as_panel_shaping(self):
      with tempfile.TemporaryDirectory() as tmp:
          root = Path(tmp)
          (root / "workspace").mkdir()
          (root / "issues").mkdir()

          routed = project_intake.route_intake(
              root,
              "모두플로 제품 방향과 포지셔닝을 다시 잡고 로드맵까지 정리해줘",
          )

          self.assertEqual(routed["recommended_action"], "panel_shape")
          self.assertEqual(routed["shaping_path"], "panel")
          self.assertLessEqual(routed["question_count"], 3)
          self.assertEqual(routed["next_command"], "product:opportunity")
  ```

- [ ] **A2. Run failing test slice**

  Run:

  ```bash
  python3 -m unittest tests.test_project_intake.ProjectIntakeTests -v
  ```

  Expected before implementation: the new tests fail because the shaping fields/actions do not exist.

- [ ] **A3. Implement shaping classification helpers**

  Add small helpers to `scripts/project_intake.py` near `request_size`:

  ```python
  STRATEGIC_KEYWORDS = {
      "strategy", "positioning", "roadmap", "direction", "vision", "market",
      "전략", "포지셔닝", "방향", "로드맵", "비전", "시장", "인기",
  }

  AMBIGUOUS_KEYWORDS = {
      "improve", "better", "popular", "why", "문제", "개선", "좋게", "왜", "이유", "인기",
  }

  def shaping_signals(text, classification=None, size=None):
      lowered = (text or "").lower()
      classification = classification or classify_request(text)
      size = size or request_size(text, classification)
      matched_domains = [
          domain for domain, score in classification.get("scores", {}).items() if score > 0
      ]
      strategic = (
          size == "large"
          or len(matched_domains) >= 2 and any(keyword in lowered for keyword in STRATEGIC_KEYWORDS)
          or any(keyword in lowered for keyword in {"전략", "포지셔닝", "방향", "vision", "strategy", "positioning"})
      )
      ambiguous = any(keyword in lowered for keyword in AMBIGUOUS_KEYWORDS)
      return {"strategic": strategic, "ambiguous": ambiguous, "matched_domains": matched_domains}

  def suggested_shaping_questions(path, text):
      if path == "panel":
          return [
              "가장 먼저 바꾸고 싶은 대상 사용자는 누구인가요?",
              "인기가 없다고 판단한 근거는 사용량, 설치, 반복 사용, 피드백 중 무엇인가요?",
              "이번 개선의 성공 기준은 채택률, 재사용률, 작업 완료율 중 어디에 두나요?",
          ]
      if path == "short":
          return [
              "이 요청의 주 대상 사용자는 누구인가요?",
              "현재 문제를 판단한 근거는 무엇인가요?",
              "완료됐다고 볼 수 있는 기준은 무엇인가요?",
          ]
      return []
  ```

- [ ] **A4. Wire shaping fields into `route_intake`**

  Update action selection so:

  - active matching issue still returns `attach_active_issue`
  - panel path returns `recommended_action = "panel_shape"` and `next_command = "product:opportunity"`
  - short shaping returns `recommended_action = "shape_then_issue"` and `next_command = "product:opportunity"`
  - fast path preserves existing `create_issue`

  Add the interface fields to `routed` with max 3 questions.

- [ ] **A5. Run intake tests**

  Run:

  ```bash
  python3 -m unittest tests.test_project_intake.ProjectIntakeTests -v
  ```

  Expected: all intake tests pass.

### Stream B — Command and skill surface

**Files:**

- Modify: `skills/pm-execution-router/SKILL.md`
- Modify: `commands/product-loop.md`
- Modify: `commands/product-issue.md`
- Modify: `commands/product-opportunity.md`
- Modify: `commands/product-spec.md`
- Modify: `README.md` only if wording from implementation needs alignment

- [ ] **B1. Document the three routing paths in `pm-execution-router`**

  Add a compact "Fast Path Shaping Router" section:

  ```markdown
  ## Fast Path Shaping Router

  - Clear/bounded request → `product:issue` directly; do not interview.
  - Ambiguous/broad request → ask 1-3 shaping questions, then create/update issue/spec/goal.
  - Strategic/high-risk/product-direction request → use a compressed panel path; show only the final 1-3 questions to the user.

  Never expose raw panel notes or make interview mandatory for all issues.
  ```

- [ ] **B2. Update `product:loop` recommendation contract**

  Add that `이거 해줘: <request>` can recommend:

  - `create_issue`: direct issue creation
  - `shape_then_issue`: ask 1-3 questions first
  - `panel_shape`: use opportunity/goal shaping before issue/spec

- [ ] **B3. Update `product:issue` fast-path wording**

  Add that clear issue requests bypass shaping, while ambiguous requests may be created as discovery issues only when the user asks for speed and unknowns are explicitly recorded.

- [ ] **B4. Update `product:opportunity` as the shaping destination**

  Add that opportunity captures short/panel shaping for product direction before issue/spec creation, without becoming a mandatory step for clear implementation work.

- [ ] **B5. Update `product:spec` preservation wording**

  Add that specs should preserve shaped product rationale from opportunity/issue/interview notes so execution and review do not lose context.

### Stream C — ModuFlow artifact handoff

**Files:**

- Modify: `issues/076-product-context-interview-and-readiness-loop.md`
- Modify: `specs/076-product-context-interview-and-readiness-loop/status.md`
- Modify: `workspace/roadmap.md`
- Create/modify: `specs/076-product-context-interview-and-readiness-loop/tasks.md`

- [ ] **C1. Create tasks checklist**

  Ensure `tasks.md` mirrors this plan at the stream level and is concise enough for execution tracking.

- [ ] **C2. Update issue workflow task**

  Check the plan task in the issue and set next command to `product:execute 076-product-context-interview-and-readiness-loop`.

- [ ] **C3. Update status and roadmap**

  Status phase becomes `plan`; roadmap next command becomes `product:execute 076-product-context-interview-and-readiness-loop`.

### Stream D — Verification

- [ ] **D1. Run focused tests**

  ```bash
  python3 -m unittest tests.test_project_intake.ProjectIntakeTests -v
  ```

- [ ] **D2. Run ModuFlow artifact validation**

  ```bash
  python3 scripts/validate_moduflow.py .
  python3 scripts/validate_project_artifacts.py .
  ```

- [ ] **D3. Run release gate**

  ```bash
  python3 scripts/release_check.py .
  ```

- [ ] **D4. Record verification in status**

  Add exact command results to `specs/076-product-context-interview-and-readiness-loop/status.md`.

## Gates

- **Test**: focused intake tests pass, then release_check pass.
- **Review**: `product:review 076-product-context-interview-and-readiness-loop` after implementation.
- **Deploy**: version bump only if behavior/docs changes require release packaging.
- **Rollback**: revert the intake helper and command-doc changes; no external storage or data migration exists.
