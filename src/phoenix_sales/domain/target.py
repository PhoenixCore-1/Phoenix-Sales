"""Sales target domain model for Phoenix Sales V1.0."""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class TargetMetric(str, Enum):
    REVENUE = "REVENUE"
    GROSS_PROFIT = "GROSS_PROFIT"
    MARGIN = "MARGIN"
    UNITS = "UNITS"
    NEW_CUSTOMERS = "NEW_CUSTOMERS"
    OPPORTUNITIES = "OPPORTUNITIES"
    ORDERS = "ORDERS"
    QUOTE_CONVERSION = "QUOTE_CONVERSION"


class TargetScopeType(str, Enum):
    COMPANY = "COMPANY"
    REGION = "REGION"
    BRANCH = "BRANCH"
    TEAM = "TEAM"
    SALESPERSON = "SALESPERSON"
    TERRITORY = "TERRITORY"
    PRODUCT = "PRODUCT"
    PRODUCT_CATEGORY = "PRODUCT_CATEGORY"
    CUSTOMER_SEGMENT = "CUSTOMER_SEGMENT"


class TargetStatus(str, Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


@dataclass
class SalesTarget:
    """An approved or planned commercial target for a defined period and scope."""

    tenant_id: str
    metric: TargetMetric
    scope_type: TargetScopeType
    scope_id: str
    period_start: date
    period_end: date
    target_value: Decimal
    currency: str | None = None
    owner_id: str | None = None
    id: UUID = field(default_factory=uuid4)
    version: int = 1
    status: TargetStatus = TargetStatus.DRAFT
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.scope_id.strip():
            raise ValueError("scope_id is required")
        if self.period_end < self.period_start:
            raise ValueError("period_end cannot be before period_start")
        if self.target_value < 0:
            raise ValueError("target_value cannot be negative")
        if self.version < 1:
            raise ValueError("version must be at least 1")
        if self.currency is not None and not self.currency.strip():
            raise ValueError("currency cannot be blank")
        if self.owner_id is not None and not self.owner_id.strip():
            raise ValueError("owner_id cannot be blank")

        count_metrics = {
            TargetMetric.REVENUE,
            TargetMetric.GROSS_PROFIT,
            TargetMetric.MARGIN,
            TargetMetric.UNITS,
            TargetMetric.NEW_CUSTOMERS,
            TargetMetric.OPPORTUNITIES,
            TargetMetric.ORDERS,
            TargetMetric.QUOTE_CONVERSION,
        }
        if self.metric in {TargetMetric.REVENUE, TargetMetric.GROSS_PROFIT} and not self.currency:
            raise ValueError("currency is required for monetary targets")
        if self.metric == TargetMetric.MARGIN and not Decimal("0") <= self.target_value <= Decimal("100"):
            raise ValueError("margin target must be between 0 and 100")
        if self.metric == TargetMetric.QUOTE_CONVERSION and not Decimal("0") <= self.target_value <= Decimal("100"):
            raise ValueError("quote conversion target must be between 0 and 100")

    @property
    def is_locked(self) -> bool:
        return self.status in {
            TargetStatus.APPROVED,
            TargetStatus.ACTIVE,
            TargetStatus.CLOSED,
            TargetStatus.CANCELLED,
        }

    def approve(self, user_id: str) -> None:
        if self.status != TargetStatus.DRAFT:
            raise ValueError("only draft targets can be approved")
        if not user_id.strip():
            raise ValueError("approver is required")
        self.status = TargetStatus.APPROVED
        self.approved_by = user_id
        self.approved_at = datetime.now(timezone.utc)
        self.updated_at = self.approved_at

    def activate(self) -> None:
        if self.status != TargetStatus.APPROVED:
            raise ValueError("only approved targets can be activated")
        self.status = TargetStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)

    def close(self) -> None:
        if self.status != TargetStatus.ACTIVE:
            raise ValueError("only active targets can be closed")
        self.status = TargetStatus.CLOSED
        self.updated_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        if self.status not in {TargetStatus.DRAFT, TargetStatus.APPROVED}:
            raise ValueError("only draft or approved targets can be cancelled")
        self.status = TargetStatus.CANCELLED
        self.updated_at = datetime.now(timezone.utc)
