"""Sales AI domain contracts for Phoenix Sales V1.0.

This module defines the Sales-owned AI boundary. Core owns provider/model
infrastructure; Sales owns capabilities, commercial context and action authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class SalesAICapability(str, Enum):
    SALES_COPILOT = "SALES_COPILOT"
    DAILY_SALES_BRIEF = "DAILY_SALES_BRIEF"
    CUSTOMER_INTELLIGENCE = "CUSTOMER_INTELLIGENCE"
    BASKET_GROWTH = "BASKET_GROWTH"
    OPPORTUNITY_INTELLIGENCE = "OPPORTUNITY_INTELLIGENCE"
    NEXT_BEST_ACTION = "NEXT_BEST_ACTION"
    SOLUTION_BUILDER = "SOLUTION_BUILDER"
    PRICING_INTELLIGENCE = "PRICING_INTELLIGENCE"
    QUOTE_INTELLIGENCE = "QUOTE_INTELLIGENCE"
    LOST_OPPORTUNITY_INTELLIGENCE = "LOST_OPPORTUNITY_INTELLIGENCE"
    COMPETITOR_INTELLIGENCE = "COMPETITOR_INTELLIGENCE"
    COMMUNICATION_INTELLIGENCE = "COMMUNICATION_INTELLIGENCE"
    FORECAST_INTELLIGENCE = "FORECAST_INTELLIGENCE"
    CUSTOMER_DECLINE_DETECTION = "CUSTOMER_DECLINE_DETECTION"


class AIAuthority(str, Enum):
    INFORM = "INFORM"
    RECOMMEND = "RECOMMEND"
    DRAFT = "DRAFT"
    EXECUTE_WITH_CONFIRMATION = "EXECUTE_WITH_CONFIRMATION"
    RESTRICTED = "RESTRICTED"


@dataclass(frozen=True)
class SalesAIContext:
    tenant_id: str
    user_id: str
    capability: SalesAICapability
    entity_type: str | None = None
    entity_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.user_id.strip():
            raise ValueError("tenant_id and user_id are required")
        if self.entity_id is not None and self.entity_type is None:
            raise ValueError("entity_type is required when entity_id is provided")


@dataclass(frozen=True)
class AIRecommendation:
    tenant_id: str
    capability: SalesAICapability
    authority: AIAuthority
    title: str
    recommendation: str
    confidence: Decimal
    reasons: tuple[str, ...] = ()
    suggested_action: str | None = None
    requires_confirmation: bool = False
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.title.strip() or not self.recommendation.strip():
            raise ValueError("tenant_id, title and recommendation are required")
        if not 0 <= self.confidence <= 100:
            raise ValueError("confidence must be between 0 and 100")
        if self.authority is AIAuthority.EXECUTE_WITH_CONFIRMATION and not self.requires_confirmation:
            raise ValueError("execute-with-confirmation recommendations require confirmation")
        if self.authority is AIAuthority.RESTRICTED:
            raise ValueError("restricted AI actions cannot be represented as executable recommendations")


@dataclass(frozen=True)
class AIDecisionRecord:
    tenant_id: str
    user_id: str
    capability: SalesAICapability
    recommendation_id: UUID
    decision: str
    result: str | None = None
    context_summary: str | None = None
    id: UUID = field(default_factory=uuid4)
    decided_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.user_id.strip() or not self.decision.strip():
            raise ValueError("tenant_id, user_id and decision are required")


@dataclass(frozen=True)
class SalesAIResult:
    recommendation: AIRecommendation
    decision: AIDecisionRecord | None = None
