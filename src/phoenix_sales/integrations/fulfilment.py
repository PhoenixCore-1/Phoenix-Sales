"""Sales-to-Inventory fulfilment integration contract."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Mapping
from uuid import UUID


class FulfilmentRequestStatus(str, Enum):
    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    PROCESSING = "PROCESSING"
    PARTIALLY_ALLOCATED = "PARTIALLY_ALLOCATED"
    ALLOCATED = "ALLOCATED"
    BACKORDERED = "BACKORDERED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class FulfilmentLineStatus(str, Enum):
    REQUESTED = "REQUESTED"
    AVAILABLE = "AVAILABLE"
    PARTIALLY_ALLOCATED = "PARTIALLY_ALLOCATED"
    ALLOCATED = "ALLOCATED"
    BACKORDERED = "BACKORDERED"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"
    UNAVAILABLE = "UNAVAILABLE"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class FulfilmentLineRequest:
    sales_order_line_id: UUID
    item_id: str
    ordered_quantity: Decimal
    required_quantity: Decimal
    unit: str

    def __post_init__(self) -> None:
        if not self.sales_order_line_id:
            raise ValueError("Sales order line ID is required.")
        if not self.item_id or not str(self.item_id).strip():
            raise ValueError("Item ID is required.")
        if self.ordered_quantity <= 0:
            raise ValueError("Ordered quantity must be greater than zero.")
        if self.required_quantity <= 0:
            raise ValueError("Required quantity must be greater than zero.")
        if self.required_quantity > self.ordered_quantity:
            raise ValueError("Required quantity cannot exceed ordered quantity.")
        if not self.unit.strip():
            raise ValueError("Unit is required.")


@dataclass(frozen=True)
class FulfilmentRequest:
    tenant_id: str
    sales_order_id: UUID
    order_number: str
    lines: tuple[FulfilmentLineRequest, ...]
    commercial_branch_id: str | None = None
    requested_delivery_date: date | None = None
    delivery_site: str | None = None
    delivery_address: str | None = None
    priority: str | None = None
    correlation_id: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("Tenant ID is required.")
        if not self.sales_order_id:
            raise ValueError("Sales order ID is required.")
        if not self.order_number.strip():
            raise ValueError("Order number is required.")
        if not self.lines:
            raise ValueError("At least one fulfilment line is required.")
        if self.commercial_branch_id is not None and not self.commercial_branch_id.strip():
            raise ValueError("Commercial branch ID cannot be blank.")
        if self.correlation_id is not None and not self.correlation_id.strip():
            raise ValueError("Correlation ID cannot be blank.")


@dataclass(frozen=True)
class FulfilmentLineResult:
    sales_order_line_id: UUID
    item_id: str
    ordered_quantity: Decimal
    required_quantity: Decimal
    available_quantity: Decimal
    allocated_quantity: Decimal
    backorder_quantity: Decimal
    status: FulfilmentLineStatus
    fulfilled_quantity: Decimal = Decimal("0")
    expected_fulfilment_date: date | None = None
    inventory_reference: str | None = None
    warehouse_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.sales_order_line_id:
            raise ValueError("Sales order line ID is required.")
        if not self.item_id or not str(self.item_id).strip():
            raise ValueError("Item ID is required.")
        for name, value in (
            ("ordered quantity", self.ordered_quantity),
            ("required quantity", self.required_quantity),
            ("available quantity", self.available_quantity),
            ("allocated quantity", self.allocated_quantity),
            ("fulfilled quantity", self.fulfilled_quantity),
            ("backorder quantity", self.backorder_quantity),
        ):
            if value < 0:
                raise ValueError(f"{name.capitalize()} cannot be negative.")
        if self.required_quantity > self.ordered_quantity:
            raise ValueError("Required quantity cannot exceed ordered quantity.")
        if self.allocated_quantity > self.required_quantity:
            raise ValueError("Allocated quantity cannot exceed required quantity.")
        if self.fulfilled_quantity > self.ordered_quantity:
            raise ValueError("Fulfilled quantity cannot exceed ordered quantity.")
        if self.backorder_quantity > self.required_quantity:
            raise ValueError("Backorder quantity cannot exceed required quantity.")
        if self.fulfilled_quantity + self.backorder_quantity > self.ordered_quantity:
            raise ValueError("Fulfilled plus backorder quantity cannot exceed ordered quantity.")


@dataclass(frozen=True)
class FulfilmentResult:
    tenant_id: str
    sales_order_id: UUID
    status: FulfilmentRequestStatus
    lines: tuple[FulfilmentLineResult, ...]
    expected_fulfilment_date: date | None = None
    inventory_reference: str | None = None
    correlation_id: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("Tenant ID is required.")
        if not self.sales_order_id:
            raise ValueError("Sales order ID is required.")
        if not self.lines:
            raise ValueError("At least one fulfilment result line is required.")
        if self.correlation_id is not None and not self.correlation_id.strip():
            raise ValueError("Correlation ID cannot be blank.")


def build_fulfilment_request(
    *,
    tenant_id: str,
    sales_order_id: UUID,
    order_number: str,
    lines: tuple[FulfilmentLineRequest, ...],
    commercial_branch_id: str | None = None,
    requested_delivery_date: date | None = None,
    delivery_site: str | None = None,
    delivery_address: str | None = None,
    priority: str | None = None,
    correlation_id: str | None = None,
    metadata: Mapping[str, str] | None = None,
) -> FulfilmentRequest:
    return FulfilmentRequest(
        tenant_id=tenant_id,
        sales_order_id=sales_order_id,
        order_number=order_number,
        lines=lines,
        commercial_branch_id=commercial_branch_id,
        requested_delivery_date=requested_delivery_date,
        delivery_site=delivery_site,
        delivery_address=delivery_address,
        priority=priority,
        correlation_id=correlation_id,
        metadata={} if metadata is None else dict(metadata),
    )
