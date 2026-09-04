from datetime import date
from decimal import Decimal

import pytest

from phoenix_sales.api.contracts import PermissionContext, RequestContext, TenantContext, UserContext
from phoenix_sales.domain.opportunity import OpportunityStage
from phoenix_sales.services.opportunity_service import OpportunityOutcome, OpportunityService


TENANT = "tenant-1"


def context(*permissions: str) -> RequestContext:
    return RequestContext(
        tenant=TenantContext(TENANT),
        user=UserContext("user-1"),
        permissions=PermissionContext(frozenset(permissions)),
    )


def service(*permissions: str) -> OpportunityService:
    return OpportunityService(context(*permissions))


def test_create_uses_request_tenant_and_requires_permission():
    opportunity = service("sales.opportunity.create").create_opportunity(
        name="Anchor project",
        customer_id="customer-1",
        owner_user_id="user-2",
    )
    assert opportunity.tenant_id == TENANT
    assert opportunity.stage is OpportunityStage.NEW


def test_create_denies_without_permission():
    with pytest.raises(PermissionError, match="sales.opportunity.create"):
        service().create_opportunity(name="A", customer_id="C", owner_user_id="U")


def test_transition_requires_permission_and_same_tenant():
    opportunity = service("sales.opportunity.create").create_opportunity(
        name="A", customer_id="C", owner_user_id="U"
    )
    with pytest.raises(PermissionError):
        service().transition_opportunity(opportunity, OpportunityStage.QUALIFIED)


def test_transition_enforces_stage_requirements():
    opportunity = service("sales.opportunity.create").create_opportunity(
        name="A", customer_id="C", owner_user_id="U"
    )
    with pytest.raises(ValueError, match="QUALIFIED requires requirement"):
        service("sales.opportunity.transition").transition_opportunity(
            opportunity, OpportunityStage.QUALIFIED
        )


def test_transition_to_qualified_after_requirement():
    opportunity = service("sales.opportunity.create").create_opportunity(
        name="A", customer_id="C", owner_user_id="U", requirement="Fixing requirement"
    )
    service("sales.opportunity.transition").transition_opportunity(
        opportunity, OpportunityStage.QUALIFIED
    )
    assert opportunity.stage is OpportunityStage.QUALIFIED


def test_deferred_requires_reason_and_future_date():
    opportunity = service("sales.opportunity.create").create_opportunity(
        name="A", customer_id="C", owner_user_id="U"
    )
    with pytest.raises(ValueError, match="outcome reason"):
        service("sales.opportunity.transition").transition_opportunity(
            opportunity, OpportunityStage.DEFERRED
        )
    with pytest.raises(ValueError, match="deferred_until"):
        service("sales.opportunity.transition").transition_opportunity(
            opportunity, OpportunityStage.DEFERRED,
            outcome=OpportunityOutcome("Project postponed"),
        )


def test_quote_requires_requirement_application_value_and_close_date():
    opportunity = service("sales.opportunity.create").create_opportunity(
        name="A", customer_id="C", owner_user_id="U",
        requirement="Requirement", application="Application",
    )
    with pytest.raises(ValueError, match="estimated_value"):
        service("sales.opportunity.transition").transition_opportunity(
            opportunity, OpportunityStage.QUOTE
        )
    opportunity.estimated_value = Decimal("1000")
    with pytest.raises(ValueError, match="close_date"):
        service("sales.opportunity.transition").transition_opportunity(
            opportunity, OpportunityStage.QUOTE
        )
    opportunity.close_date = date(2026, 10, 1)
    service("sales.opportunity.transition").transition_opportunity(
        opportunity, OpportunityStage.QUOTE
    )
    assert opportunity.stage is OpportunityStage.QUOTE


def test_terminal_opportunity_cannot_be_updated():
    opportunity = service("sales.opportunity.create").create_opportunity(
        name="A", customer_id="C", owner_user_id="U"
    )
    service("sales.opportunity.transition").transition_opportunity(
        opportunity,
        OpportunityStage.LOST,
        outcome=OpportunityOutcome("Competitor won"),
    )
    with pytest.raises(ValueError, match="terminal opportunity"):
        service("sales.opportunity.update").update_opportunity(opportunity, name="Changed")


def test_update_rejects_protected_fields():
    opportunity = service("sales.opportunity.create").create_opportunity(
        name="A", customer_id="C", owner_user_id="U"
    )
    with pytest.raises(ValueError, match="protected opportunity fields"):
        service("sales.opportunity.update").update_opportunity(
            opportunity, tenant_id="other"
        )


def test_cross_tenant_opportunity_is_denied():
    opportunity = service("sales.opportunity.create").create_opportunity(
        name="A", customer_id="C", owner_user_id="U"
    )
    other = OpportunityService(
        RequestContext(
            tenant=TenantContext("tenant-2"),
            user=UserContext("user-1"),
            permissions=PermissionContext(frozenset({"sales.opportunity.update"})),
        )
    )
    with pytest.raises(PermissionError, match="another tenant"):
        other.update_opportunity(opportunity, name="No")
