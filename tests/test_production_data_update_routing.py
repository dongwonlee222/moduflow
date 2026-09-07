import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProductionDataUpdateRoutingTests(unittest.TestCase):
    def test_recurring_data_updates_route_to_product_production(self):
        router = (ROOT / "skills" / "pm-execution-router" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        index = (ROOT / "skills" / "index" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("recurring data updates", router)
        self.assertIn("반복 데이터 업데이트", router)
        self.assertIn("데이터 업데이트 플레이북", index)

    def test_product_production_documents_data_update_playbooks(self):
        command = (ROOT / "commands" / "product-production.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("recurring data updates", command)
        self.assertIn("--type campaign-report-data-update", command)
        self.assertIn("actual or forecast", command)


if __name__ == "__main__":
    unittest.main()
