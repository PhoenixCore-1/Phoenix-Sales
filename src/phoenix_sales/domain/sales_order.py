"""Sales Order domain model for Phoenix Sales V1.0."""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class SalesOrderStatus(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    IN_PROCESS = "IN_PROCESS"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"
    CLOSED = "CLOSED"
    ON_HOLD = "ON_HOLD"
    CANCELLED = "CANCELLED"
    BACKORDER = "BACKORDER"
    PARTIALLY_CANCELLED = "PARTIALLY_CANCELLED"


@dataclass(frozen=True)
class SalesOrderLine:
    """Commercial line committed on a Sales Order."""

    item_id: str
    description: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    discount_percent: Decimal = Decimal("0")
    ordered_quantity: Decimal | None = None
    allocated_quantity: Decimal = Decimal("0")
    fulfilled_quantity: Decimal = Decimal("0")
    backorder_quantity: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ValueError("item_id is required")
        if not self.description.strip():
            raise ValueError("description is required")
        if not self.unit.strip():
            raise ValueError("unit is required")
        if self.quantity <= 0:
            raise ValueError("quantity must be greater than zero")
        if self.unit_price < 0:
            raise ValueError("unit_price cannot be negative")
        if self.discount_percent < 0 or self.discount_percent > 100:
            raise ValueError("discount_percent must be between 0 and 100")
        ordered = self.ordered_quantity if self.ordered_quantity is not None else self.quantity
        if ordered != self.quantity:
            raise ValueError("ordered_quantity must match quantity in V1")
        if min(self.allocated_quantity, self.fulfilled_quantity, self.backorder_quantity) < 0:
            raise ValueError("fulfilment quantities cannot be negative")
        if self.fulfilled_quantity > self.quantity or self.allocated_quantity > self.quantity:
            raise ValueError("fulfilment quantities cannot exceed ordered quantity")

    @property
    def net_unit_price(self) -> Decimal:
        return self.unit_price * (Decimal("1") - self.discount_percent / Decimal("100"))

    @property
    def line_total(self) -> Decimal:
        return self.net_unit_price * self.quantity


@dataclass
class SalesOrder:
    """Authorised customer commitment derived from an accepted quote."""

    tenant_id: str
    customer_id: str
    order_number: str
    currency: str
    order_date: date
    id: UUID = field(default_factory=uuid4)
    quote_id: UUID | None = None
    quote_version: int | None = None
    opportunity_id: UUID | None = None
    contact_id: str | None = None
    project_id: str | None = None
    solution_id: UUID | None = None
    branch_id: str | None = None
    status: SalesOrderStatus = SalesOrderStatus.DRAFT
    payment_terms: str | None = None
    delivery_terms: str | None = None
    customer_reference: str | None = None
    internal_reference: str | None = None
    notes: str | None = None
    lines: list[SalesOrderLine] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.customer_id.strip():
            raise ValueError("customer_id is required")
        if not self.order_number.strip():
            raise ValueError("order_number is required")
        if not self.currency.strip():
            raise ValueError("currency is required")
        if self.quote_version is not None and self.quote_version < 1:
            raise ValueError("quote_version must be at least 1")
        if self.branch_id is not None and not self.branch_id.strip():
            raise ValueError("branch_id cannot be blank")
        if self.quote_id is not None and self.quote_version is None:
            raise ValueError("quote_version is required when quote_id is supplied")

    @property
    def is_locked(self) -> bool:
        return self.status in {
            SalesOrderStatus.CONFIRMED,
            SalesOrderStatus.IN_PROCESS,
            SalesOrderStatus.PARTIALLY_FULFILLED,
            SalesOrderStatus.FULFILLED,
            SalesOrderStatus.CLOSED,
            SalesOrderStatus.CANCELLED,
            SalesOrderStatus.PARTIALLY_CANCELLED,
        }

    @property
    def total_value(self) -> Decimal:
        return sum((line.line_total for line in self.lines), Decimal("0"))

    def add_line(self, line: SalesOrderLine) -> None:
        if self.is_locked:
            raise ValueError("locked sales order cannot be changed")
        self.lines.append(line)
        self.updated_at = datetime.now(timezone.utc)
