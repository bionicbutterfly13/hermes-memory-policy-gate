from __future__ import annotations

import json
from typing import Any

from .policy import decide_memory_policy

TOOL_NAME = "memory_policy_gate"
TOOLSET = "memory_policy"


def _handler(args: dict[str, Any], **_: Any) -> str:
    decision = decide_memory_policy(args)
    return json.dumps(decision.to_dict(), indent=2, sort_keys=True)


def register(ctx) -> None:
    """Hermes plugin registration entry point."""
    ctx.register_tool(
        name=TOOL_NAME,
        toolset=TOOLSET,
        description="Classify proposed memory writes without mutating memory.",
        emoji="🧠",
        schema={
            "name": TOOL_NAME,
            "description": "Dry-run memory policy gate. Returns an auditable routing decision; performs no writes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Candidate memory content."},
                    "source": {"type": "string", "description": "Where the candidate came from."},
                    "context": {"type": "string", "description": "Optional lane/task context."},
                    "provenance": {"type": "string", "description": "Source id, file path, session id, or artifact pointer."},
                    "dry_run": {"type": "boolean", "default": True, "description": "When false, the gate may return a no-write block decision; the plugin still performs no writes."},
                    "metadata": {"type": "object", "description": "Optional structured hints."},
                },
                "required": ["text"],
            },
        },
        handler=lambda args, **kwargs: _handler(args, **kwargs),
    )
