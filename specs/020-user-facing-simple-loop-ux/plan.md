# User-Facing Simple Loop UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make ModuFlow usable through the small natural-language surface `상태`, `다음`, `이거 해줘`, and `완료` while preserving existing direct `product:*` commands.

**Architecture:** This is a plugin-command and skill-routing update, not a new runtime. Keep the durable loop kernel from issue 019 as the source of truth, then tighten command docs and routing skills so broad user phrases map to safe read-only recommendations or one explicit safe mutation.

**Tech Stack:** Markdown command files, Codex/Claude skill instructions, JSON loop state, Python validation scripts, `unittest` release gate.

---

Issue: `020-user-facing-simple-loop-ux`
Owner / decision maker: Dongwon Lee
Current phase: plan drafted
Next command: `product:execute 020-user-facing-simple-loop-ux`
Mode: `git-files`

## File Structure

- Modify: `commands/moduflow.md`
  - Responsibility: make `/moduflow` and `@ModuFlow` feel like the main simple hub rather than a command catalog first.
- Modify: `commands/product-status.md`
  - Responsibility: define the concise default status output contract.
- Modify: `commands/product-loop.md`
  - Responsibility: define `다음` as read-only recommendation and `다음 실행` / `--step` as one safe mutation.
- Modify: `skills/index/SKILL.md`
  - Responsibility: route broad natural language aliases before exposing workflow internals.
- Modify: `skills/pm-execution-router/SKILL.md`
  - Responsibility: keep exact `product:*` routing while preferring the simple aliases for broad user intent.
- Modify: `README.md` and `INSTALL.md` if needed
  - Responsibility: show practical Codex usage examples with the simple aliases.
- Modify: `specs/020-user-facing-simple-loop-ux/status.md`, `tasks.md`, and `issues/020-user-facing-simple-loop-ux.md`
  - Responsibility: record implementation progress and verification.

## Task 1: Tighten Hub And Status Output Contract

**Files:**
- Modify: `commands/moduflow.md`
- Modify: `commands/product-status.md`
- Modify: `README.md`

- [ ] **Step 1: Update `/moduflow` hub behavior**

In `commands/moduflow.md`, adjust the no-argument behavior so it reports the concise status first and moves the long quick command list behind explicit help requests.

Expected content shape:

```markdown
1. **No arguments** → act as concise `product:status`:
   - Report only current goal, active issue, phase, blocker, and next action.
   - Show the exact next command for power users.
   - Do not print the full command catalog unless the user asks for `help`, `도움말`, or `명령어`.
```

- [ ] **Step 2: Define concise `product:status` default**

In `commands/product-status.md`, add or update the expected default output:

```text
현재 목표: <goal>
현재 이슈: <issue> (<phase>)
다음: <plain-language next action>
명령: <product:* command>
막힘: 없음 | <blocker>
```

Also state that detailed artifact lists are shown only when the user asks for details.

- [ ] **Step 3: Update README Codex examples**

In `README.md`, keep direct commands documented but put these examples near the top of the command section:

```text
@ModuFlow 상태
@ModuFlow 다음
@ModuFlow 이거 해줘: 결제 우선순위 정리
@ModuFlow 완료
```

- [ ] **Step 4: Verify docs contain the simple surface**

Run:

```bash
rg -n "상태|다음|이거 해줘|완료" commands README.md
```

Expected: matches in `commands/moduflow.md`, `commands/product-status.md`, `commands/product-loop.md`, and `README.md`.

## Task 2: Make `다음` Read-Only And `다음 실행` Explicitly Mutating

**Files:**
- Modify: `commands/product-loop.md`

- [ ] **Step 1: Update recommendation mode**

In `commands/product-loop.md`, clarify:

```markdown
Aliases: `다음`, `next`, `루프`.
Default behavior is read-only. It recommends one safe next action and includes the exact command.
```

- [ ] **Step 2: Update one-step mode**

In `commands/product-loop.md`, clarify:

```markdown
Aliases: `다음 실행`, `한 단계 진행`, `product:loop --step`.
One-step mode may mutate at most one safe artifact/state update, then stops.
```

- [ ] **Step 3: Add stop-state wording**

Ensure `needs_decision`, `blocked`, and `done` responses tell the user why ModuFlow stopped and what decision or verification is needed.

- [ ] **Step 4: Verify loop docs still mention all v2 state fields**

Run:

```bash
rg -n "active_issue_id|attempts|needs_decision|다음 실행" commands/product-loop.md
```

Expected: all terms are present.

## Task 3: Update Natural-Language Routing Skills

**Files:**
- Modify: `skills/index/SKILL.md`
- Modify: `skills/pm-execution-router/SKILL.md`

- [ ] **Step 1: Add default alias priority to `skills/index/SKILL.md`**

Add a routing rule near the top of the behavior section:

```markdown
Default simple aliases take priority for broad user intent:
- `상태`, `status`, `현재 상황` → concise `product:status`
- `다음`, `next`, `루프` → read-only `product:loop`
- `다음 실행`, `한 단계 진행` → one safe `product:loop --step`
- `이거 해줘: <request>` → attach to active loop, create issue, or inbox with at most one clarification
- `완료`, `done` → guarded completion; verify artifacts before closing anything
```

- [ ] **Step 2: Add guarded completion rule**

In both skill files, state that `완료` must not close an issue or step unless required artifacts and verification are present. If missing, recommend the next verification command.

- [ ] **Step 3: Keep direct command escape hatch**

In both skill files, state that exact `product:*` user input bypasses broad alias routing and should be honored directly.

- [ ] **Step 4: Verify skill routing examples**

Run:

```bash
rg -n "이거 해줘|완료|다음 실행|guarded|direct.*product" skills/index/SKILL.md skills/pm-execution-router/SKILL.md
```

Expected: all simple alias and direct-command rules are present.

## Task 4: Record Implementation And Run Gates

**Files:**
- Modify: `issues/020-user-facing-simple-loop-ux.md`
- Modify: `specs/020-user-facing-simple-loop-ux/status.md`
- Modify: `specs/020-user-facing-simple-loop-ux/tasks.md`
- Modify: `.moduflow/state.json`
- Modify: `workspace/loop-state.json`
- Modify: `workspace/dashboard.md`
- Modify: `workspace/roadmap.md`

- [ ] **Step 1: Mark execute task complete after docs/skills are updated**

Update issue 020 Workflow Tasks:

```markdown
- [x] execute → command/router/skill UX updates
```

- [ ] **Step 2: Update status evidence**

In `specs/020-user-facing-simple-loop-ux/status.md`, add completed bullets for hub/status/loop docs and routing skill updates.

- [ ] **Step 3: Move state to review**

Update `.moduflow/state.json` and `workspace/loop-state.json`:

```json
"phase": "review",
"active_issue": "020-user-facing-simple-loop-ux",
"next_command": "product:review 020-user-facing-simple-loop-ux"
```

For loop state use `active_issue_id` and set attempts command to the review command.

- [ ] **Step 4: Run validation gates**

Run:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_project_artifacts.py .
python3 scripts/validate_moduflow.py .
python3 scripts/release_check.py .
```

Expected: all commands exit 0.

- [ ] **Step 5: Update verification notes**

Record the passing commands in `specs/020-user-facing-simple-loop-ux/status.md`.

## Self-Review

Spec coverage:

- Concise `상태` output: Task 1.
- Read-only `다음` and explicit `다음 실행`: Task 2.
- `이거 해줘` active-loop/new-issue/inbox routing: Task 3.
- Guarded `완료`: Task 3.
- Existing advanced commands preserved: Task 3.
- Validation and state handoff: Task 4.

Placeholder scan: no TBD/TODO placeholders remain.

Type and command consistency: all next-command references use `product:execute`, `product:review`, or existing `product:loop --step` command names.

## Next Command

`product:execute 020-user-facing-simple-loop-ux`
