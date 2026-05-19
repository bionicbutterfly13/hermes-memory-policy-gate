from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from . import reason_codes as rc
from .schemas import MemoryPolicyDecision, MemoryPolicyRequest, TargetTier

_NOISE_PATTERNS = [
    r"^\s*(ok|okay|yeah|yep|yes|no|cool|great|thanks|thank you|sounds good)(\s+(ok|okay|yeah|yep|yes|no|cool|great))*[.!\s]*$",
    r"^\s*(lol|haha|hmm|uh|um)\s*$",
]


def _contains_any(blob: str, needles: list[str]) -> bool:
    blob_l = blob.lower()
    return any(n in blob_l for n in needles)


def _is_noise(text: str) -> bool:
    return any(re.match(pat, text, flags=re.IGNORECASE) for pat in _NOISE_PATTERNS)


def _session_search_decision(
    request: MemoryPolicyRequest,
    *,
    confidence: float,
    reason_codes: list[str],
    source: str,
    provenance: str,
    verification_step: str,
    notes: list[str],
) -> MemoryPolicyDecision:
    """Return the only phase-2 enforced decision: block durable writes.

    Non-dry-run requests are honored only for session_search_only routes. The
    gate still performs no writes; it returns a blocking decision that callers
    can use to prevent a durable memory mutation.
    """
    enforce = not request.dry_run
    if enforce:
        notes = [
            *notes,
            "Enforced no-write: blocked durable memory mutation; transcript/session_search remains available.",
        ]
    return MemoryPolicyDecision(
        tier=TargetTier.SESSION_SEARCH_ONLY,
        confidence=confidence,
        reason_codes=reason_codes,
        source=source,
        provenance=provenance,
        approval_required=False,
        verification_step=verification_step,
        dry_run=request.dry_run,
        would_mutate=False,
        blocked=enforce,
        enforced=enforce,
        enforcement_action="block_durable_write" if enforce else "advisory_only",
        notes=notes,
    )


def decide_memory_policy(request: MemoryPolicyRequest | Mapping[str, Any]) -> MemoryPolicyDecision:
    """Return an auditable dry-run memory routing decision.

    This function is intentionally deterministic in phase 1. It performs no
    writes and calls no Hermes/Mnemosyne APIs.
    """
    if not isinstance(request, MemoryPolicyRequest):
        request = MemoryPolicyRequest.from_mapping(dict(request))

    text = request.text.strip()
    blob = "\n".join([text, request.context, str(request.metadata)]).lower()
    source = request.source or "unspecified"
    provenance = request.provenance or source
    reasons: list[str] = []
    notes: list[str] = []

    if not text:
        return _session_search_decision(
            request,
            confidence=0.35,
            reason_codes=[rc.LOW_SIGNAL],
            source=source,
            provenance=provenance,
            verification_step="No memory write: empty/low-signal input.",
            notes=["Low-signal input should not become durable memory."],
        )

    clean_field_terms = ["clean-field", "clean field", "quill", "marketing", "campaign", "old avatar", "old campaign"]
    approved_terms = ["approved source", "allowlisted", "source manifest", "explicitly approved"]
    if _contains_any(blob, clean_field_terms) and not _contains_any(blob, approved_terms):
        return MemoryPolicyDecision(
            tier=TargetTier.NO_WRITE_CLEAN_FIELD_BOUNDARY,
            confidence=0.93,
            reason_codes=[rc.CLEAN_FIELD_RISK, rc.UNAPPROVED_SOURCE],
            source=source,
            provenance=provenance,
            approval_required=True,
            verification_step="Require an approved source manifest or explicit approval before any memory write.",
            dry_run=True,
            would_mutate=False,
            notes=["Clean-field-sensitive material is blocked by default."],
        )

    operation = str(request.metadata.get("operation") or request.metadata.get("intent") or "").lower()
    if "invalidate" in operation or "remove noisy" in blob or "stale memory" in blob:
        return MemoryPolicyDecision(
            tier=TargetTier.NOISY_MEMORY_INVALIDATION,
            confidence=0.88,
            reason_codes=[rc.NOISY_MEMORY_TARGET],
            source=source,
            provenance=provenance,
            approval_required=True,
            verification_step="Review candidate memory id/text, then invalidate only after explicit approval.",
            dry_run=True,
            would_mutate=False,
            notes=["Prefer invalidation/supersession over hard deletion."],
        )

    if _contains_any(blob, ["i prefer", "my preference", "remember that i", "don't make me", "do not make me", "call me", "dr. mani wants"]):
        return MemoryPolicyDecision(
            tier=TargetTier.USER_MEMORY,
            confidence=0.86,
            reason_codes=[rc.DURABLE_USER_PREFERENCE],
            source=source,
            provenance=provenance,
            approval_required=False,
            verification_step="Write a compact declarative user preference; avoid imperative phrasing.",
            dry_run=True,
            would_mutate=False,
            notes=["Only durable preferences belong in always-injected user memory."],
        )

    if _contains_any(blob, ["supersedes", "replace prior", "correction", "instead of", "not the", "is not"]):
        return MemoryPolicyDecision(
            tier=TargetTier.SUPERSEDED_UPDATE,
            confidence=0.82,
            reason_codes=[rc.SUPERSEDES_PRIOR_FACT],
            source=source,
            provenance=provenance,
            approval_required=True,
            verification_step="Find the prior memory/fact, verify contradiction, then supersede rather than duplicate.",
            dry_run=True,
            would_mutate=False,
            notes=["Correction-like input should update an old fact, not create clutter."],
        )

    if _is_noise(text):
        return _session_search_decision(
            request,
            confidence=0.91,
            reason_codes=[rc.CONVERSATIONAL_NOISE],
            source=source,
            provenance=provenance,
            verification_step="No durable write; transcript/session search is sufficient.",
            notes=["Conversational acknowledgement only."],
        )

    if _contains_any(blob, ["reusable", "procedure", "workflow", "checklist", "skill", "playbook", "steps", "rubric"]):
        return MemoryPolicyDecision(
            tier=TargetTier.SKILL_PATCH,
            confidence=0.84,
            reason_codes=[rc.REUSABLE_PROCEDURE],
            source=source,
            provenance=provenance,
            approval_required=False,
            verification_step="Patch/create a class-level skill; put session-specific detail under references/.",
            dry_run=True,
            would_mutate=False,
            notes=["Procedures belong in skills, not user memory."],
        )

    if _contains_any(blob, ["active lane", "blocker", "approved base", "source of truth", "current artifact", "stop condition"]):
        return MemoryPolicyDecision(
            tier=TargetTier.MNEMOSYNE_SESSION,
            confidence=0.8,
            reason_codes=[rc.ACTIVE_LANE_STATE],
            source=source,
            provenance=provenance,
            approval_required=False,
            verification_step="Store compact session-scope operating state with source path and expiry if appropriate.",
            dry_run=True,
            would_mutate=False,
            notes=["Lane state should not pollute global durable memory."],
        )

    if _contains_any(blob, [
        "fixed bug",
        "bug fixed",
        "submitted pr",
        "opened pr",
        "merged pr",
        "pr #",
        "pull request",
        "closed issue",
        "completed phase",
        "phase done",
        "task done",
        "completed task",
        "finished task",
    ]):
        return _session_search_decision(
            request,
            confidence=0.87,
            reason_codes=[rc.EPHEMERAL_TASK_PROGRESS],
            source=source,
            provenance=provenance,
            verification_step="Do not write completed task logs to durable memory; use transcript/session_search unless explicitly promoted to a project artifact.",
            notes=["Completed work logs and PR/phase updates are stale quickly."],
        )

    if _contains_any(blob, ["/volumes/", "repo", "project", "file path", "artifact", "plan.md", "readme", "pyproject.toml"]):
        return MemoryPolicyDecision(
            tier=TargetTier.PROJECT_ARTIFACT,
            confidence=0.78,
            reason_codes=[rc.PROJECT_STATE],
            source=source,
            provenance=provenance,
            approval_required=False,
            verification_step="Write/update a project artifact in the active repo; do not store bulky state globally.",
            dry_run=True,
            would_mutate=False,
            notes=["Project state belongs near the project."],
        )

    if _contains_any(blob, ["always", "durable", "global", "operating rule", "cross-session", "source-of-truth pointer"]):
        return MemoryPolicyDecision(
            tier=TargetTier.MNEMOSYNE_GLOBAL,
            confidence=0.72,
            reason_codes=[rc.GLOBAL_OPERATING_RULE],
            source=source,
            provenance=provenance,
            approval_required=False,
            verification_step="Store compact global operating fact in Mnemosyne with high-quality provenance.",
            dry_run=True,
            would_mutate=False,
            notes=["Use global memory only for durable cross-session facts."],
        )

    return _session_search_decision(
        request,
        confidence=0.55,
        reason_codes=[rc.DEFAULT_SHADOW_ROUTE],
        source=source,
        provenance=provenance,
        verification_step="Do not write durable memory by default; rely on transcript/session_search unless promoted by review.",
        notes=["Default posture is conservative."],
    )
