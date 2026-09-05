"""Sales AI application commands and queries."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from phoenix_sales.domain.sales_ai import AIAuthority, AIRecommendation, SalesAIContext, SalesAICapability
from phoenix_sales.services.sales_ai import SalesAIService


@dataclass(frozen=True)
class CreateAIRecommendationCommand:
    context: SalesAIContext
    title: str
    recommendation: str
    confidence: object
    reasons: tuple[str, ...] = ()
    authority: AIAuthority = AIAuthority.RECOMMEND
    suggested_action: str | None = None


@dataclass(frozen=True)
class DecideAIRecommendationCommand:
    recommendation: AIRecommendation
    decision: str
    result: str | None = None
    context_summary: str | None = None


@dataclass(frozen=True)
class ListAIDecisionsQuery:
    recommendation_id: UUID | None = None


class SalesAIApplication:
    def __init__(self, service: SalesAIService) -> None:
        self.service = service

    def create_recommendation(self, command: CreateAIRecommendationCommand) -> AIRecommendation:
        return self.service.recommend(command.context, title=command.title, recommendation=command.recommendation, confidence=command.confidence, reasons=command.reasons, authority=command.authority, suggested_action=command.suggested_action)

    def decide(self, command: DecideAIRecommendationCommand):
        return self.service.decide(command.recommendation, command.decision, result=command.result, context_summary=command.context_summary)

    def execute_confirmed(self, recommendation: AIRecommendation):
        return self.service.execute_confirmed(recommendation)

    def list_decisions(self, query: ListAIDecisionsQuery):
        return self.service.decisions(query.recommendation_id)
