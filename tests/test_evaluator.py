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

    def test_phase4_live_write_intent_cases_never_mutate(self):
        report = evaluate_cases(Path(__file__).resolve().parents[1] / "scenarios" / "memory_routing_cases.json")
        write_intent_cases = [item for item in report["results"] if item["live_write_intent"]]
        self.assertGreaterEqual(len(write_intent_cases), 6)
        self.assertEqual(report["live_write_intents"], len(write_intent_cases))
        self.assertFalse(report["live_writes"])
        for item in write_intent_cases:
            self.assertTrue(item["ok"], item["name"])
            self.assertFalse(item["would_mutate"], item["name"])

    def test_evaluator_checks_optional_phase4_contract_fields(self):
        report = evaluate_cases(Path(__file__).resolve().parents[1] / "scenarios" / "memory_routing_cases.json")
        phase4_case = next(
            item for item in report["results"]
            if item["name"] == "phase4 live user preference write intent stays advisory"
        )
        self.assertTrue(phase4_case["ok"])
        self.assertEqual(phase4_case["checks"], {
            "tier": True,
            "blocked": True,
            "enforced": True,
            "enforcement_action": True,
            "dry_run": True,
            "would_mutate": True,
            "approval_required": True,
        })


if __name__ == "__main__":
    unittest.main()
