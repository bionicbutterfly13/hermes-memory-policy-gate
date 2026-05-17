from pathlib import Path
import unittest

from hermes_memory_policy_gate.evaluator import evaluate_cases


class EvaluatorTests(unittest.TestCase):
    def test_all_seed_scenarios_pass(self):
        report = evaluate_cases(Path(__file__).resolve().parents[1] / "scenarios" / "memory_routing_cases.json")
        self.assertEqual(report["failed"], 0)
        self.assertTrue(report["dry_run_only"])
        self.assertFalse(report["live_writes"])


if __name__ == "__main__":
    unittest.main()
