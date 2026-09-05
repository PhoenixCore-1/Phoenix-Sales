from decimal import Decimal

import pytest

from phoenix_sales.domain.discount import (
    ApprovalStatus,
    DiscountApproval,
    DiscountAuthority,
    DiscountStatus,
)


def test_discount_within_authority():
    authority = DiscountAuthority(Decimal("10"))
    assert authority.evaluate(Decimal("10")) is DiscountStatus.WITHIN_AUTHORITY


def test_discount_over_authority_requires_approval():
    authority = DiscountAuthority(Decimal("10"))
    assert authority.evaluate(Decimal("10.01")) is DiscountStatus.APPROVAL_REQUIRED


def test_discount_authority_rejects_invalid_limits():
    with pytest.raises(ValueError):
        DiscountAuthority(Decimal("-1"))
    with pytest.raises(ValueError):
        DiscountAuthority(Decimal("101"))


def test_discount_evaluation_rejects_invalid_discount():
    authority = DiscountAuthority(Decimal("10"))
    with pytest.raises(ValueError):
        authority.evaluate(Decimal("-1"))
    with pytest.raises(ValueError):
        authority.evaluate(Decimal("101"))


def test_pending_approval_requires_reason():
    with pytest.raises(ValueError):
        DiscountApproval(Decimal("5"), Decimal("12"), "")


def test_final_approval_requires_approver():
    with pytest.raises(ValueError):
        DiscountApproval(
            Decimal("5"), Decimal("12"), "Customer negotiation", ApprovalStatus.APPROVED
        )


def test_approval_records_original_and_requested_discount():
    approval = DiscountApproval(
        Decimal("5"), Decimal("12"), "Competitive pricing", ApprovalStatus.PENDING
    )
    assert approval.original_discount_percent == Decimal("5")
    assert approval.requested_discount_percent == Decimal("12")
    assert approval.status is ApprovalStatus.PENDING


def test_rejected_approval_keeps_approver_identity():
    approval = DiscountApproval(
        Decimal("5"), Decimal("12"), "Below margin", ApprovalStatus.REJECTED, "manager-1"
    )
    assert approval.approver_user_id == "manager-1"
