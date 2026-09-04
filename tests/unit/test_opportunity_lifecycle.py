import pytest

from phoenix_sales.domain.opportunity import OpportunityStage
from phoenix_sales.domain.opportunity_lifecycle import can_transition, validate_transition


def test_normal_forward_progression_is_allowed():
    assert can_transition(OpportunityStage.NEW, OpportunityStage.QUALIFIED)
    assert can_transition(OpportunityStage.QUALIFIED, OpportunityStage.DISCOVERY)
    assert can_transition(OpportunityStage.DISCOVERY, OpportunityStage.SOLUTION_DEVELOPMENT)
    assert can_transition(OpportunityStage.SOLUTION_DEVELOPMENT, OpportunityStage.QUOTE)
    assert can_transition(OpportunityStage.QUOTE, OpportunityStage.NEGOTIATION)
    assert can_transition(OpportunityStage.NEGOTIATION, OpportunityStage.WON)


def test_terminal_outcomes_are_available_from_active_stages():
    for stage in (
        OpportunityStage.NEW,
        OpportunityStage.QUALIFIED,
        OpportunityStage.DISCOVERY,
        OpportunityStage.SOLUTION_DEVELOPMENT,
        OpportunityStage.QUOTE,
        OpportunityStage.NEGOTIATION,
    ):
        assert can_transition(stage, OpportunityStage.LOST)
        assert can_transition(stage, OpportunityStage.NURTURE)
        assert can_transition(stage, OpportunityStage.DEFERRED)


def test_invalid_stage_skips_are_rejected():
    assert not can_transition(OpportunityStage.NEW, OpportunityStage.QUOTE)
    assert not can_transition(OpportunityStage.QUALIFIED, OpportunityStage.NEGOTIATION)
    assert not can_transition(OpportunityStage.DISCOVERY, OpportunityStage.WON)


def test_terminal_opportunities_cannot_reopen():
    for stage in (
        OpportunityStage.WON,
        OpportunityStage.LOST,
        OpportunityStage.NO_DECISION,
        OpportunityStage.DEFERRED,
        OpportunityStage.CANCELLED,
        OpportunityStage.NURTURE,
    ):
        assert not can_transition(stage, OpportunityStage.DISCOVERY)


def test_same_stage_transition_is_rejected():
    assert not can_transition(OpportunityStage.DISCOVERY, OpportunityStage.DISCOVERY)


def test_validate_transition_raises_for_invalid_transition():
    with pytest.raises(ValueError, match="invalid opportunity transition"):
        validate_transition(OpportunityStage.NEW, OpportunityStage.NEGOTIATION)
