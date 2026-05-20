from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from .policy import decide_memory_policy
from .schemas import MemoryPolicyDecision, MemoryPolicyRequest

MEMORY_TOOL_SURFACE = "memory_tool"
MEMORY_TOOL_ENTRYPOINT = "tools.memory_tool.memory_tool"
MEMORY_TOOL_WRITE_PATH = "builtin_memory_tool"

_MUTATING_MEMORY_ACTIONS = {"add", "replace", "remove"}


@dataclass(frozen=True)
class MemoryToolCallerPlan:
    """Non-writing caller-side plan for a future built-in memory-tool interceptor.

    The plan tells an outer caller whether it should call the original Hermes
    memory tool. It never calls the tool itself and never writes memory.
    """

    surface: str
    entrypoint: str
    caller_action: str
    call_original: bool
    policy_would_mutate: bool
    original_call_mutates_if_called: bool
    policy_request: MemoryPolicyRequest
    decision: MemoryPolicyDecision
    operator_message: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["policy_request"] = {
            "text": self.policy_request.text,
            "source": self.policy_request.source,
            "context": self.policy_request.context,
            "provenance": self.policy_request.provenance,
            "dry_run": self.policy_request.dry_run,
            "metadata": dict(self.policy_request.metadata),
        }
        data["decision"] = self.decision.to_dict()
        return data


def _candidate_text(args: Mapping[str, Any]) -> str:
    action = str(args.get("action") or "").lower()
    if action == "remove":
        return str(args.get("old_text") or args.get("content") or "")
    return str(args.get("content") or args.get("old_text") or "")


def _requested_tier_for_target(target: str) -> str:
    if target == "user":
        return "user_memory"
    return "memory"


def build_memory_tool_policy_request(args: Mapping[str, Any]) -> MemoryPolicyRequest:
    """Build a non-dry-run policy request for the built-in memory tool surface.

    This models the point immediately before `tools.memory_tool.memory_tool`
    would mutate `USER.md` or `MEMORY.md`. It does not perform that mutation.
    """

    action = str(args.get("action") or "").lower()
    target = str(args.get("target") or "memory").lower()
    existing_metadata = dict(args.get("metadata") or {})
    metadata = {
        **existing_metadata,
        "live_write_intent": True,
        "entrypoint": MEMORY_TOOL_ENTRYPOINT,
        "write_path": MEMORY_TOOL_WRITE_PATH,
        "requested_tier": existing_metadata.get("requested_tier") or _requested_tier_for_target(target),
        "action": action,
        "target": target,
    }
    return MemoryPolicyRequest(
        text=_candidate_text(args),
        source=str(args.get("source") or MEMORY_TOOL_SURFACE),
        context=str(args.get("context") or ""),
        provenance=str(args.get("provenance") or MEMORY_TOOL_ENTRYPOINT),
        dry_run=False,
        metadata=metadata,
    )


def plan_memory_tool_call(args: Mapping[str, Any]) -> MemoryToolCallerPlan:
    """Return caller-side handling for a proposed Hermes `memory` tool call.

    Phase 5 scope is design/contract only for the built-in memory tool surface:
    blocked policy decisions suppress the original write, approval-gated
    decisions hold before the original write, and advisory decisions may pass
    through to the original caller. This function itself remains non-writing.
    """

    request = build_memory_tool_policy_request(args)
    decision = decide_memory_policy(request)
    action = request.metadata.get("action", "")
    original_call_mutates = action in _MUTATING_MEMORY_ACTIONS

    if decision.blocked:
        caller_action = "block_original_memory_write"
        call_original = False
        message = (
            "Blocked original Hermes memory_tool write; route ephemeral task progress "
            "to transcript/session_search instead."
        )
    elif decision.approval_required:
        caller_action = "require_explicit_approval"
        call_original = False
        message = (
            "Hold original Hermes memory_tool write until an approved source or "
            "explicit approval is present."
        )
    else:
        caller_action = "advisory_passthrough"
        call_original = True
        message = (
            "Policy gate is advisory for this memory_tool call; the caller may "
            "choose whether to invoke the original memory tool."
        )

    return MemoryToolCallerPlan(
        surface=MEMORY_TOOL_SURFACE,
        entrypoint=MEMORY_TOOL_ENTRYPOINT,
        caller_action=caller_action,
        call_original=call_original,
        policy_would_mutate=False,
        original_call_mutates_if_called=original_call_mutates,
        policy_request=request,
        decision=decision,
        operator_message=message,
    )
