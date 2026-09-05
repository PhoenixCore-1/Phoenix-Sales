"""Application service for Phoenix Sales Orders V1.0."""

from datetime import datetime, timezone
from uuid import UUID

from phoenix_sales.api.contracts import RequestContext
from phoenix_sales.domain.sales_order import SalesOrder, SalesOrderLine, SalesOrderStatus
from phoenix_sales.domain.sales_order_lifecycle import validate_transition
from phoenix_sales.persistence.sales_order_repository import SalesOrderRepository


class SalesOrderService:
    """Coordinate Sales Order commands while enforcing platform permissions."""

    CREATE_PERMISSION = "sales.order.create"
    READ_PERMISSION = "sales.order.read"
    UPDATE_PERMISSION = "sales.order.update"
    TRANSITION_PERMISSION = "sales.order.transition"

    def __init__(self, context: RequestContext, repository: SalesOrderRepository) -> None:
        self._context = context
        self._repository = repository

    def create_order(self, order: SalesOrder) -> SalesOrder:
        self._require(self.CREATE_PERMISSION)
        self._require_tenant(order)
        if not order.lines:
            raise ValueError("sales order must contain at least one line")
        existing = self._repository.get(self._context.tenant.tenant_id, order.id)
        if existing is not None:
            raise ValueError("sales order already exists")
        return self._repository.save(order)

    def get_order(self, order_id: UUID) -> SalesOrder | None:
        self._require(self.READ_PERMISSION)
        return self._repository.get(self._context.tenant.tenant_id, order_id)

    def update_order(self, order_id: UUID, **changes: object) -> SalesOrder:
        self._require(self.UPDATE_PERMISSION)
        order = self._get(order_id)
        if order.is_locked:
            raise ValueError("locked sales order cannot be changed")
        protected = {"id", "tenant_id", "order_number", "status", "created_at", "updated_at", "lines"}
        invalid = set(changes) & protected
        if invalid:
            raise ValueError(f"protected sales order fields cannot be changed: {sorted(invalid)}")
        for field_name, value in changes.items():
            if not hasattr(order, field_name):
                raise ValueError(f"unknown sales order field: {field_name}")
            setattr(order, field_name, value)
        order.updated_at = datetime.now(timezone.utc)
        return self._repository.save(order)

    def add_line(self, order_id: UUID, line: SalesOrderLine) -> SalesOrder:
        self._require(self.UPDATE_PERMISSION)
        order = self._get(order_id)
        order.add_line(line)
        return self._repository.save(order)

    def transition(self, order_id: UUID, target: SalesOrderStatus) -> SalesOrder:
        self._require(self.TRANSITION_PERMISSION)
        order = self._get(order_id)
        validate_transition(order.status, target)
        if target is SalesOrderStatus.CONFIRMED and not order.lines:
            raise ValueError("sales order must contain at least one line before confirmation")
        order.status = target
        order.updated_at = datetime.now(timezone.utc)
        return self._repository.save(order)

    def _get(self, order_id: UUID) -> SalesOrder:
        order = self._repository.get(self._context.tenant.tenant_id, order_id)
        if order is None:
            raise LookupError("sales order not found")
        return order

    def _require_tenant(self, order: SalesOrder) -> None:
        if order.tenant_id != self._context.tenant.tenant_id:
            raise PermissionError("tenant access denied")

    def _require(self, permission: str) -> None:
        if not self._context.has_permission(permission):
            raise PermissionError(f"permission denied: {permission}")
