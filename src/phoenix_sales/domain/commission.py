"""Basic commission domain for Phoenix Sales V1.0."""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class CommissionPlanType(str, Enum):
    FIXED_PERCENTAGE = "FIXED_PERCENTAGE"
    TIERED = "TIERED"
    PROGRESSIVE = "PROGRESSIVE"
    BASE_PLUS_ACCELERATOR = "BASE_PLUS_ACCELERATOR"


class CommissionStatus(str, Enum):
    DRAFT = "DRAFT"
    CALCULATED = "CALCULATED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"
    ADJUSTED = "ADJUSTED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class CommissionTier:
    threshold: Decimal
    rate_percent: Decimal

    def __post_init__(self) -> None:
        if self.threshold < 0:
            raise ValueError("threshold cannot be negative")
        if not 0 <= self.rate_percent <= 100:
            raise ValueError("rate_percent must be between 0 and 100")


@dataclass
class CommissionPlan:
    tenant_id: str
    name: str
    plan_type: CommissionPlanType
    period_start: date
    period_end: date
    base_rate_percent: Decimal = Decimal("0")
    tiers: list[CommissionTier] = field(default_factory=list)
    accelerator_rate_percent: Decimal = Decimal("0")
    threshold: Decimal = Decimal("0")
    id: UUID = field(default_factory=uuid4)
    active: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.name.strip():
            raise ValueError("tenant_id and name are required")
        if self.period_end < self.period_start:
            raise ValueError("period_end cannot be before period_start")
        if not 0 <= self.base_rate_percent <= 100:
            raise ValueError("base rate must be between 0 and 100")
        if not 0 <= self.accelerator_rate_percent <= 100:
            raise ValueError("accelerator rate must be between 0 and 100")
        if self.threshold < 0:
            raise ValueError("threshold cannot be negative")
        if any(self.tiers[i].threshold > self.tiers[i + 1].threshold for i in range(len(self.tiers) - 1)):
            raise ValueError("commission tiers must be ordered by threshold")

    def calculate(self, basis: Decimal) -> Decimal:
        if basis < 0:
            raise ValueError("commission basis cannot be negative")
        if self.plan_type is CommissionPlanType.FIXED_PERCENTAGE:
            return basis * self.base_rate_percent / Decimal("100")
        if self.plan_type is CommissionPlanType.BASE_PLUS_ACCELERATOR:
            rate = self.base_rate_percent + (self.accelerator_rate_percent if basis >= self.threshold else Decimal("0"))
            return basis * rate / Decimal("100")
        if not self.tiers:
            raise ValueError("tiered plans require tiers")
        if self.plan_type is CommissionPlanType.TIERED:
            rate = max((tier.rate_percent for tier in self.tiers if basis >= tier.threshold), default=Decimal("0"))
            return basis * rate / Decimal("100")
        remaining = basis
        total = Decimal("0")
        ordered = sorted(self.tiers, key=lambda tier: tier.threshold)
        for index, tier in enumerate(ordered):
            upper = ordered[index + 1].threshold if index + 1 < len(ordered) else basis
            amount = max(min(remaining, upper - tier.threshold), Decimal("0")) if basis > tier.threshold else Decimal("0")
            total += amount * tier.rate_percent / Decimal("100")
        return total


@dataclass(frozen=True)
class CommissionAdjustment:
    amount: Decimal
    reason: str
    reference: str | None = None

    def __post_init__(self) -> None:
        if self.amount == 0:
            raise ValueError("adjustment amount cannot be zero")
        if not self.reason.strip():
            raise ValueError("adjustment reason is required")


@dataclass
class CommissionEntry:
    tenant_id: str
    salesperson_id: str
    plan_id: UUID
    period_start: date
    period_end: date
    basis: Decimal
    commission_amount: Decimal
    id: UUID = field(default_factory=uuid4)
    status: CommissionStatus = CommissionStatus.DRAFT
    adjustments: list[CommissionAdjustment] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.salesperson_id.strip():
            raise ValueError("tenant_id and salesperson_id are required")
        if self.basis < 0 or self.commission_amount < 0:
            raise ValueError("basis and commission amount cannot be negative")
        if self.period_end < self.period_start:
            raise ValueError("period_end cannot be before period_start")

    @property
    def adjusted_amount(self) -> Decimal:
        return self.commission_amount + sum((a.amount for a in self.adjustments), Decimal("0"))
