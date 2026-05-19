from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class TargetTier(str, Enum):
    NO_WRITE_CLEAN_FIELD_BOUNDARY = "no_write_clean_field_boundary"
    USER_MEMORY = "user_memory"
    MNEMOSYNE_GLOBAL = "mnemosyne_global"
    MNEMOSYNE_SESSION = "mnemosyne_session"
    SKILL_PATCH = "skill_patch"
    PROJECT_ARTIFACT = "project_artifact"
    SESSION_SEARCH_ONLY = "session_search_only"
    SUPERSEDED_UPDATE = "superseded_update"
    NOISY_MEMORY_INVALIDATION = "noisy_memory_invalidation"


@dataclass(frozen=True)
class MemoryPolicyRequest:
    text: str
    source: str = "unspecified"
    context: str = ""
    provenance: str = ""
    dry_run: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "MemoryPolicyRequest":
        return cls(
            text=str(data.get("text") or data.get("content") or ""),
            source=str(data.get("source") or "unspecified"),
            context=str(data.get("context") or ""),
            provenance=str(data.get("provenance") or data.get("source_id") or ""),
            dry_run=bool(data.get("dry_run", True)),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass(frozen=True)
class MemoryPolicyDecision:
    tier: TargetTier
    confidence: float
    reason_codes: list[str]
    source: str
    provenance: str
    approval_required: bool
    verification_step: str
    dry_run: bool = True
    would_mutate: bool = False
    blocked: bool = False
    enforced: bool = False
    enforcement_action: str = "advisory_only"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["tier"] = self.tier.value
        return data
