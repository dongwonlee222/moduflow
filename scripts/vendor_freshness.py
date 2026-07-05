#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.project_sync import CommandResult, run_command

GITHUB_URL_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+?)/?$")


def _parse_owner_repo(url):
    m = GITHUB_URL_RE.match(url or "")
    if not m:
        return None
    return m.group(1), m.group(2)


def _run(runner, args, cwd):
    return runner(args, cwd)


def _read_lock(lock_path):
    return json.loads(Path(lock_path).read_text(encoding="utf-8"))


def check_vendor_freshness(lock_path, runner=None):
    runner = runner or run_command
    cwd = Path(lock_path).resolve().parent
    lock_data = _read_lock(lock_path)

    results = []
    for source in lock_data.get("sources", []):
        if source.get("type") != "github":
            continue

        source_id = source.get("id")
        owner_repo = _parse_owner_repo(source.get("url"))
        last_synced = source.get("last_synced") or {}
        last_synced_sha = last_synced.get("sha")

        if not owner_repo:
            results.append(
                {
                    "id": source_id,
                    "drifted": True,
                    "last_synced_sha": last_synced_sha,
                    "latest_sha": None,
                    "latest_date": None,
                    "error": f"could not parse owner/repo from url: {source.get('url')}",
                }
            )
            continue

        owner, repo = owner_repo
        pin = source.get("pin", "main")
        api_result = _run(runner, ["gh", "api", f"repos/{owner}/{repo}/commits/{pin}"], cwd)

        if api_result.returncode != 0:
            results.append(
                {
                    "id": source_id,
                    "drifted": True,
                    "last_synced_sha": last_synced_sha,
                    "latest_sha": None,
                    "latest_date": None,
                    "error": (api_result.stderr or "").strip() or "gh api call failed",
                }
            )
            continue

        try:
            payload = json.loads(api_result.stdout)
            latest_sha = payload["sha"]
            latest_date = payload["commit"]["committer"]["date"]
        except (ValueError, KeyError):
            results.append(
                {
                    "id": source_id,
                    "drifted": True,
                    "last_synced_sha": last_synced_sha,
                    "latest_sha": None,
                    "latest_date": None,
                    "error": "could not parse gh api response",
                }
            )
            continue

        results.append(
            {
                "id": source_id,
                "drifted": latest_sha != last_synced_sha,
                "last_synced_sha": last_synced_sha,
                "latest_sha": latest_sha,
                "latest_date": latest_date,
                "error": None,
            }
        )

    return results


def sync_last_synced(lock_path, results):
    lock_data = _read_lock(lock_path)
    by_id = {r["id"]: r for r in results if r.get("error") is None}

    for source in lock_data.get("sources", []):
        result = by_id.get(source.get("id"))
        if not result:
            continue
        source["last_synced"] = {"sha": result["latest_sha"], "date": result["latest_date"]}

    Path(lock_path).write_text(json.dumps(lock_data, indent=2) + "\n", encoding="utf-8")
    return lock_data


def format_report(results):
    lines = []
    for result in results:
        if result.get("error"):
            lines.append(f"{result['id']}: check failed — {result['error']}")
        elif result["drifted"]:
            known = result["last_synced_sha"] or "(never reviewed)"
            lines.append(f"{result['id']}: drifted — last_synced {known} vs latest {result['latest_sha']}")
        else:
            lines.append(f"{result['id']}: up to date ({result['latest_sha']})")
    return lines


def main():
    parser = argparse.ArgumentParser(description="Check vendor.lock.json freshness against upstream GitHub sources.")
    parser.add_argument("lock_path", nargs="?", default="vendor.lock.json")
    parser.add_argument("--sync", action="store_true", help="Write last_synced markers for checked sources.")
    args = parser.parse_args()

    results = check_vendor_freshness(args.lock_path)
    for line in format_report(results):
        print(line)

    if args.sync:
        sync_last_synced(args.lock_path, results)
        print("last_synced updated in", args.lock_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
