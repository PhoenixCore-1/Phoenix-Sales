"""Controlled lifecycle rules for Phoenix Sales Quotes V1.0."""

from phoenix_sales.domain.quote import QuoteStatus

ALLOWED_TRANSITIONS: dict[QuoteStatus, frozenset[QuoteStatus]] = {
    QuoteStatus.DRAFT: frozenset({QuoteStatus.INTERNAL_REVIEW, QuoteStatus.CANCELLED}),
    QuoteStatus.INTERNAL_REVIEW: frozenset({QuoteStatus.APPROVAL_REQUIRED, QuoteStatus.APPROVED, QuoteStatus.CANCELLED}),
    QuoteStatus.APPROVAL_REQUIRED: frozenset({QuoteStatus.APPROVED, QuoteStatus.CANCELLED}),
    QuoteStatus.APPROVED: frozenset({QuoteStatus.SENT, QuoteStatus.CANCELLED}),
    QuoteStatus.SENT: frozenset({QuoteStatus.ACCEPTED, QuoteStatus.REJECTED, QuoteStatus.NEGOTIATING, QuoteStatus.EXPIRED, QuoteStatus.CANCELLED}),
    QuoteStatus.NEGOTIATING: frozenset({QuoteStatus.SENT, QuoteStatus.ACCEPTED, QuoteStatus.REJECTED, QuoteStatus.EXPIRED, QuoteStatus.CANCELLED}),
    QuoteStatus.ACCEPTED: frozenset(),
    QuoteStatus.REJECTED: frozenset(),
    QuoteStatus.EXPIRED: frozenset(),
    QuoteStatus.CANCELLED: frozenset(),
}


def can_transition(current: QuoteStatus, target: QuoteStatus) -> bool:
    """Return whether a quote may move from current to target status."""
    return target in ALLOWED_TRANSITIONS[current]


def validate_transition(current: QuoteStatus, target: QuoteStatus) -> None:
    """Raise ValueError when a quote status transition is not permitted."""
    if not can_transition(current, target):
        raise ValueError(f"Invalid quote transition: {current.value} -> {target.value}")
