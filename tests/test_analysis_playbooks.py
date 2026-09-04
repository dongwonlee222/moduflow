import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYBOOKS = ROOT / "templates" / "analysis-playbooks"
EXPECTED = {
    "monthly-trend": "exploratory",
    "cpo-change": "exploratory",
    "amount-band": "exploratory",
    "charging-speed": "exploratory",
    "policy-impact": "causal",
}
ALLOWED_NUMBERS = {"2026", "2027", "0.1", "1", "01", "04", "09"}


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


production = load_module("project_production", "scripts/project_production.py")
runs = load_module("project_analysis_run", "scripts/project_analysis_run.py")


class DefaultAnalysisPlaybookTest(unittest.TestCase):
    def _parsed(self):
        for name in EXPECTED:
            yield name, production.parse_playbook(ROOT, PLAYBOOKS / f"{name}.md")

    def test_the_five_accepted_analyses_ship_as_playbooks(self):
        self.assertTrue((PLAYBOOKS / "README.md").is_file())
        for name in EXPECTED:
            self.assertTrue((PLAYBOOKS / f"{name}.md").is_file(), name)

    def test_each_default_parses_and_states_when_to_use_it(self):
        for name, playbook in self._parsed():
            with self.subTest(playbook=name):
                self.assertTrue(playbook["retrieval_trigger"].strip())
                self.assertEqual(playbook["status"], "candidate")
                self.assertEqual(playbook["approved_by"], "")
                self.assertEqual(playbook["deliverable_types"], ["analysis"])

    def test_check_ids_are_unique_and_ascending(self):
        for name, playbook in self._parsed():
            with self.subTest(playbook=name):
                ids = [item["id"] for item in playbook["required_checks"]]
                self.assertTrue(ids)
                self.assertEqual(ids, sorted(ids))
                self.assertEqual(len(ids), len(set(ids)))

    def test_auto_rules_use_only_the_three_supported_forms(self):
        for name, playbook in self._parsed():
            with self.subTest(playbook=name):
                for item in playbook["required_checks"]:
                    if item["kind"] != "auto":
                        self.assertIsNone(item["rule"])
                        continue
                    self.assertIn(
                        item["rule"]["form"], ("section", "forbidden", "approved-copy")
                    )

    def test_approved_copy_rules_name_a_real_approved_block(self):
        for name, playbook in self._parsed():
            with self.subTest(playbook=name):
                block = playbook["sections"]["Approved Copy Blocks"]
                for item in playbook["required_checks"]:
                    if item["kind"] == "auto" and item["rule"]["form"] == "approved-copy":
                        self.assertIn(item["rule"]["value"], block)

    def test_prefill_reads_claim_class_and_caveats_from_every_default(self):
        for name, playbook in self._parsed():
            with self.subTest(playbook=name):
                prefill = runs.prefill_run(playbook)
                self.assertEqual(prefill["claim_class"], EXPECTED[name])
                self.assertTrue(prefill["caveats"])
                self.assertTrue(prefill["playbook_check_ids"])
                self.assertEqual(
                    prefill["required_code_checks"],
                    list(runs.CODE_CHECKS[EXPECTED[name]]),
                )

    def test_defaults_carry_no_company_metric_or_currency_values(self):
        for name in EXPECTED:
            with self.subTest(playbook=name):
                text = (PLAYBOOKS / f"{name}.md").read_text(encoding="utf-8")
                text = re.sub(r"CHK\d{3}", "", text)
                self.assertNotIn("%", text, f"{name} carries a percentage")
                self.assertIsNone(
                    re.search(r"\d[\d,]*\s*(원|만원|억)", text),
                    f"{name} carries a currency amount",
                )
                numbers = set(re.findall(r"\d+(?:\.\d+)?", text)) - ALLOWED_NUMBERS
                self.assertEqual(numbers, set(), f"{name} carries stray numbers")

    def test_no_default_records_a_procedure_it_cannot_prove(self):
        for name, playbook in self._parsed():
            with self.subTest(playbook=name):
                self.assertEqual(playbook["process_ref"]["kind"], "none")
                self.assertEqual(playbook["process_ref"]["ref"], "")
                self.assertTrue(playbook["process_ref"]["missing"])


if __name__ == "__main__":
    unittest.main()
