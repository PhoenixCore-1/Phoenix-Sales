from datetime import date
from decimal import Decimal

import pytest

from phoenix_sales.domain.opportunity import Opportunity, OpportunityStage


def make_opportunity() -> Opportunity:
    return Opportunity(
        tenant_id="tenant-001",
        name="Anchor solution for project",
        customer_id="customer-001",
        owner_user_id="user-001",
        requirement="High-load fastening solution",
        application="Structural connection",
        estimated_value=Decimal("100000"),
        estimated_margin=Decimal("25000"),
        close_date=date(2026, 10, 31),
        probability=Decimal("25"),
        source="CRM",
    )


def test_opportunity_defaults_to_new():
    opportunity = make_opportunity()

    assert opportunity.stage is OpportunityStage.NEW
    assert not opportunity.is_terminal
    assert opportunity.probability == Decimal("25")


def test_stage_and_probability_are_independent():
    opportunity = make_opportunity()

    opportunity.transition_to(OpportunityStage.QUALIFIED)
    opportunity.set_probability(Decimal("60"))

    assert opportunity.stage is OpportunityStage.QUALIFIED
    assert opportunity.probability == Decimal("60")


def test_terminal_stage_cannot_be_transitioned():
    opportunity = make_opportunity()
    opportunity.transition_to(OpportunityStage.WON)

    assert opportunity.is_terminal

    with pytest.raises(ValueError, match="terminal opportunity"):
        opportunity.transition_to(OpportunityStage.NEGOTIATION)


def test_probability_must_be_between_zero_and_hundred():
    with pytest.raises(ValueError, match="probability"):
        make_opportunity_with_probability(Decimal("101"))


def make_opportunity_with_probability(probability: Decimal) -> Opportunity:
    return Opportunity(
        tenant_id="tenant-001",
        name="Test opportunity",
        customer_id="customer-001",
        owner_user_id="user-001",
        probability=probability,
    )


def test_required_identity_fields_cannot_be_blank():
    with pytest.raises(ValueError, match="customer_id"):
        Opportunity(
            tenant_id="tenant-001",
            name="Test",
            customer_id=" ",
            owner_user_id="user-001",
        )
