from pathlib import Path
import unittest

from hermes_memory_policy_gate.evaluator import evaluate_cases


class EvaluatorTests(unittest.TestCase):
    def test_all_seed_scenarios_pass(self):
        report = evaluate_cases(Path(__file__).resolve().parents[1] / "scenarios" / "memory_routing_cases.json")
        self.assertEqual(report["failed"], 0)
        self.assertFalse(report["dry_run_only"])
        self.assertFalse(report["live_writes"])

    def test_evaluator_checks_expected_enforcement_fields(self):
        report = evaluate_cases(Path(__file__).resolve().parents[1] / "scenarios" / "memory_routing_cases.json")
        enforcement_case = next(
            item for item in report["results"]
            if item["name"] == "user memory write attempt blocks ephemeral task progress"
        )
        self.assertTrue(enforcement_case["ok"])
        self.assertTrue(enforcement_case["blocked"])
        self.assertTrue(enforcement_case["enforced"])
        self.assertEqual(enforcement_case["enforcement_action"], "block_user_memory_write")


if __name__ == "__main__":
    unittest.main()
