"""Returns, cancellations and credits domain for Phoenix Sales V1.0."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class CommercialAction(str, Enum):
    CANCELLATION = "CANCELLATION"
    RETURN = "RETURN"
    CREDIT = "CREDIT"


class ReturnReason(str, Enum):
    WRONG_PRODUCT = "WRONG_PRODUCT"
    WRONG_QUANTITY = "WRONG_QUANTITY"
    DAMAGED = "DAMAGED"
    DEFECTIVE = "DEFECTIVE"
    CUSTOMER_ERROR = "CUSTOMER_ERROR"
    DUPLICATE = "DUPLICATE"
    SPECIFICATION = "SPECIFICATION"
    WARRANTY = "WARRANTY"
    QUALITY = "QUALITY"
    SALES_ERROR = "SALES_ERROR"
    WAREHOUSE_PICKING_ERROR = "WAREHOUSE_PICKING_ERROR"
    DELIVERY_ERROR = "DELIVERY_ERROR"
    OTHER = "OTHER"


class RequestStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    AUTHORISED = "AUTHORISED"
    RECEIVED = "RECEIVED"
    INSPECTING = "INSPECTING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CreditStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUBMITTED_TO_SAGE = "SUBMITTED_TO_SAGE"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class CancellationRequest:
    tenant_id: str
    sales_order_id: UUID
    reason: str
    quantity: Decimal
    id: UUID = field(default_factory=uuid4)
    status: RequestStatus = RequestStatus.REQUESTED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.sales_order_id:
            raise ValueError("tenant and Sales Order are required")
        if not self.reason.strip():
            raise ValueError("cancellation reason is required")
        if self.quantity <= 0:
            raise ValueError("cancellation quantity must be greater than zero")


@dataclass(frozen=True)
class ReturnRequest:
    tenant_id: str
    sales_order_id: UUID
    reason: ReturnReason
    quantity: Decimal
    id: UUID = field(default_factory=uuid4)
    status: RequestStatus = RequestStatus.REQUESTED
    inventory_reference: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.sales_order_id:
            raise ValueError("tenant and Sales Order are required")
        if self.quantity <= 0:
            raise ValueError("return quantity must be greater than zero")


@dataclass(frozen=True)
class CreditRequest:
    tenant_id: str
    sales_order_id: UUID
    amount: Decimal
    reason: str
    id: UUID = field(default_factory=uuid4)
    return_request_id: UUID | None = None
    status: CreditStatus = CreditStatus.REQUESTED
    sage_reference: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.tenant_id.strip() or not self.sales_order_id:
            raise ValueError("tenant and Sales Order are required")
        if self.amount <= 0:
            raise ValueError("credit amount must be greater than zero")
        if not self.reason.strip():
            raise ValueError("credit reason is required")


class ReturnFlow:
    """Pure Sales-side lifecycle helpers; physical handling remains Inventory-owned."""

    @staticmethod
    def validate_transition(current: RequestStatus, target: RequestStatus) -> None:
        allowed = {
            RequestStatus.REQUESTED: {RequestStatus.APPROVAL_REQUIRED, RequestStatus.APPROVED, RequestStatus.REJECTED, RequestStatus.CANCELLED},
            RequestStatus.APPROVAL_REQUIRED: {RequestStatus.APPROVED, RequestStatus.REJECTED, RequestStatus.CANCELLED},
            RequestStatus.APPROVED: {RequestStatus.AUTHORISED, RequestStatus.CANCELLED},
            RequestStatus.AUTHORISED: {RequestStatus.RECEIVED, RequestStatus.CANCELLED},
            RequestStatus.RECEIVED: {RequestStatus.INSPECTING, RequestStatus.COMPLETED},
            RequestStatus.INSPECTING: {RequestStatus.COMPLETED},
        }
        if target not in allowed.get(current, set()):
            raise ValueError(f"invalid return transition: {current.value} -> {target.value}")
