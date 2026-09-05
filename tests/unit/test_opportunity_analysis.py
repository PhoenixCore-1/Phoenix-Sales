from phoenix_sales.api.opportunity_analysis import AnalyseOpportunityCommand, OpportunityAnalysisApplication
from phoenix_sales.domain.copilot_context import ContextSource, CopilotFact, FactType, SalesCopilotContextPackage
from phoenix_sales.domain.opportunity_analysis import OpportunityHealth, OpportunityRiskType
from phoenix_sales.services.opportunity_analysis import OpportunityAnalysisService


class Tenant:
    tenant_id = "t1"


class User:
    user_id = "u1"


class Context:
    tenant = Tenant()
    user = User()

    def __init__(self, permissions):
        self.permissions = permissions

    def has_permission(self, permission):
        return permission in self.permissions


def package(*facts):
    return SalesCopilotContextPackage(
        tenant_id="t1",
        user_id="u1",
        facts=facts,
        source_ids={ContextSource.OPPORTUNITY: ("opp-1",)},
    )


def fact(name, value, source=ContextSource.OPPORTUNITY, fact_type=FactType.KNOWN):
    return CopilotFact(source, name, value, fact_type)


def test_analysis_detects_missing_decision_maker_and_next_action():
    service = OpportunityAnalysisService(Context({"sales.copilot.opportunity_analysis"}))
    result = service.analyse(package(fact("requirement", "Anchor solution")))
    assert result.health is OpportunityHealth.AT_RISK
    assert "Decision maker" in result.missing_information
    assert any(r.risk_type is OpportunityRiskType.MISSING_DECISION_MAKER for r in result.risks)
    assert any(r.risk_type is OpportunityRiskType.NO_NEXT_ACTION for r in result.risks)


def test_analysis_detects_expired_quote_and_competitor():
    service = OpportunityAnalysisService(Context({"sales.copilot.opportunity_analysis"}))
    result = service.analyse(package(
        fact("requirement", "Anchor solution"),
        fact("decision_maker", "Buyer"),
        fact("next_action", "Call Friday"),
        fact("last_activity", "Yesterday"),
        fact("quote_status", "EXPIRED", ContextSource.QUOTE),
        fact("competitor", "Competitor A", ContextSource.COMPETITOR_PRICING),
    ))
    assert result.health is OpportunityHealth.CRITICAL
    assert any(r.risk_type is OpportunityRiskType.EXPIRED_QUOTE for r in result.risks)
    assert any(r.risk_type is OpportunityRiskType.COMPETITOR_PRESSURE for r in result.risks)


def test_analysis_detects_low_margin_and_value_leakage():
    service = OpportunityAnalysisService(Context({"sales.copilot.opportunity_analysis"}))
    result = service.analyse(package(
        fact("requirement", "Requirement"), fact("decision_maker", "Buyer"),
        fact("next_action", "Follow up"), fact("last_activity", "Today"),
        fact("margin", "10"), fact("estimated_value", "100000"), fact("order_value", "40000"),
    ))
    assert result.health is OpportunityHealth.AT_RISK
    assert any(r.risk_type is OpportunityRiskType.LOW_MARGIN for r in result.risks)
    assert any(r.risk_type is OpportunityRiskType.VALUE_LEAKAGE for r in result.risks)


def test_analysis_requires_permission_and_preserves_tenant_boundary():
    package_value = package(fact("requirement", "Requirement"))
    service = OpportunityAnalysisService(Context(set()))
    try:
        service.analyse(package_value)
        assert False, "permission should be required"
    except PermissionError:
        pass

    service = OpportunityAnalysisService(Context({"sales.copilot.opportunity_analysis"}))
    foreign = SalesCopilotContextPackage("t2", "u1", package_value.facts, package_value.source_ids)
    try:
        service.analyse(foreign)
        assert False, "cross-tenant access should be denied"
    except PermissionError:
        pass


def test_application_boundary_delegates():
    service = OpportunityAnalysisService(Context({"sales.copilot.opportunity_analysis"}))
    app = OpportunityAnalysisApplication(service)
    result = app.analyse(AnalyseOpportunityCommand(package(fact("requirement", "Requirement"))))
    assert result.opportunity_id == "opp-1"
