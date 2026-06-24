import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BusinessDocumentWorkflowTests(unittest.TestCase):
    def test_business_plan_skill_routes_market_entry_and_style_gate(self):
        skill = (ROOT / "skills" / "business-plan" / "SKILL.md").read_text(encoding="utf-8")

        for phrase in [
            "market-entry-analysis",
            "business-document",
            "시장 진입 분석",
            "프로젝트 메모리",
            "했습니다",
            "예상됩니다",
        ]:
            self.assertIn(phrase, skill)

    def test_market_entry_reference_templates_exist(self):
        required = [
            "document-types.md",
            "market-entry-analysis.md",
            "calculation-model.md",
            "source-checklist.md",
            "pdf-quality-gate.md",
            "writing-style.md",
        ]

        for name in required:
            path = ROOT / "templates" / "business-plan" / name
            self.assertTrue(path.is_file(), f"missing {path}")

    def test_sample_market_entry_artifact_uses_polite_korean_tone(self):
        report = ROOT / "business" / "test-market-entry-analysis" / "market-entry" / "report.md"
        content = report.read_text(encoding="utf-8")

        self.assertIn("검토했습니다", content)
        self.assertIn("예상됩니다", content)
        self.assertNotRegex(content, re.compile(r"(한다|이다|권고한다|필요하다)\."))


if __name__ == "__main__":
    unittest.main()
