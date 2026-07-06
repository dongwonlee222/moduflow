#!/usr/bin/env python3
"""SessionStart hook: inject a compact ModuFlow state banner (issue 072, A1).

Contract (specs/072-lifecycle-hooks-automation/hook-schema-notes.md):
- Runs with CWD = ${CLAUDE_PROJECT_DIR}; resolves the *user project's*
  `.moduflow/` from CWD, never the plugin's own repo (GC5).
- Non-ModuFlow-project guard: no `.moduflow/state.json` under CWD -> emit
  nothing, exit 0, no log spam (delta 3 — plugin hooks are global).
- stdout is reserved for the SessionStart JSON contract only; every
  diagnostic goes to `.moduflow/logs/hooks.log`
  (`<iso-ts> session_start <warn|error> <message>`).
- Exit 0 on every path (fail-open, GC2); 5-second self-enforced budget.
- Banner: <=10 lines Korean-first — 목표, 활성 이슈+phase, 다음 명령,
  막힘 (있을 때만), 미승격 레코드 n건 (있을 때만) (plan.md Interfaces).

Stdlib only.
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOOK_NAME = "session_start"
SELF_BUDGET_SECONDS = 5.0
BANNER_MAX_LINES = 10


def append_log(project, level, message):
    """Append one hooks.log line; never raises (logging must not break the hook)."""
    try:
        log_dir = project / ".moduflow" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat()
        with open(log_dir / "hooks.log", "a", encoding="utf-8") as fh:
            fh.write("%s %s %s %s\n" % (ts, HOOK_NAME, level, message))
    except Exception:
        pass


def load_json_object(path):
    """Return (dict-or-None, error-or-None). Missing file -> (None, None): not
    an error worth logging. Present-but-unreadable -> (None, message)."""
    try:
        if not path.is_file():
            return None, None
    except OSError as exc:
        return None, "%s stat failed: %s" % (path.name, exc)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, "%s unreadable: %s" % (path.name, exc)
    if not isinstance(data, dict):
        return None, "%s is not a JSON object" % path.name
    return data, None


def pick(*values):
    for value in values:
        if value:
            return value
    return ""


def unpromoted_record_count(project, deadline):
    """Optional fast source (GC6): retention unpromoted count via
    scripts/project_retention.py — only if importable and within budget.
    Any slowness/error -> None, dropped silently from the banner."""
    try:
        if deadline - time.monotonic() < 0.5:
            return None
        scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
        if not (scripts_dir / "project_retention.py").is_file():
            return None
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        import project_retention

        def budgeted_runner(args, cwd, timeout=10):
            remaining = deadline - time.monotonic()
            if remaining <= 0.1:
                return project_retention.CommandResult(124, "", "hook budget exhausted")
            return project_retention.run_command(
                args, cwd, timeout=min(timeout, remaining)
            )

        status = project_retention.retention_status(project, budgeted_runner)
        if time.monotonic() >= deadline or not status.get("ok"):
            return None
        count = status.get("unpromoted_count")
        return count if isinstance(count, int) else None
    except Exception:
        return None


def build_banner(state, loop, record_count):
    state = state or {}
    loop = loop or {}

    goal = pick(state.get("active_goal"), loop.get("goal_id"), loop.get("objective"))
    issue = pick(state.get("active_issue"), loop.get("active_issue_id"))
    if issue and issue == loop.get("active_issue_id"):
        phase = pick(loop.get("phase"), state.get("phase"))
    else:
        phase = pick(state.get("phase"), loop.get("phase"))
    next_command = pick(state.get("next_command"), loop.get("next_command"))

    blockers = []
    state_blockers = state.get("blockers")
    if isinstance(state_blockers, list):
        blockers.extend(str(b) for b in state_blockers if b)
    loop_blocker = loop.get("blocker")
    if loop_blocker:
        blockers.append(str(loop_blocker))

    lines = ["[ModuFlow] 세션 컨텍스트"]
    if goal:
        lines.append("목표: %s" % goal)
    if issue:
        lines.append("활성 이슈: %s (단계: %s)" % (issue, phase or "?"))
    elif phase:
        lines.append("단계: %s" % phase)
    if next_command:
        lines.append("다음 명령: %s" % next_command)
    if blockers:
        lines.append("막힘: %s" % "; ".join(blockers))
    if record_count:
        lines.append("미승격 레코드: %d건" % record_count)
    return "\n".join(lines[:BANNER_MAX_LINES])


def emit(banner):
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": banner,
        },
        "suppressOutput": True,
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.write("\n")


def main():
    start = time.monotonic()
    deadline = start + SELF_BUDGET_SECONDS

    project = Path.cwd()
    state_path = project / ".moduflow" / "state.json"
    # Non-ModuFlow-project guard: emit nothing, log nothing (schema notes delta 3).
    if not state_path.is_file():
        return

    state, state_err = load_json_object(state_path)
    loop, loop_err = load_json_object(project / "workspace" / "loop-state.json")
    if state_err:
        append_log(project, "warn", state_err)
    if loop_err:
        append_log(project, "warn", loop_err)
    if state is None and loop is None:
        append_log(
            project,
            "error",
            "no readable state (state.json, workspace/loop-state.json); banner skipped",
        )
        return

    if time.monotonic() >= deadline:
        append_log(project, "warn", "self-budget %.0fs exceeded before banner; skipped"
                   % SELF_BUDGET_SECONDS)
        return

    record_count = unpromoted_record_count(project, deadline)
    banner = build_banner(state, loop, record_count)

    if time.monotonic() >= deadline:
        append_log(project, "warn", "self-budget %.0fs exceeded before emit; skipped"
                   % SELF_BUDGET_SECONDS)
        return

    emit(banner)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # fail-open: never block a session (GC2)
        try:
            append_log(Path.cwd(), "error", "unhandled: %r" % (exc,))
        except Exception:
            pass
    sys.exit(0)
