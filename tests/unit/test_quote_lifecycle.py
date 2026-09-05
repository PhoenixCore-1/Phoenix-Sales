import pytest

from phoenix_sales.domain.quote import QuoteStatus
from phoenix_sales.domain.quote_lifecycle import can_transition, validate_transition


def test_draft_can_enter_review_or_cancel():
    assert can_transition(QuoteStatus.DRAFT, QuoteStatus.INTERNAL_REVIEW)
    assert can_transition(QuoteStatus.DRAFT, QuoteStatus.CANCELLED)


def test_internal_review_can_approve_or_require_approval():
    assert can_transition(QuoteStatus.INTERNAL_REVIEW, QuoteStatus.APPROVED)
    assert can_transition(QuoteStatus.INTERNAL_REVIEW, QuoteStatus.APPROVAL_REQUIRED)


def test_approval_required_must_be_approved_or_cancelled():
    assert can_transition(QuoteStatus.APPROVAL_REQUIRED, QuoteStatus.APPROVED)
    assert can_transition(QuoteStatus.APPROVAL_REQUIRED, QuoteStatus.CANCELLED)
    assert not can_transition(QuoteStatus.APPROVAL_REQUIRED, QuoteStatus.SENT)


def test_approved_can_be_sent_or_cancelled():
    assert can_transition(QuoteStatus.APPROVED, QuoteStatus.SENT)
    assert can_transition(QuoteStatus.APPROVED, QuoteStatus.CANCELLED)


def test_sent_supports_customer_response_outcomes():
    for target in (
        QuoteStatus.ACCEPTED,
        QuoteStatus.REJECTED,
        QuoteStatus.NEGOTIATING,
        QuoteStatus.EXPIRED,
        QuoteStatus.CANCELLED,
    ):
        assert can_transition(QuoteStatus.SENT, target)


def test_negotiating_can_return_to_sent_or_reach_outcome():
    assert can_transition(QuoteStatus.NEGOTIATING, QuoteStatus.SENT)
    assert can_transition(QuoteStatus.NEGOTIATING, QuoteStatus.ACCEPTED)
    assert can_transition(QuoteStatus.NEGOTIATING, QuoteStatus.REJECTED)


def test_terminal_statuses_have_no_outgoing_transitions():
    for status in (QuoteStatus.ACCEPTED, QuoteStatus.REJECTED, QuoteStatus.EXPIRED, QuoteStatus.CANCELLED):
        assert not can_transition(status, QuoteStatus.DRAFT)
        assert not can_transition(status, QuoteStatus.SENT)


def test_invalid_transition_raises():
    with pytest.raises(ValueError, match="Invalid quote transition"):
        validate_transition(QuoteStatus.DRAFT, QuoteStatus.SENT)


def test_valid_transition_does_not_raise():
    validate_transition(QuoteStatus.APPROVED, QuoteStatus.SENT)
