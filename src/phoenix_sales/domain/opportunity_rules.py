"""Business validation rules for Phoenix Sales opportunities."""

from datetime import date

from phoenix_sales.domain.opportunity import Opportunity, OpportunityStage


QUALIFIED_STAGES = frozenset(
    {
        OpportunityStage.QUALIFIED,
        OpportunityStage.DISCOVERY,
        OpportunityStage.SOLUTION_DEVELOPMENT,
        OpportunityStage.QUOTE,
        OpportunityStage.NEGOTIATION,
    }
)


def validate_stage_requirements(opportunity: Opportunity, target: OpportunityStage) -> None:
    """Validate information required when entering a target lifecycle stage."""
    if target in QUALIFIED_STAGES:
        if not opportunity.requirement or not opportunity.requirement.strip():
            raise ValueError("requirement is required from QUALIFIED onward")

    if target in {
        OpportunityStage.DISCOVERY,
        OpportunityStage.SOLUTION_DEVELOPMENT,
        OpportunityStage.QUOTE,
        OpportunityStage.NEGOTIATION,
    }:
        if not opportunity.application or not opportunity.application.strip():
            raise ValueError("application is required from DISCOVERY onward")

    if target in {OpportunityStage.QUOTE, OpportunityStage.NEGOTIATION}:
        if opportunity.estimated_value is None:
            raise ValueError("estimated_value is required from QUOTE onward")
        if opportunity.close_date is None:
            raise ValueError("close_date is required from QUOTE onward")

    if target in {
        OpportunityStage.WON,
        OpportunityStage.LOST,
        OpportunityStage.NO_DECISION,
        OpportunityStage.CANCELLED,
        OpportunityStage.DEFERRED,
        OpportunityStage.NURTURE,
    }:
        if opportunity.close_date is None:
            # Terminal outcomes still need a forecast/history date. The service
            # layer will normally populate today's date when recording outcome.
            raise ValueError("close_date is required for an opportunity outcome")


def validate_outcome_fields(opportunity: Opportunity, target: OpportunityStage) -> None:
    """Validate reason/detail fields required for terminal outcomes."""
    if target == OpportunityStage.LOST and not opportunity.lost_reason:
        raise ValueError("lost_reason is required when opportunity is LOST")
    if target == OpportunityStage.NO_DECISION and not opportunity.outcome_reason:
        raise ValueError("outcome_reason is required when opportunity is NO_DECISION")
    if target == OpportunityStage.CANCELLED and not opportunity.outcome_reason:
        raise ValueError("outcome_reason is required when opportunity is CANCELLED")
    if target == OpportunityStage.DEFERRED:
        if not opportunity.outcome_reason:
            raise ValueError("outcome_reason is required when opportunity is DEFERRED")
        if opportunity.deferred_until is None:
            raise ValueError("deferred_until is required when opportunity is DEFERRED")
        if opportunity.deferred_until < date.today():
            raise ValueError("deferred_until cannot be in the past")
    if target == OpportunityStage.NURTURE and not opportunity.outcome_reason:
        raise ValueError("outcome_reason is required when opportunity is NURTURE")
