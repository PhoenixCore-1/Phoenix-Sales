from decimal import Decimal

import pytest

from phoenix_sales.api.contracts import PermissionContext, RequestContext, TenantContext, UserContext
from phoenix_sales.api.opportunities import (
    CreateOpportunityCommand,
    GetOpportunityQuery,
    ListCustomerOpportunitiesQuery,
    ListOwnerOpportunitiesQuery,
    OpportunityApplication,
    SetOpportunityProbabilityCommand,
    TransitionOpportunityCommand,
    UpdateOpportunityCommand,
)
from phoenix_sales.domain.opportunity import OpportunityStage
from phoenix_sales.services.opportunity import OpportunityOutcome, OpportunityService


TENANT = "tenant-1"


def context(*permissions: str) -> RequestContext:
    return RequestContext(
        tenant=TenantContext(TENANT),
        user=UserContext("user-1"),
        permissions=PermissionContext(frozenset(permissions)),
    )


def app(*permissions: str) -> OpportunityApplication:
    return OpportunityApplication(OpportunityService(context(*permissions)))


def test_create_command_crosses_boundary_and_persists():
    application = app("sales.opportunity.create", "sales.opportunity.read")
    created = application.create(
        CreateOpportunityCommand(
            name="Anchor project",
            customer_id="customer-1",
            owner_user_id="user-1",
        )
    )

    loaded = application.get(GetOpportunityQuery(created.id))
    assert loaded is created
    assert loaded.tenant_id == TENANT
    assert loaded.stage is OpportunityStage.NEW


def test_create_boundary_preserves_permission_enforcement():
    with pytest.raises(PermissionError, match="sales.opportunity.create"):
        app().create(CreateOpportunityCommand("A", "C", "U"))


def test_query_boundary_requires_read_permission():
    application = app("sales.opportunity.create")
    created = application.create(CreateOpportunityCommand("A", "C", "U"))

    with pytest.raises(PermissionError, match="sales.opportunity.read"):
        application.get(GetOpportunityQuery(created.id))


def test_update_command_delegates_to_service():
    application = app("sales.opportunity.create", "sales.opportunity.update")
    created = application.create(CreateOpportunityCommand("A", "C", "U"))

    updated = application.update(UpdateOpportunityCommand(created, {"name": "Updated"}))
    assert updated.name == "Updated"


def test_transition_command_delegates_to_lifecycle_rules():
    application = app("sales.opportunity.create", "sales.opportunity.transition")
    created = application.create(
        CreateOpportunityCommand("A", "C", "U", requirement="Customer requirement")
    )

    updated = application.transition(
        TransitionOpportunityCommand(created, OpportunityStage.QUALIFIED)
    )
    assert updated.stage is OpportunityStage.QUALIFIED


def test_terminal_transition_outcome_crosses_boundary():
    application = app("sales.opportunity.create", "sales.opportunity.transition")
    created = application.create(CreateOpportunityCommand("A", "C", "U"))

    updated = application.transition(
        TransitionOpportunityCommand(
            created,
            OpportunityStage.LOST,
            OpportunityOutcome("Competitor won"),
        )
    )
    assert updated.stage is OpportunityStage.LOST
    assert updated.lost_reason == "Competitor won"


def test_probability_command_delegates_to_service():
    application = app("sales.opportunity.create", "sales.opportunity.update")
    created = application.create(CreateOpportunityCommand("A", "C", "U"))

    updated = application.set_probability(
        SetOpportunityProbabilityCommand(created, Decimal("65"))
    )
    assert updated.probability == Decimal("65")


def test_customer_and_owner_queries_are_exposed_as_queries():
    application = app("sales.opportunity.create", "sales.opportunity.read")
    first = application.create(CreateOpportunityCommand("A", "customer-1", "user-1"))
    second = application.create(CreateOpportunityCommand("B", "customer-2", "user-1"))

    customer_results = application.list_by_customer(ListCustomerOpportunitiesQuery("customer-1"))
    owner_results = application.list_by_owner(ListOwnerOpportunitiesQuery("user-1"))

    assert [item.id for item in customer_results] == [first.id]
    assert {item.id for item in owner_results} == {first.id, second.id}
