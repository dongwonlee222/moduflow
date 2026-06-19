#!/usr/bin/env python3
import argparse
import json
from datetime import date
from pathlib import Path


LOOP_STATE_SCHEMA = "moduflow.loop-state.v2"
DEFAULT_MAX_ATTEMPTS = 3
VALID_LOOP_STATUSES = {"active", "needs_decision", "blocked", "done"}
PHASE_ORDER = ["issue", "spec", "plan", "execute", "review", "release", "status"]
GIT_BINDING_MODES = {"git-files", "github-sync"}
EXECUTION_BACKENDS = {"codex", "claude-code", "copilot-cloud-agent", "openhands", "manual"}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def loop_state_path(root):
    return Path(root).resolve() / "workspace" / "loop-state.json"


def normalize_attempts(raw_attempts, next_command="product:loop"):
    if isinstance(raw_attempts, dict):
        return {
            "command": raw_attempts.get("command") or next_command,
            "count": int(raw_attempts.get("count") or 0),
            "max": int(raw_attempts.get("max") or DEFAULT_MAX_ATTEMPTS),
            "last_changed_at": raw_attempts.get("last_changed_at")
            or date.today().isoformat(),
        }
    return {
        "command": next_command,
        "count": int(raw_attempts or 0),
        "max": DEFAULT_MAX_ATTEMPTS,
        "last_changed_at": date.today().isoformat(),
    }

def recommend_issue_branch(issue_id):
    return f"codex/{issue_id}"


def branch_matches_issue(branch, issue_id):
    if not branch or not issue_id:
        return True
    return issue_id in branch


def normalize_execution_backend(raw_backend):
    if isinstance(raw_backend, str):
        raw_backend = {"type": raw_backend}
    if not isinstance(raw_backend, dict):
        raw_backend = {}
    backend_type = raw_backend.get("type") or "manual"
    if backend_type not in EXECUTION_BACKENDS:
        backend_type = "manual"
    return {
        "type": backend_type,
        "status": raw_backend.get("status") or "not_selected",
        "reason": raw_backend.get("reason") or "",
        "session": raw_backend.get("session"),
    }


def normalize_git_binding(raw_binding=None):
    raw_binding = raw_binding if isinstance(raw_binding, dict) else {}
    mode = raw_binding.get("mode") or "git-files"
    if mode not in GIT_BINDING_MODES:
        mode = "git-files"
    commits = raw_binding.get("commits")
    if not isinstance(commits, list):
        commits = []
    return {
        "mode": mode,
        "branch": raw_binding.get("branch"),
        "base_branch": raw_binding.get("base_branch"),
        "commits": commits,
        "pull_request": raw_binding.get("pull_request"),
        "release": raw_binding.get("release"),
        "execution_backend": normalize_execution_backend(raw_binding.get("execution_backend")),
    }


def recommend_execution_backend(task_type="code", risk="medium", github_available=False):
    if risk == "high":
        return {
            "type": "manual",
            "status": "recommended",
            "reason": "high-risk work needs explicit human control",
        }
    if task_type in {"docs", "planning", "spec"}:
        return {
            "type": "codex",
            "status": "recommended",
            "reason": "local Git-file artifact work fits Codex execution",
        }
    if github_available and task_type == "code":
        return {
            "type": "copilot-cloud-agent",
            "status": "recommended",
            "reason": "GitHub-connected code work can run in a cloud execution backend",
        }
    return {
        "type": "codex",
        "status": "recommended",
        "reason": "default local execution backend for git-files mode",
    }


def validate_git_binding_for_issue(git_binding, active_issue_id):
    errors = []
    binding = normalize_git_binding(git_binding)
    branch = binding.get("branch")
    if branch and not branch_matches_issue(branch, active_issue_id):
        errors.append(
            f"workspace/loop-state.json: git_binding.branch {branch} does not match active_issue_id {active_issue_id}"
        )
    return errors



def normalize_loop_state(raw):
    next_command = raw.get("next_command") or "product:loop"
    issue_ids = raw.get("issue_ids")
    if not isinstance(issue_ids, list) or not issue_ids:
        issue_id = raw.get("issue_id") or raw.get("active_issue_id")
        issue_ids = [issue_id] if issue_id else []
    active_issue_id = (
        raw.get("active_issue_id")
        or raw.get("issue_id")
        or (issue_ids[0] if issue_ids else None)
    )
    status = raw.get("status") or "active"
    if status not in VALID_LOOP_STATUSES:
        status = "active"
    return {
        "schema": LOOP_STATE_SCHEMA,
        "loop_id": raw.get("loop_id") or raw.get("goal_id") or "active-loop",
        "goal_id": raw.get("goal_id") or "active-goal",
        "objective": raw.get("objective") or "",
        "issue_ids": issue_ids,
        "active_issue_id": active_issue_id,
        "phase": raw.get("phase") or "goal",
        "mode": raw.get("mode") or "recommend",
        "status": status,
        "next_command": next_command,
        "attempts": normalize_attempts(raw.get("attempts"), next_command),
        "blocker": raw.get("blocker"),
        "last_action": raw.get("last_action") or "",
        "last_verification": raw.get("last_verification"),
        "git_binding": normalize_git_binding(raw.get("git_binding")),
        "updated_at": raw.get("updated_at") or raw.get("updated") or date.today().isoformat(),
    }


def load_loop_state(root):
    path = loop_state_path(root)
    if not path.exists():
        return None
    return normalize_loop_state(read_json(path))


def issue_path(root, issue_id):
    return Path(root).resolve() / "issues" / f"{issue_id}.md"


def workflow_checkbox_state(issue_text, label):
    checked_pattern = f"- [x] {label}"
    unchecked_pattern = f"- [ ] {label}"
    if checked_pattern in issue_text:
        return "done"
    if unchecked_pattern in issue_text:
        return "pending"
    return "missing"


def infer_issue_phase(root, issue_id):
    path = issue_path(root, issue_id)
    if not path.exists():
        return "issue"
    issue_text = path.read_text(encoding="utf-8")
    for phase in ["spec", "plan", "execute", "review", "release"]:
        if workflow_checkbox_state(issue_text, phase) == "pending":
            return phase
    return "status"


def recommend_next_command(issue_id, phase):
    if phase in {"spec", "plan", "execute", "review", "release"}:
        return f"product:{phase} {issue_id}"
    return "product:status"


def apply_attempts_guard(state, recommended_command):
    updated = dict(state)
    attempts = normalize_attempts(
        updated.get("attempts"), updated.get("next_command") or recommended_command
    )
    if attempts["command"] == recommended_command:
        attempts["count"] += 1
    else:
        attempts = normalize_attempts(
            {"command": recommended_command, "count": 1, "max": attempts["max"]},
            recommended_command,
        )
    updated["attempts"] = attempts
    updated["next_command"] = recommended_command
    if attempts["count"] >= attempts["max"]:
        updated["status"] = "needs_decision"
        updated["blocker"] = (
            f"Repeated next command exceeded max attempts: {recommended_command}"
        )
    else:
        updated["status"] = updated.get("status") or "active"
        updated["blocker"] = updated.get("blocker")
    updated["updated_at"] = date.today().isoformat()
    return updated


def default_loop_state(root):
    return normalize_loop_state(
        {
            "goal_id": "active-goal",
            "issue_ids": [],
            "active_issue_id": None,
            "phase": "goal",
            "mode": "recommend",
            "status": "needs_decision",
            "next_command": "product:goal",
            "blocker": "No loop-state.json found",
        }
    )


def recommend_loop(root):
    state = load_loop_state(root) or default_loop_state(root)
    active_issue_id = state.get("active_issue_id")
    if not active_issue_id:
        state["status"] = "needs_decision"
        state["blocker"] = "No active issue selected"
        state["next_command"] = "product:goal"
        return state
    phase = infer_issue_phase(root, active_issue_id)
    command = recommend_next_command(active_issue_id, phase)
    state["phase"] = phase
    return apply_attempts_guard(state, command)


def write_loop_state(root, state):
    path = loop_state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(normalize_loop_state(state), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def validate_loop_state(root):
    path = loop_state_path(root)
    if not path.exists():
        return []
    errors = []
    try:
        raw = read_json(path)
    except Exception as exc:
        return [f"workspace/loop-state.json: invalid JSON ({exc})"]
    status = raw.get("status")
    if status and status not in VALID_LOOP_STATUSES:
        errors.append(f"workspace/loop-state.json: unsupported status {status}")
    state = normalize_loop_state(raw)
    active_issue_id = state.get("active_issue_id")
    if active_issue_id and not issue_path(root, active_issue_id).exists():
        errors.append(
            f"workspace/loop-state.json: active_issue_id {active_issue_id} has no matching issue file"
        )
    for issue_id in state.get("issue_ids", []):
        if not issue_path(root, issue_id).exists():
            errors.append(
                f"workspace/loop-state.json: issue_id {issue_id} has no matching issue file"
            )
    errors.extend(validate_git_binding_for_issue(state.get("git_binding"), active_issue_id))
    return errors


def main():
    parser = argparse.ArgumentParser(description="Inspect or advance ModuFlow loop state.")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument(
        "--step",
        action="store_true",
        help="Persist one safe recommendation to workspace/loop-state.json.",
    )
    args = parser.parse_args()
    result = recommend_loop(args.project_path)
    if args.step:
        write_loop_state(args.project_path, result)
    print(
        json.dumps(
            {"schema": "moduflow.loop-recommendation.v1", **result},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
