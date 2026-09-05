from uuid import uuid4

import pytest

from phoenix_sales.api.contracts import PermissionContext, RequestContext, TenantContext, UserContext
from phoenix_sales.api.copilot import AskSalesCopilotCommand, SalesCopilotApplication
from phoenix_sales.domain.copilot import (
    CopilotAuthority,
    CopilotIntent,
    CopilotRecommendation,
    CopilotRequest,
    CopilotResponse,
    SalesCopilotContext,
)
from phoenix_sales.services.copilot import SalesCopilotService


class FakeAI:
    def respond(self, request):
        return CopilotResponse(
            request_id=request.id,
            answer="Opportunity is healthy.",
            recommendations=(CopilotRecommendation("Follow up", "Quote is approaching expiry.", 92.0),),
        )


def ctx(tenant="t1", user="u1", permissions=frozenset({"sales.copilot.use"})):
    return RequestContext(
        tenant=TenantContext(tenant),
        user=UserContext(user),
        permissions=PermissionContext(permissions),
    )


def request(tenant="t1", user="u1"):
    return CopilotRequest(
        context=SalesCopilotContext(tenant, user, opportunity_id=uuid4(), facts=("quote expires soon",)),
        prompt="Summarise this opportunity",
        intent=CopilotIntent.SUMMARIZE,
    )


def test_copilot_responds_through_core_ai_port():
    application = SalesCopilotApplication(SalesCopilotService(ctx(), FakeAI()))
    response = application.respond(AskSalesCopilotCommand(request()))
    assert response.answer == "Opportunity is healthy."
    assert response.recommendations[0].confidence == 92.0


def test_copilot_requires_permission():
    service = SalesCopilotService(ctx(permissions=frozenset()), FakeAI())
    with pytest.raises(PermissionError, match="sales.copilot.use"):
        service.respond(request())


def test_copilot_rejects_cross_tenant_request():
    service = SalesCopilotService(ctx(), FakeAI())
    with pytest.raises(PermissionError, match="cross-tenant"):
        service.respond(request(tenant="t2"))


def test_copilot_rejects_wrong_user():
    service = SalesCopilotService(ctx(), FakeAI())
    with pytest.raises(PermissionError, match="authenticated user"):
        service.respond(request(user="u2"))


def test_recommendation_requires_action_for_confirmation():
    with pytest.raises(ValueError, match="action"):
        CopilotRecommendation("Do it", "Reason", 80, CopilotAuthority.EXECUTE_WITH_CONFIRMATION)


def test_confirmation_requires_executable_recommendation():
    with pytest.raises(ValueError, match="confirmation"):
        CopilotResponse(uuid4(), "Answer", requires_confirmation=True)


def test_restricted_recommendation_cannot_execute():
    with pytest.raises(ValueError, match="executable action"):
        CopilotRecommendation("Restricted", "Reason", 80, CopilotAuthority.RESTRICTED, action="execute")
