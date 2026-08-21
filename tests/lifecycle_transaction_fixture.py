"""Stable, side-effect-free fixtures for lifecycle transaction contracts."""


def resolved_transaction_context(*, staging_root="/tmp/lifecycle-a", clock="2030-01-01T00:00:00Z"):
    """Return one resolved context with irrelevant volatile fields for identity tests."""
    return {
        "schema": "moduflow.project-resolution.v1",
        "status": "resolved",
        "project_id": "alpha",
        "canonical_root": "/projects/alpha",
        "staging_root": staging_root,
        "clock": clock,
    }


def lifecycle_intent_fields(action, *, target_lifecycle=None, production_change=None):
    """Return complete literal inputs for a lifecycle intent."""
    return {
        "issue_id": "103-atomic-lifecycle-state-transaction",
        "action": action,
        "actor": "dongwon",
        "source_event": "request:42",
        "target_lifecycle": target_lifecycle,
        "production_change": production_change,
    }
