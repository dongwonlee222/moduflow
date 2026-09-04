"""Synthetic-only builders for Issue 091 analysis run tests."""

RUN_ID = "run-22222222-2222-4222-8222-222222222222"
OTHER_ID = "run-33333333-3333-4333-8333-333333333333"


def valid_run(**overrides):
    entry = {
        "id": RUN_ID,
        "title": "Synthetic A weekly usage, week 36",
        "issue_id": "001-synthetic-a",
        "playbook_ref": {
            "playbook_id": "pb-weekly-usage",
            "version": "1.0",
            "deliverable_type": "analysis",
        },
        "decision_question": "Did synthetic A usage change enough to revisit the plan?",
        "claim_class": "exploratory",
        "population": {
            "definition": "Synthetic A active records",
            "comparison": None,
            "comparison_reason": "single-cohort trend",
        },
        "measure": {
            "numerator": "session count",
            "denominator": "active record count",
            "denominator_reason": "",
            "unit": "sessions per record",
        },
        "time_window": {
            "start": "2026-08-31",
            "end": "2026-09-06",
            "label": "week 36",
            "grain": "week",
        },
        "maturity": {"status": "mature", "observation_until": None, "reason": "window closed"},
        "costs": {
            "applicable": False,
            "items": [],
            "unknown_items": [],
            "reason": "usage trend, no cost claim",
        },
        "filters": [{"rule": "synthetic region A only", "reason": "matches the question"}],
        "exclusions": [{"rule": "drop test records", "reason": "not real usage"}],
        "method": {"steps": ["extract tab", "aggregate by week"], "tooling": "external spreadsheet"},
        "sources": [],
        "execution_evidence": {
            "skill_ref": None,
            "skill_version": None,
            "adapter_version": None,
            "query_hash": None,
            "code_hash": None,
            "snapshot_ref": None,
            "missing": [{"field": "skill_ref", "reason": "no external skill declared"}],
        },
        "checks": [
            {
                "id": "population-defined",
                "source": "code",
                "result": "pass",
                "reason": "",
                "evidence_ref": None,
            }
        ],
        "outputs": [],
        "production_record_ref": None,
        "conclusion": "Synthetic A usage rose week over week within the stated window.",
        "caveats": ["Synthetic fixture data; not a business measurement."],
        "decision_refs": [],
        "run_state": "completed",
        "validation_state": "unvalidated",
        "approval_state": "unapproved",
        "decision_state": "decided",
        "approval_ref": None,
        "state_history": [],
        "follow_up": None,
        "supersedes": None,
        "change_reason": None,
        "created_at": "2026-09-07",
    }
    entry.update(overrides)
    return entry


def runs_file(*entries):
    import json

    body = "---\nschema: moduflow.analysis-runs.v1\n---\n\n"
    for entry in entries:
        body += f"## {entry['id']}\n\n```json\n{json.dumps(entry, ensure_ascii=False, indent=2)}\n```\n\n"
    return body
