"""Controlled lifecycle rules for Phoenix Sales Solutions."""

from phoenix_sales.domain.solution import SolutionStatus


ALLOWED_TRANSITIONS: dict[SolutionStatus, frozenset[SolutionStatus]] = {
    SolutionStatus.DRAFT: frozenset({SolutionStatus.IN_REVIEW, SolutionStatus.CANCELLED}),
    SolutionStatus.IN_REVIEW: frozenset({SolutionStatus.APPROVED, SolutionStatus.CANCELLED}),
    SolutionStatus.APPROVED: frozenset({SolutionStatus.SUPERSEDED}),
    SolutionStatus.SUPERSEDED: frozenset(),
    SolutionStatus.CANCELLED: frozenset(),
}


def can_transition(current: SolutionStatus, target: SolutionStatus) -> bool:
    """Return whether a Solution status transition is allowed."""
    return target in ALLOWED_TRANSITIONS[current]


def validate_transition(current: SolutionStatus, target: SolutionStatus) -> None:
    """Raise when a Solution status transition is not permitted."""
    if not can_transition(current, target):
        raise ValueError(f"invalid solution transition: {current.value} -> {target.value}")
