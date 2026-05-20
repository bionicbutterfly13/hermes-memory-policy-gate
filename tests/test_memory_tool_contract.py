import unittest

from hermes_memory_policy_gate.memory_tool_contract import plan_memory_tool_call


class MemoryToolCallerContractTests(unittest.TestCase):
    def test_blocks_original_memory_tool_call_when_policy_blocks(self):
        plan = plan_memory_tool_call({
            "action": "add",
            "target": "memory",
            "content": "Fixed bug X, submitted PR #123, and completed Phase 4 today.",
        })

        self.assertEqual(plan.surface, "memory_tool")
        self.assertEqual(plan.caller_action, "block_original_memory_write")
        self.assertFalse(plan.call_original)
        self.assertFalse(plan.policy_would_mutate)
        self.assertTrue(plan.original_call_mutates_if_called)
        self.assertTrue(plan.decision.blocked)
        self.assertTrue(plan.decision.enforced)
        self.assertEqual(plan.decision.enforcement_action, "block_durable_write")
        self.assertIn("transcript/session_search", plan.operator_message)

    def test_blocks_user_memory_attempt_with_specific_action(self):
        plan = plan_memory_tool_call({
            "action": "add",
            "target": "user",
            "content": "Remember that I submitted PR #123 and completed Phase 4 today.",
        })

        self.assertEqual(plan.caller_action, "block_original_memory_write")
        self.assertFalse(plan.call_original)
        self.assertEqual(plan.decision.tier.value, "session_search_only")
        self.assertEqual(plan.decision.enforcement_action, "block_user_memory_write")

    def test_clean_field_memory_tool_call_requires_approval_before_original_call(self):
        plan = plan_memory_tool_call({
            "action": "add",
            "target": "user",
            "content": "Use this old campaign detail for Quill marketing memory.",
        })

        self.assertEqual(plan.caller_action, "require_explicit_approval")
        self.assertFalse(plan.call_original)
        self.assertTrue(plan.decision.approval_required)
        self.assertFalse(plan.policy_would_mutate)

    def test_durable_preference_can_passthrough_without_policy_mutation(self):
        plan = plan_memory_tool_call({
            "action": "add",
            "target": "user",
            "content": "I prefer concise approvals and blockers instead of long dumps.",
        })

        self.assertEqual(plan.caller_action, "advisory_passthrough")
        self.assertTrue(plan.call_original)
        self.assertFalse(plan.policy_would_mutate)
        self.assertTrue(plan.original_call_mutates_if_called)
        self.assertFalse(plan.decision.blocked)
        self.assertFalse(plan.decision.enforced)
        self.assertTrue(plan.decision.dry_run)

    def test_remove_uses_old_text_as_policy_text_and_defaults_to_memory_target(self):
        plan = plan_memory_tool_call({
            "action": "remove",
            "old_text": "Fixed bug X, submitted PR #123",
        })

        self.assertEqual(plan.caller_action, "block_original_memory_write")
        self.assertFalse(plan.call_original)
        self.assertEqual(plan.policy_request.metadata["target"], "memory")
        self.assertEqual(plan.policy_request.metadata["action"], "remove")


if __name__ == "__main__":
    unittest.main()
