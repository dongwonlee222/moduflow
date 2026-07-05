import json
import tempfile
import unittest
from pathlib import Path

from scripts import spec_consistency


def write_trio(root, issue_id, spec=None, plan=None, tasks=None):
    spec_dir = root / "specs" / issue_id
    spec_dir.mkdir(parents=True, exist_ok=True)
    if spec is not None:
        (spec_dir / "spec.md").write_text(spec, encoding="utf-8")
    if plan is not None:
        (spec_dir / "plan.md").write_text(plan, encoding="utf-8")
    if tasks is not None:
        (spec_dir / "tasks.md").write_text(tasks, encoding="utf-8")
    return spec_dir


class SpecConsistencyTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    # 1. uncovered AC bullet -> exactly one coverage warn naming it
    def test_uncovered_ac_bullet_flagged(self):
        spec = (
            "# Spec: Widget\n\n"
            "## Acceptance Criteria\n\n"
            "- The gizmo must reticulate splines automatically\n"
        )
        plan = "## Overview\n\nUnrelated planning text about widgets and gadgets.\n"
        tasks = "## Stream A\n\n- [ ] build widget gadget\n"
        write_trio(self.root, "001-x", spec=spec, plan=plan, tasks=tasks)

        result = spec_consistency.analyze(self.root, "001-x")
        coverage_findings = [f for f in result["findings"] if f["check"] == "coverage"]
        self.assertEqual(len(coverage_findings), 1)
        self.assertIn("reticulate splines", coverage_findings[0]["message"])
        self.assertEqual(coverage_findings[0]["severity"], "warn")

    # 2. covered fixture -> zero coverage findings
    def test_covered_ac_bullet_clean(self):
        spec = (
            "# Spec: Widget\n\n"
            "## Acceptance Criteria\n\n"
            "- The widget gadget must reticulate splines\n"
        )
        plan = "## Overview\n\nThe widget gadget reticulate splines plan.\n"
        tasks = "## Stream A\n\n- [ ] implement widget gadget splines\n"
        write_trio(self.root, "002-x", spec=spec, plan=plan, tasks=tasks)

        result = spec_consistency.analyze(self.root, "002-x")
        coverage_findings = [f for f in result["findings"] if f["check"] == "coverage"]
        self.assertEqual(coverage_findings, [])

    # 3. vague terms without digits flagged; with digits clean
    def test_vague_terms(self):
        spec = (
            "# Spec: Widget\n\n"
            "## Requirements\n\n"
            "- The system must be fast and secure\n"
            "- The system responds within 200 ms\n\n"
            "## Acceptance Criteria\n\n"
            "- Something covered elsewhere\n"
        )
        plan = "## Overview\n\ncovered elsewhere text here\n"
        tasks = "## Stream A\n\n- [ ] covered elsewhere task\n"
        write_trio(self.root, "003-x", spec=spec, plan=plan, tasks=tasks)

        result = spec_consistency.analyze(self.root, "003-x")
        vague_findings = [f for f in result["findings"] if f["check"] == "vague-term"]
        self.assertEqual(len(vague_findings), 2)
        messages = " ".join(f["message"] for f in vague_findings)
        self.assertIn("fast", messages)
        self.assertIn("secure", messages)
        for f in vague_findings:
            self.assertNotIn("200 ms", f["message"])

    # 4. plan Stream B with no tasks Stream B -> structure error; matching -> clean
    def test_stream_mismatch_plan_to_tasks(self):
        spec = "# Spec\n\n## Acceptance Criteria\n\n- covered thing here\n"
        plan_mismatch = "### Stream B — Widgets\n\nSome text.\n"
        tasks_empty = "## Stream A\n\n- [ ] covered thing here task\n"
        write_trio(self.root, "004-x", spec=spec, plan=plan_mismatch, tasks=tasks_empty)

        result = spec_consistency.analyze(self.root, "004-x")
        structure_errors = [
            f for f in result["findings"]
            if f["check"] == "structure" and "Stream B" in f["message"] and f["severity"] == "error"
        ]
        self.assertEqual(len(structure_errors), 1)

        plan_match = "### Stream B — Widgets\n\nSome text.\n"
        tasks_match = "## Stream B\n\n- [ ] covered thing here task\n"
        write_trio(self.root, "004-y", spec=spec, plan=plan_match, tasks=tasks_match)
        result2 = spec_consistency.analyze(self.root, "004-y")
        structure_errors2 = [
            f for f in result2["findings"]
            if f["check"] == "structure" and "Stream B" in f["message"]
        ]
        self.assertEqual(structure_errors2, [])

    # 5. tasks Stream Z with no plan stream -> structure warn
    def test_stream_mismatch_tasks_to_plan(self):
        spec = "# Spec\n\n## Acceptance Criteria\n\n- covered thing here\n"
        plan = "### Stream A — Widgets\n\nSome text.\n"
        tasks = "## Stream A\n\n- [ ] covered thing here task\n\n## Stream Z\n\n- [ ] extra task\n"
        write_trio(self.root, "005-x", spec=spec, plan=plan, tasks=tasks)

        result = spec_consistency.analyze(self.root, "005-x")
        warns = [
            f for f in result["findings"]
            if f["check"] == "structure" and "Stream Z" in f["message"] and f["severity"] == "warn"
        ]
        self.assertEqual(len(warns), 1)

    # 6. spec missing Acceptance Criteria -> structure error
    def test_missing_acceptance_criteria_section(self):
        spec = "# Spec\n\n## Requirements\n\n- something\n"
        plan = "### Stream A — X\n\ntext\n"
        tasks = "## Stream A\n\n- [ ] task\n"
        write_trio(self.root, "006-x", spec=spec, plan=plan, tasks=tasks)

        result = spec_consistency.analyze(self.root, "006-x")
        errors = [
            f for f in result["findings"]
            if f["check"] == "structure" and "Acceptance Criteria" in f["message"]
        ]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["severity"], "error")

    # 7. missing plan.md -> info finding AND coverage still evaluated vs tasks alone
    def test_missing_plan_info_and_coverage_runs(self):
        spec = (
            "# Spec\n\n## Acceptance Criteria\n\n"
            "- The widget gadget must reticulate splines\n"
        )
        tasks = "## Stream A\n\n- [ ] widget gadget reticulate splines task\n"
        write_trio(self.root, "007-x", spec=spec, plan=None, tasks=tasks)

        result = spec_consistency.analyze(self.root, "007-x")
        info_findings = [
            f for f in result["findings"]
            if f["check"] == "artifacts" and "plan.md" in f["message"]
        ]
        self.assertEqual(len(info_findings), 1)
        self.assertEqual(info_findings[0]["severity"], "info")
        self.assertGreaterEqual(result["summary"]["coverage_checked"], 1)
        coverage_findings = [f for f in result["findings"] if f["check"] == "coverage"]
        self.assertEqual(coverage_findings, [])

    # 8. tasks.md with zero checkboxes -> structure error
    def test_empty_tasks_checkboxes(self):
        spec = "# Spec\n\n## Acceptance Criteria\n\n- covered\n"
        plan = "## Overview\n\ncovered\n"
        tasks = "## Stream A\n\nNo checkboxes here, just prose.\n"
        write_trio(self.root, "008-x", spec=spec, plan=plan, tasks=tasks)

        result = spec_consistency.analyze(self.root, "008-x")
        errors = [
            f for f in result["findings"]
            if f["check"] == "structure" and "zero checkboxes" in f["message"]
        ]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["severity"], "error")

    # 9. JSON shape: schema key, summary counts consistent with findings list
    def test_json_shape_and_summary_consistency(self):
        spec = (
            "# Spec\n\n## Requirements\n\n- must be fast\n\n"
            "## Acceptance Criteria\n\n- uncovered bullet about zephyrs\n"
        )
        plan = "## Overview\n\nunrelated\n"
        tasks = "## Stream A\n\n- [ ] unrelated task\n"
        write_trio(self.root, "009-x", spec=spec, plan=plan, tasks=tasks)

        result = spec_consistency.analyze(self.root, "009-x")
        self.assertEqual(result["schema"], "moduflow.spec-consistency.v1")
        self.assertEqual(result["issue_id"], "009-x")
        self.assertIn("findings", result)
        self.assertIn("summary", result)

        error_count = sum(1 for f in result["findings"] if f["severity"] == "error")
        warn_count = sum(1 for f in result["findings"] if f["severity"] == "warn")
        info_count = sum(1 for f in result["findings"] if f["severity"] == "info")
        self.assertEqual(result["summary"]["error"], error_count)
        self.assertEqual(result["summary"]["warn"], warn_count)
        self.assertEqual(result["summary"]["info"], info_count)

        # json-serializable
        json.dumps(result, ensure_ascii=False)

    # 10. determinism: two runs -> identical output
    def test_determinism(self):
        spec = (
            "# Spec\n\n## Requirements\n\n- must be fast and secure\n\n"
            "## Acceptance Criteria\n\n- uncovered bullet about zephyrs\n"
            "- covered widget gadget bullet\n"
        )
        plan = "### Stream A — X\n\nwidget gadget text\n"
        tasks = "## Stream A\n\n- [ ] covered widget gadget task\n"
        write_trio(self.root, "010-x", spec=spec, plan=plan, tasks=tasks)

        result1 = spec_consistency.analyze(self.root, "010-x")
        result2 = spec_consistency.analyze(self.root, "010-x")
        self.assertEqual(result1, result2)

    # 11. fence exclusion: AC-lookalike bullet inside fenced block not scanned
    def test_fence_exclusion(self):
        spec = (
            "# Spec\n\n## Acceptance Criteria\n\n"
            "- covered widget gadget bullet\n\n"
            "```\n"
            "## Acceptance Criteria\n"
            "- The gizmo must be fast and secure and totally uncovered zephyr\n"
            "```\n"
        )
        plan = "## Overview\n\nwidget gadget text\n"
        tasks = "## Stream A\n\n- [ ] covered widget gadget task\n"
        write_trio(self.root, "011-x", spec=spec, plan=plan, tasks=tasks)

        result = spec_consistency.analyze(self.root, "011-x")
        coverage_findings = [f for f in result["findings"] if f["check"] == "coverage"]
        self.assertEqual(coverage_findings, [])
        vague_findings = [f for f in result["findings"] if f["check"] == "vague-term"]
        self.assertEqual(vague_findings, [])
        self.assertEqual(result["summary"]["coverage_checked"], 1)

    # 12. missing specs/<id> dir -> CLI-level error path
    def test_missing_specs_dir_raises(self):
        with self.assertRaises(FileNotFoundError):
            spec_consistency.analyze(self.root, "999-nonexistent")

    # Review finding: threshold boundary was untested. Flag condition is
    # shared < max(2, 0.3*len(bt)) — "whichever is stricter".
    def test_coverage_threshold_boundary(self):
        # 8-token bullet, exactly 2 shared -> 2 < max(2, 2.4) -> flagged
        spec = (
            "## Acceptance Criteria\n\n"
            "- alpha bravo charlie delta echo foxtrot golf hotel\n"
        )
        tasks = "## Stream A\n\n- [ ] alpha bravo november oscar papa\n"
        write_trio(self.root, "010-x", spec=spec, plan="### Stream A — x\n", tasks=tasks)
        result = spec_consistency.analyze(self.root, "010-x")
        self.assertEqual(result["summary"]["coverage_flagged"], 1)

        # 4-token bullet, 2 shared -> 2 >= max(2, 1.2) -> NOT flagged
        spec2 = "## Acceptance Criteria\n\n- alpha bravo charlie delta\n"
        write_trio(self.root, "011-y", spec=spec2, plan="### Stream A — x\n", tasks=tasks)
        result2 = spec_consistency.analyze(self.root, "011-y")
        self.assertEqual(result2["summary"]["coverage_flagged"], 0)

    # Review finding: zero-token (e.g. Korean-only) bullets must not inflate
    # coverage_checked — they are skipped, not evaluated.
    def test_zero_token_bullet_not_counted_as_checked(self):
        spec = (
            "## Acceptance Criteria\n\n"
            "- 한글로만 작성된 기준\n"
            "- alpha bravo charlie\n"
        )
        tasks = "## Stream A\n\n- [ ] alpha bravo charlie\n"
        write_trio(self.root, "012-z", spec=spec, plan="### Stream A — x\n", tasks=tasks)
        result = spec_consistency.analyze(self.root, "012-z")
        self.assertEqual(result["summary"]["coverage_checked"], 1)
        self.assertEqual(result["summary"]["coverage_flagged"], 0)


if __name__ == "__main__":
    unittest.main()
