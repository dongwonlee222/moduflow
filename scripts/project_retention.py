"""Release-count-based retention for issue-less records (issue 075).

Records (memory/*.md files carrying `kind:` frontmatter) that are neither
promoted (`promoted_to`) nor archived (`archived`) are archive candidates once
2 or more releases have shipped after their `date`. A release is approximated
by a commit touching `.claude-plugin/plugin.json` (every release bumps it).

Wall-clock retention was rejected in the 075 spec: at agent velocity a
90-day window just delays the flood; releases are the meaningful clock.

Usage:
    python3 scripts/project_retention.py <project-path> --status
    python3 scripts/project_retention.py <project-path> --write --date 2026-07-06
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

RETENTION_RELEASES = 2
PLUGIN_MANIFEST = ".claude-plugin/plugin.json"
RECORD_DIRS = (
    "memory/decisions",
    "memory/evidence",
    "memory/deliverables",
    "memory/notes",
    "memory/meetings",
    "memory/references",
)


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def run_command(args, cwd, timeout=10):
    try:
        completed = subprocess.run(
            args, cwd=str(cwd), capture_output=True, text=True, timeout=timeout
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)
    except subprocess.TimeoutExpired:
        return CommandResult(124, "", f"timed out after {timeout}s: {' '.join(args)}")


def parse_frontmatter(text):
    """Minimal YAML frontmatter reader: `key: value` lines between --- fences.
    Returns (dict, has_frontmatter)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, False
    data = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return data, True
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip()
    return {}, False


def releases_since(runner, cwd, iso_date):
    """Count release commits (touching the plugin manifest) after iso_date.
    Git failure surfaces as an error — never a silent zero (Global Constraint 2)."""
    args = [
        "git",
        "log",
        "--format=%H",
        f"--since={iso_date}T23:59:59",
        "--",
        PLUGIN_MANIFEST,
    ]
    result = runner(args, cwd)
    if result.returncode != 0:
        return None, f"git log failed ({' '.join(args)}): {(result.stderr or '').strip()}"
    count = len([l for l in (result.stdout or "").splitlines() if l.strip()])
    return count, None


def scan_records(root, runner=None):
    root = Path(root).resolve()
    runner = runner or run_command
    records = []
    errors = []
    for rel_dir in RECORD_DIRS:
        directory = root / rel_dir
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            fm, ok = parse_frontmatter(path.read_text(encoding="utf-8"))
            if not ok or "kind" not in fm:
                continue
            record = {
                "path": str(path.relative_to(root)),
                "kind": fm.get("kind", ""),
                "date": fm.get("date", ""),
                "promoted_to": fm.get("promoted_to", ""),
                "superseded_by": fm.get("superseded_by", "").strip("[]"),
                "archived": fm.get("archived", ""),
            }
            if record["promoted_to"] or record["archived"]:
                record["state"] = "settled"
            elif not record["date"]:
                record["state"] = "unpromoted"
                record["releases_since"] = None
            else:
                count, err = releases_since(runner, root, record["date"])
                if err:
                    errors.append(err)
                    record["state"] = "unknown"
                else:
                    record["releases_since"] = count
                    record["state"] = (
                        "archive-candidate" if count >= RETENTION_RELEASES else "unpromoted"
                    )
            records.append(record)
    return {"records": records, "errors": errors}


def retention_status(root, runner=None):
    scan = scan_records(root, runner)
    unpromoted = [r for r in scan["records"] if r["state"] in ("unpromoted", "archive-candidate")]
    oldest = min(unpromoted, key=lambda r: r["date"] or "9999", default=None)
    return {
        "schema": "moduflow.retention.v1",
        "ok": not scan["errors"],
        "errors": scan["errors"],
        "unpromoted_count": len(unpromoted),
        "oldest": {"path": oldest["path"], "date": oldest["date"]} if oldest else None,
        "archive_candidates": [
            r["path"] for r in scan["records"] if r["state"] == "archive-candidate"
        ],
        "archived_count": len(
            [r for r in scan["records"] if r["archived"]]
        ),
        "retention_releases": RETENTION_RELEASES,
    }


def archive_candidates(root, archive_date, runner=None):
    """Add `archived: <date>` to each candidate's frontmatter in place.
    Files never move (Global Constraint 3); the line is inserted before the
    closing fence, leaving everything else byte-identical."""
    root = Path(root).resolve()
    status = retention_status(root, runner)
    if not status["ok"]:
        return status
    archived = []
    for rel in status["archive_candidates"]:
        path = root / rel
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                lines.insert(idx, f"archived: {archive_date}\n")
                break
        path.write_text("".join(lines), encoding="utf-8")
        archived.append(rel)
    status["archived_now"] = archived
    return status


def main():
    parser = argparse.ArgumentParser(description="Issue-less record retention (075).")
    parser.add_argument("project_path", nargs="?", default=".")
    parser.add_argument("--status", action="store_true", help="Report retention state.")
    parser.add_argument("--write", action="store_true", help="Archive candidates in place.")
    parser.add_argument("--date", default="", help="Archive date (ISO), required with --write.")
    args = parser.parse_args()
    if args.write:
        if not args.date:
            print(json.dumps({"ok": False, "errors": ["--write requires --date"]}))
            return 1
        result = archive_candidates(args.project_path, args.date)
    else:
        result = retention_status(args.project_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
