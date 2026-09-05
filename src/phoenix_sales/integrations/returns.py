"""Integration contracts for Sales returns and Sage credits."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class InventoryReturnAuthorisation:
    tenant_id: str
    return_request_id: UUID
    sales_order_id: UUID
    item_id: str
    quantity: Decimal
    reason: str
    correlation_id: str


@dataclass(frozen=True)
class InventoryReturnResult:
    tenant_id: str
    return_request_id: UUID
    inventory_reference: str
    received_quantity: Decimal
    disposition: str
    correlation_id: str


@dataclass(frozen=True)
class SageCreditRequest:
    tenant_id: str
    credit_request_id: UUID
    sales_order_id: UUID
    amount: Decimal
    reason: str
    correlation_id: str


@dataclass(frozen=True)
class SageCreditResult:
    tenant_id: str
    credit_request_id: UUID
    status: str
    sage_reference: str | None
    correlation_id: str


class InventoryReturnPort:
    """Interface boundary; implementation belongs to Inventory."""

    def authorise_return(self, request: InventoryReturnAuthorisation) -> InventoryReturnResult:
        raise NotImplementedError


class SageCreditPort:
    """Interface boundary; implementation belongs to the Sage integration."""

    def submit_credit(self, request: SageCreditRequest) -> SageCreditResult:
        raise NotImplementedError
