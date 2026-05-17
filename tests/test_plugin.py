import json
import unittest

from hermes_memory_policy_gate.plugin import TOOL_NAME, TOOLSET, register


class DummyContext:
    def __init__(self):
        self.tools = []

    def register_tool(self, **kwargs):
        self.tools.append(kwargs)


class PluginRegistrationTests(unittest.TestCase):
    def test_registers_memory_policy_tool(self):
        ctx = DummyContext()
        register(ctx)
        self.assertEqual(len(ctx.tools), 1)
        tool = ctx.tools[0]
        self.assertEqual(tool["name"], TOOL_NAME)
        self.assertEqual(tool["toolset"], TOOLSET)
        self.assertIn("schema", tool)
        self.assertIn("handler", tool)

        payload = json.loads(tool["handler"]({"text": "I prefer concise status."}))
        self.assertEqual(payload["tier"], "user_memory")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["would_mutate"])


if __name__ == "__main__":
    unittest.main()
