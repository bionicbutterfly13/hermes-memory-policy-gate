import unittest

from hermes_memory_policy_gate import TargetTier, decide_memory_policy


class PolicyTests(unittest.TestCase):
    def test_noise_routes_to_session_search_only(self):
        decision = decide_memory_policy({"text": "yeah ok"})
        self.assertEqual(decision.tier, TargetTier.SESSION_SEARCH_ONLY)
        self.assertFalse(decision.would_mutate)
        self.assertTrue(decision.dry_run)

    def test_clean_field_blocks_unapproved_source(self):
        decision = decide_memory_policy({"text": "Old campaign detail for Quill marketing."})
        self.assertEqual(decision.tier, TargetTier.NO_WRITE_CLEAN_FIELD_BOUNDARY)
        self.assertTrue(decision.approval_required)

    def test_user_preference_routes_to_user_memory(self):
        decision = decide_memory_policy({"text": "I prefer concise status reports."})
        self.assertEqual(decision.tier, TargetTier.USER_MEMORY)

    def test_reusable_workflow_routes_to_skill_patch(self):
        decision = decide_memory_policy({"text": "Reusable procedure for plugin release checks."})
        self.assertEqual(decision.tier, TargetTier.SKILL_PATCH)

    def test_completed_task_progress_routes_to_session_search_only(self):
        decision = decide_memory_policy({"text": "Fixed bug X, submitted PR #123, and completed Phase 4 today."})
        self.assertEqual(decision.tier, TargetTier.SESSION_SEARCH_ONLY)
        self.assertIn("ephemeral_task_progress", decision.reason_codes)
        self.assertFalse(decision.would_mutate)

    def test_session_search_only_enforces_durable_write_block_when_not_dry_run(self):
        decision = decide_memory_policy({
            "text": "Fixed bug X, submitted PR #123, and completed Phase 4 today.",
            "dry_run": False,
        })
        self.assertEqual(decision.tier, TargetTier.SESSION_SEARCH_ONLY)
        self.assertFalse(decision.dry_run)
        self.assertFalse(decision.would_mutate)
        self.assertTrue(decision.blocked)
        self.assertTrue(decision.enforced)
        self.assertEqual(decision.enforcement_action, "block_durable_write")

    def test_non_session_search_tiers_remain_advisory_when_not_dry_run(self):
        decision = decide_memory_policy({
            "text": "I prefer concise status reports.",
            "dry_run": False,
        })
        self.assertEqual(decision.tier, TargetTier.USER_MEMORY)
        self.assertTrue(decision.dry_run)
        self.assertFalse(decision.would_mutate)
        self.assertFalse(decision.blocked)
        self.assertFalse(decision.enforced)
        self.assertEqual(decision.enforcement_action, "advisory_only")

    def test_user_memory_write_attempt_blocks_ephemeral_task_progress(self):
        decision = decide_memory_policy({
            "text": "Remember that I submitted PR #123 and completed Phase 4 today.",
            "dry_run": False,
            "metadata": {"requested_tier": "user_memory"},
        })
        self.assertEqual(decision.tier, TargetTier.SESSION_SEARCH_ONLY)
        self.assertIn("ephemeral_task_progress", decision.reason_codes)
        self.assertFalse(decision.dry_run)
        self.assertFalse(decision.would_mutate)
        self.assertTrue(decision.blocked)
        self.assertTrue(decision.enforced)
        self.assertEqual(decision.enforcement_action, "block_user_memory_write")

    def test_durable_user_preference_stays_advisory_for_user_memory_write_attempt(self):
        decision = decide_memory_policy({
            "text": "I prefer concise status reports.",
            "dry_run": False,
            "metadata": {"requested_tier": "user_memory"},
        })
        self.assertEqual(decision.tier, TargetTier.USER_MEMORY)
        self.assertFalse(decision.would_mutate)
        self.assertFalse(decision.blocked)
        self.assertFalse(decision.enforced)
        self.assertEqual(decision.enforcement_action, "advisory_only")


if __name__ == "__main__":
    unittest.main()
