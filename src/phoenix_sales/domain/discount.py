"""Discount authority and approval domain for Phoenix Sales V1.0."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class DiscountStatus(str, Enum):
    WITHIN_AUTHORITY = "WITHIN_AUTHORITY"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"


class ApprovalStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class DiscountAuthority:
    """Maximum discount a salesperson may apply without approval."""

    max_discount_percent: Decimal

    def __post_init__(self) -> None:
        if not Decimal("0") <= self.max_discount_percent <= Decimal("100"):
            raise ValueError("max_discount_percent must be between 0 and 100")

    def evaluate(self, discount_percent: Decimal) -> DiscountStatus:
        discount_percent = Decimal(discount_percent)
        if not Decimal("0") <= discount_percent <= Decimal("100"):
            raise ValueError("discount_percent must be between 0 and 100")
        if discount_percent <= self.max_discount_percent:
            return DiscountStatus.WITHIN_AUTHORITY
        return DiscountStatus.APPROVAL_REQUIRED


@dataclass(frozen=True)
class DiscountApproval:
    """Immutable record of a requested discount approval decision."""

    original_discount_percent: Decimal
    requested_discount_percent: Decimal
    reason: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    approver_user_id: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("original_discount_percent", self.original_discount_percent),
            ("requested_discount_percent", self.requested_discount_percent),
        ):
            if not Decimal("0") <= value <= Decimal("100"):
                raise ValueError(f"{name} must be between 0 and 100")
        if not self.reason.strip():
            raise ValueError("reason is required")
        if self.status in {ApprovalStatus.APPROVED, ApprovalStatus.REJECTED} and not self.approver_user_id:
            raise ValueError("approver_user_id is required for a final decision")
