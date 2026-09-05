"""Discount approval workflow for Phoenix Sales V1.0."""

from dataclasses import dataclass
from decimal import Decimal

from phoenix_sales.domain.discount import ApprovalStatus, DiscountApproval, DiscountAuthority
from phoenix_sales.domain.margin import MarginRule, MarginStatus


@dataclass(frozen=True)
class DiscountApprovalDecision:
    """Result of evaluating a requested discount."""

    approval: DiscountApproval
    margin_status: MarginStatus


class DiscountApprovalService:
    """Apply discount authority and margin rules without granting approval powers."""

    def evaluate_request(
        self,
        *,
        authority: DiscountAuthority,
        margin_rule: MarginRule,
        original_discount_percent: Decimal,
        requested_discount_percent: Decimal,
        resulting_margin_percent: Decimal,
        reason: str,
    ) -> DiscountApprovalDecision:
        """Create a controlled approval decision for a requested discount."""
        discount_status = authority.evaluate(requested_discount_percent)
        margin_status = margin_rule.evaluate(resulting_margin_percent)

        if margin_status is MarginStatus.BLOCKED:
            raise ValueError("requested discount is blocked by the margin rule")

        approval_status = (
            ApprovalStatus.NOT_REQUIRED
            if discount_status.value == "WITHIN_AUTHORITY"
            else ApprovalStatus.PENDING
        )
        approval = DiscountApproval(
            original_discount_percent=original_discount_percent,
            requested_discount_percent=requested_discount_percent,
            reason=reason,
            status=approval_status,
        )
        return DiscountApprovalDecision(approval=approval, margin_status=margin_status)

    @staticmethod
    def approve(approval: DiscountApproval, approver_user_id: str) -> DiscountApproval:
        """Approve a pending request using an identified approver."""
        if approval.status is not ApprovalStatus.PENDING:
            raise ValueError("only pending approvals can be approved")
        if not approver_user_id.strip():
            raise ValueError("approver_user_id is required")
        return DiscountApproval(
            original_discount_percent=approval.original_discount_percent,
            requested_discount_percent=approval.requested_discount_percent,
            reason=approval.reason,
            status=ApprovalStatus.APPROVED,
            approver_user_id=approver_user_id,
        )

    @staticmethod
    def reject(approval: DiscountApproval, approver_user_id: str) -> DiscountApproval:
        """Reject a pending request using an identified approver."""
        if approval.status is not ApprovalStatus.PENDING:
            raise ValueError("only pending approvals can be rejected")
        if not approver_user_id.strip():
            raise ValueError("approver_user_id is required")
        return DiscountApproval(
            original_discount_percent=approval.original_discount_percent,
            requested_discount_percent=approval.requested_discount_percent,
            reason=approval.reason,
            status=ApprovalStatus.REJECTED,
            approver_user_id=approver_user_id,
        )
