import pytest

from phoenix_sales.domain.solution import SolutionStatus
from phoenix_sales.domain.solution_lifecycle import can_transition, validate_transition


def test_draft_can_enter_review_or_cancel():
    assert can_transition(SolutionStatus.DRAFT, SolutionStatus.IN_REVIEW)
    assert can_transition(SolutionStatus.DRAFT, SolutionStatus.CANCELLED)


def test_review_can_be_approved_or_cancelled():
    assert can_transition(SolutionStatus.IN_REVIEW, SolutionStatus.APPROVED)
    assert can_transition(SolutionStatus.IN_REVIEW, SolutionStatus.CANCELLED)


def test_approved_can_only_be_superseded():
    assert can_transition(SolutionStatus.APPROVED, SolutionStatus.SUPERSEDED)
    assert not can_transition(SolutionStatus.APPROVED, SolutionStatus.CANCELLED)
    assert not can_transition(SolutionStatus.APPROVED, SolutionStatus.IN_REVIEW)


@pytest.mark.parametrize("status", [SolutionStatus.SUPERSEDED, SolutionStatus.CANCELLED])
def test_closed_statuses_have_no_outgoing_transitions(status):
    for target in SolutionStatus:
        assert not can_transition(status, target)


def test_invalid_transition_raises():
    with pytest.raises(ValueError, match="invalid solution transition"):
        validate_transition(SolutionStatus.DRAFT, SolutionStatus.APPROVED)


def test_valid_transition_does_not_raise():
    validate_transition(SolutionStatus.DRAFT, SolutionStatus.IN_REVIEW)
