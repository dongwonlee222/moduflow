#!/usr/bin/env python3
import json
import sys
from pathlib import Path


REQUIRED_FILES = [
    ".claude-plugin/plugin.json",
    ".mcp.json",
    "README.md",
    "vendor.lock.json",
    "docs/architecture.md",
    "docs/workflow.md",
    "commands/product-start.md",
    "commands/product-migrate.md",
    "commands/product-profile.md",
    "commands/product-knowledge.md",
    "commands/product-decision.md",
    "commands/product-research.md",
    "commands/product-benchmark.md",
    "commands/product-report.md",
    "commands/product-evidence.md",
    "commands/product-portfolio.md",
    "commands/product-projects.md",
    "commands/product-weekly.md",
    "commands/product-handoff.md",
    "commands/product-risks.md",
    "commands/product-inbox.md",
    "commands/product-opportunity.md",
    "commands/product-issue.md",
    "commands/product-spec.md",
    "commands/product-analyze.md",
    "commands/product-design.md",
    "commands/product-prototype.md",
    "commands/product-roadmap.md",
    "commands/product-plan.md",
    "commands/product-execute.md",
    "commands/product-status.md",
    "commands/product-review.md",
    "commands/product-pr.md",
    "commands/product-release.md",
    "commands/product-update.md",
    "commands/product-sync.md",
    "commands/product-doctor.md",
    "skills/pm-execution-router/SKILL.md",
    "skills/index/SKILL.md",
    "skills/git-native-artifact-model/SKILL.md",
    "skills/roadmap-management/SKILL.md",
    "skills/progress-dashboard/SKILL.md",
    "skills/source-adapter-policy/SKILL.md",
    "skills/superpowers-execution-bridge/SKILL.md",
    "skills/data-analysis-bridge/SKILL.md",
    "skills/design-prototype-bridge/SKILL.md",
    "adapters/productivity.yaml",
    "adapters/product-management.yaml",
    "adapters/spec-kit.yaml",
    "adapters/superpowers.yaml",
    "adapters/product-design.yaml",
    "adapters/data-analytics.yaml",
    "adapters/documents.yaml",
    "adapters/git.yaml",
    "templates/issues/issue.md",
    "templates/specs/spec.md",
    "templates/specs/plan.md",
    "templates/specs/tasks.md",
    "templates/specs/status.md",
    "templates/workspace/roadmap.md",
    "templates/workspace/dashboard.md",
    "templates/workspace/inbox.md",
    "templates/workspace/opportunities.md",
    "templates/profile/project-profile.md",
    "templates/profile/environments.json",
    "templates/profile/integrations.json",
    "templates/knowledge/artifact.md",
    "templates/portfolio/projects.json",
    "templates/portfolio/portfolio-dashboard.md",
    "templates/portfolio/portfolio-roadmap.md",
    "templates/portfolio/weekly-status.md",
    "templates/workflow/review-gates.md",
    "templates/workflow/approval-policy.md",
    "templates/workflow/release-policy.md",
    "templates/workflow/handoff.md",
    "templates/workflow/risks.md",
    "templates/workflow/record.md",
    "templates/moduflow-config.json",
    "templates/moduflow-state.json",
    "scripts/project_doctor.py",
    "scripts/project_migrate.py",
    "scripts/project_profile.py",
    "scripts/project_knowledge.py",
    "scripts/project_portfolio.py",
    "scripts/project_workflow.py",
    "workers/pm-strategist.md",
    "workers/roadmap-planner.md",
    "workers/spec-architect.md",
    "workers/ux-flow-worker.md",
    "workers/data-reviewer.md",
    "workers/implementation-worker.md",
    "workers/qa-reviewer.md",
    "workers/release-manager.md",
]


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    missing = [name for name in REQUIRED_FILES if not (root / name).is_file()]

    errors = []
    if missing:
        errors.append("Missing required files:")
        errors.extend(f"  - {name}" for name in missing)

    try:
        manifest = load_json(root / ".claude-plugin/plugin.json")
        if manifest.get("name") != "moduflow":
            errors.append("plugin.json name must be 'moduflow'")
    except Exception as exc:
        errors.append(f"Could not read plugin.json: {exc}")

    try:
        vendor_lock = load_json(root / "vendor.lock.json")
        source_ids = {source.get("id") for source in vendor_lock.get("sources", [])}
        for required in [
            "anthropic-skills",
            "anthropic-knowledge-work-plugins",
            "github-spec-kit",
            "superpowers",
            "codex-product-design",
            "codex-data-analytics",
        ]:
            if required not in source_ids:
                errors.append(f"vendor.lock.json missing source: {required}")
    except Exception as exc:
        errors.append(f"Could not read vendor.lock.json: {exc}")

    if errors:
        print("ModuFlow validation failed")
        for error in errors:
            print(error)
        return 1

    print(f"ModuFlow validation passed: {root}")
    print(f"Checked {len(REQUIRED_FILES)} required files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
