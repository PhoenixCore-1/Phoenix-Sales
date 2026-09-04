from datetime import date, timedelta
from decimal import Decimal

import pytest

from phoenix_sales.domain.opportunity import Opportunity, OpportunityStage
from phoenix_sales.domain.opportunity_rules import validate_outcome_fields, validate_stage_requirements


def make_opportunity(**overrides) -> Opportunity:
    values = {
        "tenant_id": "tenant-1",
        "name": "Test opportunity",
        "customer_id": "customer-1",
        "owner_user_id": "user-1",
    }
    values.update(overrides)
    return Opportunity(**values)


def test_qualified_requires_requirement():
    with pytest.raises(ValueError, match="requirement is required"):
        validate_stage_requirements(make_opportunity(), OpportunityStage.QUALIFIED)


def test_discovery_requires_application():
    opportunity = make_opportunity(requirement="Anchor solution")
    with pytest.raises(ValueError, match="application is required"):
        validate_stage_requirements(opportunity, OpportunityStage.DISCOVERY)


def test_quote_requires_value_and_close_date():
    opportunity = make_opportunity(requirement="Anchor solution", application="Concrete fixing")
    with pytest.raises(ValueError, match="estimated_value"):
        validate_stage_requirements(opportunity, OpportunityStage.QUOTE)

    opportunity.estimated_value = Decimal("10000")
    with pytest.raises(ValueError, match="close_date"):
        validate_stage_requirements(opportunity, OpportunityStage.QUOTE)


def test_quote_is_valid_with_required_information():
    opportunity = make_opportunity(
        requirement="Anchor solution",
        application="Concrete fixing",
        estimated_value=Decimal("10000"),
        close_date=date.today(),
    )
    validate_stage_requirements(opportunity, OpportunityStage.QUOTE)


def test_lost_requires_reason():
    opportunity = make_opportunity(close_date=date.today())
    with pytest.raises(ValueError, match="lost_reason"):
        validate_outcome_fields(opportunity, OpportunityStage.LOST)


def test_no_decision_requires_reason():
    opportunity = make_opportunity(close_date=date.today())
    with pytest.raises(ValueError, match="outcome_reason"):
        validate_outcome_fields(opportunity, OpportunityStage.NO_DECISION)


def test_cancelled_requires_reason():
    opportunity = make_opportunity(close_date=date.today())
    with pytest.raises(ValueError, match="outcome_reason"):
        validate_outcome_fields(opportunity, OpportunityStage.CANCELLED)


def test_deferred_requires_future_date_and_reason():
    opportunity = make_opportunity(close_date=date.today(), outcome_reason="Project delayed")
    with pytest.raises(ValueError, match="deferred_until"):
        validate_outcome_fields(opportunity, OpportunityStage.DEFERRED)

    opportunity.deferred_until = date.today() - timedelta(days=1)
    with pytest.raises(ValueError, match="cannot be in the past"):
        validate_outcome_fields(opportunity, OpportunityStage.DEFERRED)


def test_deferred_is_valid_with_reason_and_future_date():
    opportunity = make_opportunity(
        close_date=date.today(),
        outcome_reason="Project starts next quarter",
        deferred_until=date.today() + timedelta(days=30),
    )
    validate_outcome_fields(opportunity, OpportunityStage.DEFERRED)
