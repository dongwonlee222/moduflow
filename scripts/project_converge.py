#!/usr/bin/env python3
"""Spec-code converge check — evidence collection (issue 071, task A1).

`--evidence` mode resolves an issue's commits (trailer `Issue: <id>` or
merge-commit subjects mentioning `codex/<id>`), collects the touched files'
CURRENT working-tree contents (converge audits now, not the historical diff),
parses the spec's `## Acceptance Criteria` and the plan's
`## Global Constraints` exactly once (plan 071 Global Constraint 1 — every
downstream consumer reads `converge-evidence.json`, never re-parses), and
writes `specs/<id>/converge-evidence.json`.

Contracts (plan 071):
- GC4: exits non-zero on git or bundle failure, identically in `--json` and
  human modes. `no_evidence: true` with a healthy git and an existing spec is
  a valid report → exit 0.
- GC5: bundle caps (default 30 files / 200KB content) always surface as
  explicit `truncated` fields — never silent.
- GC10: `linkage_check` is imported, never modified.

Usage:
    python3 scripts/project_converge.py <project-path> --issue-id <id> \
        --evidence [--json] [--date <iso>] [--max-files N] [--max-bytes N]

A2 adds an `--apply-judgment <judgment.json>` mode to the same mode group.
"""
import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

try:
    from scripts.linkage_check import CommandResult, _error_text, run_command
except ImportError:  # running as `python3 scripts/project_converge.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from linkage_check import CommandResult, _error_text, run_command

__all__ = [
    "CommandResult",
    "run_command",
    "collect_evidence",
    "collect_files",
    "resolve_commits",
    "parse_acceptance_criteria",
    "parse_global_constraints",
    "main",
]

SCHEMA = "moduflow.converge-evidence.v1"
DEFAULT_MAX_FILES = 30
DEFAULT_MAX_BYTES = 200 * 1024

# NUL-separated fields, \x01-terminated records: sha, subject, parents, body.
GIT_LOG_FORMAT = "%H%x00%s%x00%P%x00%B%x01"
GIT_LOG_ARGS = ("git", "log", f"--format={GIT_LOG_FORMAT}")

CHECKBOX_RE = re.compile(r"^-\s+\[[ xX]\]\s+(.*)$")
BULLET_RE = re.compile(r"^-\s+(.*)$")
NUMBERED_RE = re.compile(r"^\d+\.\s+(.*)$")


# ---------------------------------------------------------------------------
# Section parsing (single parser — plan 071 Global Constraint 1)
# ---------------------------------------------------------------------------

def _section_lines(text, heading):
    """Lines of the `## <heading>` section, or None when the section is
    absent. The section ends at the next `## ` heading."""
    wanted = f"## {heading}".lower()
    lines = []
    in_section = False
    found = False
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            if in_section:
                break
            in_section = stripped.lower() == wanted
            found = found or in_section
            continue
        if in_section:
            lines.append(line)
    return lines if found else None


def parse_acceptance_criteria(text):
    """Parse `## Acceptance Criteria` from spec.md.

    Supports `- [ ] text` checkbox lines and plain `- text` bullets (both
    parseable). Non-bullet prose lines become entries with
    `"parseable": false` — the judge must emit them as `unverifiable`,
    never drop them. Returns (entries, notes); notes are non-fatal."""
    lines = _section_lines(text, "Acceptance Criteria")
    if lines is None:
        return [], ["spec.md: '## Acceptance Criteria' section not found"]
    entries = []
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        if raw[:1].isspace() and entries:
            # Wrapped continuation of the previous bullet.
            entries[-1]["text"] += " " + stripped
            continue
        match = CHECKBOX_RE.match(stripped) or BULLET_RE.match(stripped)
        if match:
            text_value, parseable = match.group(1).strip(), True
        else:
            text_value, parseable = stripped, False
        entries.append(
            {"id": f"AC#{len(entries) + 1}", "text": text_value, "parseable": parseable}
        )
    if not entries:
        return [], ["spec.md: '## Acceptance Criteria' section is empty"]
    return entries, []


def parse_global_constraints(text):
    """Parse numbered `## Global Constraints` items from plan.md.

    An absent section (old issues) is an empty list, not an error."""
    lines = _section_lines(text, "Global Constraints")
    if lines is None:
        return []
    entries = []
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        match = NUMBERED_RE.match(stripped)
        if match:
            entries.append({"id": f"GC#{len(entries) + 1}", "text": match.group(1).strip()})
        elif entries and raw[:1].isspace():
            entries[-1]["text"] += " " + stripped
        # Non-numbered preamble prose ("Binding on every task…") is skipped.
    return entries


# ---------------------------------------------------------------------------
# Commit resolution
# ---------------------------------------------------------------------------

def resolve_commits(runner, cwd, issue_id):
    """Resolve commits linked to issue_id from the full git log.

    Sources: (a) body trailer line `Issue: <id>`, (b) merge-commit subjects
    mentioning `codex/<id>` (the branch may be deleted post-merge — the merge
    subject survives). A commit matching both is recorded once with source
    'trailer'. Returns {commits: [{sha, subject, source, is_merge}], errors}."""
    errors = []
    args = list(GIT_LOG_ARGS)
    result = runner(args, cwd)
    if result.returncode != 0:
        errors.append(_error_text(args, result))
        return {"commits": [], "errors": errors}

    trailer_re = re.compile(rf"^Issue:\s*{re.escape(issue_id)}\s*$", re.MULTILINE)
    branch_token = f"codex/{issue_id}"
    by_sha = {}
    order = []
    for record in (result.stdout or "").split("\x01"):
        record = record.strip("\n")
        if not record.strip():
            continue
        parts = record.split("\x00")
        if len(parts) != 4:
            errors.append(
                f"git log produced a malformed record (expected 4 fields, "
                f"got {len(parts)}): {record[:80]!r}"
            )
            continue
        sha, subject, parents, body = parts
        sha = sha.strip()
        is_merge = len(parents.split()) >= 2
        if trailer_re.search(body):
            source = "trailer"
        elif is_merge and branch_token in subject:
            source = "merge-subject"
        else:
            continue
        if sha in by_sha:
            if source == "trailer":
                by_sha[sha]["source"] = "trailer"
            continue
        entry = {
            "sha": sha,
            "subject": subject.strip(),
            "source": source,
            "is_merge": is_merge,
        }
        by_sha[sha] = entry
        order.append(sha)
    return {"commits": [by_sha[sha] for sha in order], "errors": errors}


# ---------------------------------------------------------------------------
# File collection (current working-tree contents, capped — GC5)
# ---------------------------------------------------------------------------

def collect_files(runner, cwd, shas, max_files=DEFAULT_MAX_FILES, max_bytes=DEFAULT_MAX_BYTES):
    """Union the paths touched by the given (non-merge) commits and read each
    file's CURRENT working-tree content.

    Files deleted since → {path, content: null, missing: true}. Caps are
    never silent: past `max_files` included contents or `max_bytes` total
    content, paths are still listed with content omitted and per-file plus
    top-level `truncated: true`. Returns {files, truncated, errors}."""
    errors = []
    paths = []
    seen = set()
    for sha in shas:
        args = ["git", "show", "--name-only", "--format=", sha]
        result = runner(args, cwd)
        if result.returncode != 0:
            errors.append(_error_text(args, result))
            continue
        for line in (result.stdout or "").splitlines():
            line = line.strip()
            if line and line not in seen:
                seen.add(line)
                paths.append(line)

    root = Path(cwd)
    files = []
    truncated = False
    included = 0
    total_bytes = 0
    for path in sorted(paths):
        full = root / path
        if not full.is_file():
            files.append({"path": path, "content": None, "truncated": False, "missing": True})
            continue
        if included >= max_files:
            files.append({"path": path, "content": None, "truncated": True})
            truncated = True
            continue
        content = full.read_text(encoding="utf-8", errors="replace")
        size = len(content.encode("utf-8"))
        if total_bytes + size > max_bytes:
            files.append({"path": path, "content": None, "truncated": True})
            truncated = True
            continue
        files.append({"path": path, "content": content, "truncated": False})
        included += 1
        total_bytes += size
    return {"files": files, "truncated": truncated, "errors": errors}


# ---------------------------------------------------------------------------
# Evidence assembly
# ---------------------------------------------------------------------------

def collect_evidence(
    project_path,
    issue_id,
    generated,
    runner=None,
    max_files=DEFAULT_MAX_FILES,
    max_bytes=DEFAULT_MAX_BYTES,
):
    """Build the evidence dict (schema moduflow.converge-evidence.v1).

    Returns (evidence, ok). ok is False on git failure or missing spec file
    (GC4 exit contract); a commit-less run with healthy git and an existing
    spec sets no_evidence: true and stays ok — it is a valid report."""
    root = Path(project_path).resolve()
    runner = runner or run_command
    errors = []
    ok = True

    spec_path = root / "specs" / issue_id / "spec.md"
    plan_path = root / "specs" / issue_id / "plan.md"

    if spec_path.is_file():
        acceptance_criteria, notes = parse_acceptance_criteria(
            spec_path.read_text(encoding="utf-8")
        )
        errors.extend(notes)
    else:
        acceptance_criteria = []
        errors.append(f"spec file missing: specs/{issue_id}/spec.md")
        ok = False

    if plan_path.is_file():
        global_constraints = parse_global_constraints(plan_path.read_text(encoding="utf-8"))
    else:
        global_constraints = []  # absent for old issues — not an error

    resolution = resolve_commits(runner, root, issue_id)
    errors.extend(resolution["errors"])
    if resolution["errors"]:
        ok = False
    commits = resolution["commits"]

    non_merge_shas = [c["sha"] for c in commits if not c["is_merge"]]
    file_bundle = collect_files(runner, root, non_merge_shas, max_files, max_bytes)
    errors.extend(file_bundle["errors"])
    if file_bundle["errors"]:
        ok = False

    evidence = {
        "schema": SCHEMA,
        "issue_id": issue_id,
        "generated": generated,
        "commits": [
            {"sha": c["sha"], "subject": c["subject"], "source": c["source"]}
            for c in commits
        ],
        "files": file_bundle["files"],
        "acceptance_criteria": acceptance_criteria,
        "global_constraints": global_constraints,
        "truncated": file_bundle["truncated"],
        "no_evidence": not commits,
        "errors": errors,
    }
    return evidence, ok


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _human_summary(evidence, written_path):
    by_source = {}
    for commit in evidence["commits"]:
        by_source[commit["source"]] = by_source.get(commit["source"], 0) + 1
    source_detail = ", ".join(f"{k}: {v}" for k, v in sorted(by_source.items()))
    unparseable = sum(1 for ac in evidence["acceptance_criteria"] if not ac["parseable"])
    lines = [
        f"converge evidence: {evidence['issue_id']} (generated {evidence['generated']})",
        f"  commits: {len(evidence['commits'])}"
        + (f" ({source_detail})" if source_detail else ""),
        f"  files: {len(evidence['files'])} (truncated: "
        f"{'yes' if evidence['truncated'] else 'no'})",
        f"  acceptance criteria: {len(evidence['acceptance_criteria'])}"
        f" ({unparseable} unparseable)",
        f"  global constraints: {len(evidence['global_constraints'])}",
        f"  no_evidence: {str(evidence['no_evidence']).lower()}",
    ]
    if evidence["errors"]:
        lines.append(f"  errors ({len(evidence['errors'])}):")
        lines.extend(f"    - {error}" for error in evidence["errors"])
    if written_path is not None:
        lines.append(f"  wrote: {written_path}")
    return "\n".join(lines)


def _run_evidence(args, runner):
    root = Path(args.project_path).resolve()
    generated = args.date or _dt.date.today().isoformat()
    evidence, ok = collect_evidence(
        root,
        args.issue_id,
        generated,
        runner=runner,
        max_files=args.max_files,
        max_bytes=args.max_bytes,
    )

    out_path = root / "specs" / args.issue_id / "converge-evidence.json"
    written_path = None
    if out_path.parent.is_dir():
        out_path.write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        written_path = out_path
    else:
        evidence["errors"].append(
            f"cannot write evidence: specs/{args.issue_id}/ does not exist"
        )
        ok = False

    # GC4: identical exit behavior in both output modes.
    if args.json:
        print(json.dumps(evidence, ensure_ascii=False, indent=2))
    else:
        print(_human_summary(evidence, written_path))
    return 0 if ok else 1


def main(argv=None, runner=None):
    parser = argparse.ArgumentParser(
        description="Spec-code converge check (issue 071)."
    )
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--issue-id", required=True, help="Issue id, e.g. 071-spec-code-converge-check.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--evidence",
        action="store_true",
        help="Collect commits/files/AC/GC into specs/<id>/converge-evidence.json.",
    )
    # A2 adds: mode.add_argument("--apply-judgment", metavar="JUDGMENT_JSON", ...)
    parser.add_argument("--json", action="store_true", help="Print the evidence JSON instead of a summary.")
    parser.add_argument("--date", default=None, help="Generated date (ISO); defaults to today.")
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES, help="Max files with content included (default: 30).")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES, help="Max total content bytes (default: 204800).")
    args = parser.parse_args(argv)

    return _run_evidence(args, runner or run_command)


if __name__ == "__main__":
    raise SystemExit(main())
