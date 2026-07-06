#!/usr/bin/env python3
"""Stop hook (issue 072, task A2).

Runs when a Claude Code session's Stop event fires, from the user project's
CWD (hook-schema-notes.md: hook CWD = ${CLAUDE_PROJECT_DIR}).

Two thin triggers, no reimplementation (plan 072 GC1):
  1. issues/*.md changed since the last sync marker -> invoke
     scripts/project_lifecycle.py --sync as a subprocess.
  2. uncommitted behavior-path changes with no issue linkage -> one
     informational warning line, deduped by fingerprint.

Contract (hook-schema-notes.md, binding):
  - Exit 0 on EVERY path. Exit 2 and decision:"block" are forbidden.
  - stdout carries ONLY the JSON contract (or nothing). All diagnostics go
    to .moduflow/logs/hooks.log.
  - 5-second self-enforced budget; on overrun, log and bail (GC2).
  - Write surface: hooks.log, .moduflow/state/.last-sync,
    .moduflow/state/.linkage-warned, plus whatever --sync writes (GC7).
"""
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOOK_NAME = "on_stop"
SELF_BUDGET_SECONDS = 5.0

# The plugin root is the parent of this file's directory (hooks/..). At
# runtime this is the installed plugin cache, NOT the user's project (GC5).
PLUGIN_ROOT = Path(__file__).resolve().parent.parent

LOG_RELPATH = Path(".moduflow") / "logs" / "hooks.log"
STATE_DIR_RELPATH = Path(".moduflow") / "state"
SYNC_MARKER_RELPATH = STATE_DIR_RELPATH / ".last-sync"
WARN_FINGERPRINT_RELPATH = STATE_DIR_RELPATH / ".linkage-warned"
# Presence of this file means issue-less behavior work was deliberately
# declared; the release gate (075) validates it — out of scope for the
# quick-check, so we stay silent rather than second-guess the declaration.
NO_ISSUE_DECLARATIONS_RELPATH = Path("releases") / "no-issue-declarations.md"

WARNING_PREFIX = "⚠️ 이슈 연결 없는 동작 변경 감지: "
WARNING_SUFFIX = (
    " — product:promote 또는 이슈 브랜치/트레일러 연결 권장 (릴리즈 게이트가 차단함)"
)

_linkage_check = None


def _load_linkage_check(project_root):
    """Import linkage_check by file path (GC1: reuse, never reimplement).

    Preferred copy is the plugin's own scripts/linkage_check.py (sibling of
    hooks/), so the hook works from the installed plugin cache; the project's
    scripts/ copy is the fallback for direct-invocation dogfooding.
    """
    global _linkage_check
    if _linkage_check is not None:
        return _linkage_check
    candidates = [
        PLUGIN_ROOT / "scripts" / "linkage_check.py",
        Path(project_root) / "scripts" / "linkage_check.py",
    ]
    for candidate in candidates:
        if candidate.is_file():
            spec = importlib.util.spec_from_file_location(
                "moduflow_hook_linkage_check", candidate
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _linkage_check = module
            return module
    raise FileNotFoundError("linkage_check.py not found (plugin or project scripts/)")


def log_line(project_root, level, message):
    """Append `<iso-ts> on_stop <level> <message>` to hooks.log. Never raises."""
    try:
        path = Path(project_root) / LOG_RELPATH
        path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat()
        message = " ".join(str(message).split())  # keep the log line single-line
        with path.open("a", encoding="utf-8") as fh:
            fh.write(f"{ts} {HOOK_NAME} {level} {message}\n")
    except Exception:
        pass  # logging must never take the hook down


def is_moduflow_project(project_root):
    return (Path(project_root) / ".moduflow" / "state.json").is_file()


def compute_issues_hash(project_root):
    """SHA-256 over the sorted (relpath, mtime_ns, size) list of issues/*.md."""
    issues_dir = Path(project_root) / "issues"
    entries = []
    if issues_dir.is_dir():
        for f in issues_dir.glob("*.md"):
            if not f.is_file():
                continue
            stat = f.stat()
            entries.append((f.name, stat.st_mtime_ns, stat.st_size))
    digest = hashlib.sha256()
    for name, mtime_ns, size in sorted(entries):
        digest.update(f"{name}\t{mtime_ns}\t{size}\n".encode("utf-8"))
    return digest.hexdigest()


def _read_marker(path):
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _write_marker(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value + "\n", encoding="utf-8")


def resolve_lifecycle_script(project_root):
    """Path of project_lifecycle.py to invoke.

    Choice (documented per task A2): prefer the copy shipped next to this
    hook — Path(__file__).parent.parent / "scripts/project_lifecycle.py" —
    because at runtime the hook lives in the installed plugin cache and the
    user's project usually has no scripts/ of its own; fall back to the
    project's copy (ModuFlow repo dogfooding / vendored installs). Either
    way the subprocess runs AGAINST the CWD project, never the plugin repo.
    """
    plugin_copy = PLUGIN_ROOT / "scripts" / "project_lifecycle.py"
    if plugin_copy.is_file():
        return plugin_copy
    project_copy = Path(project_root) / "scripts" / "project_lifecycle.py"
    if project_copy.is_file():
        return project_copy
    return None


def maybe_sync(project_root, deadline):
    """Trigger lifecycle sync when issues/*.md changed since the marker.

    Returns {"synced": bool, "reason": str}. Marker is updated only after a
    successful sync, so a failed sync retries on the next Stop.
    """
    project_root = Path(project_root)
    current = compute_issues_hash(project_root)
    marker_path = project_root / SYNC_MARKER_RELPATH
    if _read_marker(marker_path) == current:
        return {"synced": False, "reason": "unchanged"}

    script = resolve_lifecycle_script(project_root)
    if script is None:
        log_line(project_root, "error", "sync skipped: project_lifecycle.py not found")
        return {"synced": False, "reason": "script-missing"}

    remaining = deadline - time.monotonic()
    if remaining <= 0.2:
        log_line(project_root, "warn", "sync skipped: self budget exhausted")
        return {"synced": False, "reason": "budget"}

    try:
        result = subprocess.run(
            [sys.executable or "python3", str(script), str(project_root), "--sync"],
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=remaining,
            check=False,
        )
    except subprocess.TimeoutExpired:
        log_line(project_root, "error", "sync subprocess timed out")
        return {"synced": False, "reason": "timeout"}
    except OSError as exc:
        log_line(project_root, "error", f"sync subprocess failed to start: {exc}")
        return {"synced": False, "reason": "spawn-failure"}

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        log_line(
            project_root,
            "error",
            f"sync exited {result.returncode}: {detail[:300]}",
        )
        return {"synced": False, "reason": "sync-failed"}

    # Re-hash after sync: --sync itself never rewrites issues/*.md, but
    # hashing fresh keeps the marker honest if anything raced.
    _write_marker(marker_path, compute_issues_hash(project_root))
    return {"synced": True, "reason": "issues-changed"}


def _paths_from_porcelain(stdout):
    """Changed paths from `git status --porcelain` output (renames -> new path)."""
    paths = []
    for line in (stdout or "").splitlines():
        if len(line) < 4:
            continue
        entry = line[3:]
        if " -> " in entry:
            entry = entry.split(" -> ", 1)[1]
        entry = entry.strip()
        if entry.startswith('"') and entry.endswith('"'):
            entry = entry[1:-1]
        if entry:
            paths.append(entry)
    return paths


def detect_unlinked(project_root, runner=None, deadline=None):
    """Working-tree linkage quick-check.

    Returns {"unlinked": [paths], "errors": [msgs], "reason": str}.
    Linked when the current branch matches codex/<issue-id>* (linkage_check's
    BRANCH_ISSUE_RE — the working tree has no trailer yet, so the branch is
    the only linkage signal), or a no-issue declaration file is present
    (release gate owns that path).
    """
    project_root = Path(project_root)
    linkage = _load_linkage_check(project_root)
    if runner is None:
        runner = linkage.run_command

    def _timeout():
        if deadline is None:
            return None
        return max(0.2, deadline - time.monotonic())

    # -uall: expand untracked directories into individual files, so a brand
    # new scripts/foo.py surfaces as a concrete path (not "scripts/").
    status = runner(
        ["git", "status", "--porcelain", "-uall"], project_root, timeout=_timeout()
    )
    if status.returncode != 0:
        detail = (status.stderr or status.stdout or "").strip()
        return {
            "unlinked": [],
            "errors": [f"git status --porcelain failed: {detail[:300]}"],
            "reason": "git-error",
        }

    classified = linkage.classify_changed_paths(_paths_from_porcelain(status.stdout))
    behavior = classified["behavior"]
    if not behavior:
        return {"unlinked": [], "errors": [], "reason": "no-behavior-changes"}

    branch = runner(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], project_root, timeout=_timeout()
    )
    if branch.returncode != 0:
        detail = (branch.stderr or branch.stdout or "").strip()
        return {
            "unlinked": [],
            "errors": [f"git rev-parse --abbrev-ref HEAD failed: {detail[:300]}"],
            "reason": "git-error",
        }
    branch_name = (branch.stdout or "").strip()
    if linkage.BRANCH_ISSUE_RE.match(branch_name):
        return {"unlinked": [], "errors": [], "reason": "codex-branch"}

    if (project_root / NO_ISSUE_DECLARATIONS_RELPATH).is_file():
        return {"unlinked": [], "errors": [], "reason": "no-issue-declaration"}

    return {
        "unlinked": sorted(set(behavior)),
        "errors": [],
        "reason": "unlinked-behavior-changes",
    }


def build_warning(unlinked):
    """One informational line; up to 3 paths, then `+n more` (GC3)."""
    shown = list(unlinked)[:3]
    extra = len(unlinked) - len(shown)
    listing = ", ".join(shown)
    if extra > 0:
        listing += f" +{extra} more"
    return WARNING_PREFIX + listing + WARNING_SUFFIX


def warning_fingerprint(unlinked):
    """SHA-256 of the sorted unlinked path set (Interfaces: .linkage-warned)."""
    canonical = "\n".join(sorted(set(unlinked)))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def linkage_warning(project_root, deadline=None, runner=None):
    """Warning text to emit, or None. Handles fingerprint dedupe + cleanup."""
    project_root = Path(project_root)
    detection = detect_unlinked(project_root, runner=runner, deadline=deadline)
    for error in detection["errors"]:
        log_line(project_root, "error", error)

    fingerprint_path = project_root / WARN_FINGERPRINT_RELPATH
    unlinked = detection["unlinked"]
    if not unlinked:
        # State resolved (or unknowable): drop the fingerprint so the next
        # occurrence warns again.
        if detection["reason"] != "git-error":
            try:
                fingerprint_path.unlink()
            except FileNotFoundError:
                pass
        return None

    fingerprint = warning_fingerprint(unlinked)
    if _read_marker(fingerprint_path) == fingerprint:
        return None  # same set already warned about — suppress
    _write_marker(fingerprint_path, fingerprint)
    warning = build_warning(unlinked)
    log_line(project_root, "warn", warning)
    return warning


def main():
    start = time.monotonic()
    deadline = start + SELF_BUDGET_SECONDS
    project_root = Path.cwd()

    # Global hook guard: not a ModuFlow project -> total silence, no log spam.
    if not is_moduflow_project(project_root):
        return 0

    try:
        try:
            maybe_sync(project_root, deadline)
        except Exception as exc:  # fail-open per step
            log_line(project_root, "error", f"sync step failed: {exc!r}")

        warning = None
        if time.monotonic() >= deadline:
            log_line(project_root, "warn", "self budget exceeded before linkage check, bailing")
        else:
            try:
                warning = linkage_warning(project_root, deadline=deadline)
            except Exception as exc:
                log_line(project_root, "error", f"linkage step failed: {exc!r}")

        if warning:
            payload = {
                "hookSpecificOutput": {
                    "hookEventName": "Stop",
                    "additionalContext": warning,
                },
                "suppressOutput": True,
            }
            sys.stdout.write(json.dumps(payload, ensure_ascii=False))
            sys.stdout.write("\n")
    except Exception as exc:  # belt and braces: never break the Stop event
        log_line(project_root, "error", f"unhandled: {exc!r}")
    return 0  # ALWAYS 0 — exit 2 / decision:"block" forbidden (schema notes)


if __name__ == "__main__":
    raise SystemExit(main())
