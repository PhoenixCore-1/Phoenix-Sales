"""Opportunity lifecycle rules for Phoenix Sales V1.0."""

from phoenix_sales.domain.opportunity import OpportunityStage


ACTIVE_STAGES = frozenset(
    {
        OpportunityStage.NEW,
        OpportunityStage.QUALIFIED,
        OpportunityStage.DISCOVERY,
        OpportunityStage.SOLUTION_DEVELOPMENT,
        OpportunityStage.QUOTE,
        OpportunityStage.NEGOTIATION,
    }
)

# Normal forward commercial progression. Terminal outcomes are reachable from
# active stages but are deliberately not allowed to reopen implicitly.
ALLOWED_TRANSITIONS: dict[OpportunityStage, frozenset[OpportunityStage]] = {
    OpportunityStage.NEW: frozenset(
        {
            OpportunityStage.QUALIFIED,
            OpportunityStage.LOST,
            OpportunityStage.NURTURE,
            OpportunityStage.DEFERRED,
        }
    ),
    OpportunityStage.QUALIFIED: frozenset(
        {
            OpportunityStage.DISCOVERY,
            OpportunityStage.LOST,
            OpportunityStage.NURTURE,
            OpportunityStage.DEFERRED,
        }
    ),
    OpportunityStage.DISCOVERY: frozenset(
        {
            OpportunityStage.SOLUTION_DEVELOPMENT,
            OpportunityStage.LOST,
            OpportunityStage.NURTURE,
            OpportunityStage.DEFERRED,
        }
    ),
    OpportunityStage.SOLUTION_DEVELOPMENT: frozenset(
        {
            OpportunityStage.QUOTE,
            OpportunityStage.LOST,
            OpportunityStage.NURTURE,
            OpportunityStage.DEFERRED,
        }
    ),
    OpportunityStage.QUOTE: frozenset(
        {
            OpportunityStage.NEGOTIATION,
            OpportunityStage.WON,
            OpportunityStage.LOST,
            OpportunityStage.NURTURE,
            OpportunityStage.DEFERRED,
        }
    ),
    OpportunityStage.NEGOTIATION: frozenset(
        {
            OpportunityStage.WON,
            OpportunityStage.LOST,
            OpportunityStage.NURTURE,
            OpportunityStage.DEFERRED,
        }
    ),
    OpportunityStage.WON: frozenset(),
    OpportunityStage.LOST: frozenset(),
    OpportunityStage.NO_DECISION: frozenset(),
    OpportunityStage.DEFERRED: frozenset(),
    OpportunityStage.CANCELLED: frozenset(),
    OpportunityStage.NURTURE: frozenset(),
}


TERMINAL_OUTCOMES = frozenset(
    {
        OpportunityStage.WON,
        OpportunityStage.LOST,
        OpportunityStage.NO_DECISION,
        OpportunityStage.DEFERRED,
        OpportunityStage.CANCELLED,
        OpportunityStage.NURTURE,
    }
)


def can_transition(current: OpportunityStage, target: OpportunityStage) -> bool:
    """Return whether the lifecycle permits the requested transition."""
    if current == target:
        return False
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


def validate_transition(current: OpportunityStage, target: OpportunityStage) -> None:
    """Raise ValueError when an opportunity transition is not permitted."""
    if not can_transition(current, target):
        raise ValueError(f"invalid opportunity transition: {current.value} -> {target.value}")
