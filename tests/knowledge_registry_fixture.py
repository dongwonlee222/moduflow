"""Synthetic inputs shared by registry tests; never company source material."""
import json
from pathlib import Path

from scripts import project_registry
from scripts.project_sync import run_command

ARTIFACT_A = "art-11111111-1111-4111-8111-111111111111"
ARTIFACT_B = "art-22222222-2222-4222-8222-222222222222"


def make_entry(**overrides):
    return {
        "id": ARTIFACT_A, "name": "Synthetic population", "kind": "definition",
        "summary": "Defines population A.", "read_when": "Before population comparisons.",
        "as_of": "2026-08-31", "updated_at": "2026-09-02",
        "period": {"start": None, "end": None, "label": "not time-bound"},
        "state": "draft", "owner": "Synthetic owner", "issue_ids": ["001-synthetic-a"],
        "local_path": "knowledge/references/population.md", "external_url": None,
        "private_ref": None, "source_requirement": "required", "unavailable_reason": None,
        "review_after": "2026-10-01", "approval_ref": None, "superseded_by": None,
        **overrides,
    }


def registry_text(entries):
    return "---\nschema: moduflow.artifacts.v1\n---\n\n# Artifacts\n\n" + "".join(
        f"## {entry['id']}\n\n```json\n{json.dumps(entry, ensure_ascii=False, indent=2)}\n```\n\n"
        for entry in entries
    )


class SyntheticProject:
    def __init__(self, root, project_id="synthetic-a", nested=False):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.context = project_registry.project_context_for_root(self.root)
        self.context["project_id"] = project_id
        if nested:
            for role in ("workspace", "knowledge", "memory", "issues"):
                relative = f"product/{role}"
                self.context["relative_paths"][role] = relative
                self.context["paths"][role] = str(self.root / relative)

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def seed(self, entries=None):
        entries = [make_entry()] if entries is None else entries
        workspace = self.context["relative_paths"]["workspace"]
        self.write(f"{workspace}/knowledge.md", "# Knowledge\n\n## Core Metrics\n\nPopulation definitions.\n")
        self.write(f"{workspace}/artifacts.md", registry_text(entries))
        for entry in entries:
            if entry["local_path"]:
                self.write(entry["local_path"], "# Synthetic source\nPOPULATION_A\n")
            for issue in entry["issue_ids"]:
                issues = self.context["relative_paths"]["issues"]
                self.write(f"{issues}/{issue}.md", "# Synthetic issue\n\n**Status: backlog** — created 2026-09-02.\n")
        return self

    def git(self, *args):
        result = run_command(["git", *args], self.root)
        if result.returncode:
            raise AssertionError(result.stderr)
        return result.stdout.strip()

    def commit(self):
        if not (self.root / ".git").exists():
            self.git("init", "-q")
            self.git("config", "user.email", "synthetic@example.test")
            self.git("config", "user.name", "Synthetic fixture")
        self.git("add", ".")
        self.git("commit", "-qm", "synthetic snapshot")
        return self.git("rev-parse", "HEAD")


def transaction_project(root, nested=False):
    from tests import test_project_lifecycle_transaction as legacy
    from scripts import project_knowledge
    fixture = legacy.TransactionPlanningTests()
    fixture.ISSUE_ID = "001-synthetic-a"
    context = fixture.scaffold(Path(root), nested=nested)
    context["project_id"] = "synthetic-a"
    project = SyntheticProject(root)
    project.context = context
    (Path(context["paths"]["workspace"]) / "transactions").mkdir()
    project.write(context["relative_paths"]["issues"] + "/001-synthetic-a.md",
                  "# Issue: `001-synthetic-a`\n\n**Status: backlog** — created 2026-09-02.\n"
                  "**Priority: p2**\n\n## Notes\n\nSynthetic issue prose.\n")
    project_knowledge.apply_knowledge_plan(project_knowledge.build_knowledge_plan(root, project_context=context),
                                          project_context=context)
    project.write(context["relative_paths"]["knowledge"] + "/references/population.md", "# Population\nSynthetic content\n")
    return project


def shared_lifecycle_bytes(project):
    workspace = project.context["relative_paths"]["workspace"]
    paths = [".moduflow/state.json", *(workspace + "/" + name for name in
              ("goal.md", "loop-state.json", "roadmap.md", "dashboard.md"))]
    return {p: (project.root / p).read_bytes() if (project.root / p).exists() else None for p in paths}
