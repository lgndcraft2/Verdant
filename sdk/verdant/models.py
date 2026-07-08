from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VerdantBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, protected_namespaces=())


class ContextType(str, Enum):
    hiring = "hiring"
    lending = "lending"
    content = "content"
    healthcare = "healthcare"

    @classmethod
    def normalize(cls, value: str | ContextType | None) -> ContextType:
        if isinstance(value, cls):
            return value
        if value is None:
            return cls.content

        normalized = str(value).strip().lower().replace(" ", "_").replace("-", "_")
        aliases = {
            "content_moderation": cls.content,
            "content_moderation_review": cls.content,
            "moderation": cls.content,
        }
        if normalized in aliases:
            return aliases[normalized]

        for member in cls:
            if member.value == normalized:
                return member
        raise ValueError(f"Unsupported context type: {value}")


class BiasSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IntentStageOutput(VerdantBaseModel):
    detected_intent: str
    context_type: ContextType
    user_intent_summary: str
    entities: list[str] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    needs_review: bool = False


class BaselineStageOutput(VerdantBaseModel):
    context_type: ContextType
    baseline_name: str
    baseline_version: str
    demographic_focus: list[str] = Field(default_factory=list)
    baseline_summary: str
    policy_notes: list[str] = Field(default_factory=list)
    baseline_data: dict[str, Any] = Field(default_factory=dict)
    source: str = "supabase"
    confidence: float = Field(ge=0.0, le=1.0)


class BiasStageOutput(VerdantBaseModel):
    flags: list[str] = Field(default_factory=list)
    matched_patterns: list[str] = Field(default_factory=list)
    severity: BiasSeverity = BiasSeverity.low
    bias_score: int = Field(ge=0, le=100)
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("bias_score", mode="before")
    @classmethod
    def _clamp_bias_score(cls, value: Any) -> int:
        return max(0, min(100, int(value)))


class ExplainStageOutput(VerdantBaseModel):
    plain_language_explanation: str
    reasoning_summary: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class TrustStageOutput(VerdantBaseModel):
    trust_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    alerts: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("trust_score", mode="before")
    @classmethod
    def _clamp_trust_score(cls, value: Any) -> int:
        return max(0, min(100, int(value)))


class PipelineStageOutputs(VerdantBaseModel):
    intent: IntentStageOutput
    baseline: BaselineStageOutput
    bias: BiasStageOutput
    explanation: ExplainStageOutput
    trust: TrustStageOutput


class AuditPayload(VerdantBaseModel):
    audit_id: UUID | None = None
    request_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    context_type: ContextType
    input_text: str
    output_text: str
    raw_output: Any = None
    clean_output: Any = None
    stages: PipelineStageOutputs
    trust_score: int = Field(ge=0, le=100)
    flags: list[str] = Field(default_factory=list)
    explanation: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_name: str = "claude-sonnet-4-6"
    duration_ms: int = 0
    error: str | None = None


class WrapResult(VerdantBaseModel):
    output: Any
    audit: AuditPayload
    trust_score: int = Field(ge=0, le=100)
    flags: list[str] = Field(default_factory=list)
    explanation: str


class PipelineRunRequest(VerdantBaseModel):
    input_text: str
    context_type: ContextType
    metadata: dict[str, Any] = Field(default_factory=dict)
