"""Sales AI application boundary."""
from __future__ import annotations

from uuid import UUID

from phoenix_sales.api.contracts import RequestContext
from phoenix_sales.domain.sales_ai import AIAuthority, AIDecisionRecord, AIRecommendation, SalesAIContext, SalesAICapability, SalesAIResult


class SalesAIService:
    CREATE = "sales.ai.create"
    READ = "sales.ai.read"
    DECIDE = "sales.ai.decide"
    EXECUTE = "sales.ai.execute"

    def __init__(self, context: RequestContext) -> None:
        self.context = context
        self._decisions: list[AIDecisionRecord] = []

    def recommend(self, request: SalesAIContext, *, title: str, recommendation: str, confidence, reasons: tuple[str, ...] = (), authority: AIAuthority = AIAuthority.RECOMMEND, suggested_action: str | None = None) -> AIRecommendation:
        self._require(self.CREATE)
        self._tenant(request.tenant_id)
        if request.user_id != self.context.user.user_id:
            raise PermissionError("AI request user does not match request context")
        return AIRecommendation(request.tenant_id, request.capability, authority, title, recommendation, confidence, reasons, suggested_action, authority is AIAuthority.EXECUTE_WITH_CONFIRMATION)

    def decide(self, recommendation: AIRecommendation, decision: str, *, result: str | None = None, context_summary: str | None = None) -> SalesAIResult:
        self._require(self.DECIDE)
        self._tenant(recommendation.tenant_id)
        if decision.upper() == "CONFIRM" and recommendation.authority is AIAuthority.RESTRICTED:
            raise PermissionError("restricted AI action cannot be confirmed")
        record = AIDecisionRecord(recommendation.tenant_id, self.context.user.user_id, recommendation.capability, recommendation.id, decision, result, context_summary)
        self._decisions.append(record)
        return SalesAIResult(recommendation, record)

    def execute_confirmed(self, recommendation: AIRecommendation) -> AIDecisionRecord:
        self._require(self.EXECUTE)
        self._tenant(recommendation.tenant_id)
        if recommendation.authority is not AIAuthority.EXECUTE_WITH_CONFIRMATION or not recommendation.requires_confirmation:
            raise PermissionError("AI action requires explicit execute-with-confirmation authority")
        return self.decide(recommendation, "CONFIRM").decision

    def decisions(self, recommendation_id: UUID | None = None) -> list[AIDecisionRecord]:
        self._require(self.READ)
        items = list(self._decisions)
        if recommendation_id is not None:
            items = [item for item in items if item.recommendation_id == recommendation_id]
        return items

    def _tenant(self, tenant_id: str) -> None:
        if tenant_id != self.context.tenant.tenant_id:
            raise PermissionError("cross-tenant AI access denied")

    def _require(self, permission: str) -> None:
        if not self.context.has_permission(permission):
            raise PermissionError(f"missing permission: {permission}")
