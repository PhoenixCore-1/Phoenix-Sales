from decimal import Decimal

import pytest

from phoenix_sales.domain.discount import ApprovalStatus, DiscountAuthority, DiscountStatus
from phoenix_sales.domain.margin import MarginRule, MarginStatus
from phoenix_sales.services.discount_approval import DiscountApprovalService


def rules():
    return DiscountAuthority(Decimal("10")), MarginRule(Decimal("20"), Decimal("30"))


def test_within_authority_requires_no_approval():
    authority, margin = rules()
    result = DiscountApprovalService().evaluate_request(
        authority=authority,
        margin_rule=margin,
        original_discount_percent=Decimal("0"),
        requested_discount_percent=Decimal("10"),
        resulting_margin_percent=Decimal("35"),
        reason="Standard customer discount",
    )
    assert result.approval.status is ApprovalStatus.NOT_REQUIRED
    assert result.margin_status is MarginStatus.ACCEPTABLE


def test_over_authority_creates_pending_approval():
    authority, margin = rules()
    result = DiscountApprovalService().evaluate_request(
        authority=authority,
        margin_rule=margin,
        original_discount_percent=Decimal("5"),
        requested_discount_percent=Decimal("12"),
        resulting_margin_percent=Decimal("32"),
        reason="Competitive quote",
    )
    assert result.approval.status is ApprovalStatus.PENDING
    assert result.approval.requested_discount_percent == Decimal("12")


def test_blocked_margin_prevents_approval_request():
    authority, margin = rules()
    with pytest.raises(ValueError, match="blocked by the margin"):
        DiscountApprovalService().evaluate_request(
            authority=authority,
            margin_rule=margin,
            original_discount_percent=Decimal("5"),
            requested_discount_percent=Decimal("12"),
            resulting_margin_percent=Decimal("19"),
            reason="Competitive quote",
        )


def test_warning_margin_does_not_block_approval_request():
    authority, margin = rules()
    result = DiscountApprovalService().evaluate_request(
        authority=authority,
        margin_rule=margin,
        original_discount_percent=Decimal("5"),
        requested_discount_percent=Decimal("12"),
        resulting_margin_percent=Decimal("25"),
        reason="Competitive quote",
    )
    assert result.approval.status is ApprovalStatus.PENDING
    assert result.margin_status is MarginStatus.WARNING


def test_pending_request_can_be_approved():
    authority, margin = rules()
    result = DiscountApprovalService().evaluate_request(
        authority=authority,
        margin_rule=margin,
        original_discount_percent=Decimal("5"),
        requested_discount_percent=Decimal("12"),
        resulting_margin_percent=Decimal("32"),
        reason="Competitive quote",
    )
    approved = DiscountApprovalService.approve(result.approval, "manager-1")
    assert approved.status is ApprovalStatus.APPROVED
    assert approved.approver_user_id == "manager-1"


def test_pending_request_can_be_rejected():
    authority, margin = rules()
    result = DiscountApprovalService().evaluate_request(
        authority=authority,
        margin_rule=margin,
        original_discount_percent=Decimal("5"),
        requested_discount_percent=Decimal("12"),
        resulting_margin_percent=Decimal("32"),
        reason="Competitive quote",
    )
    rejected = DiscountApprovalService.reject(result.approval, "manager-1")
    assert rejected.status is ApprovalStatus.REJECTED
    assert rejected.approver_user_id == "manager-1"


def test_non_pending_request_cannot_be_approved_or_rejected():
    authority, margin = rules()
    result = DiscountApprovalService().evaluate_request(
        authority=authority,
        margin_rule=margin,
        original_discount_percent=Decimal("0"),
        requested_discount_percent=Decimal("5"),
        resulting_margin_percent=Decimal("35"),
        reason="Standard",
    )
    with pytest.raises(ValueError):
        DiscountApprovalService.approve(result.approval, "manager-1")
    with pytest.raises(ValueError):
        DiscountApprovalService.reject(result.approval, "manager-1")


def test_approval_requires_approver_identity():
    authority, margin = rules()
    result = DiscountApprovalService().evaluate_request(
        authority=authority,
        margin_rule=margin,
        original_discount_percent=Decimal("5"),
        requested_discount_percent=Decimal("12"),
        resulting_margin_percent=Decimal("32"),
        reason="Competitive quote",
    )
    with pytest.raises(ValueError):
        DiscountApprovalService.approve(result.approval, "")
