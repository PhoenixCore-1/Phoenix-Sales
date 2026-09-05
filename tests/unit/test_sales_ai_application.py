from decimal import Decimal
from uuid import uuid4

import pytest

from phoenix_sales.api.contracts import PermissionContext, RequestContext, TenantContext, UserContext
from phoenix_sales.api.sales_ai import CreateAIRecommendationCommand, DecideAIRecommendationCommand, ListAIDecisionsQuery, SalesAIApplication
from phoenix_sales.domain.sales_ai import AIAuthority, SalesAIContext, SalesAICapability
from phoenix_sales.services.sales_ai import SalesAIService


def app(*permissions):
    ctx = RequestContext(TenantContext("t1"), UserContext("u1"), PermissionContext(frozenset(permissions)))
    return SalesAIApplication(SalesAIService(ctx))


def context():
    return SalesAIContext("t1", "u1", SalesAICapability.OPPORTUNITY_INTELLIGENCE, "opportunity", str(uuid4()))


def test_create_recommendation():
    application = app("sales.ai.create")
    result = application.create_recommendation(CreateAIRecommendationCommand(context(), "Opportunity health", "Follow up with the decision maker", Decimal("88"), ("No activity for 14 days",)))
    assert result.confidence == Decimal("88")
    assert result.authority is AIAuthority.RECOMMEND


def test_execute_requires_confirmation_authority():
    application = app("sales.ai.create", "sales.ai.execute", "sales.ai.decide")
    recommendation = application.create_recommendation(CreateAIRecommendationCommand(context(), "Action", "Send draft", Decimal("90"), authority=AIAuthority.RECOMMEND))
    with pytest.raises(PermissionError):
        application.execute_confirmed(recommendation)


def test_confirmed_execution_creates_decision_record():
    application = app("sales.ai.create", "sales.ai.execute", "sales.ai.decide", "sales.ai.read")
    recommendation = application.create_recommendation(CreateAIRecommendationCommand(context(), "Action", "Create follow-up task", Decimal("90"), authority=AIAuthority.EXECUTE_WITH_CONFIRMATION))
    decision = application.execute_confirmed(recommendation)
    assert decision.decision == "CONFIRM"
    assert application.list_decisions(ListAIDecisionsQuery(recommendation.id))[0].recommendation_id == recommendation.id


def test_restricted_cannot_be_confirmed():
    application = app("sales.ai.create", "sales.ai.execute", "sales.ai.decide")
    # Restricted recommendations are rejected at the domain boundary.
    with pytest.raises(ValueError):
        application.create_recommendation(CreateAIRecommendationCommand(context(), "Restricted", "Change price", Decimal("99"), authority=AIAuthority.RESTRICTED))


def test_cross_tenant_request_rejected():
    application = app("sales.ai.create")
    foreign = SalesAIContext("t2", "u1", SalesAICapability.SALES_COPILOT)
    with pytest.raises(PermissionError):
        application.create_recommendation(CreateAIRecommendationCommand(foreign, "x", "y", Decimal("50")))


def test_user_mismatch_rejected():
    application = app("sales.ai.create")
    foreign_user = SalesAIContext("t1", "u2", SalesAICapability.SALES_COPILOT)
    with pytest.raises(PermissionError):
        application.create_recommendation(CreateAIRecommendationCommand(foreign_user, "x", "y", Decimal("50")))
