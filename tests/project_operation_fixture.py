from pathlib import Path


def resolved_context(root=".", *, status="active", trust="internal", project_id="project-a"):
    canonical_root = str(Path(root).resolve())
    return {
        "schema": "moduflow.project-resolution.v1",
        "status": "resolved",
        "project_id": project_id,
        "reason_code": "explicit_id",
        "canonical_root": canonical_root,
        "relative_paths": {},
        "paths": {},
        "trust_scope": trust,
        "project_status": status,
        "policy_trust_scope": trust,
        "policy_inputs": {
            "project_status_source": status,
            "trust_scope_source": trust,
        },
        "capabilities": {},
        "capability_reasons": {},
        "warnings": [],
        "question": "",
    }


def context_with_policy(project_operation, root=".", *, status="active", trust="internal"):
    context = resolved_context(root, status=status, trust=trust)
    context.update(project_operation.compute_project_policy(status, trust))
    return context
