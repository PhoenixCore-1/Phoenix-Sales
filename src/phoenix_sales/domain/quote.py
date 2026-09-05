"""Quote domain model for Phoenix Sales V1.0."""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class QuoteStatus(str, Enum):
    DRAFT = "DRAFT"
    INTERNAL_REVIEW = "INTERNAL_REVIEW"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    NEGOTIATING = "NEGOTIATING"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class QuoteLine:
    """Commercial line captured on a quote."""

    item_id: str
    description: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    discount_percent: Decimal = Decimal("0")
    unit_cost: Decimal | None = None

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ValueError("item_id is required")
        if not self.description.strip():
            raise ValueError("description is required")
        if self.quantity <= 0:
            raise ValueError("quantity must be greater than zero")
        if not self.unit.strip():
            raise ValueError("unit is required")
        if self.unit_price < 0 or self.discount_percent < 0 or self.discount_percent > 100:
            raise ValueError("invalid price or discount")
        if self.unit_cost is not None and self.unit_cost < 0:
            raise ValueError("unit_cost cannot be negative")

    @property
    def net_unit_price(self) -> Decimal:
        return self.unit_price * (Decimal("1") - self.discount_percent / Decimal("100"))

    @property
    def line_total(self) -> Decimal:
        return self.net_unit_price * self.quantity


@dataclass
class Quote:
    """Controlled commercial offer derived from Sales context."""

    tenant_id: str
    customer_id: str
    opportunity_id: UUID
    quote_number: str
    currency: str
    valid_until: date
    id: UUID = field(default_factory=uuid4)
    contact_id: str | None = None
    project_id: str | None = None
    solution_id: UUID | None = None
    version: int = 1
    status: QuoteStatus = QuoteStatus.DRAFT
    payment_terms: str | None = None
    delivery_terms: str | None = None
    customer_reference: str | None = None
    internal_reference: str | None = None
    notes: str | None = None
    lines: list[QuoteLine] = field(default_factory=list)
    branch_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.customer_id.strip():
            raise ValueError("customer_id is required")
        if not self.quote_number.strip():
            raise ValueError("quote_number is required")
        if not self.currency.strip():
            raise ValueError("currency is required")
        if self.branch_id is not None and not self.branch_id.strip():
            raise ValueError("branch_id cannot be blank")
        if self.version < 1:
            raise ValueError("version must be at least 1")

    @property
    def is_locked(self) -> bool:
        return self.status in {
            QuoteStatus.APPROVED,
            QuoteStatus.SENT,
            QuoteStatus.ACCEPTED,
            QuoteStatus.REJECTED,
            QuoteStatus.EXPIRED,
            QuoteStatus.CANCELLED,
        }

    @property
    def total_value(self) -> Decimal:
        return sum((line.line_total for line in self.lines), Decimal("0"))

    def add_line(self, line: QuoteLine) -> None:
        if self.is_locked:
            raise ValueError("locked quote cannot be changed")
        self.lines.append(line)
        self.updated_at = datetime.now(timezone.utc)
