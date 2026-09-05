"""Sales-side orchestration for Inventory fulfilment."""

from datetime import date, datetime, timezone
from typing import Protocol
from uuid import UUID, uuid5

from phoenix_sales.api.contracts import RequestContext
from phoenix_sales.domain.sales_order import SalesOrder, SalesOrderLine, SalesOrderStatus
from phoenix_sales.domain.sales_order_lifecycle import validate_transition
from phoenix_sales.integrations.fulfilment import (
    FulfilmentLineRequest,
    FulfilmentRequest,
    FulfilmentResult,
    build_fulfilment_request,
)
from phoenix_sales.persistence.sales_order_repository import SalesOrderRepository


LINE_NAMESPACE = UUID("6d8f8e6e-8a7d-4b4f-a8f2-7d0d8f1f2e91")


class InventoryFulfilmentPort(Protocol):
    """Port implemented by the Inventory integration adapter."""

    def submit(self, request: FulfilmentRequest) -> FulfilmentResult:
        ...


def sales_order_line_reference(order_id: UUID, line_index: int) -> UUID:
    """Return a stable integration reference for a Sales Order line."""
    if line_index < 0:
        raise ValueError("line index cannot be negative")
    return uuid5(LINE_NAMESPACE, f"{order_id}:line:{line_index}")


class FulfilmentOrchestrationService:
    """Translate Sales Orders into Inventory requests and apply results."""

    FULFIL_PERMISSION = "sales.order.fulfil"

    def __init__(
        self,
        context: RequestContext,
        repository: SalesOrderRepository,
        inventory: InventoryFulfilmentPort,
    ) -> None:
        self._context = context
        self._repository = repository
        self._inventory = inventory
        self._processed_correlations: set[str] = set()

    def request_fulfilment(
        self,
        order_id: UUID,
        *,
        correlation_id: str | None = None,
        priority: str | None = None,
        requested_delivery_date: date | None = None,
        delivery_site: str | None = None,
        delivery_address: str | None = None,
    ) -> FulfilmentResult:
        self._require_permission()
        order = self._get(order_id)
        if order.status not in {
            SalesOrderStatus.CONFIRMED,
            SalesOrderStatus.IN_PROCESS,
            SalesOrderStatus.PARTIALLY_FULFILLED,
            SalesOrderStatus.BACKORDER,
        }:
            raise ValueError("sales order is not eligible for fulfilment")

        correlation = correlation_id or str(order.id)
        if correlation in self._processed_correlations:
            raise ValueError("fulfilment request already processed for correlation ID")

        lines = []
        for index, line in enumerate(order.lines):
            remaining = line.quantity - line.fulfilled_quantity - line.allocated_quantity
            if remaining <= 0:
                continue
            lines.append(
                FulfilmentLineRequest(
                    sales_order_line_id=sales_order_line_reference(order.id, index),
                    item_id=line.item_id,
                    ordered_quantity=line.quantity,
                    required_quantity=remaining,
                    unit=line.unit,
                )
            )
        if not lines:
            raise ValueError("sales order has no outstanding fulfilment requirement")

        request = build_fulfilment_request(
            tenant_id=order.tenant_id,
            sales_order_id=order.id,
            order_number=order.order_number,
            lines=tuple(lines),
            commercial_branch_id=order.branch_id,
            requested_delivery_date=requested_delivery_date,
            delivery_site=delivery_site,
            delivery_address=delivery_address,
            priority=priority,
            correlation_id=correlation,
            metadata={"source": "phoenix-sales"},
        )
        result = self._inventory.submit(request)
        self.apply_result(result)
        self._processed_correlations.add(correlation)
        return result

    def apply_result(self, result: FulfilmentResult) -> SalesOrder:
        """Apply Inventory's authoritative fulfilment quantities and status."""
        self._require_permission()
        if result.tenant_id != self._context.tenant.tenant_id:
            raise PermissionError("tenant access denied")
        order = self._get(result.sales_order_id)
        if result.correlation_id and result.correlation_id in self._processed_correlations:
            raise ValueError("fulfilment result already processed for correlation ID")

        references = {
            sales_order_line_reference(order.id, index): (index, line)
            for index, line in enumerate(order.lines)
        }
        result_refs = {line.sales_order_line_id for line in result.lines}
        if not result_refs.issubset(references):
            raise ValueError("fulfilment result contains an unknown Sales Order line")

        updated_lines = list(order.lines)
        for result_line in result.lines:
            index, current = references[result_line.sales_order_line_id]
            if str(result_line.item_id) != str(current.item_id):
                raise ValueError("fulfilment result item does not match the Sales Order line")
            if result_line.ordered_quantity != current.quantity:
                raise ValueError("fulfilment result ordered quantity does not match the Sales Order")
            if result_line.fulfilled_quantity > current.quantity:
                raise ValueError("fulfilled quantity exceeds Sales Order quantity")
            updated_lines[index] = SalesOrderLine(
                item_id=current.item_id,
                description=current.description,
                quantity=current.quantity,
                unit=current.unit,
                unit_price=current.unit_price,
                discount_percent=current.discount_percent,
                ordered_quantity=current.ordered_quantity,
                allocated_quantity=result_line.allocated_quantity,
                fulfilled_quantity=result_line.fulfilled_quantity,
                backorder_quantity=result_line.backorder_quantity,
            )

        order.lines = updated_lines
        target = self._derive_status(order)
        self._transition(order, target)
        order.updated_at = datetime.now(timezone.utc)
        saved = self._repository.save(order)
        if result.correlation_id:
            self._processed_correlations.add(result.correlation_id)
        return saved

    @staticmethod
    def _derive_status(order: SalesOrder) -> SalesOrderStatus:
        if all(line.fulfilled_quantity >= line.quantity for line in order.lines):
            return SalesOrderStatus.FULFILLED
        if all(
            line.fulfilled_quantity == 0
            and line.backorder_quantity >= line.quantity
            for line in order.lines
        ):
            return SalesOrderStatus.BACKORDER
        if any(line.fulfilled_quantity > 0 for line in order.lines):
            return SalesOrderStatus.PARTIALLY_FULFILLED
        return SalesOrderStatus.IN_PROCESS

    @staticmethod
    def _transition(order: SalesOrder, target: SalesOrderStatus) -> None:
        if target == order.status:
            return
        if target is SalesOrderStatus.FULFILLED and order.status is SalesOrderStatus.CONFIRMED:
            validate_transition(order.status, SalesOrderStatus.IN_PROCESS)
            order.status = SalesOrderStatus.IN_PROCESS
        validate_transition(order.status, target)
        order.status = target

    def _get(self, order_id: UUID) -> SalesOrder:
        order = self._repository.get(self._context.tenant.tenant_id, order_id)
        if order is None:
            raise LookupError("sales order not found")
        return order

    def _require_permission(self) -> None:
        if not self._context.has_permission(self.FULFIL_PERMISSION):
            raise PermissionError(f"permission denied: {self.FULFIL_PERMISSION}")
