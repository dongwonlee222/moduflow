"""Run the Issue 112 gates across every spec in the real checkout.

Today's count is len(parse_tasks(...)): build_worker_plan emits exactly one
worker task per parsed checkbox, so that is the number of worker tasks, prompts
and worktree names produced right now.
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

import gate_prototype as gp
from scripts.worker_orchestrator import parse_tasks

rows = []
for tasks_path in sorted(REPO.glob("specs/*/tasks.md")):
    issue = tasks_path.parent.name
    try:
        today = len(parse_tasks(tasks_path))
    except ValueError:
        continue
    scanned = gp.scan_tasks(tasks_path)
    result = gp.build_routing(scanned, REPO)
    rows.append(
        {
            "issue": issue,
            "today": today,
            "after": len(result["tasks"]),
            "status": result["status"],
            "backend": result["backend"] or "-",
            "gaps": len(result["gaps"]),
        }
    )

verdicts = Counter(r["status"] for r in rows)
backends = Counter(r["backend"] for r in rows if r["status"] == "ok")
today_total = sum(r["today"] for r in rows)
after_total = sum(r["after"] for r in rows)

print(f"specs scanned: {len(rows)}\n")
print(f"{'verdict':<18}{'specs':>6}")
for verdict in ("ok", "needs_plan", "not_applicable"):
    print(f"{verdict:<18}{verdicts[verdict]:>6}")

ok_rows = [r for r in rows if r["status"] == "ok"]
ok_today = sum(r["today"] for r in ok_rows)
ok_after = sum(r["after"] for r in ok_rows)

print("\nthree separate effects, not one ratio")
print(f"  1. filtering, on the specs that still plan : {ok_today} -> {ok_after} worker tasks")
print(f"  2. specs refused outright (needs_plan)     : {verdicts['needs_plan']}")
print(f"  3. specs recognised as finished            : {verdicts['not_applicable']}")
print(f"  (corpus-wide checkbox total today is {today_total}; comparing it to "
      f"{after_total} would merge all three)")

print("\nbackend chosen where a plan is produced")
for backend, count in backends.most_common():
    print(f"  {backend:<18}{count:>3}")

print("\nspecs that still produce a usable plan")
print(f"  {'issue':<52}{'today':>6}{'after':>6}  backend")
for row in rows:
    if row["status"] == "ok":
        print(f"  {row['issue']:<52}{row['today']:>6}{row['after']:>6}  {row['backend']}")

refused = [r for r in rows if r["status"] == "needs_plan"]
print(f"\nrefused with needs_plan: {len(refused)} specs, "
      f"{sum(r['gaps'] for r in refused)} boundary gaps total")
print("  worst offenders")
for row in sorted(refused, key=lambda r: -r["gaps"])[:5]:
    print(f"  {row['issue']:<52}{row['gaps']:>4} gaps")
