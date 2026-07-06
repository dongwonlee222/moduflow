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

`--apply-judgment <judgment.json>` mode (task A2) consumes the judge's
Judgment JSON (schema `moduflow.converge-judgment.v1`), appends a dated run
section to `specs/<id>/converge.md` (never overwrites prior sections), and
appends high/medium CV finding lines to `specs/<id>/tasks.md` under
`## Converge Findings (auto)` per the fixed GC6 grammar with dedup against
existing unchecked CV items. A fully converged run leaves tasks.md
byte-for-byte identical (GC3); converge.md always records the run.

Usage:
    python3 scripts/project_converge.py <project-path> --issue-id <id> \
        --evidence [--json] [--date <iso>] [--max-files N] [--max-bytes N]
    python3 scripts/project_converge.py <project-path> --issue-id <id> \
        --apply-judgment <judgment.json> [--json] [--date <iso>]
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
    "validate_judgment",
    "build_findings",
    "apply_judgment",
    "main",
]

SCHEMA = "moduflow.converge-evidence.v1"
JUDGMENT_SCHEMA = "moduflow.converge-judgment.v1"
APPLY_SCHEMA = "moduflow.converge-apply.v1"
DEFAULT_MAX_FILES = 30
DEFAULT_MAX_BYTES = 200 * 1024

VERDICTS = ("converged", "missing", "partial", "contradicting", "unverifiable")
SEVERITIES = ("high", "medium", "low")
FINDINGS_HEADER = "## Converge Findings (auto)"
VERDICT_KEYS = ("ac_id", "verdict", "severity", "evidence_quote", "note")
UNREQUESTED_KEYS = ("behavior", "file", "severity")

# GC6 grammar: - [ ] CV-<n> [<severity>] <finding> — <source-ref>, from converge <date>
CV_LINE_RE = re.compile(
    r"^-\s+\[(?P<state>[ xX])\]\s+CV-(?P<num>\d+)\s+\[(?P<severity>\w+)\]\s+(?P<rest>.*)$"
)

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
# Judgment application (task A2): converge.md report + tasks.md CV appender
# ---------------------------------------------------------------------------

def validate_judgment(data):
    """Validate a Judgment dict against moduflow.converge-judgment.v1.

    Returns a list of error strings; empty means valid. Unknown verdict or
    severity values and missing required keys are errors (GC4 exit contract).
    An empty severity string is allowed (e.g. on converged verdicts)."""
    if not isinstance(data, dict):
        return ["judgment: top level must be a JSON object"]
    errors = []
    if data.get("schema") != JUDGMENT_SCHEMA:
        errors.append(
            f"judgment: schema must be {JUDGMENT_SCHEMA!r}, got {data.get('schema')!r}"
        )
    verdicts = data.get("verdicts")
    if not isinstance(verdicts, list):
        errors.append("judgment: 'verdicts' must be a list")
    else:
        for index, verdict in enumerate(verdicts):
            label = f"verdicts[{index}]"
            if not isinstance(verdict, dict):
                errors.append(f"judgment: {label} must be an object")
                continue
            missing = [key for key in VERDICT_KEYS if key not in verdict]
            if missing:
                errors.append(
                    f"judgment: {label} missing required keys: {', '.join(missing)}"
                )
            if "verdict" in verdict and verdict["verdict"] not in VERDICTS:
                errors.append(
                    f"judgment: {label} unknown verdict {verdict['verdict']!r} "
                    f"(expected one of: {', '.join(VERDICTS)})"
                )
            if "severity" in verdict and verdict["severity"] not in SEVERITIES + ("",):
                errors.append(
                    f"judgment: {label} unknown severity {verdict['severity']!r}"
                )
    unrequested = data.get("unrequested")
    if not isinstance(unrequested, list):
        errors.append("judgment: 'unrequested' must be a list")
    else:
        for index, item in enumerate(unrequested):
            label = f"unrequested[{index}]"
            if not isinstance(item, dict):
                errors.append(f"judgment: {label} must be an object")
                continue
            missing = [key for key in UNREQUESTED_KEYS if key not in item]
            if missing:
                errors.append(
                    f"judgment: {label} missing required keys: {', '.join(missing)}"
                )
            if "severity" in item and item["severity"] not in SEVERITIES + ("",):
                errors.append(f"judgment: {label} unknown severity {item['severity']!r}")
    bundle_gaps = data.get("bundle_gaps")
    if not isinstance(bundle_gaps, list) or any(
        not isinstance(gap, str) for gap in (bundle_gaps or [])
    ):
        errors.append("judgment: 'bundle_gaps' must be a list of strings")
    return errors


def _summary_line(judgment):
    """One-line run summary, e.g. '9 AC: 7 converged, 1 missing, 1 unverifiable;
    2 unrequested'."""
    counts = {}
    for verdict in judgment["verdicts"]:
        counts[verdict["verdict"]] = counts.get(verdict["verdict"], 0) + 1
    parts = [f"{counts[name]} {name}" for name in VERDICTS if counts.get(name)]
    line = f"{len(judgment['verdicts'])} AC: {', '.join(parts) if parts else 'none'}"
    if judgment["unrequested"]:
        line += f"; {len(judgment['unrequested'])} unrequested"
    return line


def _run_heading(existing_text, date):
    """`## Converge Run <date>`, with a `(run N)` suffix when the same heading
    already exists (multiple runs on the same date stay separate sections)."""
    existing = {
        line.strip()
        for line in (existing_text or "").splitlines()
        if line.strip().startswith("## Converge Run")
    }
    heading = f"## Converge Run {date}"
    if heading not in existing:
        return heading
    counter = 2
    while f"{heading} (run {counter})" in existing:
        counter += 1
    return f"{heading} (run {counter})"


def _table_cell(value):
    return str(value or "").replace("|", "\\|").strip()


def render_run_section(judgment, date, existing_text):
    """Render one dated converge.md run section (heading, verdict table,
    unrequested list, bundle gaps, one-line summary)."""
    lines = [_run_heading(existing_text, date), ""]
    lines.append("| AC | Verdict | Severity | Note |")
    lines.append("| --- | --- | --- | --- |")
    for verdict in judgment["verdicts"]:
        lines.append(
            f"| {_table_cell(verdict['ac_id'])} | {_table_cell(verdict['verdict'])} "
            f"| {_table_cell(verdict['severity'])} | {_table_cell(verdict['note'])} |"
        )
    lines += ["", "Unrequested:"]
    if judgment["unrequested"]:
        for item in judgment["unrequested"]:
            severity = item["severity"] or "unspecified"
            lines.append(f"- [{severity}] {item['behavior']} — {item['file']}")
    else:
        lines.append("- none")
    lines += ["", "Bundle gaps:"]
    if judgment["bundle_gaps"]:
        lines.extend(f"- {gap}" for gap in judgment["bundle_gaps"])
    else:
        lines.append("- none")
    lines += ["", f"Summary: {_summary_line(judgment)}", ""]
    return "\n".join(lines)


def append_converge_report(converge_path, issue_id, judgment, date):
    """Append a dated run section to converge.md; create the file with its
    `# Converge: <issue-id>` header on first run. Never rewrites prior
    sections (GC2 write surface)."""
    existing = (
        converge_path.read_text(encoding="utf-8") if converge_path.is_file() else None
    )
    section = render_run_section(judgment, date, existing or "")
    if existing is None:
        text = f"# Converge: {issue_id}\n\n{section}"
    else:
        if not existing.endswith("\n"):
            existing += "\n"
        text = existing + "\n" + section
    converge_path.write_text(text, encoding="utf-8")
    return section


def build_findings(judgment):
    """High/medium actionable findings, emitted high before medium (GC7).

    Non-converged high/medium verdicts and high/medium unrequested items
    qualify; `converged` verdicts and low severity are report-only (never
    appended). source-ref is the verdict's ac_id (`AC#k`/`GC#k`) or
    `unrequested:<file>`."""
    findings = []
    for verdict in judgment["verdicts"]:
        if verdict["verdict"] == "converged":
            continue
        if verdict["severity"] not in ("high", "medium"):
            continue
        note = (verdict["note"] or "").strip()
        finding = f"{verdict['verdict']}: {note}" if note else verdict["verdict"]
        findings.append(
            {
                "severity": verdict["severity"],
                "finding": finding,
                "source_ref": verdict["ac_id"],
            }
        )
    for item in judgment["unrequested"]:
        if item["severity"] not in ("high", "medium"):
            continue
        findings.append(
            {
                "severity": item["severity"],
                "finding": (item["behavior"] or "").strip(),
                "source_ref": f"unrequested:{item['file']}",
            }
        )
    findings.sort(key=lambda f: 0 if f["severity"] == "high" else 1)  # stable
    return findings


def _dedup_key(finding, source_ref):
    """GC6 dedup key: normalized finding text (lowercase, collapsed
    whitespace) + source-ref."""
    normalized = re.sub(r"\s+", " ", finding).strip().lower()
    return f"{normalized}\x00{source_ref.strip().lower()}"


def scan_existing_cv(text):
    """Scan tasks.md for CV lines. Returns (max_n, unchecked_keys).

    max_n counts every CV-<n> (checked or not) so numbering always continues;
    only UNCHECKED items block re-append — a checked-off match is a
    regression and re-appends (GC6)."""
    max_n = 0
    unchecked = set()
    for line in (text or "").splitlines():
        match = CV_LINE_RE.match(line.strip())
        if not match:
            continue
        max_n = max(max_n, int(match.group("num")))
        if match.group("state") != " ":
            continue
        finding, sep, tail = match.group("rest").rpartition(" — ")
        if not sep:
            continue
        source_ref = tail.split(",", 1)[0]
        unchecked.add(_dedup_key(finding, source_ref))
    return max_n, unchecked


def append_cv_findings(tasks_path, findings, date):
    """Append qualifying CV lines to tasks.md under FINDINGS_HEADER.

    The section is created at file end only when at least one line is added
    (GC3: no empty header); when every finding dedups away, tasks.md is not
    touched at all — byte-for-byte identical. Existing task lines are never
    rewritten, renumbered, or reordered (GC2)."""
    text = tasks_path.read_text(encoding="utf-8") if tasks_path.is_file() else ""
    max_n, unchecked = scan_existing_cv(text)
    appended = []
    skipped = []
    next_n = max_n
    for finding in findings:
        key = _dedup_key(finding["finding"], finding["source_ref"])
        if key in unchecked:
            skipped.append(f"{finding['finding']} — {finding['source_ref']}")
            continue
        next_n += 1
        appended.append(
            f"- [ ] CV-{next_n} [{finding['severity']}] {finding['finding']} "
            f"— {finding['source_ref']}, from converge {date}"
        )
        unchecked.add(key)
    if not appended:
        return {"appended": [], "skipped": skipped, "changed": False}

    lines = text.splitlines()
    header_indexes = [
        i for i, line in enumerate(lines) if line.strip() == FINDINGS_HEADER
    ]
    if header_indexes:
        header_idx = header_indexes[0]
        end = len(lines)
        for i in range(header_idx + 1, len(lines)):
            if lines[i].startswith("## "):
                end = i
                break
        insert_at = end
        while insert_at > header_idx + 1 and not lines[insert_at - 1].strip():
            insert_at -= 1
        new_lines = lines[:insert_at] + appended + lines[insert_at:]
        new_text = "\n".join(new_lines)
        if not text or text.endswith("\n"):
            new_text += "\n"
    else:
        new_text = text
        if new_text and not new_text.endswith("\n"):
            new_text += "\n"
        if new_text:
            new_text += "\n"
        new_text += FINDINGS_HEADER + "\n\n" + "\n".join(appended) + "\n"
    tasks_path.write_text(new_text, encoding="utf-8")
    return {"appended": appended, "skipped": skipped, "changed": True}


def apply_judgment(project_path, issue_id, judgment_path, date):
    """Apply a Judgment JSON: converge.md run section + tasks.md CV lines.

    Returns (report, ok). ok is False on invalid judgment file, missing issue
    spec dir, or write failure (GC4 exit contract, both output modes)."""
    root = Path(project_path).resolve()
    report = {
        "schema": APPLY_SCHEMA,
        "issue_id": issue_id,
        "generated": date,
        "summary": None,
        "converge_md": None,
        "appended": [],
        "skipped_duplicates": [],
        "tasks_md_changed": False,
        "errors": [],
    }
    spec_dir = root / "specs" / issue_id
    if not spec_dir.is_dir():
        report["errors"].append(f"issue spec dir missing: specs/{issue_id}/")
        return report, False
    try:
        raw = Path(judgment_path).read_text(encoding="utf-8")
    except OSError as exc:
        report["errors"].append(f"cannot read judgment file: {exc}")
        return report, False
    try:
        judgment = json.loads(raw)
    except json.JSONDecodeError as exc:
        report["errors"].append(f"judgment file is not valid JSON: {exc}")
        return report, False
    validation_errors = validate_judgment(judgment)
    if validation_errors:
        report["errors"].extend(validation_errors)
        return report, False

    report["summary"] = _summary_line(judgment)
    findings = build_findings(judgment)
    try:
        # converge.md always records the run; tasks.md only gains lines when
        # a high/medium finding survives dedup (GC3 no-op path).
        append_converge_report(spec_dir / "converge.md", issue_id, judgment, date)
        report["converge_md"] = str(spec_dir / "converge.md")
        result = append_cv_findings(spec_dir / "tasks.md", findings, date)
    except OSError as exc:
        report["errors"].append(f"write failed: {exc}")
        return report, False
    report["appended"] = result["appended"]
    report["skipped_duplicates"] = result["skipped"]
    report["tasks_md_changed"] = result["changed"]
    return report, True


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


def _apply_human_summary(report):
    lines = [f"converge apply: {report['issue_id']} (date {report['generated']})"]
    if report["summary"]:
        lines.append(f"  {report['summary']}")
    if report["converge_md"]:
        lines.append(f"  wrote: {report['converge_md']}")
    if report["tasks_md_changed"]:
        lines.append(f"  tasks.md: appended {len(report['appended'])} CV line(s)")
        lines.extend(f"    {line}" for line in report["appended"])
    else:
        lines.append("  tasks.md: unchanged")
    if report["skipped_duplicates"]:
        lines.append(
            f"  skipped duplicates ({len(report['skipped_duplicates'])}):"
        )
        lines.extend(f"    - {item}" for item in report["skipped_duplicates"])
    if report["errors"]:
        lines.append(f"  errors ({len(report['errors'])}):")
        lines.extend(f"    - {error}" for error in report["errors"])
    return "\n".join(lines)


def _run_apply(args):
    root = Path(args.project_path).resolve()
    date = args.date or _dt.date.today().isoformat()
    report, ok = apply_judgment(root, args.issue_id, args.apply_judgment, date)

    # GC4: identical exit behavior in both output modes.
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_apply_human_summary(report))
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
    mode.add_argument(
        "--apply-judgment",
        metavar="JUDGMENT_JSON",
        default=None,
        help="Apply a judge's Judgment JSON: append a run section to "
        "specs/<id>/converge.md and CV findings to specs/<id>/tasks.md.",
    )
    parser.add_argument("--json", action="store_true", help="Print the evidence JSON instead of a summary.")
    parser.add_argument("--date", default=None, help="Generated date (ISO); defaults to today.")
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES, help="Max files with content included (default: 30).")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES, help="Max total content bytes (default: 204800).")
    args = parser.parse_args(argv)

    if args.evidence:
        return _run_evidence(args, runner or run_command)
    return _run_apply(args)


if __name__ == "__main__":
    raise SystemExit(main())
